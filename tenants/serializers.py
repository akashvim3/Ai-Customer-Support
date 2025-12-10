from rest_framework import serializers
from .models import Tenant, TenantUser, IntegrationSettings
from django.contrib.auth.models import User


class TenantSerializer(serializers.ModelSerializer):
    """Tenant serializer with nested relationships"""
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'schema_name', 'name', 'company_name',
            'created_on', 'subscription_plan', 'is_active',
            'max_users', 'max_tickets_per_month', 'ai_chatbot_enabled',
            'sentiment_analysis_enabled', 'auto_ticket_classification',
            'primary_color', 'logo', 'contact_email', 'users_count'
        ]
        read_only_fields = ['id', 'schema_name', 'created_on']

    @staticmethod
    def get_users_count(obj):
        return obj.tenant_users.count()


class TenantUserSerializer(serializers.ModelSerializer):
    """Tenant user serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = TenantUser
        fields = [
            'id', 'user', 'user_email', 'user_name', 'role',
            'phone_number', 'profile_picture', 'department',
            'can_manage_tickets', 'can_view_analytics',
            'can_manage_chatbot', 'can_manage_users',
            'is_active', 'last_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_email', 'user_name']


class IntegrationSettingsSerializer(serializers.ModelSerializer):
    """Integration settings serializer"""

    class Meta:
        model = IntegrationSettings
        fields = [
            'id', 'tenant', 'api_key', 'webhook_url',
            'slack_webhook', 'slack_enabled',
            'teams_webhook', 'teams_enabled',
            'zendesk_api_key', 'zendesk_enabled',
            'support_email', 'email_integration_enabled',
            'widget_position', 'widget_color', 'welcome_message'
        ]
        read_only_fields = ['id', 'api_key', 'api_secret']
        extra_kwargs = {
            'api_secret': {'write_only': True}
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    company_name = serializers.CharField(max_length=200)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm',
                  'first_name', 'last_name', 'company_name']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        company_name = validated_data.pop('company_name')

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Create tenant
        tenant = Tenant.objects.create(
            schema_name=f"tenant_{user.username}",
            name=company_name,
            company_name=company_name,
            contact_email=user.email
        )

        # Create domain
        from .models import Domain
        Domain.objects.create(
            domain=f"{user.username}.localhost",
            tenant=tenant,
            is_primary=True
        )

        # Create tenant user
        TenantUser.objects.create(
            user=user,
            tenant=tenant,
            role='owner'
        )

        return user
