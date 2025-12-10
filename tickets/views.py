from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg
from .models import Ticket, TicketComment
from .serializers import TicketSerializer, TicketCommentSerializer


class TicketViewSet(viewsets.ModelViewSet):
    """
    Advanced ticket management API with AI integration
    """
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = {
        'status': ['exact', 'in'],
        'priority': ['exact', 'in'],
        'category': ['exact', 'contains'],
        'assigned_agent': ['exact', 'isnull'],
        'created_at': ['gte', 'lte', 'exact'],
        'source': ['exact'],
    }

    search_fields = [
        'ticket_id', 'title', 'description',
        'customer_name', 'customer_email'
    ]

    ordering_fields = [
        'created_at', 'updated_at', 'priority',
        'due_date', 'status'
    ]

    ordering = ['-priority', 'created_at']

    def get_queryset(self):
        """Filter tickets based on user permissions"""
        user = self.request.user

        # Admins can see all tickets
        if hasattr(user, 'tenant-user') and user.tenantuser.role in ['owner', 'admin', 'agent']:
            return Ticket.objects.all()

        # Regular users can only see their own tickets
        return Ticket.objects.filter(customer_email=user.email)

    def perform_update(self, serializer):
        """Track changes in ticket history"""
        instance = serializer.instance
        changes = []

        # Detect changes
        if instance.status != serializer.validated_data.get('status', instance.status):
            changes.append({
                'field': 'status',
                'old': instance.status,
                'new': serializer.validated_data.get('status', instance.status)
            })

        if instance.assigned_agent != serializer.validated_data.get('assigned_agent', instance.assigned_agent):
            changes.append({
                'field': 'assigned_agent',
                'old': str(instance.assigned_agent) if instance.assigned_agent else None,
                'new': str(serializer.validated_data.get('assigned_agent')) if serializer.validated_data.get(
                    'assigned_agent') else None
            })

        # Save ticket
        ticket = serializer.save()

        # Create history entries for each change
        for change in changes:
            TicketHistory.objects.create(
                ticket=ticket,
                action='updated',
                field_changed=change['field'],
                old_value=change['old'],
                new_value=change['new'],
                user=self.request.user
            )

        return ticket

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign ticket to agent"""
        ticket = self.get_object()
        agent_id = request.data.get('agent_id')

        try:
            agent = User.objects.get(id=agent_id)
            ticket.assigned_agent = agent
            ticket.status = 'open'
            ticket.save()

            # Create history
            TicketHistory.objects.create(
                ticket=ticket,
                action='assigned',
                user=request.user
            )

            return Response({'status': 'assigned'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve ticket"""
        ticket = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')

        ticket.status = 'resolved'
        ticket.resolution_notes = resolution_notes
        ticket.resolved_at = timezone.now()

        # Calculate resolution time
        if ticket.first_response_at:
            ticket.resolution_time_minutes = int(
                (timezone.now() - ticket.first_response_at).total_seconds() / 60
            )

        ticket.save()

        # Create history
        TicketHistory.objects.create(
            ticket=ticket,
            action='resolved',
            user=request.user
        )

        return Response({'status': 'resolved'})

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get ticket metrics for dashboard"""
        queryset = self.get_queryset()

        metrics = {
            'total': queryset.count(),
            'by_status': dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_priority': dict(
                queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'by_category': dict(
                queryset.values('category').annotate(count=Count('id')).values_list('category', 'count')),
            'unassigned': queryset.filter(assigned_agent__isnull=True).count(),
            'overdue': queryset.filter(due_date__lt=timezone.now(), status__in=['new', 'open', 'in_progress']).count(),
            'avg_resolution_time': queryset.filter(resolution_time_minutes__isnull=False).aggregate(
                avg_time=Avg('resolution_time_minutes')
            )['avg_time']
        }

        return Response(metrics)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update tickets"""
        ticket_ids = request.data.get('ticket_ids', [])
        statu = request.data.get('status')
        assigned_agent_id = request.data.get('assigned_agent_id')

        if not ticket_ids:
            return Response(
                {'error': 'No tickets selected'},
                status=statu.HTTP_400_BAD_REQUEST
            )

        tickets = Ticket.objects.filter(id__in=ticket_ids)
        updated_count = 0

        for ticket in tickets:
            if statu:
                ticket.status = statu
            if assigned_agent_id:
                ticket.assigned_agent_id = assigned_agent_id

            ticket.save()
            updated_count += 1

        return Response({'updated_count': updated_count})
