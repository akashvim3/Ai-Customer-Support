from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantUserViewSet, IntegrationSettingsViewSet, RegistrationViewSet

router = DefaultRouter()
router.register(r'', TenantViewSet, basename='tenant')
router.register(r'users', TenantUserViewSet, basename='tenant-user')
router.register(r'integrations', IntegrationSettingsViewSet, basename='integration')
router.register(r'register', RegistrationViewSet, basename='register')

urlpatterns = [
    path('', include(router.urls)),
]
