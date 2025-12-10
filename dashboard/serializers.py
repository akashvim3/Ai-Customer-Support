from rest_framework import serializers
from .models import (
    DashboardWidget, UserDashboardPreference, SavedFilter,
    QuickAction, DashboardNote
)
from django.contrib.auth.models import User


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Dashboard widget serializer"""

    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'name', 'widget_type', 'config', 'position',
            'size', 'roles', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserDashboardPreferenceSerializer(serializers.ModelSerializer):
    """User dashboard preference serializer"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserDashboardPreference
        fields = [
            'id', 'user', 'username', 'layout', 'visible_widgets',
            'hidden_widgets', 'theme', 'default_view',
            'email_notifications', 'push_notifications', 'sound_notifications',
            'default_ticket_filter', 'default_ticket_sort',
            'auto_refresh', 'refresh_interval',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SavedFilterSerializer(serializers.ModelSerializer):
    """Saved filter serializer"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = SavedFilter
        fields = [
            'id', 'user', 'user_name', 'name', 'description',
            'filter_type', 'filters', 'is_shared', 'is_default',
            'usage_count', 'last_used', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'last_used', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Increment usage count on creation"""
        validated_data['usage_count'] = 1
        return super().create(validated_data)


class QuickActionSerializer(serializers.ModelSerializer):
    """Quick action serializer"""

    class Meta:
        model = QuickAction
        fields = [
            'id', 'name', 'description', 'icon', 'action_type',
            'config', 'required_role', 'is_active', 'position', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DashboardNoteSerializer(serializers.ModelSerializer):
    """Dashboard note serializer"""

    class Meta:
        model = DashboardNote
        fields = [
            'id', 'user', 'title', 'content', 'color',
            'is_pinned', 'is_archived', 'reminder_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardOverviewSerializer(serializers.Serializer):
    """Dashboard overview data serializer"""

    # Ticket stats
    total_tickets = serializers.IntegerField()
    my_tickets = serializers.IntegerField()
    unassigned_tickets = serializers.IntegerField()
    urgent_tickets = serializers.IntegerField()

    # Performance stats
    tickets_resolved_today = serializers.IntegerField()
    avg_response_time = serializers.FloatField()
    customer_satisfaction = serializers.FloatField()

    # Activity
    recent_activity = serializers.ListField()
    upcoming_tasks = serializers.ListField()

    # Trends
    ticket_trend = serializers.DictField()
    sentiment_trend = serializers.DictField()
