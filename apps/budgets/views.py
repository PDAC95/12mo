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

from .models import Budget, BudgetCategory, BudgetTemplate, CategorySuggestion, PaymentMethod, BudgetSplit
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

    # Get available categories for adding new budget categories
    used_category_ids = current_budgets.values_list('category_id', flat=True)
    available_categories = BudgetCategory.objects.filter(
        models.Q(is_system_default=True) | models.Q(space=current_space),
        is_active=True
    ).exclude(id__in=used_category_ids).order_by('name')

    # Get space members for assignment
    space_members = User.objects.filter(
        spacemember__space=current_space,
        spacemember__is_active=True
    ).distinct()

    # Get available payment methods
    available_payment_methods = PaymentMethod.objects.filter(
        space=current_space,
        is_active=True
    ).order_by('name')

    context = {
        'current_space': current_space,
        'current_month': current_month,
        'current_budgets': current_budgets,
        'total_budgeted': total_budgeted,
        'total_spent': total_spent,
        'remaining': remaining,
        'recent_months': recent_months,
        'has_budgets': current_budgets.exists(),
        'available_categories': available_categories,
        'available_payment_methods': available_payment_methods,
        'space_members': space_members,
        'payment_methods': available_payment_methods,  # Alias for component compatibility
    }

    return render(request, 'budgets/home.html', context)


@login_required
@require_http_methods(["POST"])
def budget_edit_api(request):
    """API endpoint to handle budget category editing"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return JsonResponse({'success': False, 'error': 'Please select a space'}, status=400)

    try:
        month_period = request.POST.get('month_period')
        if not month_period:
            return JsonResponse({'success': False, 'error': 'Month period is required'}, status=400)

        with transaction.atomic():
            # Handle existing budget updates and deletions
            for key, value in request.POST.items():
                if key.startswith('amount_'):
                    budget_id = key.split('_')[1]
                    amount = Decimal(value)

                    # Check if this budget should be deleted
                    delete_key = f'delete_budget_{budget_id}'
                    if delete_key in request.POST:
                        # Delete the budget
                        Budget.objects.filter(
                            id=budget_id,
                            space=current_space,
                            month_period=month_period
                        ).delete()
                    else:
                        # Update the budget amount
                        Budget.objects.filter(
                            id=budget_id,
                            space=current_space,
                            month_period=month_period
                        ).update(amount=amount)

            # Handle new category additions
            new_data = {}

            # Collect all new category data
            for key, value in request.POST.items():
                if key.startswith('new_'):
                    parts = key.split('_')
                    if len(parts) >= 3:
                        field_type = '_'.join(parts[1:-1])  # e.g., 'category', 'amount', 'assigned_to'
                        counter = parts[-1]

                        if counter not in new_data:
                            new_data[counter] = {}
                        new_data[counter][field_type] = value

            # Process each new budget item
            for counter, data in new_data.items():
                if 'category' in data and 'amount' in data:
                    category_name = data.get('category', '').strip()
                    try:
                        amount = Decimal(data.get('amount', '0'))
                    except:
                        continue

                    if category_name and amount > 0:
                        # Try to find existing category first
                        category = BudgetCategory.objects.filter(
                            models.Q(name__iexact=category_name),
                            models.Q(space=current_space) | models.Q(is_system_default=True)
                        ).first()

                        # If category doesn't exist, create it
                        if not category:
                            category = BudgetCategory.objects.create(
                                name=category_name,
                                space=current_space,
                                category_type='custom',
                                created_by=request.user
                            )

                        # Check if this category already exists for this month
                        if not Budget.objects.filter(
                            space=current_space,
                            category=category,
                            month_period=month_period
                        ).exists():
                            # Get assigned user
                            assigned_to = None
                            if data.get('assigned_to'):
                                try:
                                    assigned_to = User.objects.get(id=data.get('assigned_to'))
                                except User.DoesNotExist:
                                    pass

                            # Get payment method
                            payment_method = None
                            if data.get('payment_method'):
                                try:
                                    payment_method = PaymentMethod.objects.get(id=data.get('payment_method'))
                                except PaymentMethod.DoesNotExist:
                                    pass

                            # Parse date
                            due_date = None
                            if data.get('due_date'):
                                try:
                                    from datetime import datetime
                                    due_date = datetime.strptime(data.get('due_date'), '%Y-%m-%d').date()
                                except:
                                    pass

                            # Create budget
                            budget = Budget.objects.create(
                                space=current_space,
                                category=category,
                                amount=amount,
                                month_period=month_period,
                                created_by=request.user,
                                assigned_to=assigned_to,
                                payment_method=payment_method,
                                due_date=due_date,
                                is_estimated=data.get('is_estimated') == 'true',
                                is_recurring=data.get('is_recurring') == 'true',
                                notes=data.get('notes', '')
                            )

                            # Handle splits if enabled
                            if data.get('enable_split') == 'true':
                                # Process split data
                                split_data = {}
                                for key, value in request.POST.items():
                                    if key.startswith(f'new_split_') and key.endswith(f'_{counter}_'):
                                        # Extract split index and field
                                        split_parts = key.replace(f'new_split_', '').replace(f'_{counter}_', '').split('_')
                                        if len(split_parts) >= 2:
                                            field = split_parts[0]  # user, type, value
                                            split_index = split_parts[1]

                                            if split_index not in split_data:
                                                split_data[split_index] = {}
                                            split_data[split_index][field] = value

                                # Create split records
                                for split_index, split_info in split_data.items():
                                    if all(k in split_info for k in ['user', 'type', 'value']):
                                        try:
                                            split_user = User.objects.get(id=split_info['user'])
                                            split_value = Decimal(split_info['value'])
                                            split_type = split_info['type']

                                            if split_type == 'percentage':
                                                BudgetSplit.objects.create(
                                                    budget=budget,
                                                    user=split_user,
                                                    percentage=split_value
                                                )
                                            elif split_type == 'fixed':
                                                BudgetSplit.objects.create(
                                                    budget=budget,
                                                    user=split_user,
                                                    amount=split_value
                                                )
                                        except (User.DoesNotExist, ValueError):
                                            continue

        return JsonResponse({
            'success': True,
            'message': 'Budget updated successfully!'
        })

    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except BudgetCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error updating budget: {str(e)}'}, status=500)


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
    ).select_related('category', 'assigned_to').prefetch_related('splits__user').order_by('category__name')

    # Calculate total budget
    total_budget = current_budget_items.aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')

    # Get space members for assignment
    space_members = User.objects.filter(
        spacemember__space=current_space,
        spacemember__is_active=True
    ).distinct()

    # Get payment methods for this space
    payment_methods = PaymentMethod.objects.filter(
        space=current_space,
        is_active=True
    ).order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_item':
            # Add individual budget item
            category_name = request.POST.get('category_name', '').strip()
            amount = request.POST.get('amount')
            assigned_to_id = request.POST.get('assigned_to')
            assignment_type = request.POST.get('assignment_type', 'single')
            is_estimated = request.POST.get('is_estimated') == 'on'
            is_recurring = request.POST.get('is_recurring') == 'on'

            try:
                if not category_name:
                    raise ValueError("Category name is required")

                # Try to find existing category first
                category = BudgetCategory.objects.filter(
                    models.Q(name__iexact=category_name, space=current_space) |
                    models.Q(name__iexact=category_name, space__isnull=True)
                ).first()

                # If category doesn't exist, create a new custom one
                if not category:
                    category = BudgetCategory.objects.create(
                        name=category_name,
                        space=current_space,
                        category_type='variable'  # Default to variable
                    )

                # Increment usage count for suggestion if it exists
                suggestion = CategorySuggestion.objects.filter(name__iexact=category_name).first()
                if suggestion:
                    suggestion.increment_usage()

                # Handle payment method
                payment_method_id = request.POST.get('payment_method')
                payment_method = PaymentMethod.objects.get(id=payment_method_id) if payment_method_id else None

                # Handle payment dates
                timing_type = request.POST.get('timing_type', 'flexible')
                due_date = None
                range_start = None
                range_end = None

                if timing_type == 'exact':
                    due_date_str = request.POST.get('due_date')
                    if due_date_str:
                        from datetime import datetime
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                elif timing_type == 'range':
                    range_start_str = request.POST.get('range_start')
                    range_end_str = request.POST.get('range_end')
                    if range_start_str:
                        range_start = datetime.strptime(range_start_str, '%Y-%m-%d').date()
                    if range_end_str:
                        range_end = datetime.strptime(range_end_str, '%Y-%m-%d').date()
                elif timing_type == 'biweekly':
                    biweekly_first_str = request.POST.get('biweekly_first')
                    biweekly_second_str = request.POST.get('biweekly_second')
                    if biweekly_first_str:
                        due_date = datetime.strptime(biweekly_first_str, '%Y-%m-%d').date()
                    if biweekly_second_str:
                        range_end = datetime.strptime(biweekly_second_str, '%Y-%m-%d').date()

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
                    # Set recurrence settings for biweekly
                    recurrence_type = 'biweekly' if timing_type == 'biweekly' else None
                    is_recurring_final = is_recurring or (timing_type == 'biweekly')

                    # Handle single vs split assignment
                    if assignment_type == 'single':
                        assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None

                        budget = Budget.objects.create(
                            space=current_space,
                            category=category,
                            amount=Decimal(amount),
                            assigned_to=assigned_to,
                            month_period=month_period,
                            is_estimated=is_estimated,
                            is_recurring=is_recurring_final,
                            created_by=request.user,
                            payment_method=payment_method,
                            timing_type=timing_type,
                            due_date=due_date,
                            range_start=range_start,
                            range_end=range_end,
                            recurrence_type=recurrence_type
                        )
                        messages.success(request, f'Added {category.name} to your budget.')

                    else:  # split assignment
                        # Create budget without specific assignment
                        budget = Budget.objects.create(
                            space=current_space,
                            category=category,
                            amount=Decimal(amount),
                            assigned_to=None,  # No single assignee for splits
                            month_period=month_period,
                            is_estimated=is_estimated,
                            is_recurring=is_recurring_final,
                            created_by=request.user,
                            payment_method=payment_method,
                            timing_type=timing_type,
                            due_date=due_date,
                            range_start=range_start,
                            range_end=range_end,
                            recurrence_type=recurrence_type
                        )

                        # Process split assignments
                        total_amount = Decimal(amount)
                        split_created = False

                        # Find all split user fields
                        split_fields = {}
                        for key, value in request.POST.items():
                            if key.startswith('split_user_') and value:
                                index = key.split('_')[-1]
                                split_fields[index] = {
                                    'user_id': value,
                                    'type': request.POST.get(f'split_type_{index}'),
                                    'value': request.POST.get(f'split_value_{index}')
                                }

                        # Create BudgetSplit objects
                        for index, split_data in split_fields.items():
                            try:
                                user = User.objects.get(id=split_data['user_id'])
                                split_type = split_data['type']
                                split_value = Decimal(split_data['value'])

                                # Calculate amount based on type
                                if split_type == 'percentage':
                                    calculated_amount = (total_amount * split_value) / 100
                                else:  # fixed_amount
                                    calculated_amount = split_value

                                from .models import BudgetSplit
                                BudgetSplit.objects.create(
                                    budget=budget,
                                    user=user,
                                    split_type=split_type,
                                    percentage=split_value if split_type == 'percentage' else None,
                                    fixed_amount=split_value if split_type == 'fixed_amount' else None,
                                    calculated_amount=calculated_amount
                                )
                                split_created = True

                            except (User.DoesNotExist, ValueError) as e:
                                messages.warning(request, f'Error processing split for index {index}: {e}')

                        if split_created:
                            messages.success(request, f'Added {category.name} to your budget with expense splits.')
                        else:
                            # Delete budget if no splits were created
                            budget.delete()
                            messages.error(request, 'No valid splits were provided. Budget item not created.')

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

        elif action == 'edit_item':
            # Edit existing budget item
            budget_id = request.POST.get('budget_id')
            try:
                budget = Budget.objects.get(
                    id=budget_id,
                    space=current_space,
                    month_period=month_period
                )

                # Update basic fields
                amount = request.POST.get('amount')
                assigned_to_id = request.POST.get('assigned_to')
                is_estimated = request.POST.get('is_estimated') == 'on'
                is_recurring = request.POST.get('is_recurring') == 'on'

                # Handle payment method
                payment_method_id = request.POST.get('payment_method')
                payment_method = PaymentMethod.objects.get(id=payment_method_id) if payment_method_id else None

                # Handle payment dates
                timing_type = request.POST.get('timing_type', 'flexible')
                due_date = None
                range_start = None
                range_end = None

                if timing_type == 'exact':
                    due_date_str = request.POST.get('due_date')
                    if due_date_str:
                        from datetime import datetime
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                elif timing_type == 'range':
                    range_start_str = request.POST.get('range_start')
                    range_end_str = request.POST.get('range_end')
                    if range_start_str:
                        range_start = datetime.strptime(range_start_str, '%Y-%m-%d').date()
                    if range_end_str:
                        range_end = datetime.strptime(range_end_str, '%Y-%m-%d').date()
                elif timing_type == 'biweekly':
                    biweekly_first_str = request.POST.get('biweekly_first')
                    biweekly_second_str = request.POST.get('biweekly_second')
                    if biweekly_first_str:
                        due_date = datetime.strptime(biweekly_first_str, '%Y-%m-%d').date()
                    if biweekly_second_str:
                        range_end = datetime.strptime(biweekly_second_str, '%Y-%m-%d').date()

                # Set recurrence settings
                recurrence_type = 'biweekly' if timing_type == 'biweekly' else budget.recurrence_type
                is_recurring_final = is_recurring or (timing_type == 'biweekly')

                assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None

                # Update budget
                budget.amount = Decimal(amount)
                budget.assigned_to = assigned_to
                budget.is_estimated = is_estimated
                budget.is_recurring = is_recurring_final
                budget.payment_method = payment_method
                budget.timing_type = timing_type
                budget.due_date = due_date
                budget.range_start = range_start
                budget.range_end = range_end
                budget.recurrence_type = recurrence_type
                budget.save()

                messages.success(request, f'Updated {budget.category.name} successfully.')

            except Budget.DoesNotExist:
                messages.error(request, 'Budget item not found.')
            except (ValueError, User.DoesNotExist, PaymentMethod.DoesNotExist) as e:
                messages.error(request, 'Invalid data provided.')

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

        return redirect('budgets:create_from_scratch')

    return render(request, 'budgets/create_from_scratch.html', {
        'current_space': current_space,
        'month_period': month_period,
        'available_categories': available_categories,
        'current_budget_items': current_budget_items,
        'total_budget': total_budget,
        'space_members': space_members,
        'payment_methods': payment_methods,
    })


@login_required
def budget_edit(request, budget_id):
    """Edit individual budget"""
    current_space = SpaceContextManager.get_current_space(request)
    budget = get_object_or_404(
        Budget.objects.prefetch_related('splits__user'),
        id=budget_id,
        space=current_space,
        is_active=True
    )

    if request.method == 'POST':
        # Handle category name (autocomplete functionality)
        category_name = request.POST.get('category_name', '').strip()
        if category_name:
            # Try to find existing category first
            category = BudgetCategory.objects.filter(
                models.Q(name__iexact=category_name, space=current_space) |
                models.Q(name__iexact=category_name, space__isnull=True)
            ).first()

            # If category doesn't exist, create a new one
            if not category:
                category = BudgetCategory.objects.create(
                    name=category_name,
                    space=current_space,
                    category_type='variable'  # Default to variable
                )

            # Increment usage count for suggestion if it exists
            suggestion = CategorySuggestion.objects.filter(name__iexact=category_name).first()
            if suggestion:
                suggestion.increment_usage()

            # Update the budget's category
            budget.category = category
            budget.save()  # Save category change immediately

        # Create a mutable copy of POST data and add category field for form validation
        post_data = request.POST.copy()
        post_data['category'] = budget.category.id

        form = BudgetForm(
            post_data,
            instance=budget,
            space=current_space,
            user=request.user,
            month_period=budget.month_period
        )
        if form.is_valid():
            # Handle assignment type
            assignment_type = request.POST.get('assignment_type', 'single')

            if assignment_type == 'single':
                # Standard form save for single assignment
                budget = form.save()
                # Clear any existing splits
                budget.splits.all().delete()

            else:  # split assignment
                # Save budget but clear assigned_to for splits
                budget = form.save(commit=False)
                budget.assigned_to = None
                budget.save()

                # Clear existing splits
                budget.splits.all().delete()

                # Process new split assignments
                total_amount = budget.amount
                split_created = False

                # Find all split user fields
                split_fields = {}
                for key, value in request.POST.items():
                    if key.startswith('split_user_') and value:
                        index = key.split('_')[-1]
                        split_fields[index] = {
                            'user_id': value,
                            'type': request.POST.get(f'split_type_{index}'),
                            'value': request.POST.get(f'split_value_{index}')
                        }

                # Create BudgetSplit objects
                for index, split_data in split_fields.items():
                    try:
                        user = User.objects.get(id=split_data['user_id'])
                        split_type = split_data['type']
                        split_value = Decimal(split_data['value'])

                        # Calculate amount based on type
                        if split_type == 'percentage':
                            calculated_amount = (total_amount * split_value) / 100
                        else:  # fixed_amount
                            calculated_amount = split_value

                        from .models import BudgetSplit
                        BudgetSplit.objects.create(
                            budget=budget,
                            user=user,
                            split_type=split_type,
                            percentage=split_value if split_type == 'percentage' else None,
                            fixed_amount=split_value if split_type == 'fixed_amount' else None,
                            calculated_amount=calculated_amount
                        )
                        split_created = True

                    except (User.DoesNotExist, ValueError) as e:
                        messages.warning(request, f'Error processing split for index {index}: {e}')

                if not split_created:
                    messages.error(request, 'No valid splits were provided. Please add at least one valid split.')
                    return render(request, 'budgets/edit.html', {'form': form, 'budget': budget})
                else:
                    messages.success(request, f'Budget successfully split between {budget.splits.count()} members.')

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


# NEW TEMPLATE SYSTEM VIEWS

@login_required
def budget_create_method_selection(request):
    """Budget creation method selection: From Scratch vs Templates"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to create budgets.')
        return redirect('spaces:list')

    # Get current month
    current_month = timezone.now().strftime('%Y-%m')
    month_period = request.GET.get('month', current_month)

    # Get template counts for display
    framework_templates = BudgetTemplate.get_frameworks().filter(is_system_default=True)
    situation_templates = BudgetTemplate.get_situations().filter(is_system_default=True)

    return render(request, 'budgets/create_method_selection.html', {
        'current_space': current_space,
        'month_period': month_period,
        'framework_count': framework_templates.count(),
        'situation_count': situation_templates.count(),
        'total_templates': framework_templates.count() + situation_templates.count(),
    })


@login_required
def template_gallery(request):
    """Template gallery showing frameworks and situations"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to browse templates.')
        return redirect('spaces:list')

    # Get current month for template creation
    current_month = timezone.now().strftime('%Y-%m')
    month_period = request.GET.get('month', current_month)
    filter_type = request.GET.get('filter')  # framework or situation

    # Get templates based on filter
    framework_templates = []
    situation_templates = []

    if filter_type == 'framework':
        framework_templates = BudgetTemplate.get_frameworks().filter(is_system_default=True)
    elif filter_type == 'situation':
        situation_templates = BudgetTemplate.get_situations().filter(is_system_default=True)
    else:
        # Show both if no filter
        framework_templates = BudgetTemplate.get_frameworks().filter(is_system_default=True)
        situation_templates = BudgetTemplate.get_situations().filter(is_system_default=True)

    return render(request, 'budgets/template_gallery.html', {
        'current_space': current_space,
        'month_period': month_period,
        'framework_templates': framework_templates,
        'situation_templates': situation_templates,
        'filter_type': filter_type,
    })


@login_required
def template_detail(request, template_id):
    """Show template details with preview"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space.')
        return redirect('spaces:list')

    template = get_object_or_404(BudgetTemplate, id=template_id)

    # Get current month
    current_month = timezone.now().strftime('%Y-%m')
    month_period = request.GET.get('month', current_month)

    # Get custom total amount if provided
    custom_total = request.GET.get('total')
    if custom_total:
        try:
            total_amount = Decimal(custom_total)
        except (ValueError, TypeError):
            total_amount = template.default_total_amount
    else:
        total_amount = template.default_total_amount

    # Calculate categories and sections for preview
    calculated_categories = template.get_calculated_categories(total_amount)
    sections_summary = template.get_sections_summary(total_amount)

    return render(request, 'budgets/template_detail.html', {
        'current_space': current_space,
        'template': template,
        'month_period': month_period,
        'total_amount': total_amount,
        'calculated_categories': calculated_categories,
        'sections_summary': sections_summary,
    })


@login_required
def budget_create_from_template(request, template_id):
    """Create budget from selected template"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to create budgets.')
        return redirect('spaces:list')

    template = get_object_or_404(BudgetTemplate, id=template_id)

    # Get current month
    current_month = timezone.now().strftime('%Y-%m')
    month_period = request.GET.get('month', current_month)

    if request.method == 'POST':
        # Get form data
        total_amount = Decimal(request.POST.get('total_amount', template.default_total_amount))

        # Create budgets based on template
        budgets_created = []
        errors = []

        # Get system categories for matching
        system_categories = {cat.name: cat for cat in BudgetCategory.objects.filter(is_system_default=True)}

        for category_name, category_data in template.category_data.items():
            # Find matching system category
            category = system_categories.get(category_name)
            if not category:
                errors.append(f'Category "{category_name}" not found')
                continue

            # Calculate amount based on total
            amount = (total_amount * Decimal(category_data['percentage']) / 100).quantize(Decimal('0.01'))

            # Check if budget already exists for this category and month
            existing_budget = Budget.objects.filter(
                space=current_space,
                category=category,
                month_period=month_period
            ).first()

            if existing_budget:
                errors.append(f'Budget for {category_name} already exists for {month_period}')
                continue

            # Create the budget
            budget = Budget.objects.create(
                space=current_space,
                category=category,
                amount=amount,
                month_period=month_period,
                created_by=request.user,
                template_used=template,
                is_custom=False
            )
            budgets_created.append(budget)

        if budgets_created:
            # Increment template usage
            template.increment_usage()

            messages.success(
                request,
                f'Successfully created {len(budgets_created)} budget categories using "{template.name}" template.'
            )
            if errors:
                messages.warning(request, f'Some categories had issues: {", ".join(errors)}')
        else:
            messages.error(request, f'No budgets created. Errors: {", ".join(errors) if errors else "Unknown error"}')

        return redirect('budgets:month_view', month_period=month_period)

    # GET request - show template customization form
    calculated_categories = template.get_calculated_categories()
    sections_summary = template.get_sections_summary()

    return render(request, 'budgets/create_from_template.html', {
        'current_space': current_space,
        'template': template,
        'month_period': month_period,
        'calculated_categories': calculated_categories,
        'sections_summary': sections_summary,
    })


@login_required
def category_suggestions_api(request):
    """API endpoint for category autocomplete suggestions"""
    query = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 10)), 20)  # Max 20 suggestions

    suggestions = CategorySuggestion.get_suggestions(query, limit)

    data = []
    for suggestion in suggestions:
        data.append({
            'name': suggestion.name,
            'category_type': suggestion.category_type,
            'usage_count': suggestion.usage_count,
            'is_popular': suggestion.is_popular,
        })

    return JsonResponse({
        'suggestions': data,
        'query': query,
        'count': len(data),
    })


# Payment Methods Management Views

@login_required
def payment_methods_list(request):
    """List all payment methods for the current space"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:list')

    payment_methods = PaymentMethod.objects.filter(
        space=current_space,
        is_active=True
    ).order_by('name')

    return render(request, 'budgets/payment_methods.html', {
        'current_space': current_space,
        'payment_methods': payment_methods,
    })


@login_required
def payment_method_create(request):
    """Create a new payment method"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:list')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        payment_type = request.POST.get('payment_type', 'debit')

        if name:
            try:
                PaymentMethod.objects.create(
                    name=name,
                    payment_type=payment_type,
                    space=current_space
                )
                messages.success(request, f'Payment method "{name}" created successfully.')
                return redirect('budgets:payment_methods')
            except Exception as e:
                messages.error(request, 'Error creating payment method. Name might already exist.')
        else:
            messages.error(request, 'Payment method name is required.')

    return render(request, 'budgets/payment_method_form.html', {
        'current_space': current_space,
        'title': 'Create Payment Method',
        'payment_types': PaymentMethod.TYPE_CHOICES,
    })


@login_required
def payment_method_edit(request, method_id):
    """Edit an existing payment method"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:list')

    try:
        payment_method = PaymentMethod.objects.get(id=method_id, space=current_space)
    except PaymentMethod.DoesNotExist:
        messages.error(request, 'Payment method not found.')
        return redirect('budgets:payment_methods')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        payment_type = request.POST.get('payment_type', 'debit')

        if name:
            try:
                payment_method.name = name
                payment_method.payment_type = payment_type
                payment_method.save()
                messages.success(request, f'Payment method "{name}" updated successfully.')
                return redirect('budgets:payment_methods')
            except Exception as e:
                messages.error(request, 'Error updating payment method. Name might already exist.')
        else:
            messages.error(request, 'Payment method name is required.')

    return render(request, 'budgets/payment_method_form.html', {
        'current_space': current_space,
        'payment_method': payment_method,
        'title': 'Edit Payment Method',
        'payment_types': PaymentMethod.TYPE_CHOICES,
    })


@login_required
def payment_method_delete(request, method_id):
    """Delete a payment method"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return redirect('spaces:list')

    try:
        payment_method = PaymentMethod.objects.get(id=method_id, space=current_space)

        if request.method == 'POST':
            payment_method.is_active = False
            payment_method.save()
            messages.success(request, f'Payment method "{payment_method.name}" deleted successfully.')
            return redirect('budgets:payment_methods')

        return render(request, 'budgets/payment_method_delete.html', {
            'current_space': current_space,
            'payment_method': payment_method,
        })

    except PaymentMethod.DoesNotExist:
        messages.error(request, 'Payment method not found.')
        return redirect('budgets:payment_methods')


@login_required
@require_http_methods(["DELETE"])
def budget_delete_api(request, budget_id):
    """API endpoint for budget deletion with confirmation and audit trail"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return JsonResponse({'success': False, 'error': 'Please select a space'}, status=400)

    try:
        # Get budget with related data
        budget = Budget.objects.select_related('category', 'assigned_to', 'created_by').prefetch_related(
            'splits__user'
        ).get(
            id=budget_id,
            space=current_space,
            is_active=True
        )

        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)

        # Validate confirmation
        confirmation = data.get('confirmation', '').strip()
        if confirmation != 'ELIMINAR':
            return JsonResponse({
                'success': False,
                'error': 'Confirmación incorrecta. Debes escribir exactamente "ELIMINAR"'
            }, status=400)

        # Check permissions - only budget creator, space owner, or assigned user can delete
        user_can_delete = (
            request.user == budget.created_by or
            request.user == budget.assigned_to or
            current_space.owner == request.user or
            current_space.members.filter(user=request.user, role='admin').exists()
        )

        if not user_can_delete:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para eliminar este presupuesto'
            }, status=403)

        # Prepare undo data before deletion
        undo_data = {
            'budget_id': budget.id,
            'space_id': current_space.id,
            'category_id': budget.category.id,
            'amount': str(budget.amount),
            'month_period': budget.month_period,
            'assigned_to_id': budget.assigned_to.id if budget.assigned_to else None,
            'notes': budget.notes,
            'created_by_id': budget.created_by.id,
            'payment_method_id': budget.payment_method.id if budget.payment_method else None,
            'timing_type': budget.timing_type if hasattr(budget, 'timing_type') else 'flexible',
            'due_date': budget.due_date.isoformat() if hasattr(budget, 'due_date') and budget.due_date else None,
            'range_start': budget.range_start.isoformat() if hasattr(budget, 'range_start') and budget.range_start else None,
            'range_end': budget.range_end.isoformat() if hasattr(budget, 'range_end') and budget.range_end else None,
            'is_estimated': budget.is_estimated,
            'is_recurring': budget.is_recurring,
            'recurrence_type': budget.recurrence_type if hasattr(budget, 'recurrence_type') else None,
            'timestamp': timezone.now().isoformat(),
            'deleted_by_id': request.user.id,
        }

        # Store splits data for undo
        splits_data = []
        for split in budget.splits.all():
            splits_data.append({
                'user_id': split.user.id,
                'split_type': getattr(split, 'split_type', 'percentage'),
                'percentage': str(split.percentage) if hasattr(split, 'percentage') and split.percentage else None,
                'amount': str(split.amount) if hasattr(split, 'amount') and split.amount else None,
            })
        undo_data['splits'] = splits_data

        # Audit trail data
        audit_data = data.get('audit_data', {})
        audit_info = {
            'user_id': request.user.id,
            'user_email': request.user.email,
            'ip_address': audit_data.get('ip', request.META.get('REMOTE_ADDR', 'Unknown')),
            'user_agent': audit_data.get('user_agent', request.META.get('HTTP_USER_AGENT', 'Unknown')),
            'timestamp': audit_data.get('timestamp', timezone.now().isoformat()),
            'budget_name': budget.category.name,
            'budget_amount': str(budget.amount),
            'space_name': current_space.name,
        }

        with transaction.atomic():
            # Delete the budget
            budget_name = budget.category.name
            budget.delete()

            # Log deletion for audit
            from django.contrib.admin.models import LogEntry, DELETION
            from django.contrib.contenttypes.models import ContentType

            LogEntry.objects.create(
                user=request.user,
                content_type=ContentType.objects.get_for_model(Budget),
                object_id=budget_id,
                object_repr=budget_name,
                action_flag=DELETION,
                change_message=f"Budget deleted via API. Audit: {json.dumps(audit_info)}"
            )

        # Calculate updated totals
        remaining_budgets = Budget.objects.filter(
            space=current_space,
            month_period=budget.month_period,
            is_active=True
        )

        total_budgeted = remaining_budgets.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        total_spent = Decimal('0.00')  # Will be calculated when expenses are implemented
        remaining = total_budgeted - total_spent
        spent_percentage = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0

        return JsonResponse({
            'success': True,
            'message': f'Presupuesto "{budget_name}" eliminado correctamente',
            'undo_data': undo_data,
            'updated_totals': {
                'total_budgeted': str(total_budgeted),
                'total_spent': str(total_spent),
                'remaining': str(remaining),
                'spent_percentage': float(spent_percentage),
            }
        })

    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Presupuesto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def budget_undo_delete_api(request):
    """API endpoint to undo budget deletion"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return JsonResponse({'success': False, 'error': 'Please select a space'}, status=400)

    try:
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)

        undo_data = data.get('undo_data')
        if not undo_data:
            return JsonResponse({'success': False, 'error': 'No undo data provided'}, status=400)

        # Validate that the undo request is recent (within 5 minutes)
        deletion_time = timezone.datetime.fromisoformat(undo_data.get('timestamp', ''))
        if timezone.now() - deletion_time > timezone.timedelta(minutes=5):
            return JsonResponse({
                'success': False,
                'error': 'El tiempo para deshacer la eliminación ha expirado (máximo 5 minutos)'
            }, status=400)

        # Validate space and user permissions
        if undo_data.get('space_id') != current_space.id:
            return JsonResponse({'success': False, 'error': 'Invalid space'}, status=403)

        deleted_by_id = undo_data.get('deleted_by_id')
        if request.user.id != deleted_by_id:
            # Allow space admins to undo deletions
            if not (current_space.owner == request.user or
                   current_space.members.filter(user=request.user, role='admin').exists()):
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para deshacer esta eliminación'
                }, status=403)

        with transaction.atomic():
            # Recreate budget from undo data
            category = BudgetCategory.objects.get(id=undo_data.get('category_id'))
            created_by = User.objects.get(id=undo_data.get('created_by_id'))
            assigned_to = None
            if undo_data.get('assigned_to_id'):
                assigned_to = User.objects.get(id=undo_data.get('assigned_to_id'))

            payment_method = None
            if undo_data.get('payment_method_id'):
                payment_method = PaymentMethod.objects.get(id=undo_data.get('payment_method_id'))

            # Parse dates
            due_date = None
            if undo_data.get('due_date'):
                due_date = timezone.datetime.fromisoformat(undo_data.get('due_date')).date()

            range_start = None
            if undo_data.get('range_start'):
                range_start = timezone.datetime.fromisoformat(undo_data.get('range_start')).date()

            range_end = None
            if undo_data.get('range_end'):
                range_end = timezone.datetime.fromisoformat(undo_data.get('range_end')).date()

            # Recreate budget
            budget = Budget.objects.create(
                space=current_space,
                category=category,
                amount=Decimal(undo_data.get('amount')),
                month_period=undo_data.get('month_period'),
                assigned_to=assigned_to,
                notes=undo_data.get('notes', ''),
                created_by=created_by,
                payment_method=payment_method,
                is_estimated=undo_data.get('is_estimated', False),
                is_recurring=undo_data.get('is_recurring', False),
            )

            # Set additional fields if they exist in the model
            if hasattr(budget, 'timing_type'):
                budget.timing_type = undo_data.get('timing_type', 'flexible')
            if hasattr(budget, 'due_date'):
                budget.due_date = due_date
            if hasattr(budget, 'range_start'):
                budget.range_start = range_start
            if hasattr(budget, 'range_end'):
                budget.range_end = range_end
            if hasattr(budget, 'recurrence_type'):
                budget.recurrence_type = undo_data.get('recurrence_type')

            budget.save()

            # Recreate splits
            for split_data in undo_data.get('splits', []):
                user = User.objects.get(id=split_data['user_id'])

                split_kwargs = {
                    'budget': budget,
                    'user': user,
                }

                # Handle different BudgetSplit model structures
                if split_data.get('percentage'):
                    split_kwargs['percentage'] = Decimal(split_data['percentage'])
                if split_data.get('amount'):
                    split_kwargs['amount'] = Decimal(split_data['amount'])

                BudgetSplit.objects.create(**split_kwargs)

            # Log restoration for audit
            from django.contrib.admin.models import LogEntry, ADDITION
            from django.contrib.contenttypes.models import ContentType

            LogEntry.objects.create(
                user=request.user,
                content_type=ContentType.objects.get_for_model(Budget),
                object_id=budget.id,
                object_repr=str(budget),
                action_flag=ADDITION,
                change_message=f"Budget deletion undone via API by {request.user.email}"
            )

        return JsonResponse({
            'success': True,
            'message': f'Presupuesto restaurado correctamente',
        })

    except (BudgetCategory.DoesNotExist, User.DoesNotExist, PaymentMethod.DoesNotExist) as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al restaurar: datos de referencia no encontrados'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
