from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatbotViewSet, ConversationViewSet, KnowledgeBaseViewSet

router = DefaultRouter()
router.register(r'chat', ChatbotViewSet, basename='chat')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'knowledge-base', KnowledgeBaseViewSet, basename='knowledge-base')

urlpatterns = [
    path('', include(router.urls)),
]
