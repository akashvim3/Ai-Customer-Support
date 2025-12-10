"""
Chatbot module for AI Customer Support Platform
Provides AI-powered conversational interface with NLP capabilities
"""

default_app_config = 'chatbot.apps.ChatbotConfig'

# Import main components for easy access
from .ai_engine import chatbot_engine
from .sentiment_analyzer import sentiment_analyzer
from .ticket_classifier import ticket_classifier

__all__ = [
    'chatbot_engine',
    'sentiment_analyzer',
    'ticket_classifier',
]
