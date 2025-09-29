import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Dict, List, Optional, Tuple

from ..models import Budget, BudgetSplit, ActualExpense
from spaces.models import SpaceMember

User = get_user_model()
logger = logging.getLogger('budget_deletion')


class BudgetDeletionUtils:
    """Utility class for handling budget deletion logic with security validations"""

    @staticmethod
    def validate_user_permission(budget: Budget, user: User) -> Tuple[bool, str]:
        """
        Validate if user has permission to delete the budget

        Returns:
            Tuple[bool, str]: (has_permission, error_message)
        """
        try:
            # Check if user is a member of the space
            space_member = SpaceMember.objects.filter(
                space=budget.space,
                user=user,
                is_active=True
            ).first()

            if not space_member:
                return False, f"User is not a member of space '{budget.space.name}'"

            # Check if user is the budget creator or space admin
            if budget.created_by == user:
                return True, "User is budget creator"

            if space_member.role in ['admin', 'owner']:
                return True, f"User has {space_member.role} role in space"

            # Check if budget is assigned to the user
            if budget.assigned_to == user:
                return True, "Budget is assigned to user"

            return False, "User does not have permission to delete this budget"

        except Exception as e:
            logger.error(f"Error validating user permission: {str(e)}")
            return False, "Permission validation failed"

    @staticmethod
    def get_deletion_summary(budget: Budget) -> Dict:
        """
        Get comprehensive summary of what will be deleted

        Returns:
            Dict: Summary of deletion impact
        """
        try:
            # Get related budget splits
            budget_splits = BudgetSplit.objects.filter(budget=budget)

            # Get related actual expenses
            actual_expenses = ActualExpense.objects.filter(budget_item=budget)

            # Calculate totals
            total_expense_amount = sum(
                expense.actual_amount for expense in actual_expenses
            ) or Decimal('0.00')

            # Get affected users
            affected_users = set()

            # Add users from splits
            for split in budget_splits:
                affected_users.add(split.user.username)

            # Add users from expenses
            for expense in actual_expenses:
                affected_users.add(expense.paid_by.username)

            # Generate warning messages
            warning_messages = []

            if budget_splits.exists():
                warning_messages.append(
                    f"This will delete {budget_splits.count()} budget split(s) "
                    f"affecting {len(set(split.user.username for split in budget_splits))} user(s)"
                )

            if actual_expenses.exists():
                warning_messages.append(
                    f"This will delete {actual_expenses.count()} expense record(s) "
                    f"totaling ${total_expense_amount}"
                )

            if budget.is_recurring:
                warning_messages.append(
                    "This is a recurring budget - deletion will not affect future months"
                )

            return {
                'budget_id': budget.id,
                'budget_amount': budget.amount,
                'category_name': budget.category.name,
                'month_period': budget.month_period,
                'space_name': budget.space.name,
                'total_splits': budget_splits.count(),
                'total_expenses': actual_expenses.count(),
                'total_expense_amount': total_expense_amount,
                'affected_users': list(affected_users),
                'warning_messages': warning_messages,
                'can_delete': True,  # This will be set by the view based on permissions
            }

        except Exception as e:
            logger.error(f"Error getting deletion summary for budget {budget.id}: {str(e)}")
            return {
                'budget_id': budget.id,
                'can_delete': False,
                'warning_messages': ['Error analyzing deletion impact'],
            }

    @staticmethod
    @transaction.atomic
    def perform_deletion(
        budget: Budget,
        user: User,
        soft_delete: bool = False,
        notify_members: bool = True
    ) -> Dict:
        """
        Perform the actual budget deletion with cascade

        Args:
            budget: Budget instance to delete
            user: User performing the deletion
            soft_delete: Whether to perform soft delete
            notify_members: Whether to notify space members

        Returns:
            Dict: Deletion result summary
        """
        try:
            # Get counts before deletion for audit log
            budget_splits = BudgetSplit.objects.filter(budget=budget)
            actual_expenses = ActualExpense.objects.filter(budget_item=budget)

            deleted_splits_count = budget_splits.count()
            deleted_expenses_count = actual_expenses.count()

            # Store budget info for response
            budget_info = {
                'budget_id': budget.id,
                'space_id': budget.space.id,
                'category_name': budget.category.name,
                'month_period': budget.month_period,
                'deleted_at': timezone.now(),
            }

            if soft_delete:
                # Perform soft delete
                budget.soft_delete(deleted_by=user)

                # Log the soft deletion
                logger.info(
                    f"Budget soft deleted - ID: {budget.id}, "
                    f"Category: {budget.category.name}, "
                    f"Month: {budget.month_period}, "
                    f"Space: {budget.space.name}, "
                    f"User: {user.username}, "
                    f"Splits: {deleted_splits_count}, "
                    f"Expenses: {deleted_expenses_count}"
                )

                message = f"Budget '{budget.category.name}' for {budget.month_period} has been soft deleted and can be restored"

            else:
                # Hard delete - cascade will handle related objects
                logger.info(
                    f"Budget hard deletion started - ID: {budget.id}, "
                    f"Category: {budget.category.name}, "
                    f"Month: {budget.month_period}, "
                    f"Space: {budget.space.name}, "
                    f"User: {user.username}, "
                    f"Splits: {deleted_splits_count}, "
                    f"Expenses: {deleted_expenses_count}"
                )

                # Delete the budget (cascade will handle BudgetSplit and ActualExpense)
                budget.delete()

                logger.info(
                    f"Budget hard deleted successfully - ID: {budget_info['budget_id']}, "
                    f"Category: {budget_info['category_name']}, "
                    f"Month: {budget_info['month_period']}"
                )

                message = f"Budget '{budget_info['category_name']}' for {budget_info['month_period']} has been permanently deleted"

            # Create audit log entry
            audit_log_id = BudgetDeletionUtils._create_audit_log(
                budget_info=budget_info,
                user=user,
                deleted_splits_count=deleted_splits_count,
                deleted_expenses_count=deleted_expenses_count,
                is_soft_delete=soft_delete
            )

            return {
                'success': True,
                'message': message,
                'deleted_splits': deleted_splits_count,
                'deleted_expenses': deleted_expenses_count,
                'audit_log_id': audit_log_id,
                **budget_info
            }

        except Exception as e:
            logger.error(f"Error deleting budget {budget.id}: {str(e)}")
            transaction.set_rollback(True)
            return {
                'success': False,
                'message': f"Failed to delete budget: {str(e)}",
                'deleted_splits': 0,
                'deleted_expenses': 0,
            }

    @staticmethod
    def _create_audit_log(
        budget_info: Dict,
        user: User,
        deleted_splits_count: int,
        deleted_expenses_count: int,
        is_soft_delete: bool
    ) -> Optional[int]:
        """
        Create audit log entry for budget deletion

        Returns:
            Optional[int]: Audit log entry ID if successful
        """
        try:
            # For now, we'll use Python logging. In the future, this could be
            # replaced with a dedicated audit log model

            action_type = "SOFT_DELETE" if is_soft_delete else "HARD_DELETE"

            audit_message = (
                f"BUDGET_DELETION: {action_type} - "
                f"Budget ID: {budget_info['budget_id']}, "
                f"Category: {budget_info['category_name']}, "
                f"Month: {budget_info['month_period']}, "
                f"Space ID: {budget_info['space_id']}, "
                f"User: {user.username} ({user.id}), "
                f"Deleted Splits: {deleted_splits_count}, "
                f"Deleted Expenses: {deleted_expenses_count}, "
                f"Timestamp: {budget_info['deleted_at'].isoformat()}"
            )

            logger.info(audit_message)

            # Return a mock audit log ID for now
            # In a real implementation, this would return the actual audit log record ID
            return hash(audit_message) % 1000000

        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            return None

    @staticmethod
    def validate_deletion_safety(budget: Budget) -> Tuple[bool, List[str]]:
        """
        Validate if budget deletion is safe to perform

        Returns:
            Tuple[bool, List[str]]: (is_safe, error_messages)
        """
        errors = []

        try:
            # Check if budget is already soft-deleted
            if budget.is_deleted:
                errors.append("Budget is already deleted")

            # Check if budget has critical dependencies (custom validation can be added here)
            actual_expenses = ActualExpense.objects.filter(budget_item=budget)
            if actual_expenses.exists():
                total_amount = sum(expense.actual_amount for expense in actual_expenses)
                if total_amount > 1000:  # Example threshold
                    errors.append(
                        f"Budget has significant expenses (${total_amount}). "
                        "Consider archiving instead of deleting"
                    )

            # Check for recent activity
            recent_expenses = actual_expenses.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            )
            if recent_expenses.exists():
                errors.append("Budget has recent activity (expenses added in last 7 days)")

            return len(errors) == 0, errors

        except Exception as e:
            logger.error(f"Error validating deletion safety: {str(e)}")
            return False, ["Failed to validate deletion safety"]

    @staticmethod
    def get_affected_users_detail(budget: Budget) -> List[Dict]:
        """
        Get detailed information about users affected by budget deletion

        Returns:
            List[Dict]: List of affected user details
        """
        try:
            affected_users = {}

            # Users from budget splits
            budget_splits = BudgetSplit.objects.filter(budget=budget).select_related('user')
            for split in budget_splits:
                user_key = split.user.id
                if user_key not in affected_users:
                    affected_users[user_key] = {
                        'user_id': split.user.id,
                        'username': split.user.username,
                        'first_name': split.user.first_name,
                        'email': split.user.email,
                        'split_amount': Decimal('0.00'),
                        'expense_count': 0,
                        'expense_amount': Decimal('0.00'),
                    }
                affected_users[user_key]['split_amount'] += split.calculated_amount

            # Users from actual expenses
            actual_expenses = ActualExpense.objects.filter(budget_item=budget).select_related('paid_by')
            for expense in actual_expenses:
                user_key = expense.paid_by.id
                if user_key not in affected_users:
                    affected_users[user_key] = {
                        'user_id': expense.paid_by.id,
                        'username': expense.paid_by.username,
                        'first_name': expense.paid_by.first_name,
                        'email': expense.paid_by.email,
                        'split_amount': Decimal('0.00'),
                        'expense_count': 0,
                        'expense_amount': Decimal('0.00'),
                    }
                affected_users[user_key]['expense_count'] += 1
                affected_users[user_key]['expense_amount'] += expense.actual_amount

            return list(affected_users.values())

        except Exception as e:
            logger.error(f"Error getting affected users detail: {str(e)}")
            return []