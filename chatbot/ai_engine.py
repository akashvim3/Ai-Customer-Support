import os
import logging
from typing import Dict, List, Tuple
import openai
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from langchain.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from django.conf import settings
from .models import ChatbotKnowledgeBase, Conversation, Message

logger = logging.getLogger(__name__)


class AIchatbotEngine:
    """
    Advanced AI Chatbot Engine with NLP, ML, and contextual understanding
    """

    def __init__(self):
        """Initialize AI models and pipelines"""
        self.vectorstore = None
        self.embeddings = None
        self.llm = None
        self.intent_classifier = None
        self.setup_openai()
        self.setup_intent_classifier()
        self.setup_embeddings()
        self.conversation_memory = {}

    def setup_openai(self):
        """Setup OpenAI API"""
        try:
            openai.api_key = settings.OPENAI_API_KEY
            self.llm = OpenAI(
                temperature=0.7,
                max_tokens=500,
                model_name="gpt-3.5-turbo-instruct"
            )
            logger.info("OpenAI initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI: {e}")
            self.llm = None

    def setup_intent_classifier(self):
        """Setup intent classification model"""
        try:
            self.intent_classifier = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli",
                device=-1
            )
            logger.info("Intent classifier initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing intent classifier: {e}")

    def setup_embeddings(self):
        """Setup embeddings for knowledge base retrieval"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            self.load_knowledge_base()
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            self.embeddings = None

    def load_knowledge_base(self):
        """Load knowledge base into vector store"""
        try:
            kb_items = ChatbotKnowledgeBase.objects.filter(is_active=True)

            if kb_items.exists():
                texts = [item.question for item in kb_items]
                metadatas = [
                    {
                        'id': str(item.id),
                        'answer': item.answer,
                        'intent': item.intent,
                        'category': item.category
                    }
                    for item in kb_items
                ]

                self.vectorstore = FAISS.from_texts(
                    texts=texts,
                    embedding=self.embeddings,
                    metadatas=metadatas
                )
                logger.info(f"Knowledge base loaded with {len(texts)} items")
            else:
                self.vectorstore = None
                logger.warning("No knowledge base items found")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self.vectorstore = None

    def classify_intent(self, text: str) -> Tuple[str, float]:
        """
        Classify user intent from text
        """
        try:
            if not self.intent_classifier:
                return "general_query", 0.5

            # Define possible intents
            candidate_labels = [
                "technical_issue",
                "billing_question",
                "account_management",
                "product_inquiry",
                "feature_request",
                "bug_report",
                "general_support",
                "greeting",
                "farewell"
            ]

            result = self.intent_classifier(
                text,
                candidate_labels,
                multi_label=False
            )

            intent = result['labels'][0]
            confidence = result['scores'][0]

            logger.info(f"Intent classified: {intent} (confidence: {confidence})")
            return intent, confidence

        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "general_query", 0.5

    @staticmethod
    def extract_entities(text: str) -> Dict:
        """
        Extract entities from user message
        """
        # Simple entity extraction (can be enhanced with spaCy or custom NER)
        entities = {
            'email': [],
            'phone': [],
            'product': [],
            'date': []
        }

        # Email extraction
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['email'] = re.findall(email_pattern, text)

        # Phone extraction
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        entities['phone'] = re.findall(phone_pattern, text)

        return entities

    def search_knowledge_base(self, query: str, k: int = 3) -> List[Dict]:
        """
        Search knowledge base for relevant answers
        """
        try:
            if not self.vectorstore:
                return []

            results = self.vectorstore.similarity_search_with_score(query, k=k)

            relevant_answers = []
            for doc, score in results:
                if score < 0.5:  # Similarity threshold
                    relevant_answers.append({
                        'answer': doc.metadata.get('answer', ''),
                        'intent': doc.metadata.get('intent', ''),
                        'category': doc.metadata.get('category', ''),
                        'confidence': 1 - score
                    })

            return relevant_answers

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []

    def generate_response(
            self,
            user_message: str,
            conversation_id: str,
            context: Dict = None
    ) -> Dict:
        """
        Generate AI response to user message
        """
        try:
            # Classify intent
            intent, intent_confidence = self.classify_intent(user_message)

            # Extract entities
            entities = self.extract_entities(user_message)

            # Search knowledge base
            kb_results = self.search_knowledge_base(user_message)

            # Generate response
            if kb_results and kb_results[0]['confidence'] > 0.7:
                # Use knowledge base answer
                response_text = kb_results[0]['answer']
                confidence = kb_results[0]['confidence']
                source = 'knowledge_base'
            elif self.llm:
                # Generate with LLM
                prompt = self._build_prompt(user_message, intent, context)
                response_text = self.llm(prompt)
                confidence = intent_confidence
                source = 'llm'
            else:
                # Fallback response
                response_text = self._get_fallback_response(intent)
                confidence = 0.5
                source = 'fallback'

            return {
                'response': response_text,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'source': source,
                'suggestions': self._get_suggestions(intent)
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': "I apologize, but I'm having trouble processing your request. Please try again or contact our support team.",
                'intent': 'error',
                'confidence': 0.0,
                'entities': {},
                'source': 'error',
                'suggestions': []
            }

    @staticmethod
    def _build_prompt(user_message: str, intent: str, context: Dict = None) -> str:
        """Build prompt for LLM"""
        base_prompt = f"""You are a helpful customer support AI assistant. 

User's intent: {intent}
User's message: {user_message}

Context: {context if context else 'No additional context'}

Provide a helpful, professional, and concise response:"""

        return base_prompt

    @staticmethod
    def _get_fallback_response(intent: str) -> str:
        """Get fallback response based on intent"""
        fallback_responses = {
            'technical_issue': "I understand you're experiencing a technical issue. Let me connect you with our technical support team who can better assist you.",
            'billing_question': "For billing-related questions, I recommend speaking with our billing department. Would you like me to transfer you?",
            'greeting': "Hello! I'm here to help you. What can I assist you with today?",
            'farewell': "Thank you for contacting us! Have a great day!",
            'general_query': "I'm here to help! Could you please provide more details about what you need assistance with?"
        }

        return fallback_responses.get(intent, "I'm here to help! How can I assist you today?")

    @staticmethod
    def _get_suggestions(intent: str) -> List[str]:
        """Get quick reply suggestions based on intent"""
        suggestions_map = {
            'technical_issue': [
                "Describe the problem",
                "Check system status",
                "Talk to agent"
            ],
            'billing_question': [
                "View my invoice",
                "Update payment method",
                "Speak to billing"
            ],
            'general_support': [
                "Browse help center",
                "Contact support",
                "View documentation"
            ]
        }

        return suggestions_map.get(intent, ["How can I help you?"])

    @staticmethod
    def should_escalate(conversation: Conversation) -> Tuple[bool, str]:
        """
        Determine if conversation should be escalated to human agent
        """
        # Check negative sentiment
        if conversation.overall_sentiment == 'negative' and conversation.sentiment_score < -0.5:
            return True, "Negative sentiment detected"

        # Check conversation length
        message_count = conversation.messages.count()
        if message_count > 10:
            return True, "Extended conversation"

        # Check for escalation keywords
        recent_messages = conversation.messages.all()[:5]
        escalation_keywords = ['agent', 'human', 'person', 'manager', 'supervisor', 'speak to someone']

        for msg in recent_messages:
            if any(keyword in msg.content.lower() for keyword in escalation_keywords):
                return True, "Customer requested human agent"

        return False, ""


# Singleton instance
chatbot_engine = AIchatbotEngine()
