from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import InAppNotification, NotificationPreferences
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationService:
    """Service for managing all types of notifications"""

    @staticmethod
    def send_approval_request_notification(change_request):
        """Send notification about budget change approval request"""

        # Get space settings
        space_settings = change_request.budget_item.space.settings

        # Only send if notifications are enabled
        if not space_settings.notifications_in_app:
            return []

        # Get users who need to approve (exclude requester)
        from spaces.models import SpaceMember
        approvers = User.objects.filter(
            spacemember__space=change_request.budget_item.space,
            spacemember__is_active=True
        ).exclude(id=change_request.requested_by.id)

        # Filter users based on their notification preferences
        notifiable_users = []
        for user in approvers:
            prefs, created = NotificationPreferences.objects.get_or_create(user=user)
            if prefs.approval_requests:
                notifiable_users.append(user)

        # Create in-app notifications
        notifications = InAppNotification.create_approval_request(change_request, notifiable_users)

        # Send email notifications if enabled
        if space_settings.notifications_email:
            NotificationService._send_approval_request_emails(change_request, notifiable_users)

        return notifications

    @staticmethod
    def send_approval_result_notification(change_request, result_type):
        """Send notification about approval result to the requester"""

        # Check if user wants approval result notifications
        prefs, created = NotificationPreferences.objects.get_or_create(
            user=change_request.requested_by
        )

        if not prefs.approval_results:
            return None

        # Create in-app notification
        notification = InAppNotification.create_approval_result(change_request, result_type)

        # Send email if user has email notifications enabled
        space_settings = change_request.budget_item.space.settings
        if space_settings.notifications_email and prefs.email_important_only:
            NotificationService._send_approval_result_email(change_request, result_type)

        return notification

    @staticmethod
    def send_space_member_notification(space, new_member, event_type='member_joined'):
        """Send notification about space membership events"""

        # Create in-app notifications for other members
        notifications = InAppNotification.create_member_notification(space, new_member, event_type)

        return notifications

    @staticmethod
    def send_budget_reminder(user, space, overdue_items):
        """Send reminder about overdue budget items"""

        prefs, created = NotificationPreferences.objects.get_or_create(user=user)
        if not prefs.budget_reminders:
            return None

        overdue_count = len(overdue_items)
        item_names = ", ".join([item.category.name for item in overdue_items[:3]])

        if overdue_count > 3:
            item_names += f" and {overdue_count - 3} more"

        notification = InAppNotification.objects.create(
            recipient=user,
            notification_type='budget_reminder',
            priority='high',
            title=f"Budget items overdue in {space.name}",
            message=f"You have {overdue_count} overdue items: {item_names}",
            action_url=f"/budgets/?space={space.id}",
            action_text="View Budget",
            space=space
        )

        return notification

    @staticmethod
    def get_user_notifications(user, unread_only=False):
        """Get notifications for a specific user"""
        from django.db import models

        notifications = InAppNotification.objects.filter(recipient=user)

        if unread_only:
            notifications = notifications.filter(is_read=False)

        # Exclude expired notifications
        notifications = notifications.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )

        return notifications.order_by('-created_at')

    @staticmethod
    def mark_notifications_read(user, notification_ids=None):
        """Mark notifications as read"""

        notifications = InAppNotification.objects.filter(recipient=user, is_read=False)

        if notification_ids:
            notifications = notifications.filter(id__in=notification_ids)

        count = notifications.count()
        notifications.update(is_read=True, read_at=timezone.now())

        return count

    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for user"""

        from django.db import models

        return InAppNotification.objects.filter(
            recipient=user,
            is_read=False
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).count()

    @staticmethod
    def cleanup_notifications():
        """Clean up expired and old notifications"""

        # Remove expired notifications
        expired_count = InAppNotification.cleanup_expired()

        # Remove old read notifications (older than 30 days)
        old_read_count = InAppNotification.cleanup_old_read(days=30)

        return {
            'expired_removed': expired_count,
            'old_read_removed': old_read_count
        }

    @staticmethod
    def _send_approval_request_emails(change_request, recipients):
        """Send email notifications for approval requests"""

        if not settings.EMAIL_HOST:
            return  # Email not configured

        for user in recipients:
            prefs = getattr(user, 'notification_preferences', None)
            if prefs and prefs.email_approval_requests:

                context = {
                    'user': user,
                    'change_request': change_request,
                    'space': change_request.budget_item.space,
                    'item_name': change_request.budget_item.category.name,
                    'requester': change_request.requested_by,
                    'change_summary': change_request.get_change_summary(),
                }

                subject = f"Budget change approval needed - {change_request.budget_item.space.name}"

                html_message = render_to_string('notifications/emails/approval_request.html', context)
                plain_message = render_to_string('notifications/emails/approval_request.txt', context)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,  # Don't break if email fails
                )

    @staticmethod
    def _send_approval_result_email(change_request, result_type):
        """Send email notification about approval result"""

        if not settings.EMAIL_HOST:
            return  # Email not configured

        user = change_request.requested_by

        subject_map = {
            'approval_approved': f'Budget change approved - {change_request.budget_item.space.name}',
            'approval_rejected': f'Budget change rejected - {change_request.budget_item.space.name}',
            'approval_auto_approved': f'Budget change auto-approved - {change_request.budget_item.space.name}',
        }

        context = {
            'user': user,
            'change_request': change_request,
            'space': change_request.budget_item.space,
            'item_name': change_request.budget_item.category.name,
            'result_type': result_type,
        }

        subject = subject_map.get(result_type, 'Budget change update')

        html_message = render_to_string('notifications/emails/approval_result.html', context)
        plain_message = render_to_string('notifications/emails/approval_result.txt', context)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


class NotificationContext:
    """Context processor for notifications"""

    @staticmethod
    def notification_context(request):
        """Add notification data to template context"""
        if request.user.is_authenticated:
            unread_count = NotificationService.get_unread_count(request.user)
            recent_notifications = NotificationService.get_user_notifications(
                request.user, unread_only=False
            )[:5]  # Get 5 most recent

            return {
                'notification_count': unread_count,
                'recent_notifications': recent_notifications,
                'has_notifications': unread_count > 0,
            }

        return {
            'notification_count': 0,
            'recent_notifications': [],
            'has_notifications': False,
        }