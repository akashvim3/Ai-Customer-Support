import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .ai_engine import chatbot_engine
from .sentiment_analyzer import sentiment_analyzer
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat"""

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message = data['message']

        # Process message
        response = await self.process_message(message)

        # Send response back to WebSocket
        await self.send(text_data=json.dumps(response))

    @database_sync_to_async
    def process_message(self, message_text):
        """Process chat message with AI"""
        # Get or create conversation
        conversation, _ = Conversation.objects.get_or_create(
            session_id=self.session_id
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
        Message.objects.create(
            conversation=conversation,
            content=ai_response['response'],
            message_type='bot',
            intent=ai_response['intent'],
            confidence_score=ai_response['confidence']
        )

        return {
            'type': 'chat_message',
            'message': ai_response['response'],
            'intent': ai_response['intent'],
            'sentiment': sentiment_result['sentiment']
        }
