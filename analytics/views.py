from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, F, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from tickets.models import Ticket
from chatbot.models import Conversation


class AnalyticsViewSet(viewsets.ViewSet):
    """
    Comprehensive analytics API for dashboard
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get dashboard overview metrics"""
        # Date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Ticket metrics
        tickets = Ticket.objects.filter(created_at__range=[start_date, end_date])
        total_tickets = tickets.count()

        resolved_tickets = tickets.filter(status='resolved')
        avg_resolution_time = resolved_tickets.aggregate(
            avg_time=Avg('resolution_time_minutes')
        )['avg_time'] or 0

        # Chatbot metrics
        conversations = Conversation.objects.filter(
            started_at__range=[start_date, end_date]
        )
        total_conversations = conversations.count()

        # Sentiment distribution
        sentiment_data = conversations.values('overall_sentiment').annotate(
            count=Count('id')
        )

        # Escalation rate
        escalated_count = conversations.filter(escalated_to_human=True).count()
        escalation_rate = (escalated_count / total_conversations * 100) if total_conversations > 0 else 0

        return Response({
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'tickets': {
                'total': total_tickets,
                'resolved': resolved_tickets.count(),
                'resolution_rate': (resolved_tickets.count() / total_tickets * 100) if total_tickets > 0 else 0,
                'avg_resolution_hours': round(avg_resolution_time / 60, 2)
            },
            'chatbot': {
                'total_conversations': total_conversations,
                'escalation_rate': round(escalation_rate, 2),
                'avg_sentiment': self._calculate_avg_sentiment(conversations)
            },
            'sentiment_distribution': {
                item['overall_sentiment']: item['count']
                for item in sentiment_data
            }
        })

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trend data for charts"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Daily ticket trends
        daily_tickets = Ticket.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Daily sentiment trends
        daily_sentiment = Conversation.objects.filter(
            started_at__range=[start_date, end_date]
        ).annotate(
            date=TruncDate('started_at')
        ).values('date').annotate(
            avg_sentiment=Avg('sentiment_score'),
            count=Count('id')
        ).order_by('date')

        return Response({
            'tickets': {
                'dates': [item['date'].isoformat() for item in daily_tickets],
                'counts': [item['count'] for item in daily_tickets]
            },
            'sentiment': {
                'dates': [item['date'].isoformat() for item in daily_sentiment],
                'scores': [round(item['avg_sentiment'] or 0, 2) for item in daily_sentiment],
                'counts': [item['count'] for item in daily_sentiment]
            }
        })

    @action(detail=False, methods=['get'])
    def agent_performance(self, request):
        """Get agent performance metrics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        performance = Ticket.objects.filter(
            assigned_agent__isnull=False,
            created_at__range=[start_date, end_date]
        ).values(
            'assigned_agent__id',
            'assigned_agent__first_name',
            'assigned_agent__last_name'
        ).annotate(
            tickets_assigned=Count('id'),
            tickets_resolved=Count('id', filter=Q(status='resolved')),
            avg_resolution_time=Avg('resolution_time_minutes', filter=Q(status='resolved')),
            avg_customer_satisfaction=Avg('customer_satisfaction', filter=Q(customer_satisfaction__isnull=False))
        ).order_by('-tickets_resolved')

        return Response(performance)

    def _calculate_avg_sentiment(self, conversations):
        """Calculate average sentiment score"""
        sentiment_scores = conversations.exclude(
            sentiment_score=0
        ).values_list('sentiment_score', flat=True)

        if sentiment_scores:
            return round(sum(sentiment_scores) / len(sentiment_scores), 2)
        return 0
