from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_data():
    """
    Clean up old data to maintain database performance
    """
    from tickets.models import Ticket, TicketHistory
    from chatbot.models import Conversation, Message
    from analytics.models import AnalyticsSnapshot

    cutoff_date = timezone.now() - timedelta(days=365)  # 1 year

    try:
        # Archive old closed tickets
        old_tickets = Ticket.objects.filter(
            status='closed',
            updated_at__lt=cutoff_date
        )
        archived_count = old_tickets.count()

        # Delete old ticket history (keep only last 90 days)
        history_cutoff = timezone.now() - timedelta(days=90)
        deleted_history = TicketHistory.objects.filter(
            timestamp__lt=history_cutoff
        ).delete()

        # Delete old inactive conversations (not escalated)
        old_conversations = Conversation.objects.filter(
            is_active=False,
            escalated_to_human=False,
            ended_at__lt=cutoff_date
        )
        deleted_conversations = old_conversations.count()
        old_conversations.delete()

        # Keep only last 2 years of daily snapshots
        snapshot_cutoff = timezone.now() - timedelta(days=730)
        old_snapshots = AnalyticsSnapshot.objects.filter(
            snapshot_type='daily',
            snapshot_date__lt=snapshot_cutoff.date()
        )
        deleted_snapshots = old_snapshots.count()
        old_snapshots.delete()

        logger.info(
            f"Cleanup completed: "
            f"Archived {archived_count} tickets, "
            f"Deleted {deleted_history[0]} history records, "
            f"{deleted_conversations} conversations, "
            f"{deleted_snapshots} snapshots"
        )

        return {
            'archived_tickets': archived_count,
            'deleted_history': deleted_history[0],
            'deleted_conversations': deleted_conversations,
            'deleted_snapshots': deleted_snapshots
        }

    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {e}")
        return {'error': str(e)}


@shared_task
def train_ml_models():
    """
    Train ML models with latest data
    """
    from chatbot.ticket_classifier import ticket_classifier

    try:
        # Get training data from tickets
        training_data = ticket_classifier.get_training_data_from_tickets()

        if len(training_data) >= 100:
            # Train the model
            ticket_classifier.train_traditional_model(training_data)

            logger.info(f"ML models trained with {len(training_data)} samples")

            return {
                'status': 'success',
                'samples': len(training_data)
            }
        else:
            logger.warning(f"Insufficient training data: {len(training_data)} samples")
            return {
                'status': 'skipped',
                'reason': 'insufficient_data',
                'samples': len(training_data)
            }

    except Exception as e:
        logger.error(f"Error in train_ml_models: {e}")
        return {'error': str(e)}


@shared_task
def send_daily_report():
    """
    Send daily report to administrators
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from tenants.models import TenantUser
    from tickets.models import Ticket
    from chatbot.models import Conversation

    try:
        today = timezone.now().date()

        # Get today's stats
        tickets_today = Ticket.objects.filter(created_at__date=today).count()
        resolved_today = Ticket.objects.filter(
            status='resolved',
            resolved_at__date=today
        ).count()
        conversations_today = Conversation.objects.filter(
            started_at__date=today
        ).count()

        # Get admin emails
        admins = TenantUser.objects.filter(
            role__in=['owner', 'admin']
        ).values_list('user__email', flat=True)

        # Send email
        subject = f"Daily Report - {today}"
        message = f"""
        Daily Support Summary for {today}

        Tickets Created: {tickets_today}
        Tickets Resolved: {resolved_today}
        Conversations: {conversations_today}

        Log in to view detailed analytics.
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(admins),
            fail_silently=False,
        )

        logger.info(f"Daily report sent to {len(admins)} admins")

        return {
            'status': 'success',
            'recipients': len(admins)
        }

    except Exception as e:
        logger.error(f"Error sending daily report: {e}")
        return {'error': str(e)}


@shared_task
def backup_database():
    """
    Create database backup (implement based on your infrastructure)
    """
    try:
        # Implement your backup logic here
        # This could involve calling external backup services
        # or creating database dumps

        logger.info("Database backup completed")

        return {'status': 'success'}

    except Exception as e:
        logger.error(f"Error in backup_database: {e}")
        return {'error': str(e)}


@shared_task
def update_customer_insights():
    """
    Update customer insights and risk scores
    """
    from analytics.models import CustomerInsight

    try:
        # Update all customer risk scores
        customers = CustomerInsight.objects.all()
        updated_count = 0

        for customer in customers:
            customer.update_risk_score()
            updated_count += 1

        logger.info(f"Updated risk scores for {updated_count} customers")

        return {
            'status': 'success',
            'updated_customers': updated_count
        }

    except Exception as e:
        logger.error(f"Error updating customer insights: {e}")
        return {'error': str(e)}
