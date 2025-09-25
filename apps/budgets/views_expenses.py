from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
from decimal import Decimal
import json

from .models import Budget, ActualExpense, ExpenseSplit
from spaces.utils import SpaceContextManager

User = get_user_model()


@login_required
@csrf_protect
def add_expense(request, budget_id):
    """Add an actual expense to a budget item with optional splitting"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        messages.error(request, 'Please select a space to add expenses.')
        return redirect('spaces:list')

    budget = get_object_or_404(Budget, id=budget_id, space=current_space, is_active=True)

    # Get space members for splitting
    space_members = User.objects.filter(
        spacemember__space=current_space,
        spacemember__is_active=True
    ).distinct()

    if request.method == 'POST':
        try:
            # Get form data
            total_amount = Decimal(request.POST.get('total_amount', '0'))
            date_paid = request.POST.get('date_paid')
            description = request.POST.get('description', '')
            paid_by_id = request.POST.get('paid_by')
            is_shared = request.POST.get('is_shared') == 'on'
            split_type = request.POST.get('split_type', 'equal')  # equal, percentage, custom

            if total_amount <= 0:
                messages.error(request, 'Amount must be greater than 0.')
                return render(request, 'budgets/add_expense.html', {
                    'budget': budget,
                    'space_members': space_members,
                    'current_space': current_space,
                })

            paid_by = User.objects.get(id=paid_by_id)

            with transaction.atomic():
                # Create the actual expense
                expense = ActualExpense.objects.create(
                    budget_item=budget,
                    actual_amount=total_amount,
                    date_paid=date_paid,
                    month_period=budget.month_period,
                    paid_by=paid_by,
                    description=description,
                    is_shared=is_shared
                )

                if is_shared:
                    # Handle split expenses
                    splits_data = []

                    if split_type == 'equal':
                        # Split equally among selected members
                        selected_members = request.POST.getlist('split_members')
                        if not selected_members:
                            selected_members = [str(paid_by.id)]

                        percentage_per_member = Decimal('100') / len(selected_members)

                        for member_id in selected_members:
                            member = User.objects.get(id=member_id)
                            amount = (total_amount * percentage_per_member / Decimal('100')).quantize(Decimal('0.01'))
                            splits_data.append({
                                'user': member,
                                'percentage': percentage_per_member,
                                'amount': amount
                            })

                    elif split_type == 'percentage':
                        # Custom percentages
                        total_percentage = Decimal('0')
                        for member in space_members:
                            percentage_key = f'percentage_{member.id}'
                            if percentage_key in request.POST:
                                percentage = Decimal(request.POST.get(percentage_key, '0'))
                                if percentage > 0:
                                    amount = (total_amount * percentage / Decimal('100')).quantize(Decimal('0.01'))
                                    splits_data.append({
                                        'user': member,
                                        'percentage': percentage,
                                        'amount': amount
                                    })
                                    total_percentage += percentage

                        if abs(total_percentage - Decimal('100')) > Decimal('0.01'):
                            messages.error(request, f'Percentages must add up to 100%. Current total: {total_percentage}%')
                            expense.delete()
                            return render(request, 'budgets/add_expense.html', {
                                'budget': budget,
                                'space_members': space_members,
                                'current_space': current_space,
                            })

                    elif split_type == 'custom':
                        # Custom amounts
                        total_split_amount = Decimal('0')
                        for member in space_members:
                            amount_key = f'amount_{member.id}'
                            if amount_key in request.POST:
                                amount = Decimal(request.POST.get(amount_key, '0'))
                                if amount > 0:
                                    percentage = (amount / total_amount * Decimal('100')).quantize(Decimal('0.01'))
                                    splits_data.append({
                                        'user': member,
                                        'percentage': percentage,
                                        'amount': amount
                                    })
                                    total_split_amount += amount

                        if abs(total_split_amount - total_amount) > Decimal('0.01'):
                            messages.error(request, f'Split amounts must add up to total amount. Current total: ${total_split_amount}')
                            expense.delete()
                            return render(request, 'budgets/add_expense.html', {
                                'budget': budget,
                                'space_members': space_members,
                                'current_space': current_space,
                            })

                    # Create the splits
                    for split_data in splits_data:
                        ExpenseSplit.objects.create(
                            actual_expense=expense,
                            user=split_data['user'],
                            percentage=split_data['percentage'],
                            amount=split_data['amount']
                        )

                else:
                    # Single person expense
                    ExpenseSplit.objects.create(
                        actual_expense=expense,
                        user=paid_by,
                        percentage=Decimal('100'),
                        amount=total_amount
                    )

                messages.success(request, f'Expense of ${total_amount} added successfully!')
                return redirect('budgets:home')

        except Exception as e:
            messages.error(request, f'Error adding expense: {str(e)}')

    return render(request, 'budgets/add_expense.html', {
        'budget': budget,
        'space_members': space_members,
        'current_space': current_space,
    })


@login_required
def expense_calculator(request):
    """AJAX endpoint for calculating splits"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            total_amount = Decimal(str(data.get('total_amount', '0')))
            split_type = data.get('split_type', 'equal')
            members_data = data.get('members', [])

            if total_amount <= 0:
                return JsonResponse({'error': 'Invalid amount'}, status=400)

            results = []

            if split_type == 'equal':
                if not members_data:
                    return JsonResponse({'error': 'No members selected'}, status=400)

                percentage_per_member = Decimal('100') / len(members_data)
                amount_per_member = (total_amount / len(members_data)).quantize(Decimal('0.01'))

                for member_id in members_data:
                    results.append({
                        'user_id': member_id,
                        'percentage': float(percentage_per_member),
                        'amount': float(amount_per_member)
                    })

            elif split_type == 'percentage':
                for member_data in members_data:
                    percentage = Decimal(str(member_data.get('percentage', '0')))
                    amount = (total_amount * percentage / Decimal('100')).quantize(Decimal('0.01'))
                    results.append({
                        'user_id': member_data.get('user_id'),
                        'percentage': float(percentage),
                        'amount': float(amount)
                    })

            return JsonResponse({'splits': results})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=405)


@login_required
@csrf_protect
def create_expense_api(request):
    """API endpoint to create a new expense"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return JsonResponse({'success': False, 'error': 'Please select a space'}, status=400)

    try:
        budget_id = request.POST.get('budget_id')
        amount = Decimal(request.POST.get('amount', '0'))
        description = request.POST.get('description', '')
        date = request.POST.get('date')
        paid_by_id = request.POST.get('paid_by')
        notes = request.POST.get('notes', '')

        # Validation
        if not budget_id:
            return JsonResponse({'success': False, 'error': 'Budget ID is required'}, status=400)

        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Amount must be greater than 0'}, status=400)

        if not description:
            return JsonResponse({'success': False, 'error': 'Description is required'}, status=400)

        if not date:
            return JsonResponse({'success': False, 'error': 'Date is required'}, status=400)

        if not paid_by_id:
            return JsonResponse({'success': False, 'error': 'Paid by is required'}, status=400)

        # Get budget and validate
        budget = get_object_or_404(Budget, id=budget_id, space=current_space, is_active=True)
        paid_by = get_object_or_404(User, id=paid_by_id)

        # Validate paid_by is a space member
        from spaces.models import SpaceMember
        if not SpaceMember.objects.filter(space=current_space, user=paid_by, is_active=True).exists():
            return JsonResponse({'success': False, 'error': 'User must be a member of the space'}, status=400)

        with transaction.atomic():
            # Create the expense
            expense = ActualExpense.objects.create(
                budget_item=budget,
                actual_amount=amount,
                date_paid=date,
                paid_by=paid_by,
                description=description,
                is_shared=False  # For now, we'll implement basic single-person expenses
            )

            # Create a single expense split for the person who paid
            ExpenseSplit.objects.create(
                actual_expense=expense,
                user=paid_by,
                percentage=Decimal('100'),
                amount=amount
            )

        return JsonResponse({
            'success': True,
            'message': f'Expense of ${amount} added successfully!',
            'expense_id': expense.id
        })

    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error creating expense: {str(e)}'}, status=500)


@login_required
def list_expenses_api(request, budget_id):
    """API endpoint to list expenses for a specific budget"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return JsonResponse({'success': False, 'error': 'Please select a space'}, status=400)

    try:
        budget = get_object_or_404(Budget, id=budget_id, space=current_space, is_active=True)

        expenses = ActualExpense.objects.filter(
            budget_item=budget
        ).select_related('paid_by').order_by('-date_paid')

        expenses_data = []
        for expense in expenses:
            expenses_data.append({
                'id': expense.id,
                'amount': str(expense.actual_amount),
                'description': expense.description,
                'date': expense.date_paid.strftime('%Y-%m-%d'),
                'paid_by_name': expense.paid_by.first_name or expense.paid_by.username,
                'notes': getattr(expense, 'notes', ''),  # In case notes field doesn't exist
                'is_shared': expense.is_shared
            })

        return JsonResponse({
            'success': True,
            'expenses': expenses_data,
            'total_count': len(expenses_data)
        })

    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error loading expenses: {str(e)}'}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_expense_api(request, expense_id):
    """API endpoint to delete an expense"""
    current_space = SpaceContextManager.get_current_space(request)
    if not current_space:
        return JsonResponse({'success': False, 'error': 'Please select a space'}, status=400)

    try:
        expense = get_object_or_404(
            ActualExpense,
            id=expense_id,
            budget_item__space=current_space
        )

        # Check if user has permission to delete (either the person who paid or space admin)
        from spaces.models import SpaceMember
        user_member = SpaceMember.objects.filter(space=current_space, user=request.user).first()

        if expense.paid_by != request.user and (not user_member or user_member.role != 'admin'):
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        # Delete the expense (splits will be cascaded)
        expense.delete()

        return JsonResponse({
            'success': True,
            'message': 'Expense deleted successfully'
        })

    except ActualExpense.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Expense not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error deleting expense: {str(e)}'}, status=500)