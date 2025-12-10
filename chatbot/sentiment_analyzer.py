import logging
from typing import Dict, Tuple
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from django.conf import settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Multi-model sentiment analysis engine with ensemble approach
    """

    def __init__(self):
        """Initialize sentiment analysis models"""
        self.vader = None
        self.sentiment_pipeline = None
        self.model = None
        self.tokenizer = None
        self.textblob_enabled = None
        self.setup_transformer_model()
        self.setup_vader()
        self.setup_textblob()

    def setup_transformer_model(self):
        """Setup transformer-based sentiment model"""
        try:
            model_name = settings.SENTIMENT_MODEL
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1  # CPU
            )

            logger.info(f"Transformer sentiment model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Error loading transformer model: {e}")
            self.sentiment_pipeline = None

    def setup_vader(self):
        """Setup VADER sentiment analyzer"""
        try:
            self.vader = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Error initializing VADER: {e}")
            self.vader = None

    def setup_textblob(self):
        """Setup TextBlob"""
        try:
            # TextBlob doesn't need explicit initialization
            self.textblob_enabled = True
            logger.info("TextBlob enabled")
        except Exception as e:
            logger.error(f"Error enabling TextBlob: {e}")
            self.textblob_enabled = False

    def analyze_with_transformer(self, text: str) -> Dict:
        """
        Analyze sentiment using transformer model
        """
        try:
            if not self.sentiment_pipeline:
                return {'label': 'neutral', 'score': 0.5}

            result = self.sentiment_pipeline(text)[0]

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
                'label': label,
                'score': normalized_score,
                'confidence': score
            }

        except Exception as e:
            logger.error(f"Error in transformer sentiment analysis: {e}")
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.5}

    def analyze_with_vader(self, text: str) -> Dict:
        """
        Analyze sentiment using VADER
        """
        try:
            if not self.vader:
                return {'label': 'neutral', 'score': 0.0}

            scores = self.vader.polarity_scores(text)
            compound_score = scores['compound']

            # Classify based on compound score
            if compound_score >= 0.05:
                label = 'positive'
            elif compound_score <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'

            return {
                'label': label,
                'score': compound_score,
                'details': scores
            }

        except Exception as e:
            logger.error(f"Error in VADER sentiment analysis: {e}")
            return {'label': 'neutral', 'score': 0.0}

    def analyze_with_textblob(self, text: str) -> Dict:
        """
        Analyze sentiment using TextBlob
        """
        try:
            if not self.textblob_enabled:
                return {'label': 'neutral', 'score': 0.0}

            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Classify based on polarity
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'

            return {
                'label': label,
                'score': polarity,
                'subjectivity': subjectivity
            }

        except Exception as e:
            logger.error(f"Error in TextBlob sentiment analysis: {e}")
            return {'label': 'neutral', 'score': 0.0}

    def analyze(self, text: str, method: str = 'ensemble') -> Dict:
        """
        Analyze sentiment using specified method or ensemble

        Args:
            text: Input text to analyze
            method: 'transformer', 'vader', 'textblob', or 'ensemble'

        Returns:
            Dictionary with sentiment analysis results
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
            return {
                'sentiment': result['label'],
                'score': result['score'],
                'confidence': result.get('confidence', 0.5),
                'method': 'transformer'
            }
        elif method == 'vader':
            result = self.analyze_with_vader(text)
            return {
                'sentiment': result['label'],
                'score': result['score'],
                'confidence': abs(result['score']),
                'method': 'vader'
            }
        elif method == 'textblob':
            result = self.analyze_with_textblob(text)
            return {
                'sentiment': result['label'],
                'score': result['score'],
                'confidence': abs(result['score']),
                'method': 'textblob'
            }
        else:
            return self.ensemble_analysis(text)

    def ensemble_analysis(self, text: str) -> Dict:
        """
        Perform ensemble sentiment analysis using multiple models
        """
        try:
            # Get results from all models
            transformer_result = self.analyze_with_transformer(text)
            vader_result = self.analyze_with_vader(text)
            textblob_result = self.analyze_with_textblob(text)

            # Calculate weighted average score
            scores = []
            weights = []

            if transformer_result:
                scores.append(transformer_result['score'])
                weights.append(0.5)  # Higher weight for transformer

            if vader_result:
                scores.append(vader_result['score'])
                weights.append(0.3)

            if textblob_result:
                scores.append(textblob_result['score'])
                weights.append(0.2)

            # Weighted average
            if scores:
                total_weight = sum(weights)
                weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            else:
                weighted_score = 0.0

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
                'score': weighted_score,
                'confidence': confidence,
                'method': 'ensemble',
                'details': {
                    'transformer': transformer_result,
                    'vader': vader_result,
                    'textblob': textblob_result
                }
            }

        except Exception as e:
            logger.error(f"Error in ensemble sentiment analysis: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'method': 'ensemble',
                'error': str(e)
            }

    def analyze_conversation(self, messages: list) -> Dict:
        """
        Analyze sentiment across entire conversation
        """
        try:
            if not messages:
                return {
                    'overall_sentiment': 'neutral',
                    'average_score': 0.0,
                    'sentiment_trend': [],
                    'message_sentiments': []
                }

            message_sentiments = []
            scores = []

            for msg in messages:
                result = self.analyze(msg.content)
                message_sentiments.append({
                    'message_id': str(msg.id),
                    'sentiment': result['sentiment'],
                    'score': result['score'],
                    'timestamp': msg.timestamp.isoformat()
                })
                scores.append(result['score'])

            # Calculate overall sentiment
            average_score = sum(scores) / len(scores)

            if average_score > 0.1:
                overall_sentiment = 'positive'
            elif average_score < -0.1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'

            # Detect sentiment trend
            sentiment_trend = 'stable'
            if len(scores) >= 3:
                recent_avg = sum(scores[-3:]) / 3
                earlier_avg = sum(scores[:-3]) / max(len(scores) - 3, 1)

                if recent_avg > earlier_avg + 0.2:
                    sentiment_trend = 'improving'
                elif recent_avg < earlier_avg - 0.2:
                    sentiment_trend = 'declining'

            return {
                'overall_sentiment': overall_sentiment,
                'average_score': average_score,
                'sentiment_trend': sentiment_trend,
                'message_sentiments': message_sentiments
            }

        except Exception as e:
            logger.error(f"Error analyzing conversation sentiment: {e}")
            return {
                'overall_sentiment': 'neutral',
                'average_score': 0.0,
                'sentiment_trend': 'unknown',
                'message_sentiments': [],
                'error': str(e)
            }


# Singleton instance
sentiment_analyzer = SentimentAnalyzer()
