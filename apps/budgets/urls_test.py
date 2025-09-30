from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .views.delete_views import BudgetDeleteView, budget_delete_api, budget_deletion_summary

app_name = 'budgets'

@login_required
def budget_home(request):
    """Budget home page - temporary simple implementation"""
    return render(request, 'budgets/temp_home.html', {
        'page_title': 'Budget Management',
        'current_section': 'budgets'
    })

urlpatterns = [
    # Budget home page
    path('', budget_home, name='home'),

    # Budget deletion endpoints only
    path('api/budgets/<int:budget_id>/', BudgetDeleteView.as_view(), name='delete_budget_api'),
    path('api/budgets/<int:budget_id>/delete/', budget_delete_api, name='delete_api'),
    path('api/budgets/<int:budget_id>/deletion-summary/', budget_deletion_summary, name='deletion_summary'),
]