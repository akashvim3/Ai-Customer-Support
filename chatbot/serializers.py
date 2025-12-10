from rest_framework import serializers
from .models import Conversation, Message, ChatbotKnowledgeBase


class MessageSerializer(serializers.ModelSerializer):
    """Message serializer"""

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'content', 'message_type',
            'intent', 'entities', 'sentiment', 'sentiment_score',
            'confidence_score', 'timestamp', 'has_attachment', 'attachment_url'
        ]
        read_only_fields = ['id', 'timestamp', 'intent', 'entities',
                            'sentiment', 'sentiment_score', 'confidence_score']


class ConversationSerializer(serializers.ModelSerializer):
    """Conversation serializer with messages"""
    messages = MessageSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'session_id', 'customer_name', 'customer_email',
            'customer_phone', 'started_at', 'ended_at', 'is_active',
            'overall_sentiment', 'sentiment_score', 'conversation_category',
            'tags', 'escalated_to_human', 'escalation_reason',
            'assigned_agent', 'customer_rating', 'customer_feedback',
            'messages', 'messages_count'
        ]
        read_only_fields = ['id', 'started_at', 'overall_sentiment',
                            'sentiment_score']

    def get_messages_count(self, obj):
        return obj.messages.count()


class ChatMessageSerializer(serializers.Serializer):
    """Serializer for incoming chat messages"""
    message = serializers.CharField(max_length=5000)
    session_id = serializers.CharField(max_length=255)
    customer_name = serializers.CharField(max_length=200, required=False)
    customer_email = serializers.EmailField(required=False)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses"""
    response = serializers.CharField()
    intent = serializers.CharField()
    confidence = serializers.FloatField()
    sentiment = serializers.CharField()
    sentiment_score = serializers.FloatField()
    suggestions = serializers.ListField(child=serializers.CharField())
    should_escalate = serializers.BooleanField()


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """Knowledge base serializer"""

    class Meta:
        model = ChatbotKnowledgeBase
        fields = [
            'id', 'question', 'intent', 'keywords', 'answer',
            'answer_variations', 'category', 'subcategory',
            'is_active', 'priority', 'usage_count', 'success_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'success_rate',
                            'created_at', 'updated_at']


class SentimentSerializer(serializers.Serializer):
    """Sentiment analysis result serializer"""
    sentiment = serializers.CharField()
    score = serializers.FloatField()
    confidence = serializers.FloatField()
    method = serializers.CharField()
