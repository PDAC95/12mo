from django.urls import path
from . import views

app_name = 'spaces'

urlpatterns = [
    # Test URL (temporary)
    path('test/', views.space_test, name='test'),

    # Main space management
    path('', views.space_list, name='list'),
    path('create/', views.space_create, name='create'),
    path('join/', views.space_join, name='join'),

    # Individual space management
    path('<int:pk>/', views.space_detail, name='detail'),
    path('<int:pk>/update/', views.space_update, name='update'),
    path('<int:pk>/leave/', views.leave_space, name='leave'),
    path('<int:pk>/regenerate-code/', views.regenerate_invite_code, name='regenerate_code'),

    # API endpoints
    path('<int:pk>/members/api/', views.space_members_api, name='members_api'),
]