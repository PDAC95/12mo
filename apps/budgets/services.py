from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import Budget
from .approval_models import BudgetChangeRequest, ChangeHistoryLog
from spaces.models import SpaceSettings


class BudgetChangeService:
    """Service for handling budget changes with approval workflow"""

    @staticmethod
    def request_change(budget_item, requested_by, change_type, new_values, reason=''):
        """
        Request a change to a budget item, checking if approval is needed

        Args:
            budget_item: The Budget instance to change
            requested_by: User requesting the change
            change_type: Type of change ('amount', 'assignment', 'date', 'delete')
            new_values: Dict with new values
            reason: Optional reason for the change

        Returns:
            tuple: (change_request_or_none, applied_immediately)
        """

        # Get current values
        old_values = BudgetChangeService._get_current_values(budget_item, change_type)

        # Check if approval is required
        space_settings = budget_item.space.settings
        requires_approval = BudgetChangeService._requires_approval(
            space_settings, change_type, old_values, new_values, budget_item
        )

        if not requires_approval:
            # Apply change immediately
            BudgetChangeService._apply_change_directly(
                budget_item, change_type, old_values, new_values, requested_by
            )
            return None, True

        else:
            # Create change request for approval
            change_request = BudgetChangeRequest.objects.create(
                budget_item=budget_item,
                requested_by=requested_by,
                change_type=change_type,
                old_values=old_values,
                new_values=new_values,
                reason=reason
            )

            # Send notifications to other space members
            BudgetChangeService._send_approval_notifications(change_request)

            return change_request, False

    @staticmethod
    def _get_current_values(budget_item, change_type):
        """Get current values for the specific change type"""
        if change_type == 'amount':
            return {
                'amount': float(budget_item.amount),
                'category_name': budget_item.category.name
            }

        elif change_type == 'assignment':
            return {
                'assigned_to': budget_item.assigned_to.id if budget_item.assigned_to else None,
                'assigned_to_name': budget_item.assigned_to.username if budget_item.assigned_to else 'Unassigned',
                'category_name': budget_item.category.name
            }

        elif change_type == 'date':
            return {
                'expected_day': budget_item.expected_day,
                'next_due_date': budget_item.next_due_date.strftime('%Y-%m-%d') if budget_item.next_due_date else None,
                'category_name': budget_item.category.name
            }

        elif change_type == 'recurrence':
            return {
                'is_recurring': budget_item.is_recurring,
                'recurrence_type': budget_item.recurrence_type,
                'category_name': budget_item.category.name
            }

        elif change_type == 'delete':
            return {
                'category_name': budget_item.category.name,
                'amount': float(budget_item.amount),
                'assigned_to_name': budget_item.assigned_to.username if budget_item.assigned_to else 'Unassigned'
            }

        return {}

    @staticmethod
    def _requires_approval(space_settings, change_type, old_values, new_values, budget_item):
        """Check if a change requires approval based on space settings"""

        # Determine if expense is shared (has assignment or multiple members)
        from spaces.models import SpaceMember
        member_count = SpaceMember.objects.filter(
            space=budget_item.space,
            is_active=True
        ).count()
        is_shared = member_count > 1

        # Determine if it's recurring
        is_recurring = budget_item.is_recurring

        return space_settings.requires_approval_for_change(
            change_type=change_type,
            old_amount=Decimal(str(old_values.get('amount', 0))) if 'amount' in old_values else None,
            new_amount=Decimal(str(new_values.get('amount', 0))) if 'amount' in new_values else None,
            is_shared=is_shared,
            is_recurring=is_recurring
        )

    @staticmethod
    def _apply_change_directly(budget_item, change_type, old_values, new_values, changed_by):
        """Apply a change directly without approval"""

        if change_type == 'amount':
            budget_item.amount = Decimal(str(new_values.get('amount')))

        elif change_type == 'assignment':
            from django.contrib.auth import get_user_model
            User = get_user_model()
            assigned_to_id = new_values.get('assigned_to')
            if assigned_to_id:
                budget_item.assigned_to = User.objects.get(id=assigned_to_id)
            else:
                budget_item.assigned_to = None

        elif change_type == 'date':
            budget_item.expected_day = new_values.get('expected_day')
            if 'next_due_date' in new_values and new_values['next_due_date']:
                from datetime import datetime
                budget_item.next_due_date = datetime.strptime(
                    new_values['next_due_date'], '%Y-%m-%d'
                ).date()

        elif change_type == 'recurrence':
            budget_item.is_recurring = new_values.get('is_recurring', False)
            budget_item.recurrence_type = new_values.get('recurrence_type')

        elif change_type == 'delete':
            budget_item.is_active = False

        budget_item.save()

        # Log the change
        ChangeHistoryLog.objects.create(
            space=budget_item.space,
            change_request=None,  # No approval request for direct changes
            change_type=change_type,
            old_value=old_values,
            new_value=new_values,
            changed_by=changed_by,
            was_auto_approved=False
        )

    @staticmethod
    def _send_approval_notifications(change_request):
        """Send notifications to space members about pending approval"""
        from notifications.services import NotificationService
        return NotificationService.send_approval_request_notification(change_request)

    @staticmethod
    def check_expired_requests():
        """Check for expired requests and auto-approve them"""
        expired_requests = BudgetChangeRequest.objects.filter(
            status='pending',
            expires_at__lte=timezone.now()
        )

        auto_approved_count = 0
        for request in expired_requests:
            if request.check_auto_approval():
                auto_approved_count += 1

        return auto_approved_count

    @staticmethod
    def get_pending_approvals_for_user(user):
        """Get all pending approval requests for a specific user"""
        from spaces.models import SpaceMember

        # Get all spaces user is a member of
        user_spaces = SpaceMember.objects.filter(
            user=user,
            is_active=True
        ).values_list('space_id', flat=True)

        # Get pending requests in those spaces, excluding user's own requests
        pending_requests = BudgetChangeRequest.objects.filter(
            budget_item__space_id__in=user_spaces,
            status='pending'
        ).exclude(
            requested_by=user
        ).exclude(
            votes__user=user  # Exclude already voted
        )

        return pending_requests

    @staticmethod
    def get_space_change_history(space, limit=20):
        """Get recent change history for a space"""
        return ChangeHistoryLog.objects.filter(
            space=space
        ).order_by('-timestamp')[:limit]


class BudgetInsightsService:
    """Service for generating budget insights and recommendations"""

    @staticmethod
    def generate_monthly_insights(space, month_period):
        """Generate insights for a space's budget performance"""
        insights = []

        # Get all budgets for the month
        budgets = Budget.objects.filter(
            space=space,
            month_period=month_period,
            is_active=True
        )

        total_budgeted = sum(budget.amount for budget in budgets)
        total_spent = sum(budget.total_spent for budget in budgets)

        # Overall budget performance
        if total_budgeted > 0:
            overall_percentage = (total_spent / total_budgeted) * 100

            if overall_percentage > 110:
                insights.append({
                    'type': 'overspend_critical',
                    'title': 'Critical Overspending',
                    'message': f'You\'ve spent {overall_percentage:.1f}% of your total budget. Consider reviewing your expenses.',
                    'amount': total_spent - total_budgeted,
                    'category': 'overall'
                })
            elif overall_percentage < 80:
                insights.append({
                    'type': 'savings_opportunity',
                    'title': 'Great Savings!',
                    'message': f'You\'re {100 - overall_percentage:.1f}% under budget. Consider allocating savings to goals.',
                    'amount': total_budgeted - total_spent,
                    'category': 'overall'
                })

        # Category-specific insights
        for budget in budgets:
            if budget.is_estimated:
                variance = budget.get_spending_variance()

                if variance > 15:  # 15% over estimate
                    insights.append({
                        'type': 'overspend_warning',
                        'title': f'{budget.category.name} Over Estimate',
                        'message': f'Spending {variance:.1f}% more than estimated. Consider adjusting estimate.',
                        'amount': budget.total_spent - budget.amount,
                        'category': budget.category.name
                    })
                elif variance < -15:  # 15% under estimate
                    insights.append({
                        'type': 'savings_opportunity',
                        'title': f'{budget.category.name} Under Estimate',
                        'message': f'Spending {abs(variance):.1f}% less than estimated. Good job!',
                        'amount': budget.amount - budget.total_spent,
                        'category': budget.category.name
                    })

        return insights

    @staticmethod
    def get_balance_recommendations(space):
        """Get recommendations for balancing member expenses"""
        # This would calculate who owes what and suggest balancing actions
        # Implementation depends on expense splitting logic
        return []

    @staticmethod
    def predict_monthly_spending(budget_item):
        """Predict monthly spending based on historical data"""
        if not budget_item.is_estimated:
            return budget_item.amount

        # Calculate average from historical data
        average_spending = budget_item.get_average_real_spending()
        return average_spending