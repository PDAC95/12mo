from django.shortcuts import render, redirect
from django.views.generic import TemplateView

class LandingView(TemplateView):
    """Public landing page"""
    template_name = 'public/landing.html'
    
    def get(self, request, *args, **kwargs):
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Shared Financial Management',
            'hero_title': 'Shared finances made simple',
            'hero_subtitle': 'Wallai helps you share expenses, create budgets and maintain financial control with your family and friends.',
            'cta_login': 'Sign In',
            'cta_register': 'Get Started Free',
            'features': [
                {
                    'title': 'Shared Spaces',
                    'description': 'Create spaces for different groups: family, roommates, couple.',
                    'icon': 'users'
                },
                {
                    'title': 'Split Expenses', 
                    'description': 'Divide expenses automatically and keep clear balances.',
                    'icon': 'calculator'
                },
                {
                    'title': 'Smart Budgets',
                    'description': 'Plan monthly expenses and receive limit alerts.',
                    'icon': 'chart-bar'
                }
            ]
        })
        return context
