from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.LandingView.as_view(), name='home'),
]