# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MonAI is a Django-based Progressive Web App (PWA) for managing shared personal finances with multi-user spaces, budgets, and expense tracking. It uses a modular Django architecture with separate settings for development and production environments.

## Commands

### Development Setup
```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Code Quality
```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Run tests with pytest
pytest

# Run tests with coverage
pytest --cov
```

### Django Commands
```bash
# Create new app
python manage.py startapp <app_name> apps/<app_name>

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Django shell with extensions
python manage.py shell_plus
```

## Architecture

### Project Structure
- **config/**: Django configuration module
  - `settings/`: Environment-specific settings (base, development, production)
  - `urls.py`: Main URL configuration
  - Uses `DJANGO_SETTINGS_MODULE='config.settings.development'` by default
  
- **apps/**: Application modules directory
  - `authentication/`: Custom user model extending AbstractUser with email as primary identifier
  - Each app follows Django's standard structure (models, views, admin, tests)

### Key Technical Details
- **Custom User Model**: `apps.authentication.User` uses email as USERNAME_FIELD
- **Authentication**: JWT tokens via djangorestframework-simplejwt
- **API**: Django REST Framework with JWT authentication by default
- **Database**: SQLite for development, PostgreSQL for production
- **CORS**: Configured for localhost:3000 and localhost:8000
- **Environment Variables**: Production uses python-decouple for configuration

### Settings Configuration
- Base settings in `config/settings/base.py` contain shared configuration
- Development settings override with `DEBUG=True` and SQLite
- Production settings use environment variables via python-decouple
- manage.py defaults to development settings

### Testing
- pytest is configured as the test runner
- pytest-django for Django integration
- pytest-cov for coverage reports
- Test files should follow pytest conventions (test_*.py or *_test.py)