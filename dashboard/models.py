from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


# Dashboard primarily uses models from other apps
# But we can add dashboard-specific models for customization

class DashboardWidget(models.Model):
    """
    Customizable dashboard widgets for different user roles
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    widget_type = models.CharField(
        max_length=50,
        choices=[
            ('stats', 'Statistics Card'),
            ('chart', 'Chart'),
            ('table', 'Data Table'),
            ('list', 'List View'),
            ('calendar', 'Calendar'),
            ('activity', 'Activity Feed'),
        ]
    )

    # Configuration
    config = models.JSONField(default=dict, blank=True)
    position = models.IntegerField(default=0)
    size = models.CharField(
        max_length=20,
        choices=[
            ('small', 'Small (1/4 width)'),
            ('medium', 'Medium (1/2 width)'),
            ('large', 'Large (Full width)'),
        ],
        default='medium'
    )

    # Permissions
    roles = models.JSONField(default=list, blank=True)  # ['admin', 'agent', etc.]

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.name


class UserDashboardPreference(models.Model):
    """
    User-specific dashboard preferences and customization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_preference')

    # Layout preferences
    layout = models.CharField(
        max_length=20,
        choices=[
            ('default', 'Default Layout'),
            ('compact', 'Compact Layout'),
            ('expanded', 'Expanded Layout'),
        ],
        default='default'
    )

    # Widget visibility
    visible_widgets = models.JSONField(default=list, blank=True)
    hidden_widgets = models.JSONField(default=list, blank=True)

    # Display preferences
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light Theme'),
            ('dark', 'Dark Theme'),
            ('auto', 'Auto (System)'),
        ],
        default='light'
    )

    default_view = models.CharField(
        max_length=50,
        choices=[
            ('dashboard', 'Dashboard'),
            ('tickets', 'Tickets'),
            ('conversations', 'Conversations'),
            ('analytics', 'Analytics'),
        ],
        default='dashboard'
    )

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sound_notifications = models.BooleanField(default=False)

    # Filters and sorting
    default_ticket_filter = models.JSONField(default=dict, blank=True)
    default_ticket_sort = models.CharField(max_length=50, default='-created_at')

    # Refresh settings
    auto_refresh = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(default=60)  # seconds

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dashboard Preference'
        verbose_name_plural = 'Dashboard Preferences'

    def __str__(self):
        return f"{self.user.username}'s Dashboard Preferences"


class SavedFilter(models.Model):
    """
    User-saved filters for tickets and conversations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_filters')

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    filter_type = models.CharField(
        max_length=20,
        choices=[
            ('ticket', 'Ticket Filter'),
            ('conversation', 'Conversation Filter'),
            ('analytics', 'Analytics Filter'),
        ]
    )

    # Filter configuration
    filters = models.JSONField(default=dict)

    # Sharing
    is_shared = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class QuickAction(models.Model):
    """
    Quick action shortcuts for common tasks
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-bolt')

    action_type = models.CharField(
        max_length=50,
        choices=[
            ('create_ticket', 'Create Ticket'),
            ('bulk_update', 'Bulk Update'),
            ('export_data', 'Export Data'),
            ('generate_report', 'Generate Report'),
            ('assign_agent', 'Assign to Agent'),
            ('custom', 'Custom Action'),
        ]
    )

    # Action configuration
    config = models.JSONField(default=dict, blank=True)

    # Permissions
    required_role = models.CharField(
        max_length=20,
        choices=[
            ('viewer', 'Viewer'),
            ('agent', 'Agent'),
            ('admin', 'Admin'),
            ('owner', 'Owner'),
        ],
        default='agent'
    )

    is_active = models.BooleanField(default=True)
    position = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'name']

    def __str__(self):
        return self.name


class DashboardNote(models.Model):
    """
    Personal notes and reminders on dashboard
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_notes')

    title = models.CharField(max_length=200)
    content = models.TextField()

    color = models.CharField(
        max_length=20,
        choices=[
            ('yellow', 'Yellow'),
            ('blue', 'Blue'),
            ('green', 'Green'),
            ('red', 'Red'),
            ('purple', 'Purple'),
        ],
        default='yellow'
    )

    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    reminder_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title
