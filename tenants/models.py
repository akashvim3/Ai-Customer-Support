from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import User


class Tenant(TenantMixin):
    """
    Tenant model for multi-tenant architecture
    Each tenant represents a business/organization using the platform
    """
    name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    # Business Information
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)

    # Subscription & Billing
    subscription_plan = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    is_active = models.BooleanField(default=True)
    max_users = models.IntegerField(default=5)
    max_tickets_per_month = models.IntegerField(default=100)

    # AI Features Configuration
    ai_chatbot_enabled = models.BooleanField(default=True)
    sentiment_analysis_enabled = models.BooleanField(default=True)
    auto_ticket_classification = models.BooleanField(default=True)

    # Customization
    primary_color = models.CharField(max_length=7, default='#87CEEB')
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)

    # Contact Information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)

    # Billing Information
    billing_email = models.EmailField(blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    auto_create_schema = True

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Domain model for tenant routing
    """
    pass


class TenantUser(models.Model):
    """
    Extended user model for tenant-specific user data
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tenant_users')

    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('agent', 'Support Agent'),
            ('viewer', 'Viewer'),
        ],
        default='agent'
    )

    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)

    # Permissions
    can_manage_tickets = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)
    can_manage_chatbot = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)

    # Activity
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'tenant')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name}"


class IntegrationSettings(models.Model):
    """
    Store integration settings for each tenant
    """
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='integration_settings')

    # API Integration
    api_key = models.CharField(max_length=255, unique=True)
    api_secret = models.CharField(max_length=255)
    webhook_url = models.URLField(blank=True)

    # Third-party Integrations
    slack_webhook = models.URLField(blank=True)
    slack_enabled = models.BooleanField(default=False)

    teams_webhook = models.URLField(blank=True)
    teams_enabled = models.BooleanField(default=False)

    zendesk_api_key = models.CharField(max_length=255, blank=True)
    zendesk_enabled = models.BooleanField(default=False)

    # Email Integration
    support_email = models.EmailField(blank=True)
    email_integration_enabled = models.BooleanField(default=False)

    # Chatbot Widget Configuration
    widget_position = models.CharField(
        max_length=20,
        choices=[('bottom-right', 'Bottom Right'), ('bottom-left', 'Bottom Left')],
        default='bottom-right'
    )
    widget_color = models.CharField(max_length=7, default='#87CEEB')
    welcome_message = models.TextField(default='Hello! How can I help you today?')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Integration Settings - {self.tenant.name}"
