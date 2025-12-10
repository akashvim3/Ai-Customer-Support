from rest_framework import serializers
from .models import (
    AnalyticsSnapshot, AgentPerformance, CategoryPerformance,
    SentimentTrend, CustomerInsight, Report, Alert
)
from django.contrib.auth.models import User


class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    """Analytics snapshot serializer"""

    class Meta:
        model = AnalyticsSnapshot
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentPerformanceSerializer(serializers.ModelSerializer):
    """Agent performance serializer"""
    agent_name = serializers.CharField(source='agent.get_full_name', read_only=True)
    agent_email = serializers.EmailField(source='agent.email', read_only=True)
    performance_score = serializers.ReadOnlyField()

    class Meta:
        model = AgentPerformance
        fields = [
            'id', 'agent', 'agent_name', 'agent_email', 'date', 'period_type',
            'tickets_assigned', 'tickets_resolved', 'tickets_reopened',
            'avg_first_response_time', 'avg_resolution_time', 'total_active_time',
            'avg_customer_rating', 'total_ratings', 'positive_feedback_count',
            'negative_feedback_count', 'resolution_rate', 'sla_compliance_rate',
            'conversations_handled', 'messages_sent', 'performance_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'performance_score']


class CategoryPerformanceSerializer(serializers.ModelSerializer):
    """Category performance serializer"""

    class Meta:
        model = CategoryPerformance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SentimentTrendSerializer(serializers.ModelSerializer):
    """Sentiment trend serializer"""
    total_interactions = serializers.ReadOnlyField()
    sentiment_distribution = serializers.ReadOnlyField()

    class Meta:
        model = SentimentTrend
        fields = [
            'id', 'date', 'hour', 'positive_count', 'neutral_count',
            'negative_count', 'avg_sentiment_score', 'ticket_sentiment_avg',
            'chat_sentiment_avg', 'category_sentiment', 'total_interactions',
            'sentiment_distribution', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'total_interactions', 'sentiment_distribution']


class CustomerInsightSerializer(serializers.ModelSerializer):
    """Customer insight serializer"""

    class Meta:
        model = CustomerInsight
        fields = [
            'id', 'customer_email', 'customer_name', 'total_tickets',
            'total_conversations', 'total_interactions', 'avg_sentiment_score',
            'sentiment_trend', 'avg_satisfaction_rating', 'total_ratings',
            'last_interaction_date', 'first_interaction_date',
            'days_since_last_interaction', 'top_categories', 'is_vip',
            'is_at_risk', 'risk_score', 'preferences', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportSerializer(serializers.ModelSerializer):
    """Report serializer"""
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'title', 'report_type', 'date_from', 'date_to',
            'filters', 'file', 'file_url', 'file_format', 'status',
            'generated_by', 'generated_by_name', 'generated_at',
            'file_size', 'is_scheduled', 'schedule_frequency', 'created_at'
        ]
        read_only_fields = ['id', 'file_url', 'file_size', 'generated_at', 'created_at']

    def get_file_url(self, obj):
        """Get full URL for report file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class AlertSerializer(serializers.ModelSerializer):
    """Alert serializer"""
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    notified_users_count = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id', 'alert_type', 'severity', 'title', 'message', 'data',
            'is_resolved', 'resolved_at', 'resolved_by', 'resolved_by_name',
            'is_notified', 'notified_users_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'notified_users_count']

    def get_notified_users_count(self, obj):
        """Get count of notified users"""
        return obj.notified_users.count()


class DashboardMetricsSerializer(serializers.Serializer):
    """Dashboard overview metrics serializer"""

    # Ticket metrics
    total_tickets = serializers.IntegerField()
    new_tickets = serializers.IntegerField()
    open_tickets = serializers.IntegerField()
    resolved_tickets = serializers.IntegerField()
    resolution_rate = serializers.FloatField()
    avg_resolution_time = serializers.FloatField()

    # Chatbot metrics
    total_conversations = serializers.IntegerField()
    ai_resolved = serializers.IntegerField()
    escalation_rate = serializers.FloatField()

    # Sentiment metrics
    avg_sentiment = serializers.FloatField()
    sentiment_distribution = serializers.DictField()

    # Performance metrics
    avg_first_response_time = serializers.FloatField()
    sla_compliance_rate = serializers.FloatField()
    avg_csat_score = serializers.FloatField()


class TrendDataSerializer(serializers.Serializer):
    """Trend data serializer"""
    dates = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.FloatField())
    label = serializers.CharField()


class ComparisonDataSerializer(serializers.Serializer):
    """Comparison data serializer"""
    current_period = serializers.DictField()
    previous_period = serializers.DictField()
    change_percentage = serializers.FloatField()
    trend = serializers.CharField()  # 'up', 'down', 'stable'
