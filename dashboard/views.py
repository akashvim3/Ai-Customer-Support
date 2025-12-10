from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from tickets.models import Ticket
from chatbot.models import Conversation
from tenants.models import TenantUser

@login_required
def dashboard_home(request):
    """Dashboard home view"""
    context = {
        'page_title': 'Dashboard',
        'active_page': 'dashboard'
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def tickets_view(request):
    """Tickets management view"""
    context = {
        'page_title': 'Tickets',
        'active_page': 'tickets'
    }
    return render(request, 'dashboard/tickets.html', context)

@login_required
def analytics_view(request):
    """Analytics dashboard view"""
    context = {
        'page_title': 'Analytics',
        'active_page': 'analytics'
    }
    return render(request, 'dashboard/analytics.html', context)

@login_required
def settings_view(request):
    """Settings view"""
    context = {
        'page_title': 'Settings',
        'active_page': 'settings'
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
def conversations_view(request):
    """Conversations view"""
    context = {
        'page_title': 'Conversations',
        'active_page': 'conversations'
    }
    return render(request, 'dashboard/conversations.html', context)

@login_required
def knowledge_base_view(request):
    """Knowledge base management view"""
    context = {
        'page_title': 'Knowledge Base',
        'active_page': 'knowledge_base'
    }
    return render(request, 'dashboard/knowledge_base.html', context)

@login_required
def team_view(request):
    """Team management view"""
    context = {
        'page_title': 'Team',
        'active_page': 'team'
    }
    return render(request, 'dashboard/team.html', context)
