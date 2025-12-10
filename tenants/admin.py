from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Tenant, Domain, TenantUser, IntegrationSettings


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'company_name', 'subscription_plan', 'is_active', 'created_on']
    list_filter = ['subscription_plan', 'is_active', 'created_on']
    search_fields = ['name', 'company_name', 'contact_email']
    readonly_fields = ['created_on', 'updated_on']

    fieldsets = (
        ('Basic Information', {
            'fields': ('schema_name', 'name', 'company_name', 'industry',
                       'company_size', 'website')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'is_active', 'max_users',
                       'max_tickets_per_month')
        }),
        ('AI Features', {
            'fields': ('ai_chatbot_enabled', 'sentiment_analysis_enabled',
                       'auto_ticket_classification')
        }),
        ('Customization', {
            'fields': ('primary_color', 'logo')
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(IntegrationSettings)
class IntegrationSettingsAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'slack_enabled', 'teams_enabled', 'zendesk_enabled']
    list_filter = ['slack_enabled', 'teams_enabled', 'zendesk_enabled']
    readonly_fields = ['api_key', 'created_at', 'updated_at']
