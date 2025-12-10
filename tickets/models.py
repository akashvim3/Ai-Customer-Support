from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import uuid


class Ticket(models.Model):
    """
    Core ticket model for customer support requests
    """
    # Identifiers
    meta = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_id = models.CharField(max_length=50, unique=True, editable=False)

    # Customer Information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_id = models.CharField(max_length=100, blank=True)  # For external customer ID

    # Ticket Content
    title = models.CharField(max_length=500)
    description = models.TextField()

    # Categorization & Classification
    category = models.CharField(max_length=100, blank=True)
    subcategory = models.CharField(max_length=100, blank=True)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    priority = models.CharField(
        max_length=20,
        choices=[
            ('urgent', 'Urgent'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        default='medium'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('new', 'New'),
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('pending', 'Pending'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('reopened', 'Reopened'),
        ],
        default='new'
    )

    # Assignment
    assigned_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    assigned_team = models.CharField(max_length=100, blank=True)

    # SLA & Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)

    # SLA Status
    sla_status = models.CharField(
        max_length=20,
        choices=[
            ('within_sla', 'Within SLA'),
            ('warning', 'SLA Warning'),
            ('breached', 'SLA Breached'),
        ],
        default='within_sla'
    )
    sla_breach_time = models.DateTimeField(null=True, blank=True)

    # Source & Channel
    source = models.CharField(
        max_length=50,
        choices=[
            ('email', 'Email'),
            ('web', 'Web Form'),
            ('chatbot', 'Chatbot'),
            ('phone', 'Phone'),
            ('api', 'API'),
            ('mobile', 'Mobile App'),
            ('social', 'Social Media'),
        ],
        default='web'
    )

    # AI Analysis
    ai_confidence = models.FloatField(default=0.0)
    ai_suggestions = models.JSONField(default=dict, blank=True)
    sentiment_analysis = models.JSONField(default=dict, blank=True)

    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolution_time_minutes = models.IntegerField(null=True, blank=True)
    customer_satisfaction = models.IntegerField(null=True, blank=True)

    # Flags
    is_escalated = models.BooleanField(default=False)
    escalation_reason = models.TextField(blank=True)
    is_spam = models.BooleanField(default=False)
    requires_follow_up = models.BooleanField(default=False)

    # External References
    external_id = models.CharField(max_length=100, blank=True)
    integration_data = models.JSONField(default=dict, blank=True)

    # Attachments
    has_attachments = models.BooleanField(default=False)

    class Meta:
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['ticket_id']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_agent', 'status']),
            models.Index(fields=['customer_email']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = f"TKT-{timezone.now().strftime('%Y%m%d')}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.title[:50]}"


class TicketComment(models.Model):
    """
    Comments and responses on tickets
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    content = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal note vs customer response
    is_automated = models.BooleanField(default=False)  # AI-generated response

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # AI Analysis
    sentiment_analysis = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.ticket.ticket_id} by {self.author.username}"


class TicketHistory(models.Model):
    """
    Audit trail for ticket changes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    action = models.CharField(max_length=100)
    field_changed = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.ticket.ticket_id} - {self.action}"


class TicketAttachment(models.Model):
    """
    File attachments for tickets
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')

    file = models.FileField(upload_to='ticket_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100)

    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']


class SLAPolicy(models.Model):
    """
    SLA policies for different ticket types
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Conditions
    priority = models.CharField(max_length=20, choices=Ticket.meta.get_field('priority').choices)
    category = models.CharField(max_length=100, blank=True)

    # Time targets (in hours)
    first_response_time = models.IntegerField(default=1)
    resolution_time = models.IntegerField(default=24)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "SLA Policies"


class TicketTemplate(models.Model):
    """
    Pre-defined templates for common tickets
    """
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description_template = models.TextField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
