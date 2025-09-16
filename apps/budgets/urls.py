from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    # Main budget views
    path('', views.budget_home, name='home'),
    path('month/<str:month_period>/', views.budget_month_view, name='month_view'),
    path('analytics/', views.budget_analytics, name='analytics'),

    # Budget creation and management
    path('create-monthly/', views.create_monthly_budget, name='create_monthly'),
    path('create/', views.budget_create, name='create'),
    path('edit/<int:budget_id>/', views.budget_edit, name='edit'),
    path('delete/<int:budget_id>/', views.budget_delete, name='delete'),
    path('bulk-edit/<str:month_period>/', views.budget_bulk_edit, name='bulk_edit'),
    path('copy/', views.budget_copy, name='copy'),

    # AJAX endpoints
    path('api/quick-update/<int:budget_id>/', views.budget_quick_update, name='quick_update'),

    # Budget categories
    path('categories/', views.category_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
]