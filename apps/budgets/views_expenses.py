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