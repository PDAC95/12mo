from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database for development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Enhanced Hot Reload Configuration
USE_TZ = True

# Auto-reload settings for better development experience
RUNSERVER_PLUS_PRINT_SQL = True if DEBUG else False

# File watching improvements
import sys
if 'runserver' in sys.argv or 'runserver_enhanced' in sys.argv:
    # Improve file watching for hot reload
    import os

    # Watch additional file types
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]

    # Enable template debugging
    TEMPLATES[0]['OPTIONS']['debug'] = True

# Development-specific logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'colored': {
            'format': '🔧 {asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'budget_deletion': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Development tools
if DEBUG:
    # Enable SQL debugging in console (optional)
    # Uncomment next lines to see SQL queries in console
    # LOGGING['loggers']['django.db.backends'] = {
    #     'handlers': ['console'],
    #     'level': 'DEBUG',
    #     'propagate': False,
    # }

    # Enable template context debugging
    INTERNAL_IPS = ['127.0.0.1', 'localhost']