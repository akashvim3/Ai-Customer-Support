from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('tickets/', views.tickets_view, name='tickets'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('settings/', views.settings_view, name='settings'),
    path('conversations/', views.conversations_view, name='conversations'),
    path('knowledge-base/', views.knowledge_base_view, name='knowledge_base'),
    path('team/', views.team_view, name='team'),
]
