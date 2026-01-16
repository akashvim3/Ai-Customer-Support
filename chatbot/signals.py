from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Conversation
# from .sentiment_analyzer import sentiment_analyzer  # Temporarily disabled


@receiver(post_save, sender=Message)
def analyze_message_sentiment(sender, instance, created, **kwargs):
    """Automatically analyze sentiment when new message is created"""
    if created and instance.message_type == 'user':
        try:
            # Analyze sentiment - temporarily disabled
            # sentiment_result = sentiment_analyzer.analyze(instance.content)
            #
            # # Update message
            # instance.sentiment = sentiment_result['sentiment']
            # instance.sentiment_score = sentiment_result['score']
            # instance.save(update_fields=['sentiment', 'sentiment_score'])

            # Update conversation overall sentiment
            conversation = instance.conversation
            update_conversation_sentiment(conversation)

        except Exception as e:
            print(f"Error analyzing sentiment: {e}")


@receiver(post_save, sender=Conversation)
def check_escalation_needed(sender, instance, **kwargs):
    """Check if conversation needs escalation"""
    if not instance.escalated_to_human and instance.is_active:
        # from .ai_engine import chatbot_engine  # Temporarily disabled

        try:
            # should_escalate, reason = chatbot_engine.should_escalate(instance)
            # Temporarily disabled AI escalation check
            should_escalate = False
            reason = ""

            if should_escalate:
                instance.escalated_to_human = True
                instance.escalation_reason = reason
                instance.save(update_fields=['escalated_to_human', 'escalation_reason'])

                # Create notification for agents
                from django.contrib.auth.models import User
                from tenants.models import TenantUser

                agents = User.objects.filter(
                    tenantuser__role__in=['agent', 'admin'],
                    tenantuser__can_manage_tickets=True
                ).distinct()

                # Send notification (implement your notification system)
                print(f"Escalation needed for conversation {instance.session_id}")

        except Exception as e:
            print(f"Error checking escalation: {e}")


def update_conversation_sentiment(conversation):
    """Update overall conversation sentiment based on messages"""
    messages = conversation.messages.exclude(sentiment_score=0)

    if messages.exists():
        sentiment_scores = messages.values_list('sentiment_score', flat=True)
        avg_score = sum(sentiment_scores) / len(sentiment_scores)

        conversation.sentiment_score = avg_score

        if avg_score > 0.1:
            conversation.overall_sentiment = 'positive'
        elif avg_score < -0.1:
            conversation.overall_sentiment = 'negative'
        else:
            conversation.overall_sentiment = 'neutral'

        conversation.save(update_fields=['overall_sentiment', 'sentiment_score'])
