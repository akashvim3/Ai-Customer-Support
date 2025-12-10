from celery import shared_task
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
from datetime import timedelta
from .models import (
    AnalyticsSnapshot, AgentPerformance, CategoryPerformance,
    SentimentTrend, CustomerInsight, Alert
)
from tickets.models import Ticket
from chatbot.models import Conversation


@shared_task
def generate_daily_snapshot():
    """Generate daily analytics snapshot"""
    today = timezone.now().date()

    # Get ticket metrics
    tickets_today = Ticket.objects.filter(created_at__date=today)

    snapshot_data = {
        'snapshot_date': today,
        'snapshot_type': 'daily',
        'total_tickets': tickets_today.count(),
        'new_tickets': tickets_today.filter(status='new').count(),
        'open_tickets': tickets_today.filter(status='open').count(),
        'in_progress_tickets': tickets_today.filter(status='in_progress').count(),
        'resolved_tickets': tickets_today.filter(status='resolved').count(),
        'closed_tickets': tickets_today.filter(status='closed').count(),
    }

    # Calculate averages
    resolved_tickets = tickets_today.filter(status='resolved')
    if resolved_tickets.exists():
        snapshot_data['avg_resolution_time'] = resolved_tickets.aggregate(
            avg=Avg('resolution_time_minutes')
        )['avg'] or 0.0

    # Chatbot metrics
    conversations_today = Conversation.objects.filter(started_at__date=today)
    snapshot_data['total_conversations'] = conversations_today.count()
    snapshot_data['escalated_conversations'] = conversations_today.filter(
        escalated_to_human=True
    ).count()

    # Create or update snapshot
    snapshot, created = AnalyticsSnapshot.objects.update_or_create(
        snapshot_date=today,
        snapshot_type='daily',
        defaults=snapshot_data
    )

    return f"Daily snapshot generated for {today}"


@shared_task
def update_agent_performance():
    """Update agent performance metrics"""
    from django.contrib.auth.models import User
    from tenants.models import TenantUser

    today = timezone.now().date()

    # Get all agents
    agents = User.objects.filter(
        tenantuser__role__in=['agent', 'admin']
    ).distinct()

    for agent in agents:
        # Get tickets for today
        tickets = Ticket.objects.filter(
            assigned_agent=agent,
            created_at__date=today
        )

        performance_data = {
            'agent': agent,
            'date': today,
            'period_type': 'daily',
            'tickets_assigned': tickets.count(),
            'tickets_resolved': tickets.filter(status='resolved').count(),
            'tickets_reopened': tickets.filter(status='reopened').count(),
        }

        # Calculate averages
        resolved = tickets.filter(status='resolved')
        if resolved.exists():
            performance_data['avg_resolution_time'] = resolved.aggregate(
                avg=Avg('resolution_time_minutes')
            )['avg'] or 0.0

        # Create or update performance record
        AgentPerformance.objects.update_or_create(
            agent=agent,
            date=today,
            period_type='daily',
            defaults=performance_data
        )

    return f"Updated performance for {agents.count()} agents"


@shared_task
def update_sentiment_trends():
    """Update sentiment trend data"""
    today = timezone.now().date()

    # Get all conversations for today
    conversations = Conversation.objects.filter(started_at__date=today)

    sentiment_data = {
        'date': today,
        'positive_count': conversations.filter(overall_sentiment='positive').count(),
        'neutral_count': conversations.filter(overall_sentiment='neutral').count(),
        'negative_count': conversations.filter(overall_sentiment='negative').count(),
        'avg_sentiment_score': conversations.aggregate(
            avg=Avg('sentiment_score')
        )['avg'] or 0.0
    }

    SentimentTrend.objects.update_or_create(
        date=today,
        hour=None,  # Daily aggregation
        defaults=sentiment_data
    )

    return f"Sentiment trends updated for {today}"


@shared_task
def check_for_alerts():
    """Check metrics and create alerts if thresholds are breached"""
    # Check for high ticket volume
    today = timezone.now().date()
    tickets_today = Ticket.objects.filter(created_at__date=today).count()

    if tickets_today > 100:  # Threshold
        Alert.objects.get_or_create(
            alert_type='high_ticket_volume',
            title=f"High Ticket Volume Alert - {today}",
            defaults={
                'severity': 'medium',
                'message': f"Ticket volume today ({tickets_today}) exceeds normal threshold",
                'data': {'ticket_count': tickets_today, 'date': str(today)}
            }
        )

    return "Alert check completed"
