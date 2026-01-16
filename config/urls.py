from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from config.views import CustomLoginView

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
    path('accounts/', include('allauth.urls')),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),
    path('auth/login/', CustomLoginView.as_view(), name='login'),
    path('auth/logout/', TemplateView.as_view(template_name='auth/logout.html'), name='logout'),
    path('auth/password_change/', TemplateView.as_view(template_name='auth/password_change.html'), name='password_change'),
    path('auth/password_change/done/', TemplateView.as_view(template_name='auth/password_change_done.html'), name='password_change_done'),
    path('auth/password_reset/', TemplateView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('auth/password_reset/done/', TemplateView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/', TemplateView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('auth/reset/done/', TemplateView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

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
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')

    # Debug toolbar
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns

# Custom error handlers
handler404 = 'config.views.handler404'
handler500 = 'config.views.handler500'
