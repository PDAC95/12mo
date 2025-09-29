from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from datetime import datetime, date, timedelta
import random

# Import spaces models and utils
from spaces.models import Space, SpaceMember
from spaces.utils import SpaceContextManager, get_space_context

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view for authenticated users"""
    template_name = 'dashboard/home.html'
    login_url = '/login/'
    
    def get_greeting(self):
        """Return appropriate greeting based on current time"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "Good morning"
        elif 12 <= current_hour < 18:
            return "Good afternoon"
        else:
            return "Good evening"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current space context
        current_space = SpaceContextManager.get_current_space(self.request)
        space_context = get_space_context(self.request)

        # Greeting based on time of day
        greeting = self.get_greeting()

        # Determine dashboard title based on current space
        if current_space:
            dashboard_title = f"{current_space.name} Dashboard"
            space_description = f"Financial overview for {current_space.name}"
        else:
            dashboard_title = "Personal Dashboard"
            space_description = "Your personal financial overview"

        # Savings Goal Data (TODO: Connect to real space-specific savings data)
        # For now, show different demo data based on current space
        if current_space and current_space.name != 'Personal':
            current_savings = 2000
            target_savings = 5000
        else:
            current_savings = 5000
            target_savings = 10000

        savings_goal = {
            'current': current_savings,
            'target': target_savings,
            'percentage': int((current_savings / target_savings) * 100),
            'remaining': target_savings - current_savings
        }
        
        # Balance Data (TODO: Connect to real space-specific balance data)
        # Show different demo data based on current space
        if current_space and current_space.name != 'Personal':
            balance = {
                'total': 1200.50,
                'spent': 850.00,
                'budget': 1500.00,
                'spent_percentage': 57,
                'remaining': 650.00,
                'trend': 'better',
                'month_change': 8.3,
                'month': 'September 2025'
            }
        else:
            balance = {
                'total': 2450.78,
                'spent': 1549.00,
                'budget': 3000.00,
                'spent_percentage': 52,
                'remaining': 1451.00,
                'trend': 'better',
                'month_change': 12.5,
                'month': 'September 2025'
            }
        
        # Daily Limits Categories
        daily_limits = [
            {
                'name': "Today's Spending",
                'spent': 45.60,
                'limit': 75.00,
                'percentage': 61,
                'color': 'red',
                'icon': 'wallet'
            },
            {
                'name': 'Weekly Average',
                'spent': 312.50,
                'limit': 400.00,
                'percentage': 78,
                'color': 'blue',
                'icon': 'calendar',
                'trend': -5  # -5% vs last week
            },
            {
                'name': 'Monthly Target',
                'spent': 1549.00,
                'limit': 3000.00,
                'percentage': 52,
                'color': 'green',
                'icon': 'target'
            }
        ]
        
        # Recent Expenses (TODO: Connect to real space-specific expense data)
        # Show different demo data based on current space
        if current_space and current_space.name != 'Personal':
            recent_expenses = [
                {
                    'id': 1,
                    'description': f'{current_space.name} - Shared Expense',
                    'detail': 'Monthly utilities split',
                    'amount': -125.00,
                    'date': 'Today, 1:15 PM',
                    'category': 'Bills & Utilities',
                    'category_color': 'blue',
                    'user': self.request.user.username,
                    'icon': 'lightning'
                },
                {
                    'id': 2,
                    'description': 'Grocery Shopping',
                    'detail': 'Weekly groceries',
                    'amount': -68.30,
                    'date': 'Yesterday, 6:20 PM',
                    'category': 'Food & Dining',
                    'category_color': 'red',
                    'user': self.request.user.username,
                    'icon': 'shopping-cart'
                },
                {
                    'id': 3,
                    'description': 'Shared Transport',
                    'detail': 'Taxi to event',
                    'amount': -25.00,
                    'date': 'Sep 12, 7:45 PM',
                    'category': 'Transportation',
                    'category_color': 'yellow',
                    'user': self.request.user.username,
                    'icon': 'car'
                }
            ]
        else:
            recent_expenses = [
                {
                    'id': 1,
                    'description': 'Whole Foods Market',
                    'detail': 'Groceries for the week',
                    'amount': -87.45,
                    'date': 'Today, 2:30 PM',
                    'category': 'Food & Dining',
                    'category_color': 'red',
                    'user': self.request.user.username,
                    'icon': 'shopping-cart'
                },
                {
                    'id': 2,
                    'description': 'Electric Bill',
                    'detail': 'September utilities',
                    'amount': -125.30,
                    'date': 'Yesterday, 9:15 AM',
                    'category': 'Bills & Utilities',
                    'category_color': 'blue',
                    'user': self.request.user.username,
                    'icon': 'lightning'
                },
                {
                    'id': 3,
                    'description': 'Netflix Subscription',
                    'detail': 'Monthly entertainment',
                    'amount': -15.99,
                    'date': 'Sep 10, 11:22 AM',
                    'category': 'Entertainment',
                    'category_color': 'purple',
                    'user': self.request.user.username,
                    'icon': 'film'
                },
                {
                    'id': 4,
                    'description': 'Freelance Project',
                    'detail': 'Web development work',
                    'amount': 750.00,
                    'date': 'Sep 9, 4:45 PM',
                    'category': 'Income',
                    'category_color': 'green',
                    'user': self.request.user.username,
                    'icon': 'currency'
                },
                {
                    'id': 5,
                    'description': 'Uber Ride',
                    'detail': 'Downtown to office',
                    'amount': -18.50,
                    'date': 'Sep 8, 8:30 AM',
                    'category': 'Transportation',
                    'category_color': 'yellow',
                    'user': self.request.user.username,
                    'icon': 'car'
                }
            ]
        
        # Weekly Challenge Data
        weekly_challenge = {
            'title': 'Weekly Challenge',
            'description': 'Save $50 on dining out',
            'progress': 32,
            'target': 50,
            'percentage': 64,
            'remaining': 18,
            'status': 'active',
            'icon': 'trophy',
            'color': 'purple'
        }
        
        # Quick Stats
        quick_stats = {
            'active_spaces': 1,
            'this_week_spent': 228.74,
            'total_transactions': 47,
            'active_categories': 8
        }
        
        # Upcoming Bills
        upcoming_bills = [
            {
                'name': 'Rent Payment',
                'amount': 1200.00,
                'due_date': 'Due tomorrow',
                'status': 'urgent',
                'color': 'yellow',
                'icon': 'warning'
            },
            {
                'name': 'Internet',
                'amount': 89.99,
                'due_date': 'Due Sep 18',
                'status': 'pending',
                'color': 'gray',
                'icon': 'clock'
            },
            {
                'name': 'Phone Plan',
                'amount': 45.00,
                'due_date': 'Due Sep 25',
                'status': 'scheduled',
                'color': 'gray',
                'icon': 'check'
            }
        ]
        
        # Get user's spaces for navigation menu (max 5 for dropdown)
        user_spaces = Space.objects.filter(
            spacemember__user=self.request.user,
            spacemember__is_active=True,
            is_active=True
        ).select_related('created_by').prefetch_related('spacemember_set__user')[:5]

        # Format spaces data for template
        spaces_data = []
        for space in user_spaces:
            try:
                member = space.spacemember_set.get(user=self.request.user, is_active=True)
                spaces_data.append({
                    'space': space,
                    'role': member.role,
                    'member_count': space.member_count,
                    'is_owner': member.role == 'owner',
                    'is_default': member.is_default,
                })
            except SpaceMember.DoesNotExist:
                continue

        # Calculate total spaces count
        total_spaces_count = Space.objects.filter(
            spacemember__user=self.request.user,
            spacemember__is_active=True,
            is_active=True
        ).count()

        context.update({
            'title': dashboard_title,
            'greeting': greeting,
            'space_description': space_description,
            'savings_goal': savings_goal,
            'balance': balance,
            'daily_limits': daily_limits,
            'recent_expenses': recent_expenses,
            'weekly_challenge': weekly_challenge,
            'quick_stats': quick_stats,
            'upcoming_bills': upcoming_bills,
            'current_space': current_space,
            'user_spaces': spaces_data,  # Real spaces for dropdown
            'total_spaces_count': total_spaces_count,
            'show_all_spaces_link': total_spaces_count > 5,  # Show "View All" if more than 5
        })

        return context

@login_required
def dashboard(request):
    """Legacy dashboard view - kept for compatibility"""
    context = {
        'page_title': 'Dashboard',
        'balance_title': 'Balance',
        'expenses_title': 'Expenses',
        'budget_title': 'Monthly Budget',
    }
    return render(request, 'dashboard/index.html', context)

def set_language(request):
    """Language switching endpoint"""
    from django.conf import settings
    from django.http import HttpResponseRedirect
    from django.utils import translation
    
    language = request.GET.get('language')
    if language and language in dict(settings.LANGUAGES):
        translation.activate(language)
        response = HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
        return response
    
    return JsonResponse({'error': 'Invalid language'}, status=400)
