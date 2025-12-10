from django.shortcuts import render
from django.http import JsonResponse


def handler404(request, exception=None):
    """Custom 404 error handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }, status=404)

    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Custom 500 error handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }, status=500)

    return render(request, 'errors/500.html', status=500)


def handler403(request, exception=None):
    """Custom 403 error handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }, status=403)

    return render(request, 'errors/403.html', status=403)


def handler400(request, exception=None):
    """Custom 400 error handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Bad Request',
            'message': 'The request could not be understood',
            'status_code': 400
        }, status=400)

    return render(request, 'errors/400.html', status=400)
