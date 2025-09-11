from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Extended User model for Wallai"""
    email = models.EmailField(unique=True)
    preferred_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('es', 'Español')],
        default='en'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'