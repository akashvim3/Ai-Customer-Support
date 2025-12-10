from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import uuid


class AnalyticsSnapshot(models.Model):
    """
    Periodic snapshot of analytics data for historical tracking
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Time period
    snapshot_date = models.DateField()
    snapshot_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )

    # Ticket Metrics
    total_tickets = models.IntegerField(default=0)
    new_tickets = models.IntegerField(default=0)
    open_tickets = models.IntegerField(default=0)
    in_progress_tickets = models.IntegerField(default=0)
    resolved_tickets = models.IntegerField(default=0)
    closed_tickets = models.IntegerField(default=0)

    # Performance Metrics
    avg_first_response_time = models.FloatField(default=0.0)  # in minutes
    avg_resolution_time = models.FloatField(default=0.0)  # in minutes
    resolution_rate = models.FloatField(default=0.0)  # percentage
    sla_compliance_rate = models.FloatField(default=0.0)  # percentage

    # Chatbot Metrics
    total_conversations = models.IntegerField(default=0)
    ai_resolved_conversations = models.IntegerField(default=0)
    escalated_conversations = models.IntegerField(default=0)
    escalation_rate = models.FloatField(default=0.0)  # percentage

    # Sentiment Metrics
    positive_sentiment_count = models.IntegerField(default=0)
    neutral_sentiment_count = models.IntegerField(default=0)
    negative_sentiment_count = models.IntegerField(default=0)
    avg_sentiment_score = models.FloatField(default=0.0)

    # Customer Satisfaction
    avg_csat_score = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)

    # Agent Metrics
    total_agents = models.IntegerField(default=0)
    active_agents = models.IntegerField(default=0)
    avg_tickets_per_agent = models.FloatField(default=0.0)

    # Category Distribution (JSON)
    category_distribution = models.JSONField(default=dict, blank=True)
    priority_distribution = models.JSONField(default=dict, blank=True)
    source_distribution = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-snapshot_date']
        unique_together = ['snapshot_date', 'snapshot_type']
        indexes = [
            models.Index(fields=['snapshot_date', 'snapshot_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.snapshot_type.title()} Snapshot - {self.snapshot_date}"


class AgentPerformance(models.Model):
    """
    Track individual agent performance metrics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_metrics')

    # Time period
    date = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )

    # Ticket Metrics
    tickets_assigned = models.IntegerField(default=0)
    tickets_resolved = models.IntegerField(default=0)
    tickets_reopened = models.IntegerField(default=0)

    # Time Metrics
    avg_first_response_time = models.FloatField(default=0.0)  # minutes
    avg_resolution_time = models.FloatField(default=0.0)  # minutes
    total_active_time = models.FloatField(default=0.0)  # hours

    # Quality Metrics
    avg_customer_rating = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)
    positive_feedback_count = models.IntegerField(default=0)
    negative_feedback_count = models.IntegerField(default=0)

    # Efficiency Metrics
    resolution_rate = models.FloatField(default=0.0)  # percentage
    sla_compliance_rate = models.FloatField(default=0.0)  # percentage

    # Conversation Metrics
    conversations_handled = models.IntegerField(default=0)
    messages_sent = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'agent']
        unique_together = ['agent', 'date', 'period_type']
        indexes = [
            models.Index(fields=['agent', 'date']),
            models.Index(fields=['date', 'period_type']),
        ]

    def __str__(self):
        return f"{self.agent.get_full_name()} - {self.date}"

    @property
    def performance_score(self):
        """Calculate overall performance score (0-100)"""
        score = 0

        # Resolution rate (30%)
        score += (self.resolution_rate / 100) * 30

        # Customer rating (30%)
        if self.total_ratings > 0:
            score += (self.avg_customer_rating / 5) * 30

        # SLA compliance (20%)
        score += (self.sla_compliance_rate / 100) * 20

        # Response time (20%) - inverse relationship
        if self.avg_first_response_time > 0:
            # Better score for faster response times
            time_score = max(0, 20 - (self.avg_first_response_time / 60))  # assuming 60 min target
            score += time_score

        return round(min(score, 100), 2)


class CategoryPerformance(models.Model):
    """
    Track performance metrics by ticket category
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    category = models.CharField(max_length=100)
    date = models.DateField()

    # Volume Metrics
    total_tickets = models.IntegerField(default=0)
    resolved_tickets = models.IntegerField(default=0)

    # Time Metrics
    avg_resolution_time = models.FloatField(default=0.0)  # minutes
    avg_first_response_time = models.FloatField(default=0.0)  # minutes

    # Quality Metrics
    avg_customer_satisfaction = models.FloatField(default=0.0)
    reopened_count = models.IntegerField(default=0)

    # AI Metrics
    ai_classification_accuracy = models.FloatField(default=0.0)  # percentage
    avg_ai_confidence = models.FloatField(default=0.0)

    # Sentiment
    avg_sentiment_score = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'category']
        unique_together = ['category', 'date']
        indexes = [
            models.Index(fields=['category', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.category} - {self.date}"


class SentimentTrend(models.Model):
    """
    Track sentiment trends over time
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    date = models.DateField()
    hour = models.IntegerField(null=True, blank=True)  # For hourly tracking

    # Sentiment Counts
    positive_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)

    # Average Scores
    avg_sentiment_score = models.FloatField(default=0.0)

    # Source breakdown
    ticket_sentiment_avg = models.FloatField(default=0.0)
    chat_sentiment_avg = models.FloatField(default=0.0)

    # Category-wise sentiment (JSON)
    category_sentiment = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-hour']
        unique_together = ['date', 'hour']
        indexes = [
            models.Index(fields=['date', 'hour']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        if self.hour is not None:
            return f"Sentiment Trend - {self.date} {self.hour:02d}:00"
        return f"Sentiment Trend - {self.date}"

    @property
    def total_interactions(self):
        return self.positive_count + self.neutral_count + self.negative_count

    @property
    def sentiment_distribution(self):
        total = self.total_interactions
        if total == 0:
            return {'positive': 0, 'neutral': 0, 'negative': 0}

        return {
            'positive': round((self.positive_count / total) * 100, 2),
            'neutral': round((self.neutral_count / total) * 100, 2),
            'negative': round((self.negative_count / total) * 100, 2)
        }


class CustomerInsight(models.Model):
    """
    Store customer-specific insights and history
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer_email = models.EmailField(unique=True)
    customer_name = models.CharField(max_length=200, blank=True)

    # Interaction Metrics
    total_tickets = models.IntegerField(default=0)
    total_conversations = models.IntegerField(default=0)
    total_interactions = models.IntegerField(default=0)

    # Sentiment History
    avg_sentiment_score = models.FloatField(default=0.0)
    sentiment_trend = models.CharField(
        max_length=20,
        choices=[
            ('improving', 'Improving'),
            ('stable', 'Stable'),
            ('declining', 'Declining'),
        ],
        default='stable'
    )

    # Satisfaction
    avg_satisfaction_rating = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)

    # Engagement
    last_interaction_date = models.DateTimeField(null=True, blank=True)
    first_interaction_date = models.DateTimeField(null=True, blank=True)
    days_since_last_interaction = models.IntegerField(default=0)

    # Issue Categories
    top_categories = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True
    )

    # Status
    is_vip = models.BooleanField(default=False)
    is_at_risk = models.BooleanField(default=False)
    risk_score = models.FloatField(default=0.0)  # 0-100

    # Preferences (JSON)
    preferences = models.JSONField(default=dict, blank=True)
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['customer_email']),
            models.Index(fields=['is_at_risk']),
            models.Index(fields=['is_vip']),
            models.Index(fields=['last_interaction_date']),
        ]

    def __str__(self):
        return f"{self.customer_name or self.customer_email}"

    def update_risk_score(self):
        """Calculate customer risk score based on various factors"""
        risk = 0

        # Negative sentiment
        if self.avg_sentiment_score < -0.3:
            risk += 30

        # Low satisfaction
        if self.total_ratings > 0 and self.avg_satisfaction_rating < 3:
            risk += 25

        # High ticket volume
        if self.total_tickets > 10:
            risk += 15

        # Recent negative trend
        if self.sentiment_trend == 'declining':
            risk += 20

        # Inactivity
        if self.days_since_last_interaction > 90:
            risk += 10

        self.risk_score = min(risk, 100)
        self.is_at_risk = risk >= 50
        self.save()


class Report(models.Model):
    """
    Generated reports for download and scheduling
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200)
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('ticket_summary', 'Ticket Summary'),
            ('agent_performance', 'Agent Performance'),
            ('sentiment_analysis', 'Sentiment Analysis'),
            ('customer_insights', 'Customer Insights'),
            ('custom', 'Custom Report'),
        ]
    )

    # Parameters
    date_from = models.DateField()
    date_to = models.DateField()
    filters = models.JSONField(default=dict, blank=True)

    # File
    file = models.FileField(upload_to='reports/%Y/%m/', null=True, blank=True)
    file_format = models.CharField(
        max_length=10,
        choices=[
            ('pdf', 'PDF'),
            ('csv', 'CSV'),
            ('xlsx', 'Excel'),
            ('json', 'JSON'),
        ],
        default='pdf'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )

    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    file_size = models.IntegerField(default=0)  # in bytes

    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['generated_by', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d')}"


class Alert(models.Model):
    """
    System alerts based on analytics thresholds
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    alert_type = models.CharField(
        max_length=50,
        choices=[
            ('sla_breach', 'SLA Breach'),
            ('high_ticket_volume', 'High Ticket Volume'),
            ('negative_sentiment', 'Negative Sentiment'),
            ('low_csat', 'Low Customer Satisfaction'),
            ('system_performance', 'System Performance'),
            ('agent_overload', 'Agent Overload'),
        ]
    )

    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )

    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)

    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )

    # Notifications
    is_notified = models.BooleanField(default=False)
    notified_users = models.ManyToManyField(User, related_name='alerts_received', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]

    def __str__(self):
        return f"{self.severity.upper()}: {self.title}"
