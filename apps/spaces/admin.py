from django.contrib import admin
from .models import Space, SpaceMember


class SpaceMemberInline(admin.TabularInline):
    """Inline display of space members in Space admin"""
    model = SpaceMember
    extra = 0
    readonly_fields = ('joined_at',)
    fields = ('user', 'role', 'is_active', 'joined_at')


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    """Admin interface for Space model"""
    list_display = ('name', 'invite_code', 'created_by', 'member_count_display', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'invite_code', 'created_by__username', 'created_by__email')
    readonly_fields = ('invite_code', 'created_at', 'updated_at', 'member_count_display')
    inlines = [SpaceMemberInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Ownership & Access', {
            'fields': ('created_by', 'invite_code')
        }),
        ('Statistics', {
            'fields': ('member_count_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def member_count_display(self, obj):
        """Display member count in admin"""
        return f"{obj.member_count}/10"
    member_count_display.short_description = 'Members'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('created_by')


@admin.register(SpaceMember)
class SpaceMemberAdmin(admin.ModelAdmin):
    """Admin interface for SpaceMember model"""
    list_display = ('user', 'space', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__username', 'user__email', 'space__name')
    readonly_fields = ('joined_at',)

    fieldsets = (
        ('Membership Details', {
            'fields': ('space', 'user', 'role', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'space')
