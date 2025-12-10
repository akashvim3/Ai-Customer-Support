"""
Celery Tasks for Ticket Management
Handles background processing for tickets
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def auto_assign_ticket(ticket_id):
    """
    Automatically assign ticket to available agent
    """
    from .models import Ticket
    from tenants.models import TenantUser
    from django.contrib.auth.models import User

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        # Skip if already assigned
        if ticket.assigned_agent:
            return f"Ticket {ticket.ticket_id} already assigned"

        # Get category-based team
        category_team_map = {
            'Technical Issue': 'technical',
            'Bug Report': 'technical',
            'Billing': 'billing',
            'Account Management': 'support',
            'Product Inquiry': 'support',
            'Feature Request': 'product',
            'General Support': 'general'
        }

        team = category_team_map.get(ticket.category, 'general')

        # Find available agents in team
        agents = TenantUser.objects.filter(
            role__in=['agent', 'admin'],
            is_active=True,
            can_manage_tickets=True,
            department=team
        ).select_related('user')

        if not agents.exists():
            # Fallback to any available agent
            agents = TenantUser.objects.filter(
                role__in=['agent', 'admin'],
                is_active=True,
                can_manage_tickets=True
            ).select_related('user')

        if agents.exists():
            # Get agent with least tickets
            from django.db.models import Count
            agent = agents.annotate(
                ticket_count=Count('user__assigned_tickets', filter=Q(
                    user__assigned_tickets__status__in=['new', 'open', 'in_progress']
                ))
            ).order_by('ticket_count').first()

            # Assign ticket
            ticket.assigned_agent = agent.user
            ticket.status = 'open'
            ticket.save()

            # Send notification to agent
            send_ticket_assignment_notification.delay(ticket.id, agent.user.id)

            logger.info(f"Ticket {ticket.ticket_id} assigned to {agent.user.username}")
            return f"Ticket {ticket.ticket_id} assigned to {agent.user.username}"
        else:
            logger.warning(f"No available agents for ticket {ticket.ticket_id}")
            return f"No available agents for ticket {ticket.ticket_id}"

    except Ticket.DoesNotExist:
        logger.error(f"Ticket with id {ticket_id} not found")
        return f"Ticket not found"
    except Exception as e:
        logger.error(f"Error auto-assigning ticket: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_ticket_assignment_notification(ticket_id, agent_id):
    """
    Send email notification when ticket is assigned
    """
    from .models import Ticket
    from django.contrib.auth.models import User

    try:
        ticket = Ticket.objects.get(id=ticket_id)
        agent = User.objects.get(id=agent_id)

        subject = f"New Ticket Assigned: {ticket.ticket_id}"
        message = f"""
        Hello {agent.get_full_name()},

        A new ticket has been assigned to you:

        Ticket ID: {ticket.ticket_id}
        Subject: {ticket.title}
        Priority: {ticket.priority}
        Category: {ticket.category}
        Customer: {ticket.customer_name} ({ticket.customer_email})

        Please review and respond at your earliest convenience.

        View ticket: {settings.SITE_URL}/tickets/{ticket.id}

        Best regards,
        AI Support Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [agent.email],
            fail_silently=False,
        )

        logger.info(f"Assignment notification sent to {agent.email}")
        return f"Notification sent to {agent.email}"

    except Exception as e:
        logger.error(f"Error sending assignment notification: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_ticket_update_notification(ticket_id, update_type='status_change'):
    """
    Send notification when ticket is updated
    """
    from .models import Ticket

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        subject = f"Ticket Update: {ticket.ticket_id}"
        message = f"""
        Hello {ticket.customer_name},

        Your support ticket has been updated:

        Ticket ID: {ticket.ticket_id}
        Subject: {ticket.title}
        Status: {ticket.status}

        {'Resolution: ' + ticket.resolution_notes if ticket.status == 'resolved' else ''}

        You can view the ticket details and add comments here:
        {settings.SITE_URL}/tickets/{ticket.id}

        Thank you for your patience.

        Best regards,
        Support Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [ticket.customer_email],
            fail_silently=False,
        )

        logger.info(f"Update notification sent to {ticket.customer_email}")
        return f"Notification sent"

    except Exception as e:
        logger.error(f"Error sending update notification: {e}")
        return f"Error: {str(e)}"


@shared_task
def check_sla_breaches():
    """
    Check for SLA breaches and send alerts
    """
    from .models import Ticket, SLAPolicy

    try:
        now = timezone.now()

        # Get active tickets
        active_tickets = Ticket.objects.filter(
            status__in=['new', 'open', 'in_progress']
        )

        breached_count = 0
        warning_count = 0

        for ticket in active_tickets:
            # Get SLA policy for ticket
            try:
                sla_policy = SLAPolicy.objects.filter(
                    priority=ticket.priority,
                    is_active=True
                ).first()

                if not sla_policy:
                    continue

                # Calculate time elapsed
                time_elapsed = (now - ticket.created_at).total_seconds() / 3600  # hours

                # Check first response SLA
                if not ticket.first_response_at:
                    if time_elapsed >= sla_policy.first_response_time:
                        ticket.sla_status = 'breached'
                        ticket.sla_breach_time = now
                        ticket.save()
                        breached_count += 1

                        # Send alert
                        send_sla_breach_alert.delay(ticket.id, 'first_response')

                    elif time_elapsed >= sla_policy.first_response_time * 0.8:
                        ticket.sla_status = 'warning'
                        ticket.save()
                        warning_count += 1

                # Check resolution SLA
                if not ticket.resolved_at:
                    if time_elapsed >= sla_policy.resolution_time:
                        ticket.sla_status = 'breached'
                        ticket.sla_breach_time = now
                        ticket.save()
                        breached_count += 1

                        # Send alert
                        send_sla_breach_alert.delay(ticket.id, 'resolution')

                    elif time_elapsed >= sla_policy.resolution_time * 0.8:
                        if ticket.sla_status != 'breached':
                            ticket.sla_status = 'warning'
                            ticket.save()
                            warning_count += 1

            except Exception as e:
                logger.error(f"Error checking SLA for ticket {ticket.ticket_id}: {e}")
                continue

        logger.info(f"SLA check completed: {breached_count} breached, {warning_count} warnings")
        return {
            'breached': breached_count,
            'warnings': warning_count
        }

    except Exception as e:
        logger.error(f"Error in SLA check: {e}")
        return {'error': str(e)}


@shared_task
def send_sla_breach_alert(ticket_id, breach_type='resolution'):
    """
    Send alert when SLA is breached
    """
    from .models import Ticket
    from tenants.models import TenantUser

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        # Get admins and managers
        admins = TenantUser.objects.filter(
            role__in=['owner', 'admin'],
            is_active=True
        ).select_related('user')

        admin_emails = [admin.user.email for admin in admins]

        if ticket.assigned_agent:
            admin_emails.append(ticket.assigned_agent.email)

        subject = f"SLA BREACH ALERT: {ticket.ticket_id}"
        message = f"""
        URGENT: SLA Breach Alert

        Ticket: {ticket.ticket_id}
        Subject: {ticket.title}
        Priority: {ticket.priority}
        Customer: {ticket.customer_name}
        Breach Type: {breach_type.replace('_', ' ').title()}
        Created: {ticket.created_at}

        Immediate action required!

        View ticket: {settings.SITE_URL}/tickets/{ticket.id}
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            admin_emails,
            fail_silently=False,
        )

        logger.info(f"SLA breach alert sent for ticket {ticket.ticket_id}")
        return f"Alert sent"

    except Exception as e:
        logger.error(f"Error sending SLA breach alert: {e}")
        return f"Error: {str(e)}"


@shared_task
def auto_close_resolved_tickets():
    """
    Automatically close tickets that have been resolved for a period
    """
    from .models import Ticket

    try:
        # Close tickets resolved for more than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)

        tickets_to_close = Ticket.objects.filter(
            status='resolved',
            resolved_at__lt=cutoff_date
        )

        count = tickets_to_close.count()

        for ticket in tickets_to_close:
            ticket.status = 'closed'
            ticket.save()

            # Send notification
            send_ticket_update_notification.delay(ticket.id, 'auto_closed')

        logger.info(f"Auto-closed {count} resolved tickets")
        return f"Closed {count} tickets"

    except Exception as e:
        logger.error(f"Error auto-closing tickets: {e}")
        return f"Error: {str(e)}"


@shared_task
def generate_ticket_report(report_type='daily'):
    """
    Generate ticket reports
    """
    from .models import Ticket
    from django.db.models import Count, Avg

    try:
        if report_type == 'daily':
            start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif report_type == 'weekly':
            start_date = timezone.now() - timedelta(days=7)
        else:
            start_date = timezone.now() - timedelta(days=30)

        # Get statistics
        tickets = Ticket.objects.filter(created_at__gte=start_date)

        stats = {
            'total': tickets.count(),
            'by_status': dict(tickets.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_priority': dict(
                tickets.values('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'by_category': dict(
                tickets.values('category').annotate(count=Count('id')).values_list('category', 'count')),
            'avg_resolution_time': tickets.filter(
                resolved_at__isnull=False
            ).aggregate(avg=Avg('resolution_time_minutes'))['avg']
        }

        logger.info(f"{report_type.title()} ticket report generated")
        return stats

    except Exception as e:
        logger.error(f"Error generating ticket report: {e}")
        return {'error': str(e)}


@shared_task
def clean_spam_tickets():
    """
    Mark and clean up spam tickets
    """
    from .models import Ticket

    try:
        # Simple spam detection based on patterns
        spam_patterns = [
            'viagra', 'cialis', 'casino', 'lottery', 'winner',
            'congratulations', 'click here now', 'free money'
        ]

        tickets = Ticket.objects.filter(is_spam=False)
        spam_count = 0

        for ticket in tickets:
            content = (ticket.title + ' ' + ticket.description).lower()

            if any(pattern in content for pattern in spam_patterns):
                ticket.is_spam = True
                ticket.status = 'closed'
                ticket.save()
                spam_count += 1

        logger.info(f"Marked {spam_count} tickets as spam")
        return f"Marked {spam_count} spam tickets"

    except Exception as e:
        logger.error(f"Error cleaning spam tickets: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_customer_satisfaction_survey(ticket_id):
    """
    Send customer satisfaction survey after ticket resolution
    """
    from .models import Ticket

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        if ticket.status != 'resolved':
            return "Ticket not resolved"

        subject = f"How was your support experience? - {ticket.ticket_id}"
        message = f"""
        Hello {ticket.customer_name},

        Your ticket has been resolved. We'd love to hear about your experience!

        Please take a moment to rate your support experience:

        Rate your experience: {settings.SITE_URL}/feedback/{ticket.id}

        Your feedback helps us improve our service.

        Thank you!
        Support Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [ticket.customer_email],
            fail_silently=False,
        )

        logger.info(f"CSAT survey sent for ticket {ticket.ticket_id}")
        return "Survey sent"

    except Exception as e:
        logger.error(f"Error sending CSAT survey: {e}")
        return f"Error: {str(e)}"
