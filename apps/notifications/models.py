from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class InAppNotification(models.Model):
    """In-app notifications for users"""

    NOTIFICATION_TYPES = [
        ('approval_request', 'Approval Request'),
        ('approval_approved', 'Request Approved'),
        ('approval_rejected', 'Request Rejected'),
        ('approval_auto_approved', 'Auto-approved'),
        ('space_invite', 'Space Invitation'),
        ('member_joined', 'New Member'),
        ('member_left', 'Member Left'),
        ('budget_reminder', 'Budget Reminder'),
        ('expense_added', 'Expense Added'),
        ('general', 'General'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Basic info
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who will receive this notification"
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='general',
        help_text="Type of notification"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text="Priority level of the notification"
    )

    # Content
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    message = models.TextField(
        max_length=500,
        help_text="Notification message"
    )

    # Optional action
    action_url = models.CharField(
        max_length=200,
        blank=True,
        help_text="URL to redirect when notification is clicked"
    )
    action_text = models.CharField(
        max_length=50,
        blank=True,
        help_text="Text for action button (e.g., 'Approve', 'View')"
    )

    # Related objects (optional)
    space = models.ForeignKey(
        'spaces.Space',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Related space (if applicable)"
    )

    # Metadata
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the user has read this notification"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was marked as read"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this notification expires (optional)"
    )

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.title} for {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def age_in_hours(self):
        """Get notification age in hours"""
        delta = timezone.now() - self.created_at
        return delta.total_seconds() / 3600

    @property
    def is_recent(self):
        """Check if notification is recent (less than 24 hours old)"""
        return self.age_in_hours < 24

    @classmethod
    def create_approval_request(cls, change_request, recipients):
        """Create approval request notifications for multiple recipients"""
        notifications = []

        for recipient in recipients:
            notification = cls.objects.create(
                recipient=recipient,
                notification_type='approval_request',
                priority='normal',
                title=f"Budget change approval needed",
                message=f"{change_request.requested_by.first_name or change_request.requested_by.username} "
                       f"wants to change {change_request.budget_item.category.name} "
                       f"({change_request.get_change_summary()})",
                action_url=f"/spaces/approve/{change_request.id}/",
                action_text="Review",
                space=change_request.budget_item.space,
                expires_at=change_request.expires_at
            )
            notifications.append(notification)

        return notifications

    @classmethod
    def create_approval_result(cls, change_request, notification_type):
        """Create notification when approval is approved/rejected/auto-approved"""

        title_map = {
            'approval_approved': 'Budget change approved',
            'approval_rejected': 'Budget change rejected',
            'approval_auto_approved': 'Budget change auto-approved',
        }

        message_map = {
            'approval_approved': f'Your change to {change_request.budget_item.category.name} has been approved and applied.',
            'approval_rejected': f'Your change to {change_request.budget_item.category.name} has been rejected.',
            'approval_auto_approved': f'Your change to {change_request.budget_item.category.name} was auto-approved due to timeout.',
        }

        return cls.objects.create(
            recipient=change_request.requested_by,
            notification_type=notification_type,
            priority='normal',
            title=title_map.get(notification_type, 'Budget change update'),
            message=message_map.get(notification_type, 'Your budget change has been processed.'),
            action_url=f"/budgets/",
            action_text="View Budget",
            space=change_request.budget_item.space
        )

    @classmethod
    def create_member_notification(cls, space, new_member, notification_type='member_joined'):
        """Create notifications for space events"""

        # Notify all other members about the new member
        other_members = User.objects.filter(
            spacemember__space=space,
            spacemember__is_active=True
        ).exclude(id=new_member.id)

        notifications = []
        for member in other_members:
            notification = cls.objects.create(
                recipient=member,
                notification_type=notification_type,
                priority='low',
                title=f"New member joined {space.name}",
                message=f"{new_member.first_name or new_member.username} has joined your space.",
                action_url=f"/spaces/{space.id}/",
                action_text="View Space",
                space=space
            )
            notifications.append(notification)

        return notifications

    @classmethod
    def cleanup_expired(cls):
        """Remove expired notifications"""
        expired_count = cls.objects.filter(
            expires_at__lte=timezone.now()
        ).count()

        cls.objects.filter(
            expires_at__lte=timezone.now()
        ).delete()

        return expired_count

    @classmethod
    def cleanup_old_read(cls, days=30):
        """Remove old read notifications"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        old_read_count = cls.objects.filter(
            is_read=True,
            read_at__lte=cutoff_date
        ).count()

        cls.objects.filter(
            is_read=True,
            read_at__lte=cutoff_date
        ).delete()

        return old_read_count


class NotificationPreferences(models.Model):
    """User preferences for notifications"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # In-app notification preferences
    approval_requests = models.BooleanField(
        default=True,
        help_text="Receive notifications for approval requests"
    )
    approval_results = models.BooleanField(
        default=True,
        help_text="Receive notifications when your requests are approved/rejected"
    )
    space_events = models.BooleanField(
        default=True,
        help_text="Receive notifications for space events (new members, etc.)"
    )
    budget_reminders = models.BooleanField(
        default=True,
        help_text="Receive budget and expense reminders"
    )

    # Email notification preferences
    email_approval_requests = models.BooleanField(
        default=False,
        help_text="Also send approval requests via email"
    )
    email_important_only = models.BooleanField(
        default=True,
        help_text="Only send important notifications via email"
    )

    # Frequency settings
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No digest'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='none',
        help_text="How often to send notification digest emails"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preferences'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Notification preferences for {self.user.username}"


# Signal to create default notification preferences
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create default notification preferences when user is created"""
    if created:
        NotificationPreferences.objects.create(user=instance)