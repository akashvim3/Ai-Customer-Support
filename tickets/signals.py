from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Ticket, TicketHistory, TicketComment


@receiver(pre_save, sender=Ticket)
def track_ticket_changes(sender, instance, **kwargs):
    """Track changes to ticket fields"""
    if instance.pk:  # Only for existing tickets
        try:
            old_ticket = Ticket.objects.get(pk=instance.pk)

            # Track status changes
            if old_ticket.status != instance.status:
                TicketHistory.objects.create(
                    ticket=instance,
                    action='status_changed',
                    field_changed='status',
                    old_value=old_ticket.status,
                    new_value=instance.status
                )

                # Set resolved time
                if instance.status == 'resolved' and not instance.resolved_at:
                    instance.resolved_at = timezone.now()

            # Track assignment changes
            if old_ticket.assigned_agent != instance.assigned_agent:
                TicketHistory.objects.create(
                    ticket=instance,
                    action='assigned',
                    field_changed='assigned_agent',
                    old_value=str(old_ticket.assigned_agent) if old_ticket.assigned_agent else None,
                    new_value=str(instance.assigned_agent) if instance.assigned_agent else None
                )

            # Track priority changes
            if old_ticket.priority != instance.priority:
                TicketHistory.objects.create(
                    ticket=instance,
                    action='priority_changed',
                    field_changed='priority',
                    old_value=old_ticket.priority,
                    new_value=instance.priority
                )

        except Ticket.DoesNotExist:
            pass


@receiver(post_save, sender=Ticket)
def auto_classify_ticket(sender, instance, created, **kwargs):
    """Automatically classify ticket on creation"""
    if created:
        from chatbot.ticket_classifier import ticket_classifier

        try:
            # Run AI classification
            classification = ticket_classifier.classify_ticket(
                title=instance.title,
                description=instance.description
            )

            # Update ticket with classification results
            Ticket.objects.filter(pk=instance.pk).update(
                category=classification['category'],
                priority=classification['priority'],
                ai_confidence=classification['category_confidence'],
                ai_suggestions=classification,
                tags=classification['tags']
            )

        except Exception as e:
            print(f"Error in auto-classification: {e}")


@receiver(post_save, sender=TicketComment)
def update_ticket_on_comment(sender, instance, created, **kwargs):
    """Update ticket timestamps when comment is added"""
    if created:
        ticket = instance.ticket

        # Update first response time if this is first agent response
        if instance.author != ticket.customer_email and not ticket.first_response_at:
            ticket.first_response_at = timezone.now()
            ticket.save(update_fields=['first_response_at'])

        # Update ticket updated_at
        ticket.updated_at = timezone.now()
        ticket.save(update_fields=['updated_at'])
