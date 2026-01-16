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
# TODO: Re-enable AI engine when models are properly configured
# from .ai_engine import chatbot_engine
# from .sentiment_analyzer import sentiment_analyzer


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

        # TODO: Re-enable sentiment analysis when AI engine is ready
        # For now, use basic sentiment detection
        user_message.sentiment = self._detect_basic_sentiment(message_text)
        user_message.sentiment_score = self._calculate_sentiment_score(message_text)
        user_message.save()

        # Generate basic AI-like response
        ai_response = self._generate_basic_response(message_text, conversation)
        
        # TODO: Re-enable advanced AI when ready
        # ai_response = chatbot_engine.generate_response(
        #     user_message=message_text,
        #     conversation_id=str(conversation.id)
        # )

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

        # Check if escalation needed - temporarily disabled
        # should_escalate, reason = chatbot_engine.should_escalate(conversation)
        should_escalate = False
        reason = ''
        if should_escalate and not conversation.escalated_to_human:
            conversation.escalated_to_human = True
            conversation.escalation_reason = reason
            conversation.save()

        # Prepare response
        response_data = {
            'response': ai_response['response'],
            'intent': ai_response['intent'],
            'confidence': ai_response['confidence'],
            'sentiment': 'neutral',
            'sentiment_score': 0.0,
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

    def _detect_basic_sentiment(self, message_text):
        """Basic sentiment detection without AI"""
        message_lower = message_text.lower()
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'love', 'like', 'happy', 'pleased']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry', 'frustrated', 'annoyed', 'problem']
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _calculate_sentiment_score(self, message_text):
        """Calculate basic sentiment score"""
        message_lower = message_text.lower()
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'love', 'like', 'happy', 'pleased']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry', 'frustrated', 'annoyed', 'problem']
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        # Simple scoring: -1 to 1 range
        total_emotional_words = positive_count + negative_count
        if total_emotional_words == 0:
            return 0.0
        
        score = (positive_count - negative_count) / total_emotional_words
        return round(score, 2)

    def _generate_basic_response(self, message_text, conversation):
        """Generate basic contextual responses"""
        message_lower = message_text.lower()
        
        # Greeting responses
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(greeting in message_lower for greeting in greetings):
            return {
                'response': "Hello! I'm your AI support assistant. How can I help you today?",
                'intent': 'greeting',
                'confidence': 0.9,
                'entities': {},
                'suggestions': ['Track my order', 'Billing question', 'Technical support', 'General inquiry']
            }
        
        # Order tracking
        order_keywords = ['order', 'tracking', 'shipment', 'delivery', 'package']
        if any(keyword in message_lower for keyword in order_keywords):
            return {
                'response': "I'd be happy to help you track your order. Could you please provide your order number?",
                'intent': 'order_tracking',
                'confidence': 0.8,
                'entities': {},
                'suggestions': ['Order #12345', 'Recent orders', 'Delivery status']
            }
        
        # Billing questions
        billing_keywords = ['bill', 'payment', 'charge', 'invoice', 'refund', 'credit']
        if any(keyword in message_lower for keyword in billing_keywords):
            return {
                'response': "I can help with billing questions. What specific billing issue are you experiencing?",
                'intent': 'billing_inquiry',
                'confidence': 0.8,
                'entities': {},
                'suggestions': ['Payment failed', 'Wrong charge', 'Request refund', 'Invoice needed']
            }
        
        # Technical support
        tech_keywords = ['error', 'bug', 'issue', 'problem', 'broken', 'not working', 'help']
        if any(keyword in message_lower for keyword in tech_keywords):
            return {
                'response': "I understand you're experiencing a technical issue. Can you describe the problem you're facing?",
                'intent': 'technical_support',
                'confidence': 0.7,
                'entities': {},
                'suggestions': ['Website not loading', 'App crashing', 'Feature broken', 'Account access']
            }
        
        # Default response
        return {
            'response': "I'm here to help! Could you please provide more details about what you need assistance with?",
            'intent': 'general_inquiry',
            'confidence': 0.6,
            'entities': {},
            'suggestions': ['Track order', 'Billing help', 'Technical support', 'Speak to agent']
        }

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
