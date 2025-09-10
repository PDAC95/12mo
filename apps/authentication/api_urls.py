from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# API URLs for mobile/API usage
urlpatterns = [
    path('register/', views.api_register, name='register'),
    path('login/', views.api_login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]