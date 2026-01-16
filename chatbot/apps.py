from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    verbose_name = 'AI Chatbot'

    def ready(self):
        """Initialize chatbot components when app is ready"""
        import chatbot.signals

        # Pre-load ML models (optional, for better performance)
        # Temporarily disabled due to dependency issues
        # try:
        #     from .ai_engine import chatbot_engine
        #     from .sentiment_analyzer import sentiment_analyzer
        #     from .ticket_classifier import ticket_classifier
        #
        #     # Models will be lazy-loaded on first use
        #     print("✓ Chatbot module initialized")
        # except Exception as e:
        #     print(f"⚠ Chatbot initialization warning: {e}")
        print("✓ Chatbot module initialized (AI components temporarily disabled)")
