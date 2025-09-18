from django.contrib import admin
from .models import InAppNotification, NotificationPreferences


@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__username', 'recipient__email']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'space')


@admin.register(NotificationPreferences)
class NotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'approval_requests', 'space_events', 'email_approval_requests', 'digest_frequency']
    list_filter = ['approval_requests', 'space_events', 'email_approval_requests', 'digest_frequency']
    search_fields = ['user__username', 'user__email']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')