from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all requests for monitoring"""

    def process_request(self, request):
        logger.info(
            f"{request.method} {request.path} "
            f"from {request.META.get('REMOTE_ADDR')}"
        )
        return None


class APIVersionMiddleware(MiddlewareMixin):
    """Add API version to response headers"""

    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            response['X-API-Version'] = '1.0.0'
        return response


class TenantContextMiddleware(MiddlewareMixin):
    """Add tenant context to requests"""

    def process_request(self, request):
        if hasattr(request.user, 'tenantuser'):
            request.tenant = request.user.tenantuser.tenant
        else:
            request.tenant = None
        return None
