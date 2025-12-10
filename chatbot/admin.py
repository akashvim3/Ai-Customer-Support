from django.contrib import admin
from .models import Conversation, Message, ChatbotKnowledgeBase, ChatbotTrainingData


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'customer_email', 'started_at', 'overall_sentiment',
                    'escalated_to_human', 'is_active']
    list_filter = ['overall_sentiment', 'escalated_to_human', 'is_active', 'started_at']
    search_fields = ['session_id', 'customer_name', 'customer_email']
    readonly_fields = ['started_at', 'ended_at']

    fieldsets = (
        ('Customer Information', {
            'fields': ('session_id', 'customer_name', 'customer_email', 'customer_phone')
        }),
        ('Conversation Details', {
            'fields': ('started_at', 'ended_at', 'is_active', 'conversation_category', 'tags')
        }),
        ('Sentiment Analysis', {
            'fields': ('overall_sentiment', 'sentiment_score')
        }),
        ('Escalation', {
            'fields': ('escalated_to_human', 'escalation_reason', 'assigned_agent')
        }),
        ('Feedback', {
            'fields': ('customer_rating', 'customer_feedback')
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'message_type', 'content_preview', 'sentiment', 'timestamp']
    list_filter = ['message_type', 'sentiment', 'timestamp']
    search_fields = ['content', 'conversation__session_id']
    readonly_fields = ['timestamp']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'


@admin.register(ChatbotKnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'intent', 'category', 'is_active', 'priority', 'usage_count']
    list_filter = ['is_active', 'category', 'priority']
    search_fields = ['question', 'answer', 'intent', 'keywords']
    readonly_fields = ['usage_count', 'success_rate', 'created_at', 'updated_at']

    def question_preview(self, obj):
        return obj.question[:100] + '...' if len(obj.question) > 100 else obj.question

    question_preview.short_description = 'Question'


@admin.register(ChatbotTrainingData)
class TrainingDataAdmin(admin.ModelAdmin):
    list_display = ['query_preview', 'intent', 'was_helpful', 'is_used_for_training', 'created_at']
    list_filter = ['was_helpful', 'is_used_for_training', 'intent', 'created_at']
    search_fields = ['user_query', 'bot_response', 'correct_response']
    readonly_fields = ['created_at']

    def query_preview(self, obj):
        return obj.user_query[:80] + '...' if len(obj.user_query) > 80 else obj.user_query

    query_preview.short_description = 'Query'
