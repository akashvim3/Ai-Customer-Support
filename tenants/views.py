from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .models import Tenant, TenantUser, IntegrationSettings
from .serializers import (
    TenantSerializer, TenantUserSerializer,
    IntegrationSettingsSerializer, UserRegistrationSerializer
)


class TenantViewSet(viewsets.ModelViewSet):
    """Tenant management API"""
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own tenant
        if hasattr(self.request.user, 'tenant-user'):
            return Tenant.objects.filter(id=self.request.user.tenantuser.tenant.id)
        return Tenant.objects.none()

    @action(detail=True, methods=['get'])
    def settings(self, request, pk=None):
        """Get tenant settings"""
        tenant = self.get_object()
        serializer = self.get_serializer(tenant)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_settings(self, request, pk=None):
        """Update tenant settings"""
        tenant = self.get_object()
        serializer = self.get_serializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TenantUserViewSet(viewsets.ModelViewSet):
    """Tenant user management API"""
    serializer_class = TenantUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant-user'):
            return TenantUser.objects.filter(tenant=self.request.user.tenantuser.tenant)
        return TenantUser.objects.none()

    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """Change user role"""
        tenant_user = self.get_object()
        new_role = request.data.get('role')

        if new_role not in ['owner', 'admin', 'agent', 'viewer']:
            return Response(
                {'error': 'Invalid role'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant_user.role = new_role
        tenant_user.save()

        return Response({'status': 'role updated'})


class IntegrationSettingsViewSet(viewsets.ModelViewSet):
    """Integration settings API"""
    serializer_class = IntegrationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, 'tenant-user'):
            return IntegrationSettings.objects.filter(
                tenant=self.request.user.tenantuser.tenant
            )
        return IntegrationSettings.objects.none()


class RegistrationViewSet(viewsets.ViewSet):
    """User registration API"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register new user and create tenant"""
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'message': 'Registration successful',
            'user_id': user.id,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
