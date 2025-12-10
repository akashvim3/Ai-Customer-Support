from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from tickets.models import Ticket
from chatbot.models import Conversation
from .models import CustomerInsight, Alert


@receiver(post_save, sender=Ticket)
def update_customer_insight_on_ticket(sender, instance, created, **kwargs):
    """Update customer insights when ticket is created or updated"""
    if created:
        insight, created = CustomerInsight.objects.get_or_create(
            customer_email=instance.customer_email,
            defaults={
                'customer_name': instance.customer_name,
                'first_interaction_date': timezone.now()
            }
        )

        insight.total_tickets += 1
        insight.total_interactions += 1
        insight.last_interaction_date = timezone.now()

        # Update top categories
        if instance.category and instance.category not in insight.top_categories:
            insight.top_categories.append(instance.category)
            insight.top_categories = insight.top_categories[:5]  # Keep top 5

        insight.save()
        insight.update_risk_score()


@receiver(post_save, sender=Conversation)
def update_customer_insight_on_conversation(sender, instance, created, **kwargs):
    """Update customer insights when conversation is created or updated"""
    if instance.customer_email and created:
        insight, created = CustomerInsight.objects.get_or_create(
            customer_email=instance.customer_email,
            defaults={
                'customer_name': instance.customer_name,
                'first_interaction_date': timezone.now()
            }
        )

        insight.total_conversations += 1
        insight.total_interactions += 1
        insight.last_interaction_date = timezone.now()

        # Update sentiment
        if instance.sentiment_score != 0:
            total_sentiment = (insight.avg_sentiment_score * (insight.total_interactions - 1) +
                               instance.sentiment_score)
            insight.avg_sentiment_score = total_sentiment / insight.total_interactions

        insight.save()


@receiver(post_save, sender=Ticket)
def create_sla_breach_alert(sender, instance, **kwargs):
    """Create alert when SLA is breached"""
    if instance.sla_status == 'breached' and not instance.is_spam:
        Alert.objects.get_or_create(
            alert_type='sla_breach',
            title=f"SLA Breach: {instance.ticket_id}",
            defaults={
                'severity': 'high' if instance.priority == 'urgent' else 'medium',
                'message': f"Ticket {instance.ticket_id} has breached SLA. "
                           f"Priority: {instance.priority}, Category: {instance.category}",
                'data': {
                    'ticket_id': instance.ticket_id,
                    'priority': instance.priority,
                    'category': instance.category,
                    'created_at': instance.created_at.isoformat()
                }
            }
        )
