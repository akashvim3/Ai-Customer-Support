"""
Chatbot Model for conversational AI
Handles intent detection, entity extraction, and response generation
"""

import os
import logging
import torch
import numpy as np
from transformers import (
    GPT2LMHeadModel, GPT2Tokenizer,
    AutoModelForSequenceClassification, AutoTokenizer,
    pipeline
)
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ChatbotModel:
    """
    Advanced chatbot model with multiple capabilities:
    - Intent classification
    - Entity extraction
    - Context-aware response generation
    - Conversation flow management
    """

    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize the chatbot model

        Args:
            model_dir: Directory containing saved models
        """
        self.model_dir = model_dir or Path(__file__).parent / 'saved_models'
        self.model_dir.mkdir(exist_ok=True)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        # Initialize components
        self.intent_classifier = None
        self.entity_extractor = None
        self.response_generator = None
        self.tokenizer = None

        # Load models
        self.load_models()

        # Conversation context
        self.conversation_history = {}

    def load_models(self):
        """Load all required models"""
        try:
            self._load_intent_classifier()
            self._load_entity_extractor()
            self._load_response_generator()
            logger.info("All chatbot models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading chatbot models: {e}")

    def _load_intent_classifier(self):
        """Load intent classification model"""
        try:
            # Use zero-shot classification for flexible intent detection
            self.intent_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Intent classifier loaded")
        except Exception as e:
            logger.error(f"Error loading intent classifier: {e}")

    def _load_entity_extractor(self):
        """Load named entity recognition model"""
        try:
            self.entity_extractor = pipeline(
                "ner",
                model="slim/bert-base-NER",
                device=0 if torch.cuda.is_available() else -1,
                aggregation_strategy="simple"
            )
            logger.info("Entity extractor loaded")
        except Exception as e:
            logger.error(f"Error loading entity extractor: {e}")

    def _load_response_generator(self):
        """Load response generation model"""
        try:
            model_path = self.model_dir / 'chatbot_gpt2'

            if model_path.exists():
                # Load fine-tuned model
                self.response_generator = GPT2LMHeadModel.from_pretrained(model_path)
                self.tokenizer = GPT2Tokenizer.from_pretrained(model_path)
                logger.info("Fine-tuned response generator loaded")
            else:
                # Load pre-trained model
                self.response_generator = GPT2LMHeadModel.from_pretrained('gpt2')
                self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
                logger.info("Pre-trained response generator loaded")

            self.response_generator.to(self.device)
            self.response_generator.eval()

            # Set pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

        except Exception as e:
            logger.error(f"Error loading response generator: {e}")

    def classify_intent(self, text: str, candidate_intents: Optional[List[str]] = None) -> Dict:
        """
        Classify the intent of user message

        Args:
            text: User message
            candidate_intents: List of possible intents

        Returns:
            Dictionary with intent and confidence
        """
        if candidate_intents is None:
            candidate_intents = [
                "greeting",
                "farewell",
                "technical_support",
                "billing_inquiry",
                "account_management",
                "product_question",
                "complaint",
                "feedback",
                "feature_request",
                "general_inquiry"
            ]

        try:
            if self.intent_classifier:
                result = self.intent_classifier(
                    text,
                    candidate_intents,
                    multi_label=False
                )

                return {
                    'intent': result['labels'][0],
                    'confidence': result['scores'][0],
                    'all_intents': [
                        {'intent': label, 'score': score}
                        for label, score in zip(result['labels'], result['scores'])
                    ]
                }
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")

        return {
            'intent': 'general_inquiry',
            'confidence': 0.5,
            'all_intents': []
        }

    def extract_entities(self, text: str) -> List[Dict]:
        """
        Extract named entities from text

        Args:
            text: Input text

        Returns:
            List of extracted entities
        """
        try:
            if self.entity_extractor:
                entities = self.entity_extractor(text)

                # Format entities
                formatted_entities = []
                for entity in entities:
                    formatted_entities.append({
                        'text': entity['word'],
                        'type': entity['entity_group'],
                        'score': entity['score'],
                        'start': entity.get('start'),
                        'end': entity.get('end')
                    })

                return formatted_entities
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")

        return []

    def generate_response(
            self,
            user_message: str,
            context: Optional[Dict] = None,
            max_length: int = 150,
            temperature: float = 0.7,
            top_p: float = 0.9
    ) -> Dict:
        """
        Generate AI response to user message

        Args:
            user_message: User's message
            context: Conversation context
            max_length: Maximum response length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter

        Returns:
            Dictionary with response and metadata
        """
        try:
            # Classify intent
            intent_result = self.classify_intent(user_message)

            # Extract entities
            entities = self.extract_entities(user_message)

            # Build prompt with context
            prompt = self._build_prompt(user_message, context, intent_result)

            # Generate response
            if self.response_generator and self.tokenizer:
                response_text = self._generate_text(
                    prompt,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p
                )
            else:
                # Fallback response
                response_text = self._get_template_response(intent_result['intent'])

            return {
                'response': response_text,
                'intent': intent_result['intent'],
                'intent_confidence': intent_result['confidence'],
                'entities': entities,
                'context_used': context is not None
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': "I apologize, but I'm having trouble processing your request. Could you please rephrase that?",
                'intent': 'error',
                'intent_confidence': 0.0,
                'entities': [],
                'error': str(e)
            }

    @staticmethod
    def _build_prompt(
            user_message: str,
            context: Optional[Dict],
            intent_result: Dict
    ) -> str:
        """Build prompt for response generation"""
        prompt_parts = []

        # Add context if available
        if context and context.get('history'):
            history = context['history'][-3:]  # Last 3 exchanges
            for msg in history:
                prompt_parts.append(f"User: {msg['user']}")
                prompt_parts.append(f"Assistant: {msg['assistant']}")

        # Add current message
        prompt_parts.append(f"User: {user_message}")

        # Add intent hint
        intent = intent_result['intent']
        if intent == 'technical_support':
            prompt_parts.append("Assistant (providing technical support):")
        elif intent == 'billing_inquiry':
            prompt_parts.append("Assistant (helping with billing):")
        else:
            prompt_parts.append("Assistant:")

        return " ".join(prompt_parts)


def _generate_text(
        self,
        prompt: str,
        max_length: int = 150,
        temperature: float = 0.7,
        top_p: float = 0.9
) -> str:
    """Generate text using GPT-2 model"""
    try:
        # Encode input
        inputs = self.tokenizer.encode(
            prompt,
            return_tensors='pt',
            max_length=512,
            truncation=True
        ).to(self.device)

        # Generate
        with torch.no_grad():
            outputs = self.response_generator.generate(
                inputs,
                max_length=inputs.shape[1] + max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=3,
                num_return_sequences=1
            )

        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the assistant's response
        if "Assistant:" in generated_text:
            response = generated_text.split("Assistant:")[-1].strip()
        else:
            response = generated_text[len(prompt):].strip()

        # Clean up
        response = self._clean_response(response)

        return response

    except Exception as e:
        logger.error(f"Error in text generation: {e}")
        return self._get_template_response('general_inquiry')


def _clean_response(self, response: str) -> str:
    """Clean generated response"""
    # Remove incomplete sentences
    if response and not response[-1] in '.!?':
        last_punct = max(
            response.rfind('.'),
            response.rfind('!'),
            response.rfind('?')
        )
        if last_punct > 0:
            response = response[:last_punct + 1]

    # Remove user prompts that might have been generated
    if "User:" in response:
        response = response.split("User:")[0].strip()

    return response.strip()


def _get_template_response(self, intent: str) -> str:
    """Get template response based on intent"""
    templates = {
        'greeting': "Hello! How can I assist you today?",
        'farewell': "Thank you for contacting us. Have a great day!",
        'technical_support': "I'll help you with your technical issue. Could you provide more details about the problem?",
        'billing_inquiry': "I can help you with billing questions. What would you like to know?",
        'account_management': "I'm here to help with your account. What do you need assistance with?",
        'product_question': "I'd be happy to answer your product questions. What would you like to know?",
        'complaint': "I apologize for the inconvenience. Let me help resolve this issue for you.",
        'feedback': "Thank you for your feedback! We appreciate your input.",
        'feature_request': "Thank you for the suggestion! I'll make sure it's forwarded to our product team.",
        'general_inquiry': "I'm here to help! Could you provide more details about what you need?"
    }

    return templates.get(intent, templates['general_inquiry'])


def fine_tune(
        self,
        training_data: List[Dict],
        epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 5e-5
):
    """
    Fine-tune the response generator on custom data

    Args:
        training_data: List of conversation examples
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
    """
    try:
        from torch.utils.data import Dataset, DataLoader
        from transformers import AdamW, get_linear_schedule_with_warmup

        # Prepare dataset
        class ConversationDataset(Dataset):
            def __init__(self, data, tokenizer, max_length=512):
                self.data = data
                self.tokenizer = tokenizer
                self.max_length = max_length

            def __len__(self):
                return len(self.data)

            def __getitem__(self, idx):
                item = self.data[idx]
                text = f"User: {item['user']}Assistant: {item['assistant']}
                return {
                        'input_ids': encoding['input_ids'].flatten(),
                        'attention_mask': encoding['attention_mask'].flatten(),
                        'labels': encoding['input_ids'].flatten()
                        }

encoding = self.tokenizer(
    text,
    max_length=self.max_length,
    padding='max_length',
    truncation=True,
    return_tensors='pt'
)



# Create dataset and dataloader
dataset = ConversationDataset(training_data, self.tokenizer)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# Setup optimizer
optimizer = AdamW(self.response_generator.parameters(), lr=learning_rate)
total_steps = len(dataloader) * epochs
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=total_steps // 10,
    num_training_steps=total_steps
)

# Training loop
self.response_generator.train()

for epoch in range(epochs):
    total_loss = 0

    for batch in dataloader:
        input_ids = batch['input_ids'].to(self.device)
        attention_mask = batch['attention_mask'].to(self.device)
        labels = batch['labels'].to(self.device)

        outputs = self.response_generator(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss
        total_loss += loss.item()

        loss.backward()
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()

    avg_loss = total_loss / len(dataloader)
    logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")



# Save fine-tuned model
save_path = self.model_dir / 'chatbot_gpt2'
self.response_generator.save_pretrained(save_path)
self.tokenizer.save_pretrained(save_path)

logger.info(f"Fine-tuned model saved to {save_path}")


