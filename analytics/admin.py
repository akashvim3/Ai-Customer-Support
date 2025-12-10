from django.contrib import admin
from .models import (
    AnalyticsSnapshot, AgentPerformance, CategoryPerformance,
    SentimentTrend, CustomerInsight, Report, Alert
)


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'snapshot_date', 'snapshot_type', 'total_tickets',
        'resolved_tickets', 'resolution_rate', 'avg_sentiment_score'
    ]
    list_filter = ['snapshot_type', 'snapshot_date']
    search_fields = ['snapshot_date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'snapshot_date'


@admin.register(AgentPerformance)
class AgentPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'agent', 'date', 'period_type', 'tickets_resolved',
        'avg_customer_rating', 'resolution_rate', 'performance_score'
    ]
    list_filter = ['period_type', 'date', 'agent']
    search_fields = ['agent__username', 'agent__email']
    readonly_fields = ['created_at', 'updated_at', 'performance_score']
    date_hierarchy = 'date'

    def performance_score(self, obj):
        return f"{obj.performance_score}%"

    performance_score.short_description = 'Performance Score'


@admin.register(CategoryPerformance)
class CategoryPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'date', 'total_tickets', 'resolved_tickets',
        'avg_resolution_time', 'avg_customer_satisfaction'
    ]
    list_filter = ['category', 'date']
    search_fields = ['category']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(SentimentTrend)
class SentimentTrendAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'hour', 'total_interactions', 'positive_count',
        'neutral_count', 'negative_count', 'avg_sentiment_score'
    ]
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at', 'total_interactions']
    date_hierarchy = 'date'


@admin.register(CustomerInsight)
class CustomerInsightAdmin(admin.ModelAdmin):
    list_display = [
        'customer_email', 'customer_name', 'total_tickets',
        'avg_sentiment_score', 'is_vip', 'is_at_risk', 'risk_score'
    ]
    list_filter = ['is_vip', 'is_at_risk', 'sentiment_trend']
    search_fields = ['customer_email', 'customer_name']
    readonly_fields = ['created_at', 'updated_at']

    actions = ['mark_as_vip', 'update_risk_scores']

    def mark_as_vip(self, request, queryset):
        queryset.update(is_vip=True)
        self.message_user(request, f"{queryset.count()} customers marked as VIP")

    mark_as_vip.short_description = "Mark selected customers as VIP"

    def update_risk_scores(self, request, queryset):
        for customer in queryset:
            customer.update_risk_score()
        self.message_user(request, f"Updated risk scores for {queryset.count()} customers")

    update_risk_scores.short_description = "Update risk scores"


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'report_type', 'date_from', 'date_to',
        'status', 'file_format', 'generated_by', 'created_at'
    ]
    list_filter = ['report_type', 'status', 'file_format', 'is_scheduled']
    search_fields = ['title', 'generated_by__username']
    readonly_fields = ['generated_at', 'created_at', 'file_size']
    date_hierarchy = 'created_at'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'alert_type', 'severity', 'is_resolved',
        'is_notified', 'created_at'
    ]
    list_filter = ['alert_type', 'severity', 'is_resolved', 'is_notified']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'resolved_at']
    date_hierarchy = 'created_at'

    actions = ['mark_as_resolved', 'send_notifications']

    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f"{queryset.count()} alerts marked as resolved")

    mark_as_resolved.short_description = "Mark selected alerts as resolved"

    def send_notifications(self, request, queryset):
        # Implement notification logic here
        queryset.update(is_notified=True)
        self.message_user(request, f"Notifications sent for {queryset.count()} alerts")

    send_notifications.short_description = "Send notifications for selected alerts"
