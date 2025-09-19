from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json

from .models import Budget, BudgetCategory, BudgetTemplate
from .forms import BudgetForm, BudgetCategoryForm, MonthlyBudgetForm, BudgetBulkEditForm, BudgetCopyForm, SmartBudgetCreationForm, BudgetTemplateForm
from spaces.models import Space, SpaceMember
from spaces.utils import SpaceContextManager

User = get_user_model()


@login_required
def budget_home(request):
    """Main budget dashboard view"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to view budgets.')
        return redirect('spaces:list')

    # Get current month
    current_month = timezone.now().strftime('%Y-%m')

    # Get current month budgets
    current_budgets = Budget.objects.filter(
        space=current_space,
        month_period=current_month,
        is_active=True
    ).select_related('category', 'assigned_to').order_by('category__name')

    # Calculate totals
    total_budgeted = current_budgets.aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')

    total_spent = Decimal('0.00')  # Will be calculated when expenses are implemented
    remaining = total_budgeted - total_spent

    # Get recent months for navigation
    recent_months = Budget.objects.filter(
        space=current_space,
        is_active=True
    ).values_list('month_period', flat=True).distinct().order_by('-month_period')[:6]

    context = {
        'current_space': current_space,
        'current_month': current_month,
        'current_budgets': current_budgets,
        'total_budgeted': total_budgeted,
        'total_spent': total_spent,
        'remaining': remaining,
        'recent_months': recent_months,
        'has_budgets': current_budgets.exists(),
    }

    return render(request, 'budgets/home.html', context)


@login_required
def budget_month_view(request, month_period):
    """View budgets for a specific month"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to view budgets.')
        return redirect('spaces:list')

    # Validate month format
    try:
        from datetime import datetime
        datetime.strptime(month_period, '%Y-%m')
    except ValueError:
        messages.error(request, 'Invalid month format.')
        return redirect('budgets:home')

    # Get budgets for the month
    budgets = Budget.objects.filter(
        space=current_space,
        month_period=month_period,
        is_active=True
    ).select_related('category', 'assigned_to').order_by('category__name')

    # Calculate totals
    total_budgeted = budgets.aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')

    context = {
        'current_space': current_space,
        'month_period': month_period,
        'budgets': budgets,
        'total_budgeted': total_budgeted,
        'has_budgets': budgets.exists(),
    }

    return render(request, 'budgets/month_view.html', context)


@login_required
def create_monthly_budget(request):
    """Create a complete monthly budget"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to create budgets.')
        return redirect('spaces:list')

    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST, space=current_space)
        if form.is_valid():
            month_period = form.cleaned_data['month_period']
            copy_from_previous = form.cleaned_data['copy_from_previous']

            try:
                with transaction.atomic():
                    if copy_from_previous:
                        budgets_created = Budget.copy_from_previous_month(
                            space=current_space,
                            target_month=month_period,
                            created_by=request.user
                        )
                    else:
                        budgets_created = Budget.create_monthly_budget(
                            space=current_space,
                            month_period=month_period,
                            created_by=request.user
                        )

                    if budgets_created:
                        messages.success(
                            request,
                            f'Created {len(budgets_created)} budget categories for {month_period}.'
                        )
                        return redirect('budgets:month_view', month_period=month_period)
                    else:
                        messages.info(request, f'Budget for {month_period} already exists.')
                        return redirect('budgets:month_view', month_period=month_period)

            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = MonthlyBudgetForm(space=current_space)

    return render(request, 'budgets/create_monthly.html', {
        'form': form,
        'current_space': current_space,
    })


@login_required
def budget_create(request):
    """Create individual budget"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to create budgets.')
        return redirect('spaces:list')

    # Get current month
    current_month = timezone.now().strftime('%Y-%m')
    month_period = request.GET.get('month', current_month)

    if request.method == 'POST':
        form = BudgetForm(
            request.POST,
            space=current_space,
            user=request.user,
            month_period=month_period
        )
        if form.is_valid():
            budget = form.save()
            messages.success(request, f'Budget for {budget.category.name} created successfully.')
            return redirect('budgets:month_view', month_period=month_period)
    else:
        form = BudgetForm(
            space=current_space,
            user=request.user,
            month_period=month_period
        )

    return render(request, 'budgets/create.html', {
        'form': form,
        'current_space': current_space,
        'month_period': month_period,
    })


@login_required
def budget_create_from_scratch(request):
    """Create budget from scratch with step-by-step interface"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to create budgets.')
        return redirect('spaces:list')

    # Get current month
    current_month = timezone.now().strftime('%Y-%m')
    month_period = request.GET.get('month', current_month)

    # Get available categories for this space
    available_categories = BudgetCategory.objects.filter(
        models.Q(space=current_space) | models.Q(space__isnull=True)
    ).exclude(
        budgets__space=current_space,
        budgets__month_period=month_period,
        budgets__is_active=True
    ).order_by('name')

    # Get current budget items for this month
    current_budget_items = Budget.objects.filter(
        space=current_space,
        month_period=month_period,
        is_active=True
    ).select_related('category', 'assigned_to').order_by('category__name')

    # Calculate total budget
    total_budget = current_budget_items.aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')

    # Get space members for assignment
    space_members = User.objects.filter(
        spacemember__space=current_space,
        spacemember__is_active=True
    ).distinct()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_item':
            # Add individual budget item
            category_id = request.POST.get('category')
            amount = request.POST.get('amount')
            assigned_to_id = request.POST.get('assigned_to')
            is_estimated = request.POST.get('is_estimated') == 'on'
            is_recurring = request.POST.get('is_recurring') == 'on'

            try:
                category = BudgetCategory.objects.get(id=category_id)
                assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None

                # Check if budget item already exists
                existing = Budget.objects.filter(
                    space=current_space,
                    category=category,
                    month_period=month_period,
                    is_active=True
                ).first()

                if existing:
                    messages.error(request, f'Budget item for {category.name} already exists for this month.')
                else:
                    Budget.objects.create(
                        space=current_space,
                        category=category,
                        amount=Decimal(amount),
                        assigned_to=assigned_to,
                        month_period=month_period,
                        is_estimated=is_estimated,
                        is_recurring=is_recurring,
                        created_by=request.user
                    )
                    messages.success(request, f'Added {category.name} to your budget.')

            except (BudgetCategory.DoesNotExist, ValueError) as e:
                messages.error(request, 'Invalid category or amount.')

        elif action == 'remove_item':
            # Remove budget item
            budget_id = request.POST.get('budget_id')
            try:
                budget = Budget.objects.get(
                    id=budget_id,
                    space=current_space,
                    month_period=month_period
                )
                budget_name = budget.category.name
                budget.delete()
                messages.success(request, f'Removed {budget_name} from your budget.')
            except Budget.DoesNotExist:
                messages.error(request, 'Budget item not found.')

        elif action in ['add_essentials', 'add_savings', 'add_lifestyle']:
            # Add template categories
            template_categories = {
                'add_essentials': ['Housing & Rent', 'Food & Groceries', 'Transportation'],
                'add_savings': ['Savings', 'Emergency Fund'],
                'add_lifestyle': ['Entertainment', 'Dining Out', 'Hobbies']
            }

            added_count = 0
            for cat_name in template_categories[action]:
                category = BudgetCategory.objects.filter(
                    models.Q(space=current_space) | models.Q(space__isnull=True),
                    name=cat_name
                ).first()

                if category:
                    existing = Budget.objects.filter(
                        space=current_space,
                        category=category,
                        month_period=month_period,
                        is_active=True
                    ).first()

                    if not existing:
                        Budget.objects.create(
                            space=current_space,
                            category=category,
                            amount=Decimal('0.01'),  # Minimal amount to start
                            month_period=month_period,
                            created_by=request.user
                        )
                        added_count += 1

            if added_count > 0:
                messages.success(request, f'Added {added_count} template categories. Set your amounts above.')
            else:
                messages.info(request, 'All template categories already exist in your budget.')

        return redirect(f'?month={month_period}')

    return render(request, 'budgets/create_from_scratch.html', {
        'current_space': current_space,
        'month_period': month_period,
        'available_categories': available_categories,
        'current_budget_items': current_budget_items,
        'total_budget': total_budget,
        'space_members': space_members,
    })


@login_required
def budget_edit(request, budget_id):
    """Edit individual budget"""
    current_space = SpaceContextManager.get_current_space(request)
    budget = get_object_or_404(Budget, id=budget_id, space=current_space, is_active=True)

    if request.method == 'POST':
        form = BudgetForm(
            request.POST,
            instance=budget,
            space=current_space,
            user=request.user,
            month_period=budget.month_period
        )
        if form.is_valid():
            budget = form.save()
            messages.success(request, f'Budget for {budget.category.name} updated successfully.')
            return redirect('budgets:home')
    else:
        form = BudgetForm(
            instance=budget,
            space=current_space,
            user=request.user,
            month_period=budget.month_period
        )

    return render(request, 'budgets/edit.html', {
        'form': form,
        'budget': budget,
        'current_space': current_space,
    })


@login_required
def budget_delete(request, budget_id):
    """Delete individual budget"""
    current_space = SpaceContextManager.get_current_space(request)
    budget = get_object_or_404(Budget, id=budget_id, space=current_space, is_active=True)

    if request.method == 'POST':
        month_period = budget.month_period
        category_name = budget.category.name
        budget.delete()
        messages.success(request, f'Budget for {category_name} deleted successfully.')
        return redirect('budgets:month_view', month_period=month_period)

    return render(request, 'budgets/delete.html', {
        'budget': budget,
        'current_space': current_space,
    })


@login_required
def budget_bulk_edit(request, month_period):
    """Bulk edit budgets for a month"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to edit budgets.')
        return redirect('spaces:list')

    budgets = Budget.objects.filter(
        space=current_space,
        month_period=month_period,
        is_active=True
    ).select_related('category', 'assigned_to').order_by('category__name')

    if not budgets.exists():
        messages.error(request, f'No budgets found for {month_period}.')
        return redirect('budgets:home')

    if request.method == 'POST':
        form = BudgetBulkEditForm(request.POST, budgets=budgets)
        if form.is_valid():
            updated_budgets = form.save()
            messages.success(
                request,
                f'Updated {len(updated_budgets)} budgets for {month_period}.'
            )
            return redirect('budgets:month_view', month_period=month_period)
    else:
        form = BudgetBulkEditForm(budgets=budgets)

    return render(request, 'budgets/bulk_edit.html', {
        'form': form,
        'budgets': budgets,
        'month_period': month_period,
        'current_space': current_space,
    })


@login_required
def category_create(request):
    """Create custom budget category"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to create categories.')
        return redirect('spaces:list')

    if request.method == 'POST':
        form = BudgetCategoryForm(request.POST, space=current_space, user=request.user)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect('budgets:categories')
    else:
        form = BudgetCategoryForm(space=current_space, user=request.user)

    return render(request, 'budgets/category_create.html', {
        'form': form,
        'current_space': current_space,
    })


@login_required
def category_list(request):
    """List budget categories"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to view categories.')
        return redirect('spaces:list')

    # System categories
    system_categories = BudgetCategory.objects.filter(
        is_system_default=True,
        is_active=True
    ).order_by('name')

    # Custom categories for this space
    custom_categories = BudgetCategory.objects.filter(
        space=current_space,
        is_active=True
    ).order_by('name')

    return render(request, 'budgets/categories.html', {
        'system_categories': system_categories,
        'custom_categories': custom_categories,
        'current_space': current_space,
    })


@login_required
def budget_copy(request):
    """Copy budgets from one month to another"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to copy budgets.')
        return redirect('spaces:list')

    if request.method == 'POST':
        form = BudgetCopyForm(request.POST, space=current_space)
        if form.is_valid():
            source_month = form.cleaned_data['source_month']
            target_month = form.cleaned_data['target_month']
            multiply_by = form.cleaned_data['multiply_by']

            try:
                with transaction.atomic():
                    # Get source budgets
                    source_budgets = Budget.objects.filter(
                        space=current_space,
                        month_period=source_month,
                        is_active=True
                    )

                    budgets_created = []
                    for source_budget in source_budgets:
                        new_amount = source_budget.amount * multiply_by

                        budget, created = Budget.objects.get_or_create(
                            space=current_space,
                            category=source_budget.category,
                            month_period=target_month,
                            defaults={
                                'amount': new_amount,
                                'assigned_to': source_budget.assigned_to,
                                'notes': f'Copied from {source_month}',
                                'created_by': request.user,
                            }
                        )

                        if created:
                            budgets_created.append(budget)

                    if budgets_created:
                        messages.success(
                            request,
                            f'Copied {len(budgets_created)} budgets from {source_month} to {target_month}.'
                        )
                    else:
                        messages.info(request, f'All budgets already exist for {target_month}.')

                    return redirect('budgets:month_view', month_period=target_month)

            except Exception as e:
                messages.error(request, f'Error copying budgets: {e}')
    else:
        form = BudgetCopyForm(space=current_space)

    return render(request, 'budgets/copy.html', {
        'form': form,
        'current_space': current_space,
    })


@login_required
@require_http_methods(["POST"])
def budget_quick_update(request, budget_id):
    """AJAX endpoint for quick budget updates"""
    current_space = SpaceContextManager.get_current_space(request)
    budget = get_object_or_404(Budget, id=budget_id, space=current_space, is_active=True)

    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', budget.amount)))

        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Amount must be greater than 0'})

        if amount > 999999.99:
            return JsonResponse({'success': False, 'error': 'Amount cannot exceed $999,999.99'})

        budget.amount = amount
        budget.save()

        return JsonResponse({
            'success': True,
            'amount': str(budget.amount),
            'formatted_amount': f'${budget.amount:,.2f}'
        })

    except (ValueError, ValidationError) as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred while updating the budget'})


@login_required
def budget_analytics(request):
    """Budget analytics and insights"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to view analytics.')
        return redirect('spaces:list')

    # Get analytics data for the last 6 months
    from datetime import datetime, timedelta
    import calendar

    current_date = timezone.now()
    months_data = []

    for i in range(6):
        # Calculate month
        if current_date.month - i <= 0:
            year = current_date.year - 1
            month = 12 + (current_date.month - i)
        else:
            year = current_date.year
            month = current_date.month - i

        month_period = f"{year:04d}-{month:02d}"
        month_name = calendar.month_name[month]

        # Get budgets for this month
        month_budgets = Budget.objects.filter(
            space=current_space,
            month_period=month_period,
            is_active=True
        ).aggregate(
            total_budgeted=models.Sum('amount'),
            count=models.Count('id')
        )

        months_data.append({
            'period': month_period,
            'name': f"{month_name} {year}",
            'total_budgeted': month_budgets['total_budgeted'] or Decimal('0.00'),
            'budget_count': month_budgets['count'],
        })

    # Category breakdown for current month
    current_month = timezone.now().strftime('%Y-%m')
    category_breakdown = Budget.objects.filter(
        space=current_space,
        month_period=current_month,
        is_active=True
    ).select_related('category').order_by('-amount')

    return render(request, 'budgets/analytics.html', {
        'current_space': current_space,
        'months_data': months_data,
        'category_breakdown': category_breakdown,
        'current_month': current_month,
    })


# SMART TEMPLATES SYSTEM VIEWS

@login_required
def smart_create_budget(request):
    """Enhanced budget creation with templates and timing options"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:select')

    current_month = timezone.now().strftime('%Y-%m')

    if request.method == 'POST':
        form = SmartBudgetCreationForm(
            request.POST,
            space=current_space,
            user=request.user,
            month_period=current_month
        )
        if form.is_valid():
            budget = form.save()

            # Create system default templates if they don't exist
            if not BudgetTemplate.objects.filter(is_system_default=True).exists():
                BudgetTemplate.create_system_defaults()

            messages.success(request, f'Budget for {budget.category.name} created successfully!')
            return redirect('budgets:home')
    else:
        form = SmartBudgetCreationForm(
            space=current_space,
            user=request.user,
            month_period=current_month
        )

    # Get available templates for display
    templates = BudgetTemplate.objects.filter(
        Q(is_system_default=True) | Q(space=current_space),
        is_active=True
    ).order_by('template_type', 'name')

    return render(request, 'budgets/smart_create.html', {
        'current_space': current_space,
        'form': form,
        'templates': templates,
        'current_month': current_month,
    })


@login_required
def template_data_api(request, template_id):
    """API endpoint to get template data for JS"""
    try:
        template = BudgetTemplate.objects.get(id=template_id)
        # Verify access (system template or user's space template)
        current_space = SpaceContextManager.get_current_space(request)
        if not template.is_system_default and template.space != current_space:
            return JsonResponse({'error': 'Access denied'}, status=403)

        data = {
            'category_id': template.default_category.id,
            'suggested_amount': str(template.suggested_amount) if template.suggested_amount else '',
            'timing_type': template.default_timing_type,
            'reminder_days': template.default_reminder_days,
            'time_of_day': template.default_time_of_day,
            'is_recurring': template.default_is_recurring,
            'recurrence_pattern': template.default_recurrence_pattern or '',
            'description': template.description,
        }
        return JsonResponse(data)
    except BudgetTemplate.DoesNotExist:
        return JsonResponse({'error': 'Template not found'}, status=404)


@login_required
def template_list(request):
    """List all templates available to user"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:select')

    # Get system and custom templates
    system_templates = BudgetTemplate.objects.filter(
        is_system_default=True,
        is_active=True
    ).order_by('template_type', 'name')

    custom_templates = BudgetTemplate.objects.filter(
        space=current_space,
        is_active=True
    ).order_by('template_type', 'name')

    return render(request, 'budgets/templates/list.html', {
        'current_space': current_space,
        'system_templates': system_templates,
        'custom_templates': custom_templates,
    })


@login_required
def template_create(request):
    """Create a custom template"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:select')

    if request.method == 'POST':
        form = BudgetTemplateForm(
            request.POST,
            space=current_space,
            user=request.user
        )
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Template "{template.name}" created successfully!')
            return redirect('budgets:template_list')
    else:
        form = BudgetTemplateForm(
            space=current_space,
            user=request.user
        )

    return render(request, 'budgets/templates/create.html', {
        'current_space': current_space,
        'form': form,
    })


@login_required
def template_edit(request, template_id):
    """Edit a custom template"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:select')

    template = get_object_or_404(
        BudgetTemplate,
        id=template_id,
        space=current_space  # Only allow editing space templates
    )

    if request.method == 'POST':
        form = BudgetTemplateForm(
            request.POST,
            instance=template,
            space=current_space,
            user=request.user
        )
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect('budgets:template_list')
    else:
        form = BudgetTemplateForm(
            instance=template,
            space=current_space,
            user=request.user
        )

    return render(request, 'budgets/templates/edit.html', {
        'current_space': current_space,
        'form': form,
        'template': template,
    })


@login_required
def template_delete(request, template_id):
    """Delete a custom template"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:select')

    template = get_object_or_404(
        BudgetTemplate,
        id=template_id,
        space=current_space  # Only allow deleting space templates
    )

    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return redirect('budgets:template_list')

    return render(request, 'budgets/templates/delete.html', {
        'current_space': current_space,
        'template': template,
    })
