from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
import uuid


class Conversation(models.Model):
    """
    Stores chatbot conversation sessions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True)

    # Customer Information
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    # Conversation Metadata
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # AI Analysis
    overall_sentiment = models.CharField(
        max_length=20,
        choices=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral'),
        ],
        default='neutral'
    )
    sentiment_score = models.FloatField(default=0.0)

    # Classification
    conversation_category = models.CharField(max_length=100, blank=True)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    # Escalation
    escalated_to_human = models.BooleanField(default=False)
    escalation_reason = models.TextField(blank=True)
    assigned_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_conversations'
    )

    # Rating
    customer_rating = models.IntegerField(null=True, blank=True)
    customer_feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['started_at']),
            models.Index(fields=['overall_sentiment']),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.messages = None

    def __str__(self):
        return f"Conversation {self.session_id} - {self.started_at}"


class Message(models.Model):
    """
    Individual messages in a conversation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')

    # Message Content
    content = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('user', 'User Message'),
            ('bot', 'Bot Response'),
            ('system', 'System Message'),
        ],
        default='user'
    )

    # AI Analysis
    intent = models.CharField(max_length=100, blank=True)
    entities = models.JSONField(default=dict, blank=True)
    sentiment = models.CharField(
        max_length=20,
        choices=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral'),
        ],
        default='neutral'
    )
    sentiment_score = models.FloatField(default=0.0)
    confidence_score = models.FloatField(default=0.0)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    # Attachments
    has_attachment = models.BooleanField(default=False)
    attachment_url = models.URLField(blank=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sentiment']),
        ]

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}"


class ChatbotKnowledgeBase(models.Model):
    """
    Knowledge base for chatbot responses
    """
    objects = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Question/Query
    question = models.TextField()
    intent = models.CharField(max_length=100)
    keywords = ArrayField(models.CharField(max_length=100), blank=True, default=list)

    # Answer
    answer = models.TextField()
    answer_variations = models.JSONField(default=list, blank=True)

    # Categorization
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100, blank=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    usage_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-priority', '-usage_count']
        indexes = [
            models.Index(fields=['intent']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.intent}: {self.question[:50]}"


class ChatbotTrainingData(models.Model):
    """
    Training data for improving chatbot responses
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Input
    user_query = models.TextField()
    context = models.JSONField(default=dict, blank=True)

    # Output
    bot_response = models.TextField()
    correct_response = models.TextField(blank=True)

    # Feedback
    was_helpful = models.BooleanField(null=True, blank=True)
    user_feedback = models.TextField(blank=True)

    # Classification
    intent = models.CharField(max_length=100)
    confidence = models.FloatField(default=0.0)

    # Training Status
    is_used_for_training = models.BooleanField(default=False)
    training_batch = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Training Data: {self.user_query[:50]}"