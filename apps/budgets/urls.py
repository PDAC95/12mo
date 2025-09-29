from django.urls import path
from . import views as budget_views, views_expenses
from .views_modules.delete_views import BudgetDeleteView, budget_delete_api, budget_deletion_summary

app_name = 'budgets'

urlpatterns = [
    # Main budget views
    path('', budget_views.budget_home, name='home'),
    path('month/<str:month_period>/', budget_views.budget_month_view, name='month_view'),
    path('analytics/', budget_views.budget_analytics, name='analytics'),

    # API endpoints
    path('api/category-suggestions/', budget_views.category_suggestions_api, name='category_suggestions_api'),
    path('api/delete/<int:budget_id>/', budget_views.budget_delete_api, name='budget_delete_api'),
    path('api/undo-delete/', budget_views.budget_undo_delete_api, name='budget_undo_delete_api'),

    # Budget deletion endpoints
    path('api/budgets/<int:budget_id>/', BudgetDeleteView.as_view(), name='delete_budget_api'),
    path('api/budgets/<int:budget_id>/delete/', budget_delete_api, name='delete_api'),
    path('api/budgets/<int:budget_id>/deletion-summary/', budget_deletion_summary, name='deletion_summary'),

    # Budget creation and management
    path('create-monthly/', budget_views.create_monthly_budget, name='create_monthly'),
    path('create/', budget_views.budget_create_method_selection, name='create'),
    path('create/scratch/', budget_views.budget_create_from_scratch, name='create_from_scratch'),
    path('create/template/<int:template_id>/', budget_views.budget_create_from_template, name='create_from_template'),
    path('smart-create/', budget_views.smart_create_budget, name='smart_create'),
    path('edit/<int:budget_id>/', budget_views.budget_edit, name='edit'),
    path('delete/<int:budget_id>/', budget_views.budget_delete, name='delete'),
    path('bulk-edit/<str:month_period>/', budget_views.budget_bulk_edit, name='bulk_edit'),
    path('copy/', budget_views.budget_copy, name='copy'),

    # AJAX endpoints
    path('api/quick-update/<int:budget_id>/', budget_views.budget_quick_update, name='quick_update'),
    path('api/template/<int:template_id>/', budget_views.template_data_api, name='template_data'),
    path('api/budget-edit/', budget_views.budget_edit_api, name='budget_edit_api'),

    # Budget categories
    path('categories/', budget_views.category_list, name='categories'),
    path('categories/create/', budget_views.category_create, name='category_create'),

    # Budget templates
    path('templates/', budget_views.template_gallery, name='template_gallery'),
    path('templates/list/', budget_views.template_list, name='template_list'),
    path('templates/create/', budget_views.template_create, name='template_create'),
    path('templates/<int:template_id>/', budget_views.template_detail, name='template_detail'),
    path('templates/<int:template_id>/edit/', budget_views.template_edit, name='template_edit'),
    path('templates/<int:template_id>/delete/', budget_views.template_delete, name='template_delete'),

    # Payment methods
    path('payment-methods/', budget_views.payment_methods_list, name='payment_methods'),
    path('payment-methods/create/', budget_views.payment_method_create, name='payment_method_create'),
    path('payment-methods/<int:method_id>/edit/', budget_views.payment_method_edit, name='payment_method_edit'),
    path('payment-methods/<int:method_id>/delete/', budget_views.payment_method_delete, name='payment_method_delete'),

    # Expenses
    path('add-expense/<int:budget_id>/', views_expenses.add_expense, name='add_expense'),
    path('api/expense-calculator/', views_expenses.expense_calculator, name='expense_calculator'),

    # Expense API endpoints
    path('api/expense/create/', views_expenses.create_expense_api, name='create_expense_api'),
    path('api/expenses/<int:budget_id>/', views_expenses.list_expenses_api, name='list_expenses_api'),
    path('api/expense/<int:expense_id>/delete/', views_expenses.delete_expense_api, name='delete_expense_api'),
]