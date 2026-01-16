from rest_framework import serializers
from django.utils import timezone
from .models import Ticket, TicketComment, TicketAttachment, TicketHistory
from chatbot.serializers import SentimentSerializer


class TicketSerializer(serializers.ModelSerializer):
    """Advanced ticket serializer with nested relationships"""
    comments = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    sentiment_analysis = SentimentSerializer(read_only=True)
    assigned_agent_name = serializers.CharField(source='assigned_agent.get_full_name', read_only=True)
    customer_initials = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = [
            'id', 'ticket_id', 'created_at', 'updated_at',
            'sentiment_analysis', 'ai_confidence', 'sla_status'
        ]

    @staticmethod
    def get_comments(obj):
        """Get ticket comments"""
        from .serializers import TicketCommentSerializer
        comments = obj.comments.all()[:5]  # Limit for performance
        return TicketCommentSerializer(comments, many=True).data

    @staticmethod
    def get_attachments(obj):
        """Get ticket attachments"""
        from .serializers import TicketAttachmentSerializer
        attachments = obj.attachments.all()
        return TicketAttachmentSerializer(attachments, many=True).data

    @staticmethod
    def get_customer_initials(obj):
        """Generate customer initials"""
        if obj.customer_name:
            parts = obj.customer_name.split()
            return ''.join([p[0].upper() for p in parts[:2]])
        return obj.customer_email[:2].upper()

    def validate(self, data):
        """Custom validation logic"""
        if data.get('status') == 'resolved' and not data.get('resolution_notes'):
            raise serializers.ValidationError(
                {"resolution_notes": "Resolution notes required when closing ticket"}
            )
        return data

    def create(self, validated_data):
        """Create ticket with AI classification"""
        from chatbot.ticket_classifier import ticket_classifier

        # Generate AI classification
        classification = ticket_classifier.classify_ticket(
            title=validated_data.get('title', ''),
            description=validated_data.get('description', '')
        )

        # Apply AI suggestions
        validated_data['category'] = classification['category']
        validated_data['priority'] = classification['priority']
        validated_data['ai_confidence'] = classification['category_confidence']
        validated_data['ai_suggestions'] = classification

        # Set due date based on priority
        if not validated_data.get('due_date'):
            priority_hours = {
                'urgent': 4,
                'high': 24,
                'medium': 72,
                'low': 168
            }
            hours = priority_hours.get(validated_data['priority'], 72)
            validated_data['due_date'] = timezone.now() + timezone.timedelta(hours=hours)

        ticket = super().create(validated_data)

        # Create history entry
        TicketHistory.objects.create(
            ticket=ticket,
            action='created',
            user=self.context['request'].user if self.context.get('request') else None
        )

        return ticket


class TicketCommentSerializer(serializers.ModelSerializer):
    """Serializer for ticket comments"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = TicketComment
        fields = [
            'id', 'ticket', 'author', 'author_name', 'content', 
            'is_internal', 'is_automated', 'created_at', 'updated_at',
            'sentiment_analysis'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'sentiment_analysis']


class TicketAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for ticket attachments"""
    filename = serializers.CharField(read_only=True)
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketAttachment
        fields = [
            'id', 'ticket', 'file', 'filename', 'file_size', 
            'mime_type', 'uploaded_by', 'uploaded_at', 'file_size_display'
        ]
        read_only_fields = ['id', 'filename', 'file_size', 'mime_type', 'uploaded_at']
    
    def get_file_size_display(self, obj):
        """Display file size in human readable format"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
