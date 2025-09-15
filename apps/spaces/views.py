from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import Space, SpaceMember
from .forms import SpaceCreateForm, JoinSpaceForm, SpaceUpdateForm, RegenerateInviteCodeForm


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

    context = {
        'spaces_data': spaces_data,
        'total_spaces': len(spaces_data),
    }
    return render(request, 'spaces/list.html', context)


@login_required
@csrf_protect
def space_create(request):
    """Create a new space"""
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
