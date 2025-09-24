from django.urls import path
from . import views, views_expenses

app_name = 'budgets'

urlpatterns = [
    # Main budget views
    path('', views.budget_home, name='home'),
    path('month/<str:month_period>/', views.budget_month_view, name='month_view'),
    path('analytics/', views.budget_analytics, name='analytics'),

    # API endpoints
    path('api/category-suggestions/', views.category_suggestions_api, name='category_suggestions_api'),

    # Budget creation and management
    path('create-monthly/', views.create_monthly_budget, name='create_monthly'),
    path('create/', views.budget_create_method_selection, name='create'),
    path('create/scratch/', views.budget_create_from_scratch, name='create_from_scratch'),
    path('create/template/<int:template_id>/', views.budget_create_from_template, name='create_from_template'),
    path('smart-create/', views.smart_create_budget, name='smart_create'),
    path('edit/<int:budget_id>/', views.budget_edit, name='edit'),
    path('delete/<int:budget_id>/', views.budget_delete, name='delete'),
    path('bulk-edit/<str:month_period>/', views.budget_bulk_edit, name='bulk_edit'),
    path('copy/', views.budget_copy, name='copy'),

    # AJAX endpoints
    path('api/quick-update/<int:budget_id>/', views.budget_quick_update, name='quick_update'),
    path('api/template/<int:template_id>/', views.template_data_api, name='template_data'),

    # Budget categories
    path('categories/', views.category_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),

    # Budget templates
    path('templates/', views.template_gallery, name='template_gallery'),
    path('templates/list/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:template_id>/delete/', views.template_delete, name='template_delete'),

    # Payment methods
    path('payment-methods/', views.payment_methods_list, name='payment_methods'),
    path('payment-methods/create/', views.payment_method_create, name='payment_method_create'),
    path('payment-methods/<int:method_id>/edit/', views.payment_method_edit, name='payment_method_edit'),
    path('payment-methods/<int:method_id>/delete/', views.payment_method_delete, name='payment_method_delete'),

    # Expenses
    path('add-expense/<int:budget_id>/', views_expenses.add_expense, name='add_expense'),
    path('api/expense-calculator/', views_expenses.expense_calculator, name='expense_calculator'),
]