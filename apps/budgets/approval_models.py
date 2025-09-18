from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json

User = get_user_model()


class BudgetChangeRequest(models.Model):
    """Request for changes to budget items requiring approval"""

    CHANGE_TYPE_CHOICES = [
        ('amount', 'Change amount'),
        ('assignment', 'Change assignment'),
        ('date', 'Change date'),
        ('recurrence', 'Change recurrence'),
        ('delete', 'Delete item'),
        ('create', 'Create new item'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('auto_approved', 'Auto-approved'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic info
    budget_item = models.ForeignKey(
        'Budget',
        on_delete=models.CASCADE,
        related_name='change_requests',
        help_text="Budget item being changed"
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budget_change_requests',
        help_text="User requesting the change"
    )
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        help_text="Type of change being requested"
    )

    # Change details (stored as JSON for flexibility)
    old_values = models.JSONField(
        default=dict,
        help_text="Original values before change"
    )
    new_values = models.JSONField(
        default=dict,
        help_text="Proposed new values"
    )

    # Request details
    reason = models.TextField(
        max_length=500,
        blank=True,
        help_text="Reason for the change"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the request"
    )

    # Approval tracking
    required_approvals = models.IntegerField(
        default=1,
        help_text="Number of approvals required"
    )
    received_approvals = models.IntegerField(
        default=0,
        help_text="Number of approvals received"
    )

    # Auto-approval tracking
    auto_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this was auto-approved due to timeout"
    )
    auto_approval_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Reason for auto-approval"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text="When this request expires and gets auto-approved"
    )

    class Meta:
        db_table = 'budget_change_requests'
        ordering = ['-created_at']
        verbose_name = 'Budget Change Request'
        verbose_name_plural = 'Budget Change Requests'

    def __str__(self):
        return f"{self.get_change_type_display()} for {self.budget_item.category.name} by {self.requested_by.username}"

    def clean(self):
        """Custom validation"""
        # Set expiration based on space settings
        if not self.expires_at and self.budget_item:
            space_settings = self.budget_item.space.settings
            self.expires_at = timezone.now() + timedelta(days=space_settings.approval_timeout_days)

        # Calculate required approvals based on space members
        if not self.required_approvals and self.budget_item:
            # All active members except requester need to approve
            from spaces.models import SpaceMember
            member_count = SpaceMember.objects.filter(
                space=self.budget_item.space,
                is_active=True
            ).exclude(user=self.requested_by).count()
            self.required_approvals = max(1, member_count)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def check_auto_approval(self):
        """Check if this request should be auto-approved due to timeout"""
        if self.status == 'pending' and timezone.now() >= self.expires_at:
            self.status = 'auto_approved'
            self.auto_approved_at = timezone.now()
            self.auto_approval_reason = f'Auto-approved after {self.budget_item.space.settings.approval_timeout_days} days'
            self.save()

            # Apply the change
            self.apply_change()

            # Send notification to requester
            self._send_result_notification('approval_auto_approved')

            return True
        return False

    def approve(self, user):
        """Record an approval from a user"""
        if self.status != 'pending':
            raise ValidationError('Cannot approve a request that is not pending')

        # Check if user can approve
        from spaces.models import SpaceMember
        if not SpaceMember.objects.filter(
            space=self.budget_item.space,
            user=user,
            is_active=True
        ).exclude(user=self.requested_by).exists():
            raise ValidationError('User cannot approve this request')

        # Check if user already approved
        if self.votes.filter(user=user).exists():
            raise ValidationError('User has already voted on this request')

        # Create approval vote
        BudgetChangeVote.objects.create(
            change_request=self,
            user=user,
            vote='approve'
        )

        self.received_approvals += 1

        # Check if we have enough approvals
        if self.received_approvals >= self.required_approvals:
            self.status = 'approved'
            self.apply_change()

            # Send notification to requester
            self._send_result_notification('approval_approved')

        self.save()

    def reject(self, user, reason=''):
        """Reject the request"""
        if self.status != 'pending':
            raise ValidationError('Cannot reject a request that is not pending')

        # Check if user can reject
        from spaces.models import SpaceMember
        if not SpaceMember.objects.filter(
            space=self.budget_item.space,
            user=user,
            is_active=True
        ).exclude(user=self.requested_by).exists():
            raise ValidationError('User cannot reject this request')

        # Create rejection vote
        BudgetChangeVote.objects.create(
            change_request=self,
            user=user,
            vote='reject',
            reason=reason
        )

        self.status = 'rejected'

        # Send notification to requester
        self._send_result_notification('approval_rejected')

        self.save()

    def apply_change(self):
        """Apply the approved change to the budget item"""
        if self.status not in ['approved', 'auto_approved']:
            raise ValidationError('Can only apply approved changes')

        try:
            if self.change_type == 'amount':
                self.budget_item.amount = Decimal(str(self.new_values.get('amount')))

            elif self.change_type == 'assignment':
                assigned_to_id = self.new_values.get('assigned_to')
                if assigned_to_id:
                    self.budget_item.assigned_to = User.objects.get(id=assigned_to_id)
                else:
                    self.budget_item.assigned_to = None

            elif self.change_type == 'date':
                self.budget_item.expected_day = self.new_values.get('expected_day')
                if 'next_due_date' in self.new_values:
                    from datetime import datetime
                    self.budget_item.next_due_date = datetime.strptime(
                        self.new_values['next_due_date'], '%Y-%m-%d'
                    ).date()

            elif self.change_type == 'recurrence':
                self.budget_item.is_recurring = self.new_values.get('is_recurring', False)
                self.budget_item.recurrence_type = self.new_values.get('recurrence_type')

            elif self.change_type == 'delete':
                self.budget_item.is_active = False

            self.budget_item.save()

            # Log the change
            ChangeHistoryLog.objects.create(
                space=self.budget_item.space,
                change_request=self,
                change_type=self.change_type,
                old_value=self.old_values,
                new_value=self.new_values,
                changed_by=self.requested_by,
                was_auto_approved=(self.status == 'auto_approved')
            )

        except Exception as e:
            raise ValidationError(f'Failed to apply change: {str(e)}')

    @property
    def pending_approvers(self):
        """Get users who still need to approve"""
        from spaces.models import SpaceMember
        voted_users = self.votes.values_list('user_id', flat=True)

        return User.objects.filter(
            spacemember__space=self.budget_item.space,
            spacemember__is_active=True
        ).exclude(
            id__in=voted_users
        ).exclude(
            id=self.requested_by.id
        )

    def get_change_summary(self):
        """Get human-readable summary of the change"""
        if self.change_type == 'amount':
            old_amount = self.old_values.get('amount', 0)
            new_amount = self.new_values.get('amount', 0)
            return f"Change amount from ${old_amount} to ${new_amount}"

        elif self.change_type == 'assignment':
            old_user = self.old_values.get('assigned_to_name', 'Unassigned')
            new_user = self.new_values.get('assigned_to_name', 'Unassigned')
            return f"Change assignment from {old_user} to {new_user}"

        elif self.change_type == 'delete':
            return f"Delete {self.budget_item.category.name}"

        return f"{self.get_change_type_display()}"

    def _send_result_notification(self, notification_type):
        """Send notification about approval result"""
        try:
            from notifications.services import NotificationService
            return NotificationService.send_approval_result_notification(self, notification_type)
        except ImportError:
            # Notifications not available
            pass


class BudgetChangeVote(models.Model):
    """Individual votes on budget change requests"""

    VOTE_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]

    change_request = models.ForeignKey(
        BudgetChangeRequest,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who cast this vote"
    )
    vote = models.CharField(
        max_length=10,
        choices=VOTE_CHOICES,
        help_text="The vote cast"
    )
    reason = models.TextField(
        max_length=500,
        blank=True,
        help_text="Optional reason for the vote"
    )
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'budget_change_votes'
        unique_together = [['change_request', 'user']]
        ordering = ['-voted_at']

    def __str__(self):
        return f"{self.user.username} voted {self.vote} on {self.change_request}"


class ChangeHistoryLog(models.Model):
    """Complete history of all changes for auditing"""

    space = models.ForeignKey(
        'spaces.Space',
        on_delete=models.CASCADE,
        related_name='change_history',
        help_text="Space where the change occurred"
    )
    change_request = models.ForeignKey(
        BudgetChangeRequest,
        on_delete=models.CASCADE,
        related_name='history_logs',
        help_text="The change request that caused this change"
    )
    change_type = models.CharField(
        max_length=20,
        help_text="Type of change that was made"
    )
    old_value = models.JSONField(
        help_text="Values before the change"
    )
    new_value = models.JSONField(
        help_text="Values after the change"
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who requested the change"
    )
    approved_by = models.ManyToManyField(
        User,
        related_name='approved_changes',
        blank=True,
        help_text="Users who approved this change"
    )
    was_auto_approved = models.BooleanField(
        default=False,
        help_text="Whether this change was auto-approved due to timeout"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'change_history_logs'
        ordering = ['-timestamp']
        verbose_name = 'Change History Log'
        verbose_name_plural = 'Change History Logs'

    def __str__(self):
        return f"{self.change_type} in {self.space.name} by {self.changed_by.username}"

    def get_summary(self):
        """Get human-readable summary of the change"""
        if self.change_type == 'amount':
            old_amount = self.old_value.get('amount', 0)
            new_amount = self.new_value.get('amount', 0)
            return f"Changed amount from ${old_amount} to ${new_amount}"

        elif self.change_type == 'assignment':
            old_user = self.old_value.get('assigned_to_name', 'Unassigned')
            new_user = self.new_value.get('assigned_to_name', 'Unassigned')
            return f"Changed assignment from {old_user} to {new_user}"

        elif self.change_type == 'delete':
            item_name = self.old_value.get('category_name', 'Item')
            return f"Deleted {item_name}"

        return f"Changed {self.change_type}"