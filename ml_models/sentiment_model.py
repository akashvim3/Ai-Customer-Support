"""
Sentiment Analysis Model
Multi-model ensemble for accurate sentiment detection
"""

import os
import logging
import torch
import numpy as np
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline
)
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SentimentAnalysisModel:
    """
    Advanced sentiment analysis with ensemble of multiple models:
    - Transformer-based (RoBERTa)
    - VADER (rule-based)
    - TextBlob (lexicon-based)
    """

    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize sentiment analysis models

        Args:
            model_dir: Directory for model storage
        """
        self.model_dir = model_dir or Path(__file__).parent / 'saved_models'
        self.model_dir.mkdir(exist_ok=True)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        # Models
        self.transformer_model = None
        self.vader_analyzer = None
        self.textblob_enabled = True

        # Load models
        self.load_models()

    def load_models(self):
        """Load all sentiment analysis models"""
        try:
            self._load_transformer_model()
            self._load_vader()
            logger.info("Sentiment analysis models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentiment models: {e}")

    def _load_transformer_model(self):
        """Load transformer-based sentiment model"""
        try:
            model_path = self.model_dir / 'sentiment_roberta'

            if model_path.exists():
                # Load fine-tuned model
                self.transformer_model = pipeline(
                    "sentiment-analysis",
                    model=str(model_path),
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("Fine-tuned transformer sentiment model loaded")
            else:
                # Load pre-trained RoBERTa sentiment model
                self.transformer_model = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment",
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("Pre-trained transformer sentiment model loaded")

        except Exception as e:
            logger.error(f"Error loading transformer model: {e}")

    def _load_vader(self):
        """Load VADER sentiment analyzer"""
        try:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer loaded")
        except Exception as e:
            logger.error(f"Error loading VADER: {e}")

    def analyze_with_transformer(self, text: str) -> Dict:
        """
        Analyze sentiment using transformer model

        Args:
            text: Input text

        Returns:
            Sentiment analysis result
        """
        try:
            if not self.transformer_model:
                return {'label': 'neutral', 'score': 0.0}

            result = self.transformer_model(text)[0]

            # Normalize label
            label_map = {
                'LABEL_0': 'negative',
                'LABEL_1': 'neutral',
                'LABEL_2': 'positive',
                'NEGATIVE': 'negative',
                'NEUTRAL': 'neutral',
                'POSITIVE': 'positive'
            }

            label = label_map.get(result['label'].upper(), 'neutral')
            score = result['score']

            # Convert to -1 to 1 scale
            if label == 'negative':
                normalized_score = -score
            elif label == 'positive':
                normalized_score = score
            else:
                normalized_score = 0.0

            return {
                'sentiment': label,
                'score': normalized_score,
                'confidence': score
            }

        except Exception as e:
            logger.error(f"Error in transformer sentiment analysis: {e}")
            return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.5}

    def analyze_with_vader(self, text: str) -> Dict:
        """
        Analyze sentiment using VADER

        Args:
            text: Input text

        Returns:
            Sentiment analysis result
        """
        try:
            if not self.vader_analyzer:
                return {'sentiment': 'neutral', 'score': 0.0}

            scores = self.vader_analyzer.polarity_scores(text)
            compound_score = scores['compound']

            # Classify based on compound score
            if compound_score >= 0.05:
                sentiment = 'positive'
            elif compound_score <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return {
                'sentiment': sentiment,
                'score': compound_score,
                'details': scores
            }

        except Exception as e:
            logger.error(f"Error in VADER sentiment analysis: {e}")
            return {'sentiment': 'neutral', 'score': 0.0}

    def analyze_with_textblob(self, text: str) -> Dict:
        """
        Analyze sentiment using TextBlob

        Args:
            text: Input text

        Returns:
            Sentiment analysis result
        """
        try:
            if not self.textblob_enabled:
                return {'sentiment': 'neutral', 'score': 0.0}

            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Classify based on polarity
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return {
                'sentiment': sentiment,
                'score': polarity,
                'subjectivity': subjectivity
            }

        except Exception as e:
            logger.error(f"Error in TextBlob sentiment analysis: {e}")
            return {'sentiment': 'neutral', 'score': 0.0}

    def analyze(self, text: str, method: str = 'ensemble') -> Dict:
        """
        Analyze sentiment using specified method

        Args:
            text: Input text
            method: 'transformer', 'vader', 'textblob', or 'ensemble'

        Returns:
            Sentiment analysis result
        """
        if not text or not text.strip():
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'method': method
            }

        if method == 'ensemble':
            return self.ensemble_analysis(text)
        elif method == 'transformer':
            result = self.analyze_with_transformer(text)
            result['method'] = 'transformer'
            return result
        elif method == 'vader':
            result = self.analyze_with_vader(text)
            result['method'] = 'vader'
            result['confidence'] = abs(result['score'])
            return result
        elif method == 'textblob':
            result = self.analyze_with_textblob(text)
            result['method'] = 'textblob'
            result['confidence'] = abs(result['score'])
            return result
        else:
            return self.ensemble_analysis(text)

    def ensemble_analysis(self, text: str) -> Dict:
        """
        Perform ensemble sentiment analysis

        Args:
            text: Input text

        Returns:
            Aggregated sentiment result
        """
        try:
            # Get results from all models
            transformer_result = self.analyze_with_transformer(text)
            vader_result = self.analyze_with_vader(text)
            textblob_result = self.analyze_with_textblob(text)

            # Weighted average (transformer gets higher weight)
            weights = {'transformer': 0.5, 'vader': 0.3, 'textblob': 0.2}

            weighted_score = (
                    transformer_result['score'] * weights['transformer'] +
                    vader_result['score'] * weights['vader'] +
                    textblob_result['score'] * weights['textblob']
            )

            # Determine final sentiment
            if weighted_score > 0.1:
                final_sentiment = 'positive'
            elif weighted_score < -0.1:
                final_sentiment = 'negative'
            else:
                final_sentiment = 'neutral'

            # Calculate confidence
            confidence = abs(weighted_score)

            return {
                'sentiment': final_sentiment,
                'score': float(weighted_score),
                'confidence': float(confidence),
                'method': 'ensemble',
                'details': {
                    'transformer': transformer_result,
                    'vader': vader_result,
                    'textblob': textblob_result
                }
            }

        except Exception as e:
            logger.error(f"Error in ensemble analysis: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'method': 'ensemble',
                'error': str(e)
            }

    def batch_analyze(self, texts: List[str], method: str = 'ensemble') -> List[Dict]:
        """
        Analyze sentiment for multiple texts

        Args:
            texts: List of input texts
            method: Analysis method

        Returns:
            List of sentiment results
        """
        return [self.analyze(text, method) for text in texts]
