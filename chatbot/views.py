from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from .models import Conversation, Message, ChatbotKnowledgeBase
from .serializers import (
    ConversationSerializer, MessageSerializer,
    ChatMessageSerializer, ChatResponseSerializer,
    KnowledgeBaseSerializer
)
from .ai_engine import chatbot_engine
from .sentiment_analyzer import sentiment_analyzer


class ChatbotViewSet(viewsets.ViewSet):
    """Chatbot API endpoints"""
    permission_classes = [AllowAny]  # Allow anonymous chat

    @action(detail=False, methods=['post'])
    def message(self, request):
        """Process incoming chat message"""
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message_text = serializer.validated_data['message']
        session_id = serializer.validated_data['session_id']

        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(
            session_id=session_id,
            defaults={
                'customer_name': serializer.validated_data.get('customer_name', ''),
                'customer_email': serializer.validated_data.get('customer_email', '')
            }
        )

        # Create user message
        user_message = Message.objects.create(
            conversation=conversation,
            content=message_text,
            message_type='user'
        )

        # Analyze sentiment
        sentiment_result = sentiment_analyzer.analyze(message_text)
        user_message.sentiment = sentiment_result['sentiment']
        user_message.sentiment_score = sentiment_result['score']
        user_message.save()

        # Generate AI response
        ai_response = chatbot_engine.generate_response(
            user_message=message_text,
            conversation_id=str(conversation.id)
        )

        # Create bot message
        bot_message = Message.objects.create(
            conversation=conversation,
            content=ai_response['response'],
            message_type='bot',
            intent=ai_response['intent'],
            entities=ai_response['entities'],
            confidence_score=ai_response['confidence']
        )

        # Update conversation sentiment
        self._update_conversation_sentiment(conversation)

        # Check if escalation needed
        should_escalate, reason = chatbot_engine.should_escalate(conversation)
        if should_escalate and not conversation.escalated_to_human:
            conversation.escalated_to_human = True
            conversation.escalation_reason = reason
            conversation.save()

        # Prepare response
        response_data = {
            'response': ai_response['response'],
            'intent': ai_response['intent'],
            'confidence': ai_response['confidence'],
            'sentiment': sentiment_result['sentiment'],
            'sentiment_score': sentiment_result['score'],
            'suggestions': ai_response['suggestions'],
            'should_escalate': should_escalate
        }

        return Response(response_data)

    def _update_conversation_sentiment(self, conversation):
        """Update overall conversation sentiment"""
        messages = conversation.messages.exclude(sentiment_score=0)

        if messages.exists():
            avg_score = sum(msg.sentiment_score for msg in messages) / len(messages)
            conversation.sentiment_score = avg_score

            if avg_score > 0.1:
                conversation.overall_sentiment = 'positive'
            elif avg_score < -0.1:
                conversation.overall_sentiment = 'negative'
            else:
                conversation.overall_sentiment = 'neutral'

            conversation.save()

    @action(detail=False, methods=['post'])
    def end_conversation(self, request):
        """End a conversation"""
        session_id = request.data.get('session_id')
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')

        try:
            conversation = Conversation.objects.get(session_id=session_id)
            conversation.is_active = False
            conversation.ended_at = timezone.now()
            conversation.customer_rating = rating
            conversation.customer_feedback = feedback
            conversation.save()

            return Response({'status': 'conversation ended'})
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """Conversation management API"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.all().order_by('-started_at')

    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Manually escalate conversation to human agent"""
        conversation = self.get_object()
        reason = request.data.get('reason', 'Manual escalation')

        conversation.escalated_to_human = True
        conversation.escalation_reason = reason
        conversation.assigned_agent = request.user
        conversation.save()

        return Response({'status': 'escalated'})


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """Knowledge base management API"""
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [IsAuthenticated]
    queryset = ChatbotKnowledgeBase.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """Bulk import knowledge base items"""
        items = request.data.get('items', [])
        created_count = 0

        for item in items:
            serializer = self.get_serializer(data=item)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                created_count += 1

        return Response({'imported': created_count})
