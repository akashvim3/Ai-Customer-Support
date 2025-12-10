from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Frontend Pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('features/', TemplateView.as_view(template_name='features.html'), name='features'),
    path('pricing/', TemplateView.as_view(template_name='pricing.html'), name='pricing'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),

    # Authentication
    path('auth/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),

    # Dashboard
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),

    # API Routes
    path('api/tenants/', include('tenants.urls')),
    path('api/chatbot/', include('chatbot.urls')),
    path('api/tickets/', include('tickets.urls')),
    path('api/analytics/', include('analytics.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # JWT Authentication
    path('api/auth/', include('rest_framework_simplejson.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns

# Custom error handlers
handler404 = 'config.views.handler404'
handler500 = 'config.views.handler500'
