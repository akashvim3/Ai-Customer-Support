"""
Ticket Classifier Model
Multi-class classification for ticket categorization and priority detection
"""

import os
import logging
import torch
import numpy as np
from transformers import (
    BertForSequenceClassification,
    BertTokenizer,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments
)
from sklearn.metrics import classification_report, accuracy_score, f1_score
from typing import Dict, List, Tuple, Optional
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class TicketClassifierModel:
    """
    BERT-based ticket classification model
    Supports both category and priority classification
    """

    def __init__(self, model_dir: Optional[Path] = None, num_categories: int = 7):
        """
        Initialize ticket classifier

        Args:
            model_dir: Directory for saving/loading models
            num_categories: Number of ticket categories
        """
        self.model_dir = model_dir or Path(__file__).parent / 'saved_models'
        self.model_dir.mkdir(exist_ok=True)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        self.num_categories = num_categories
        self.categories = [
            'Technical Issue',
            'Billing',
            'Account Management',
            'Product Inquiry',
            'Feature Request',
            'Bug Report',
            'General Support'
        ]

        self.priorities = ['low', 'medium', 'high', 'urgent']

        # Models
        self.category_model = None
        self.category_tokenizer = None
        self.priority_model = None
        self.priority_tokenizer = None

        # Label encoders
        self.category_label_encoder = None
        self.priority_label_encoder = None

        # Load models
        self.load_models()

    def load_models(self):
        """Load pre-trained or fine-tuned models"""
        try:
            self._load_category_model()
            self._load_priority_model()
            logger.info("Classifier models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading classifier models: {e}")

    def _load_category_model(self):
        """Load category classification model"""
        try:
            model_path = self.model_dir / 'category_classifier'

            if model_path.exists():
                # Load fine-tuned model
                self.category_model = AutoModelForSequenceClassification.from_pretrained(
                    model_path
                )
                self.category_tokenizer = AutoTokenizer.from_pretrained(model_path)
                logger.info("Fine-tuned category classifier loaded")
            else:
                # Load pre-trained BERT
                self.category_model = BertForSequenceClassification.from_pretrained(
                    'bert-base-uncased',
                    num_labels=self.num_categories
                )
                self.category_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
                logger.info("Pre-trained category classifier loaded")

            self.category_model.to(self.device)
            self.category_model.eval()

            # Load label encoder
            encoder_path = self.model_dir / 'category_label_encoder.pkl'
            if encoder_path.exists():
                self.category_label_encoder = joblib.load(encoder_path)
            else:
                from sklearn.preprocessing import LabelEncoder
                self.category_label_encoder = LabelEncoder()
                self.category_label_encoder.fit(self.categories)

        except Exception as e:
            logger.error(f"Error loading category model: {e}")

    def _load_priority_model(self):
        """Load priority classification model"""
        try:
            model_path = self.model_dir / 'priority_classifier'

            if model_path.exists():
                self.priority_model = AutoModelForSequenceClassification.from_pretrained(
                    model_path
                )
                self.priority_tokenizer = AutoTokenizer.from_pretrained(model_path)
                logger.info("Fine-tuned priority classifier loaded")
            else:
                self.priority_model = BertForSequenceClassification.from_pretrained(
                    'bert-base-uncased',
                    num_labels=len(self.priorities)
                )
                self.priority_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
                logger.info("Pre-trained priority classifier loaded")

            self.priority_model.to(self.device)
            self.priority_model.eval()

            # Load label encoder
            encoder_path = self.model_dir / 'priority_label_encoder.pkl'
            if encoder_path.exists():
                self.priority_label_encoder = joblib.load(encoder_path)
            else:
                from sklearn.preprocessing import LabelEncoder
                self.priority_label_encoder = LabelEncoder()
                self.priority_label_encoder.fit(self.priorities)

        except Exception as e:
            logger.error(f"Error loading priority model: {e}")

    def predict_category(self, text: str) -> Dict:
        """
        Predict ticket category

        Args:
            text: Ticket text (title + description)

        Returns:
            Dictionary with predicted category and confidence
        """
        try:
            if not self.category_model or not self.category_tokenizer:
                return {'category': 'General Support', 'confidence': 0.5, 'error': 'Model not loaded'}

            # Tokenize
            inputs = self.category_tokenizer(
                text,
                return_tensors='pt',
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)

            # Predict
            with torch.no_grad():
                outputs = self.category_model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)

            # Get prediction
            predicted_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0][predicted_idx].item()

            # Decode label
            if self.category_label_encoder:
                category = self.category_label_encoder.inverse_transform([predicted_idx])[0]
            else:
                category = self.categories[predicted_idx]

            # Get top 3 predictions
            top_probs, top_indices = torch.topk(probs[0], k=min(3, len(self.categories)))
            top_predictions = []
            for prob, idx in zip(top_probs, top_indices):
                if self.category_label_encoder:
                    cat = self.category_label_encoder.inverse_transform([idx.item()])[0]
                else:
                    cat = self.categories[idx.item()]
                top_predictions.append({
                    'category': cat,
                    'confidence': prob.item()
                })

            return {
                'category': category,
                'confidence': float(confidence),
                'top_predictions': top_predictions
            }

        except Exception as e:
            logger.error(f"Error in category prediction: {e}")
            return {
                'category': 'General Support',
                'confidence': 0.5,
                'error': str(e)
            }

    def predict_priority(self, text: str) -> Dict:
        """
        Predict ticket priority

        Args:
            text: Ticket text (title + description)

        Returns:
            Dictionary with predicted priority and confidence
        """
        try:
            if not self.priority_model or not self.priority_tokenizer:
                return {'priority': 'medium', 'confidence': 0.5, 'error': 'Model not loaded'}

            # Tokenize
            inputs = self.priority_tokenizer(
                text,
                return_tensors='pt',
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)

            # Predict
            with torch.no_grad():
                outputs = self.priority_model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)

            # Get prediction
            predicted_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0][predicted_idx].item()

            # Decode label
            if self.priority_label_encoder:
                priority = self.priority_label_encoder.inverse_transform([predicted_idx])[0]
            else:
                priority = self.priorities[predicted_idx]

            return {
                'priority': priority,
                'confidence': float(confidence)
            }

        except Exception as e:
            logger.error(f"Error in priority prediction: {e}")
            return {
                'priority': 'medium',
                'confidence': 0.5,
                'error': str(e)
            }

    def predict(self, text: str) -> Dict:
        """
        Predict both category and priority

        Args:
            text: Ticket text

        Returns:
            Dictionary with both predictions
        """
        category_result = self.predict_category(text)
        priority_result = self.predict_priority(text)

        return {
            'category': category_result['category'],
            'category_confidence': category_result['confidence'],
            'priority': priority_result['priority'],
            'priority_confidence': priority_result['confidence'],
            'top_categories': category_result.get('top_predictions', [])
        }

    def train_category_model(
            self,
            training_data: List[Tuple[str, str]],
            validation_data: Optional[List[Tuple[str, str]]] = None,
            epochs: int = 3,
            batch_size: int = 16,
            learning_rate: float = 2e-5
    ):
        """
        Train category classification model

        Args:
            training_data: List of (text, category) tuples
            validation_data: Optional validation data
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        """
        try:
            from torch.utils.data import Dataset

            # Prepare dataset
            class TicketDataset(Dataset):
                def __init__(self, data, tokenizer, label_encoder):
                    self.texts = [item[0] for item in data]
                    self.labels = label_encoder.transform([item[1] for item in data])
                    self.tokenizer = tokenizer

                def __len__(self):
                    return len(self.texts)

                def __getitem__(self, idx):
                    encoding = self.tokenizer(
                        self.texts[idx],
                        max_length=512,
                        padding='max_length',
                        truncation=True,
                        return_tensors='pt'
                    )

                    return {
                        'input_ids': encoding['input_ids'].flatten(),
                        'attention_mask': encoding['attention_mask'].flatten(),
                        'labels': torch.tensor(self.labels[idx], dtype=torch.long)
                    }

            # Fit label encoder
            categories = list(set([item[1] for item in training_data]))
            self.category_label_encoder.fit(categories)

            # Create datasets
            train_dataset = TicketDataset(
                training_data,
                self.category_tokenizer,
                self.category_label_encoder
            )

            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.model_dir / 'category_classifier_training'),
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                learning_rate=learning_rate,
                warmup_steps=500,
                weight_decay=0.01,
                logging_dir=str(self.model_dir / 'logs'),
                logging_steps=100,
                save_steps=1000,
                evaluation_strategy="steps" if validation_data else "no",
                save_total_limit=2,
            )

            # Trainer
            trainer = Trainer(
                model=self.category_model,
                args=training_args,
                train_dataset=train_dataset,
            )

            # Train
            trainer.train()

            # Save model
            save_path = self.model_dir / 'category_classifier'
            self.category_model.save_pretrained(save_path)
            self.category_tokenizer.save_pretrained(save_path)

            # Save label encoder
            joblib.dump(
                self.category_label_encoder,
                self.model_dir / 'category_label_encoder.pkl'
            )

            logger.info(f"Category model trained and saved to {save_path}")

        except Exception as e:
            logger.error(f"Error training category model: {e}")

    def evaluate(self, test_data: List[Tuple[str, str]]) -> Dict:
        """
        Evaluate model performance

        Args:
            test_data: List of (text, label) tuples

        Returns:
            Dictionary with evaluation metrics
        """
        try:
            texts = [item[0] for item in test_data]
            true_labels = [item[1] for item in test_data]

            # Predict
            predictions = []
            for text in texts:
                result = self.predict_category(text)
                predictions.append(result['category'])

            # Calculate metrics
            accuracy = accuracy_score(true_labels, predictions)
            f1 = f1_score(true_labels, predictions, average='weighted')

            # Classification report
            report = classification_report(
                true_labels,
                predictions,
                output_dict=True
            )

            return {
                'accuracy': accuracy,
                'f1_score': f1,
                'classification_report': report
            }

        except Exception as e:
            logger.error(f"Error in evaluation: {e}")
            return {'error': str(e)}
