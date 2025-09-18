from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import Space, SpaceMember
from .forms import SpaceCreateForm, JoinSpaceForm, SpaceUpdateForm, RegenerateInviteCodeForm, SpaceSettingsForm
from .utils import SpaceContextManager, get_space_context
# Force reload for new templates


@login_required
def space_test(request):
    """Test view to debug spaces functionality"""
    user_spaces = Space.objects.filter(
        spacemember__user=request.user,
        spacemember__is_active=True,
        is_active=True
    ).select_related('created_by').prefetch_related('spacemember_set__user')

    # Add member counts and roles
    spaces_data = []
    for space in user_spaces:
        try:
            member = space.spacemember_set.get(user=request.user, is_active=True)
            spaces_data.append({
                'space': space,
                'role': member.role,
                'member_count': space.member_count,
                'is_owner': member.role == 'owner',
            })
        except SpaceMember.DoesNotExist:
            continue

    context = {
        'spaces_data': spaces_data,
        'total_spaces': len(spaces_data),
    }
    return render(request, 'spaces/test.html', context)


@login_required
def space_list(request):
    """List all spaces the user is a member of"""
    user_spaces = Space.objects.filter(
        spacemember__user=request.user,
        spacemember__is_active=True,
        is_active=True
    ).select_related('created_by').prefetch_related('spacemember_set__user')

    # Add member counts and roles
    spaces_data = []
    for space in user_spaces:
        try:
            member = space.spacemember_set.get(user=request.user, is_active=True)
            spaces_data.append({
                'space': space,
                'role': member.role,
                'member_count': space.member_count,
                'is_owner': member.role == 'owner',
            })
        except SpaceMember.DoesNotExist:
            # Skip spaces where user is not an active member
            continue

    # Calculate owned and joined counts
    owned_count = sum(1 for item in spaces_data if item['is_owner'])
    joined_count = len(spaces_data) - owned_count

    context = {
        'spaces_data': spaces_data,
        'total_spaces': len(spaces_data),
        'owned_count': owned_count,
        'joined_count': joined_count,
    }
    return render(request, 'spaces/list.html', context)


@login_required
@csrf_protect
def space_create(request):
    """Create a new space"""
    # Check space limit per user (max 10 owned spaces)
    owned_spaces_count = Space.objects.filter(
        spacemember__user=request.user,
        spacemember__role='owner',
        spacemember__is_active=True,
        is_active=True
    ).count()

    if owned_spaces_count >= 10:
        messages.error(
            request,
            'You have reached the maximum limit of 10 owned spaces. '
            'Please archive or delete some spaces before creating new ones.'
        )
        return redirect('spaces:list')

    if request.method == 'POST':
        form = SpaceCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    space = form.save(user=request.user)
                    messages.success(
                        request,
                        f'Space "{space.name}" created successfully! '
                        f'Share invite code: {space.invite_code}'
                    )
                    return redirect('spaces:detail', pk=space.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = SpaceCreateForm()

    context = {
        'form': form,
        'page_title': 'Create New Space',
    }
    return render(request, 'spaces/create.html', context)


@login_required
@csrf_protect
def space_join(request):
    """Join a space using invite code"""
    # Check total spaces limit per user (max 20 total spaces - owned + joined)
    total_spaces_count = Space.objects.filter(
        spacemember__user=request.user,
        spacemember__is_active=True,
        is_active=True
    ).count()

    if total_spaces_count >= 20:
        messages.error(
            request,
            'You have reached the maximum limit of 20 spaces. '
            'Please leave some spaces before joining new ones.'
        )
        return redirect('spaces:list')

    if request.method == 'POST':
        form = JoinSpaceForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    member, space = form.join_space(request.user)
                    messages.success(
                        request,
                        f'Successfully joined "{space.name}"! '
                        f'You are now a member of this space.'
                    )
                    return redirect('spaces:detail', pk=space.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = JoinSpaceForm()

    context = {
        'form': form,
        'page_title': 'Join Space',
    }
    return render(request, 'spaces/join.html', context)


@login_required
def space_detail(request, pk):
    """Show space details and members"""
    space = get_object_or_404(Space, pk=pk, is_active=True)

    # Check if user is a member
    try:
        user_member = space.spacemember_set.get(user=request.user, is_active=True)
    except SpaceMember.DoesNotExist:
        messages.error(request, 'You are not a member of this space.')
        return redirect('spaces:list')

    # Get all members
    members = space.spacemember_set.filter(is_active=True).select_related('user').order_by('role', 'joined_at')

    context = {
        'space': space,
        'user_member': user_member,
        'members': members,
        'is_owner': user_member.role == 'owner',
        'member_count': space.member_count,
        'can_invite': space.member_count < 10,
    }
    return render(request, 'spaces/detail.html', context)


@login_required
@csrf_protect
def space_update(request, pk):
    """Update space details (owner only)"""
    space = get_object_or_404(Space, pk=pk, is_active=True)

    # Check if user is owner
    try:
        user_member = space.spacemember_set.get(user=request.user, is_active=True)
        if user_member.role != 'owner':
            messages.error(request, 'Only space owners can update space details.')
            return redirect('spaces:detail', pk=space.pk)
    except SpaceMember.DoesNotExist:
        messages.error(request, 'You are not a member of this space.')
        return redirect('spaces:list')

    if request.method == 'POST':
        form = SpaceUpdateForm(request.POST, instance=space)
        if form.is_valid():
            form.save()
            messages.success(request, 'Space details updated successfully!')
            return redirect('spaces:detail', pk=space.pk)
    else:
        form = SpaceUpdateForm(instance=space)

    context = {
        'form': form,
        'space': space,
        'page_title': f'Update {space.name}',
    }
    return render(request, 'spaces/update.html', context)


@login_required
@csrf_protect
def regenerate_invite_code(request, pk):
    """Regenerate invite code for space (owner only)"""
    space = get_object_or_404(Space, pk=pk, is_active=True)

    # Check if user is owner
    try:
        user_member = space.spacemember_set.get(user=request.user, is_active=True)
        if user_member.role != 'owner':
            messages.error(request, 'Only space owners can regenerate invite codes.')
            return redirect('spaces:detail', pk=space.pk)
    except SpaceMember.DoesNotExist:
        messages.error(request, 'You are not a member of this space.')
        return redirect('spaces:list')

    if request.method == 'POST':
        form = RegenerateInviteCodeForm(request.POST)
        if form.is_valid():
            old_code = space.invite_code
            form.regenerate_code(space)
            messages.success(
                request,
                f'New invite code generated: {space.invite_code} '
                f'(old code {old_code} is no longer valid)'
            )
            return redirect('spaces:detail', pk=space.pk)
    else:
        form = RegenerateInviteCodeForm()

    context = {
        'form': form,
        'space': space,
        'current_code': space.invite_code,
        'page_title': 'Regenerate Invite Code',
    }
    return render(request, 'spaces/regenerate_code.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def leave_space(request, pk):
    """Leave a space (members only, not owner)"""
    space = get_object_or_404(Space, pk=pk, is_active=True)

    try:
        user_member = space.spacemember_set.get(user=request.user, is_active=True)

        if user_member.role == 'owner':
            messages.error(
                request,
                'Space owners cannot leave their space. '
                'Transfer ownership first or delete the space.'
            )
        else:
            user_member.is_active = False
            user_member.save()
            messages.success(request, f'You have left "{space.name}".')
            return redirect('spaces:list')

    except SpaceMember.DoesNotExist:
        messages.error(request, 'You are not a member of this space.')

    return redirect('spaces:detail', pk=space.pk)


@login_required
def space_members_api(request, pk):
    """API endpoint to get space members (for AJAX requests)"""
    space = get_object_or_404(Space, pk=pk, is_active=True)

    # Check if user is a member
    try:
        space.spacemember_set.get(user=request.user, is_active=True)
    except SpaceMember.DoesNotExist:
        return JsonResponse({'error': 'Access denied'}, status=403)

    members = space.spacemember_set.filter(is_active=True).select_related('user')
    members_data = []

    for member in members:
        members_data.append({
            'id': member.id,
            'username': member.user.username,
            'first_name': member.user.first_name,
            'last_name': member.user.last_name,
            'email': member.user.email,
            'role': member.role,
            'joined_at': member.joined_at.isoformat(),
        })

    return JsonResponse({
        'members': members_data,
        'member_count': len(members_data),
        'space_name': space.name,
        'invite_code': space.invite_code,
    })


@login_required
def switch_space(request, pk):
    """Switch to a different space context"""
    try:
        # Use SpaceContextManager to switch space
        space = SpaceContextManager.switch_space(request, pk)
        messages.success(request, f'Switched to "{space.name}" space.')

        # Redirect to dashboard of the new space
        return redirect('dashboard:home')

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('spaces:list')
    except Exception as e:
        messages.error(request, 'Unable to switch spaces. Please try again.')
        return redirect('spaces:list')


@login_required
def set_default_space(request, pk):
    """Set a space as the user's default space"""
    try:
        space = SpaceContextManager.set_default_space(request, pk)
        messages.success(request, f'Set "{space.name}" as your default space.')
        return redirect('dashboard:home')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('spaces:list')
    except Exception as e:
        messages.error(request, 'Unable to set default space. Please try again.')
        return redirect('spaces:list')


@login_required
def delete_space(request, pk):
    """Delete a space (owner only)"""
    try:
        space = get_object_or_404(Space, pk=pk, is_active=True)

        # Check if user is the owner
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=True)
            if user_member.role != 'owner':
                messages.error(request, 'Only space owners can delete spaces.')
                return redirect('spaces:detail', pk=space.pk)
        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not a member of this space.')
            return redirect('spaces:list')

        if request.method == 'POST':
            space_name = space.name

            # Check if this is the user's current space in session
            current_space_id = request.session.get('current_space_id')
            if current_space_id and int(current_space_id) == space.pk:
                # Clear current space from session
                request.session.pop('current_space_id', None)

            # Permanently delete the space
            space.is_active = False
            space.save()

            # Also deactivate all memberships
            space.spacemember_set.all().update(is_active=False)

            messages.success(request, f'Space "{space_name}" has been deleted permanently.')
            return redirect('spaces:list')

        # GET request - show confirmation page
        context = {
            'space': space,
            'member_count': space.member_count,
        }
        return render(request, 'spaces/delete.html', context)

    except Exception as e:
        messages.error(request, 'Unable to delete space. Please try again.')
        return redirect('spaces:list')


@login_required
@require_http_methods(["POST"])
@csrf_protect
def remove_member(request, pk, member_id):
    """Remove a member from space (owner only)"""
    try:
        space = get_object_or_404(Space, pk=pk, is_active=True)

        # Check if user is the owner
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=True)
            if user_member.role != 'owner':
                messages.error(request, 'Only space owners can remove members.')
                return redirect('spaces:detail', pk=space.pk)
        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not a member of this space.')
            return redirect('spaces:list')

        # Get the member to remove
        try:
            member_to_remove = space.spacemember_set.get(id=member_id, is_active=True)

            # Prevent owner from removing themselves
            if member_to_remove.user == request.user:
                messages.error(request, 'You cannot remove yourself. Transfer ownership first or delete the space.')
                return redirect('spaces:detail', pk=space.pk)

            # Prevent removing another owner (if multiple owners existed)
            if member_to_remove.role == 'owner':
                messages.error(request, 'Cannot remove another owner. Transfer ownership first.')
                return redirect('spaces:detail', pk=space.pk)

            # Remove the member (soft delete)
            member_name = member_to_remove.user.first_name or member_to_remove.user.username
            member_to_remove.is_active = False
            member_to_remove.save()

            messages.success(request, f'{member_name} has been removed from "{space.name}".')

        except SpaceMember.DoesNotExist:
            messages.error(request, 'Member not found or already removed.')

        return redirect('spaces:detail', pk=space.pk)

    except Exception as e:
        messages.error(request, 'Unable to remove member. Please try again.')
        return redirect('spaces:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def transfer_ownership(request, pk, member_id):
    """Transfer ownership to another member (owner only)"""
    try:
        space = get_object_or_404(Space, pk=pk, is_active=True)

        # Check if user is the owner
        try:
            current_owner = space.spacemember_set.get(user=request.user, is_active=True)
            if current_owner.role != 'owner':
                messages.error(request, 'Only space owners can transfer ownership.')
                return redirect('spaces:detail', pk=space.pk)
        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not a member of this space.')
            return redirect('spaces:list')

        # Get the new owner
        try:
            new_owner = space.spacemember_set.get(id=member_id, is_active=True)

            # Ensure it's not the same person
            if new_owner.user == request.user:
                messages.error(request, 'You cannot transfer ownership to yourself.')
                return redirect('spaces:detail', pk=space.pk)

            # Ensure it's not already an owner
            if new_owner.role == 'owner':
                messages.error(request, 'This member is already an owner.')
                return redirect('spaces:detail', pk=space.pk)

            with transaction.atomic():
                # Change current owner to member
                current_owner.role = 'member'
                current_owner.save()

                # Change new member to owner
                new_owner.role = 'owner'
                new_owner.save()

                # Update space created_by if needed (optional)
                space.created_by = new_owner.user
                space.save()

                new_owner_name = new_owner.user.first_name or new_owner.user.username
                messages.success(
                    request,
                    f'Ownership of "{space.name}" has been transferred to {new_owner_name}. '
                    f'You are now a regular member.'
                )

        except SpaceMember.DoesNotExist:
            messages.error(request, 'Member not found.')

        return redirect('spaces:detail', pk=space.pk)

    except Exception as e:
        messages.error(request, 'Unable to transfer ownership. Please try again.')
        return redirect('spaces:detail', pk=pk)


@login_required
def archive_space(request, pk):
    """Archive a space (owner only) - can be restored later"""
    try:
        space = get_object_or_404(Space, pk=pk, is_active=True)

        # Check if user is the owner
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=True)
            if user_member.role != 'owner':
                messages.error(request, 'Only space owners can archive spaces.')
                return redirect('spaces:detail', pk=space.pk)
        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not a member of this space.')
            return redirect('spaces:list')

        if request.method == 'POST':
            space_name = space.name

            # Check if this is the user's current space in session
            current_space_id = request.session.get('current_space_id')
            if current_space_id and int(current_space_id) == space.pk:
                # Clear current space from session
                request.session.pop('current_space_id', None)

            # Archive the space (preserves data)
            space.archive()

            # Also deactivate all memberships
            space.spacemember_set.all().update(is_active=False)

            messages.success(request, f'Space "{space_name}" has been archived successfully. You can restore it later if needed.')
            return redirect('spaces:list')

        # GET request - show confirmation page
        context = {
            'space': space,
            'member_count': space.member_count,
            'action': 'archive'
        }
        return render(request, 'spaces/archive.html', context)

    except Exception as e:
        messages.error(request, 'Unable to archive space. Please try again.')
        return redirect('spaces:list')


@login_required
@require_http_methods(["POST"])
@csrf_protect
def restore_space(request, pk):
    """Restore an archived space (owner only)"""
    try:
        # Look for archived spaces (is_active=False and archived_at is not None)
        space = get_object_or_404(Space, pk=pk, is_active=False, archived_at__isnull=False)

        # Check if user is the owner
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=False)
            if user_member.role != 'owner':
                messages.error(request, 'Only space owners can restore spaces.')
                return redirect('spaces:archived')
        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not a member of this space.')
            return redirect('spaces:archived')

        space_name = space.name

        # Restore the space
        space.unarchive()

        # Reactivate all memberships
        space.spacemember_set.all().update(is_active=True)

        messages.success(request, f'Space "{space_name}" has been restored successfully!')
        return redirect('spaces:detail', pk=space.pk)

    except Exception as e:
        messages.error(request, 'Unable to restore space. Please try again.')
        return redirect('spaces:archived')


@login_required
def archived_spaces(request):
    """List all archived spaces the user owned"""
    archived_spaces = Space.objects.filter(
        spacemember__user=request.user,
        spacemember__role='owner',
        spacemember__is_active=False,
        is_active=False,
        archived_at__isnull=False
    ).select_related('created_by').prefetch_related('spacemember_set__user')

    # Add member counts and archive dates
    spaces_data = []
    for space in archived_spaces:
        spaces_data.append({
            'space': space,
            'archived_date': space.archived_at,
            'member_count': space.spacemember_set.filter(is_active=False).count(),
        })

    context = {
        'spaces_data': spaces_data,
        'total_archived': len(spaces_data),
    }
    return render(request, 'spaces/archived.html', context)


@login_required
def space_settings(request, pk):
    """Configure space settings and approval rules (owner only)"""
    try:
        space = get_object_or_404(Space, pk=pk, is_active=True)

        # Check if user is the owner
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=True)
            if user_member.role != 'owner':
                messages.error(request, 'Only space owners can configure settings.')
                return redirect('spaces:detail', pk=space.pk)
        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not a member of this space.')
            return redirect('spaces:list')

        # Get or create space settings
        settings, created = space.settings, False
        if not hasattr(space, 'settings'):
            from .models import SpaceSettings
            settings = SpaceSettings.objects.create(space=space)
            created = True

        if request.method == 'POST':
            from .forms import SpaceSettingsForm
            form = SpaceSettingsForm(request.POST, instance=settings)

            if form.is_valid():
                form.save()
                messages.success(request, f'Settings for "{space.name}" have been updated successfully.')
                return redirect('spaces:settings', pk=space.pk)
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            from .forms import SpaceSettingsForm
            form = SpaceSettingsForm(instance=settings)

        # Get space member count for context
        member_count = space.member_count

        context = {
            'space': space,
            'settings': settings,
            'form': form,
            'member_count': member_count,
            'is_new_settings': created,
        }
        return render(request, 'spaces/settings.html', context)

    except Exception as e:
        messages.error(request, 'Unable to load space settings. Please try again.')
        return redirect('spaces:detail', pk=pk)


@login_required
def pending_approvals(request):
    """View pending approval requests for user"""
    from budgets.services import BudgetChangeService

    pending_requests = BudgetChangeService.get_pending_approvals_for_user(request.user)

    context = {
        'pending_requests': pending_requests,
        'total_pending': pending_requests.count(),
    }
    return render(request, 'spaces/pending_approvals.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def approve_change(request, request_id):
    """Approve a budget change request"""
    try:
        from budgets.approval_models import BudgetChangeRequest

        change_request = get_object_or_404(BudgetChangeRequest, id=request_id, status='pending')

        # Check if user is a member of the space and can approve
        space = change_request.budget_item.space
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=True)

            # Cannot approve own requests
            if change_request.requested_by == request.user:
                messages.error(request, 'You cannot approve your own requests.')
                return redirect('spaces:pending_approvals')

        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not authorized to approve this request.')
            return redirect('spaces:pending_approvals')

        # Approve the request
        change_request.approve(request.user)

        item_name = change_request.budget_item.category.name
        requester_name = change_request.requested_by.first_name or change_request.requested_by.username

        if change_request.status == 'approved':
            messages.success(request, f'Approved change to "{item_name}" requested by {requester_name}. Change has been applied.')
        else:
            messages.success(request, f'Your approval for "{item_name}" has been recorded. Waiting for other members.')

        return redirect('spaces:pending_approvals')

    except Exception as e:
        messages.error(request, 'Unable to approve request. Please try again.')
        return redirect('spaces:pending_approvals')


@login_required
@require_http_methods(["POST"])
@csrf_protect
def reject_change(request, request_id):
    """Reject a budget change request"""
    try:
        from budgets.approval_models import BudgetChangeRequest

        change_request = get_object_or_404(BudgetChangeRequest, id=request_id, status='pending')

        # Check if user is a member of the space and can reject
        space = change_request.budget_item.space
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=True)

            # Cannot reject own requests
            if change_request.requested_by == request.user:
                messages.error(request, 'You cannot reject your own requests.')
                return redirect('spaces:pending_approvals')

        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not authorized to reject this request.')
            return redirect('spaces:pending_approvals')

        # Get rejection reason from form
        reason = request.POST.get('reason', '').strip()

        # Reject the request
        change_request.reject(request.user, reason)

        item_name = change_request.budget_item.category.name
        requester_name = change_request.requested_by.first_name or change_request.requested_by.username

        messages.success(request, f'Rejected change to "{item_name}" requested by {requester_name}.')

        return redirect('spaces:pending_approvals')

    except Exception as e:
        messages.error(request, 'Unable to reject request. Please try again.')
        return redirect('spaces:pending_approvals')


@login_required
def change_history(request, pk):
    """View change history for a space"""
    try:
        space = get_object_or_404(Space, pk=pk, is_active=True)

        # Check if user is a member
        try:
            user_member = space.spacemember_set.get(user=request.user, is_active=True)
        except SpaceMember.DoesNotExist:
            messages.error(request, 'You are not a member of this space.')
            return redirect('spaces:list')

        # Get change history
        from budgets.services import BudgetChangeService
        history = BudgetChangeService.get_space_change_history(space, limit=50)

        context = {
            'space': space,
            'history': history,
            'total_changes': history.count() if hasattr(history, 'count') else len(history),
        }
        return render(request, 'spaces/change_history.html', context)

    except Exception as e:
        messages.error(request, 'Unable to load change history. Please try again.')
        return redirect('spaces:detail', pk=pk)
