from django.contrib import admin
from .models import Ticket, TicketComment, TicketHistory, TicketAttachment, SLAPolicy


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'title_preview', 'status', 'priority', 'assigned_agent', 'created_at']
    list_filter = ['status', 'priority', 'category', 'source', 'sla_status', 'created_at']
    search_fields = ['ticket_id', 'title', 'description', 'customer_email']
    readonly_fields = ['ticket_id', 'created_at', 'updated_at', 'resolved_at']

    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_id', 'title', 'description')
        }),
        ('Customer', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_id')
        }),
        ('Classification', {
            'fields': ('category', 'subcategory', 'tags', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_agent', 'assigned_team')
        }),
        ('SLA', {
            'fields': ('due_date', 'sla_status', 'sla_breach_time')
        }),
        ('AI Analysis', {
            'fields': ('ai_confidence', 'ai_suggestions', 'sentiment_analysis')
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'resolved_at', 'resolution_time_minutes', 'customer_satisfaction')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def title_preview(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title

    title_preview.short_description = 'Title'


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'content_preview', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'is_automated', 'created_at']
    search_fields = ['content', 'ticket__ticket_id']
    readonly_fields = ['created_at', 'updated_at']

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content

    content_preview.short_description = 'Content'


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'action', 'field_changed', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['ticket__ticket_id', 'action']
    readonly_fields = ['timestamp']


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'ticket', 'uploaded_by', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'ticket__ticket_id']
    readonly_fields = ['uploaded_at']


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'first_response_time', 'resolution_time', 'is_active']
    list_filter = ['priority', 'is_active']
    search_fields = ['name', 'description']
