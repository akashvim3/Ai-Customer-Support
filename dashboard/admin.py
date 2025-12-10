from django.contrib import admin
from .models import (
    DashboardWidget, UserDashboardPreference, SavedFilter,
    QuickAction, DashboardNote
)


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'size', 'position', 'is_active']
    list_filter = ['widget_type', 'size', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'widget_type', 'size', 'position')
        }),
        ('Configuration', {
            'fields': ('config', 'roles')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserDashboardPreference)
class UserDashboardPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'layout', 'theme', 'default_view',
        'auto_refresh', 'refresh_interval'
    ]
    list_filter = ['layout', 'theme', 'default_view', 'auto_refresh']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Layout Preferences', {
            'fields': ('layout', 'visible_widgets', 'hidden_widgets')
        }),
        ('Display Preferences', {
            'fields': ('theme', 'default_view')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'push_notifications', 'sound_notifications')
        }),
        ('Filters & Sorting', {
            'fields': ('default_ticket_filter', 'default_ticket_sort')
        }),
        ('Refresh Settings', {
            'fields': ('auto_refresh', 'refresh_interval')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'filter_type', 'is_shared',
        'is_default', 'usage_count', 'last_used'
    ]
    list_filter = ['filter_type', 'is_shared', 'is_default']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']

    actions = ['make_shared', 'make_private', 'set_as_default']

    def make_shared(self, request, queryset):
        queryset.update(is_shared=True)
        self.message_user(request, f"{queryset.count()} filters marked as shared")

    make_shared.short_description = "Mark selected filters as shared"

    def make_private(self, request, queryset):
        queryset.update(is_shared=False)
        self.message_user(request, f"{queryset.count()} filters marked as private")

    make_private.short_description = "Mark selected filters as private"

    def set_as_default(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one filter to set as default", level='error')
        else:
            filter_obj = queryset.first()
            SavedFilter.objects.filter(
                user=filter_obj.user,
                filter_type=filter_obj.filter_type
            ).update(is_default=False)
            queryset.update(is_default=True)
            self.message_user(request, f"{filter_obj.name} set as default")

    set_as_default.short_description = "Set as default filter"


@admin.register(QuickAction)
class QuickActionAdmin(admin.ModelAdmin):
    list_display = ['name', 'action_type', 'required_role', 'position', 'is_active']
    list_filter = ['action_type', 'required_role', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon')
        }),
        ('Action Configuration', {
            'fields': ('action_type', 'config')
        }),
        ('Permissions & Display', {
            'fields': ('required_role', 'position', 'is_active')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DashboardNote)
class DashboardNoteAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'color', 'is_pinned',
        'is_archived', 'reminder_date', 'created_at'
    ]
    list_filter = ['color', 'is_pinned', 'is_archived', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

    actions = ['pin_notes', 'unpin_notes', 'archive_notes']

    def pin_notes(self, request, queryset):
        queryset.update(is_pinned=True)
        self.message_user(request, f"{queryset.count()} notes pinned")

    pin_notes.short_description = "Pin selected notes"

    def unpin_notes(self, request, queryset):
        queryset.update(is_pinned=False)
        self.message_user(request, f"{queryset.count()} notes unpinned")

    unpin_notes.short_description = "Unpin selected notes"

    def archive_notes(self, request, queryset):
        queryset.update(is_archived=True)
        self.message_user(request, f"{queryset.count()} notes archived")

    archive_notes.short_description = "Archive selected notes"
