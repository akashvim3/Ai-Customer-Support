"""
Machine Learning Models Package for AI Customer Support Platform

This package contains ML model implementations for:
- Chatbot response generation
- Ticket classification
- Sentiment analysis
- Intent detection
- Entity extraction
"""

from .chatbot_model import ChatbotModel
from .classifier_model import TicketClassifierModel
from .sentiment_model import SentimentAnalysisModel

__all__ = [
    'ChatbotModel',
    'TicketClassifierModel',
    'SentimentAnalysisModel',
]

__version__ = '1.0.0'

# Model paths
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / 'saved_models'

# Ensure model directory exists
MODEL_DIR.mkdir(exist_ok=True)

# Model configurations
MODEL_CONFIG = {
    'chatbot': {
        'model_name': 'gpt2',
        'max_length': 512,
        'temperature': 0.7,
        'top_p': 0.9,
        'top_k': 50,
    },
    'classifier': {
        'model_name': 'bert-base-uncased',
        'num_labels': 7,  # Number of ticket categories
        'max_length': 512,
    },
    'sentiment': {
        'model_name': 'cardiffnlp/twitter-roberta-base-sentiment',
        'max_length': 512,
    }
}
