from django.urls import path
from . import views

app_name = 'spaces'

urlpatterns = [
    # Test URL (temporary)
    path('test/', views.space_test, name='test'),

    # Main space management
    path('', views.space_list, name='list'),
    path('archived/', views.archived_spaces, name='archived'),
    path('create/', views.space_create, name='create'),
    path('join/', views.space_join, name='join'),

    # Individual space management
    path('<int:pk>/', views.space_detail, name='detail'),
    path('<int:pk>/update/', views.space_update, name='update'),
    path('<int:pk>/leave/', views.leave_space, name='leave'),
    path('<int:pk>/archive/', views.archive_space, name='archive'),
    path('<int:pk>/delete/', views.delete_space, name='delete'),
    path('<int:pk>/regenerate-code/', views.regenerate_invite_code, name='regenerate_code'),
    path('<int:pk>/remove-member/<int:member_id>/', views.remove_member, name='remove_member'),
    path('<int:pk>/transfer-ownership/<int:member_id>/', views.transfer_ownership, name='transfer_ownership'),
    path('<int:pk>/restore/', views.restore_space, name='restore'),

    # Space context management
    path('<int:pk>/switch/', views.switch_space, name='switch'),
    path('<int:pk>/set-default/', views.set_default_space, name='set_default'),

    # Space settings and configuration
    path('<int:pk>/settings/', views.space_settings, name='settings'),
    path('<int:pk>/history/', views.change_history, name='history'),

    # Approval system
    path('pending/', views.pending_approvals, name='pending_approvals'),
    path('approve/<int:request_id>/', views.approve_change, name='approve_change'),
    path('reject/<int:request_id>/', views.reject_change, name='reject_change'),

    # API endpoints
    path('<int:pk>/members/api/', views.space_members_api, name='members_api'),
]