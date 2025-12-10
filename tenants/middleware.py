"""
Tenant Middleware
Handles tenant resolution and context management
"""

from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from .models import Tenant, Domain
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to identify and set the current tenant based on domain
    """

    def process_request(self, request):
        """
        Identify tenant from hostname and set it in request
        """
        hostname = request.get_host().split(':')[0].lower()

        try:
            # Try to get domain
            domain = Domain.objects.select_related('tenant').get(
                domain=hostname
            )

            # Set tenant in request
            request.tenant = domain.tenant

            # Check if tenant is active
            if not request.tenant.is_active:
                logger.warning(f"Inactive tenant accessed: {request.tenant.name}")
                return self.tenant_inactive_response(request)

            # Set tenant schema
            request.tenant.activate()

        except Domain.DoesNotExist:
            # Check if this is the public schema
            if hostname in ['localhost', '127.0.0.1', 'test-server']:
                try:
                    # Get public tenant
                    public_tenant = Tenant.objects.get(schema_name='public')
                    request.tenant = public_tenant
                    public_tenant.activate()
                except Tenant.DoesNotExist:
                    logger.error("Public tenant not found")
                    raise Http404("Tenant not found")
            else:
                logger.warning(f"Unknown domain accessed: {hostname}")
                raise Http404("Tenant not found")

        return None

    @staticmethod
    def tenant_inactive_response(request):
        """
        Return response for inactive tenant
        """
        from django.http import HttpResponse
        return HttpResponse(
            '<h1>Account Suspended</h1><p>This account has been suspended. Please contact support.</p>',
            status=503
        )


class TenantContextMiddleware(MiddlewareMixin):
    """
    Add tenant context to all requests
    """

    @staticmethod
    def process_request(request):
        """
        Add tenant information to request context
        """
        if hasattr(request, 'tenant'):
            # Add tenant to template context
            if not hasattr(request, '_tenant_context'):
                request._tenant_context = {
                    'tenant': request.tenant,
                    'tenant_name': request.tenant.name,
                    'tenant_schema': request.tenant.schema_name,
                }

        return None

    @staticmethod
    def process_template_response(request, response):
        """
        Add tenant context to template response
        """
        if hasattr(request, '_tenant_context') and hasattr(response, 'context_data'):
            if response.context_data is None:
                response.context_data = {}
            response.context_data.update(request.tenant_context)

        return response


# noinspection PyGlobalUndefined
class TenantUserMiddleware(MiddlewareMixin):
    """
    Ensure user belongs to the current tenant
    """

    def process_request(self, request):
        """
        Verify user tenant membership
        """
        global TenantUser
        if request.user.is_authenticated and hasattr(request, 'tenant'):
            # Skip for superusers
            if request.user.is_superuser:
                return None

            # Check if user belongs to tenant
            try:
                from .models import TenantUser
                tenant_user = TenantUser.objects.get(
                    user=request.user,
                    tenant=request.tenant
                )

                # Check if user is active
                if not tenant_user.is_active:
                    logger.warning(f"Inactive user accessed: {request.user.username}")
                    return self.user_inactive_response(request)

                # Add tenant user to request
                request.tenant_user = tenant_user

                # Update last active
                tenant_user.update_last_active()

            except TenantUser.DoesNotExist:
                # User doesn't belong to this tenant
                logger.warning(
                    f"User {request.user.username} attempted to access "
                    f"tenant {request.tenant.name} without membership"
                )

                # Redirect to appropriate page or return 403
                if request.path.startswith('/api/'):
                    from django.http import JsonResponse
                    return JsonResponse(
                        {'error': 'You do not have access to this organization'},
                        status=403
                    )
                else:
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect(reverse('login'))

        return None

    @staticmethod
    def user_inactive_response(request):
        """
        Return response for inactive user
        """
        from django.http import HttpResponse
        return HttpResponse(
            '<h1>Account Inactive</h1><p>Your account has been deactivated. Please contact your administrator.</p>',
            status=403
        )


class TenantQuotaMiddleware(MiddlewareMixin):
    """
    Check tenant quotas and limits
    """

    def process_request(self, request):
        """
        Check if tenant has exceeded quotas
        """
        if not hasattr(request, 'tenant'):
            return None

        tenant = request.tenant

        # Skip for GET requests
        if request.method == 'GET':
            return None

        # Check ticket quota for ticket creation
        if request.path.startswith('/api/tickets/') and request.method == 'POST':
            if not self.check_ticket_quota(tenant):
                logger.warning(f"Tenant {tenant.name} exceeded ticket quota")

                if request.path.startswith('/api/'):
                    from django.http import JsonResponse
                    return JsonResponse(
                        {
                            'error': 'Ticket quota exceeded',
                            'message': 'You have reached your monthly ticket limit. Please upgrade your plan.'
                        },
                        status=429
                    )

        # Check user quota for user invitation
        if request.path.startswith('/api/tenants/users/') and request.method == 'POST':
            if not self.check_user_quota(tenant):
                logger.warning(f"Tenant {tenant.name} exceeded user quota")

                if request.path.startswith('/api/'):
                    from django.http import JsonResponse
                    return JsonResponse(
                        {
                            'error': 'User quota exceeded',
                            'message': 'You have reached your user limit. Please upgrade your plan.'
                        },
                        status=429
                    )

        return None

    @staticmethod
    def check_ticket_quota(tenant):
        """
        Check if tenant can create more tickets
        """
        from tickets.models import Ticket
        from django.utils import timezone

        # Get current month's ticket count
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        current_count = Ticket.objects.filter(
            created_at__gte=start_of_month
        ).count()

        max_tickets = tenant.max_tickets_per_month or float('inf')

        return current_count < max_tickets

    @staticmethod
    def check_user_quota(tenant):
        """
        Check if tenant can add more users
        """
        from .models import TenantUser

        current_count = TenantUser.objects.filter(
            tenant=tenant,
            is_active=True
        ).count()

        max_users = tenant.max_users or float('inf')

        return current_count < max_users


class TenantSecurityMiddleware(MiddlewareMixin):
    """
    Additional security measures for multi-tenant system
    """

    @staticmethod
    def process_request(request):
        """
        Apply security checks
        """
        # Add security headers
        return None

    @staticmethod
    def process_response(request, response):
        """
        Add security headers to response
        """
        if hasattr(request, 'tenant'):
            # Add tenant identifier header (for debugging)
            response['X-Tenant-Schema'] = request.tenant.schema_name

        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'

        return response
