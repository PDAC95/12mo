# ERROR LOG - MonAI

## HOW TO DOCUMENT ERRORS

Each error entry must include:

1. **Date & Time** when error occurred
2. **File & Line** where error happened
3. **Error Message** complete and exact
4. **Context** what was being attempted
5. **Stack Trace** if applicable
6. **Solution Attempts** what was tried
7. **Resolution** final solution or current status

Format:

```markdown
- [ ] [YYYY-MM-DD HH:MM] Brief error description
  - **File:** path/to/file.py:lineNumber
  - **Error:** Complete error message
  - **Context:** What operation was being performed
  - **Stack:** Stack trace if relevant
  - **Attempted:**
    1. First solution attempt
    2. Second solution attempt
  - **Status:** [ACTIVE/RESOLVED/BLOCKED]
  - **Solution:** How it was fixed (if resolved)
```

---

## 🔴 CRITICAL ERRORS (Blockers)

Errors that completely prevent development or break the system

### Active Critical Errors:

- [ ] [2025-09-08 13:20] psycopg2-binary installation failure
  - **File:** requirements/base.txt
  - **Error:** "error: Microsoft Visual C++ 14.0 or greater is required"
  - **Context:** Installing PostgreSQL adapter for production
  - **Stack:**
    ```
    Building wheel for psycopg2-binary (pyproject.toml) ... error
    error: Microsoft Visual C++ 14.0 or greater is required
    ```
  - **Attempted:**
    1. Direct pip install psycopg2-binary
    2. Tried different version (2.9.9)
    3. Commented out temporarily
  - **Status:** BLOCKED (works without it using SQLite)
  - **Solution:** Install Visual C++ Build Tools or use psycopg2 wheels

---

## 🟡 ACTIVE ERRORS (Non-Critical)

Errors that don't block development but need fixing

### Active Non-Critical Errors:

- [ ] [2025-09-08 14:00] Import path confusion with apps folder
  - **File:** config/settings/base.py
  - **Error:** "ModuleNotFoundError: No module named 'authentication'"
  - **Context:** Django couldn't find apps when using 'apps.authentication'
  - **Stack:** During INSTALLED_APPS loading
  - **Attempted:**
    1. Used 'apps.authentication' in INSTALLED_APPS
    2. Added sys.path.insert for apps folder
    3. Changed to direct imports without 'apps.'
  - **Status:** ACTIVE (workaround in place)
  - **Solution:** Using direct imports works, but apps prefix would be cleaner

---

## 🟢 RESOLVED ERRORS (Reference)

Keep for future reference when similar issues occur

### Recently Resolved:

- [x] [2025-09-08 13:45] BASE_DIR pointing to wrong directory

  - **File:** config/settings/base.py:16
  - **Error:** Settings not found, wrong path resolution
  - **Context:** Settings split into multiple files
  - **Solution:** Changed from `parent.parent` to `parent.parent.parent`

- [x] [2025-09-08 13:15] **init**.py file naming issue
  - **File:** apps/**init**.py
  - **Error:** File created as **init**.py instead of **init**.py
  - **Context:** PowerShell interpreted double underscores incorrectly
  - **Solution:** Created file manually in file explorer

---

## ⚠️ PROBLEMATIC PATTERNS

Recurring issues and their solutions

### Pattern: Django App Import Issues

**Problem:** Apps in subdirectory not importing correctly
**Solution:** Add apps folder to Python path

```python
# In settings/base.py
import sys
import os
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Then use direct imports
INSTALLED_APPS = [
    'authentication',  # not 'apps.authentication'
]
```

### Pattern: Missing Environment Variables

**Problem:** Django crashes when .env variables are missing
**Solution:** Use python-decouple with defaults

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
DEBUG = config('DEBUG', default=True, cast=bool)
```

### Pattern: CORS Issues with PWA

**Problem:** PWA can't communicate with Django API
**Solution:** Proper CORS configuration

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
```

### Pattern: JWT Token Refresh Issues

**Problem:** Refresh tokens not rotating properly
**Solution:** Configure SIMPLE_JWT correctly

```python
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## 📚 LESSONS LEARNED

### Django Configuration Issues

- Always verify BASE_DIR when using nested settings folders
- Use python-decouple for environment variables
- Keep development and production settings separate
- Test imports after moving apps to subdirectories

### Authentication Issues

- Custom User model must be defined before first migration
- EMAIL field needs unique=True for email login
- JWT refresh tokens need explicit rotation config
- Always test with multiple user sessions

### PWA Issues

- Service Worker needs HTTPS in production
- manifest.json must be in static/pwa/
- Cache versioning is critical for updates
- Test offline functionality thoroughly

### Database Issues

- SQLite sufficient for development
- PostgreSQL setup can wait until deployment
- Always use Django ORM, avoid raw SQL
- Index foreign keys for performance

---

## 🔧 COMMON SOLUTION SNIPPETS

### Django: Robust Database Connection

```python
# settings/production.py
import dj_database_url
from decouple import config

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

### Django: Custom User Model Setup

```python
# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

# settings/base.py
AUTH_USER_MODEL = 'authentication.User'
```

### Django: JWT Authentication View

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    try:
        user = authenticate(
            username=request.data.get('email'),
            password=request.data.get('password')
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        return Response({
            'success': False,
            'error': {'message': 'Invalid credentials'}
        }, status=401)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return Response({
            'success': False,
            'error': {'message': 'Login failed'}
        }, status=500)
```

### PWA: Service Worker Registration

```javascript
// static/js/main.js
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/pwa/sw.js")
      .then((reg) => console.log("SW registered"))
      .catch((err) => console.error("SW registration failed", err));
  });
}
```

### Django: File Upload Validation

```python
from django import forms
from django.core.exceptions import ValidationError

def validate_file_size(file):
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise ValidationError(f'File too large. Max size: 5MB')

class ExpenseForm(forms.ModelForm):
    receipt = forms.FileField(
        validators=[validate_file_size],
        required=False
    )

    def clean_receipt(self):
        file = self.cleaned_data.get('receipt')
        if file:
            if not file.content_type.startswith('image/'):
                raise ValidationError('Only image files allowed')
        return file
```

---

## 🚨 DJANGO-SPECIFIC ERRORS

### Migration Errors

- Always run makemigrations with app name: `python manage.py makemigrations app_name`
- Check for conflicts with: `python manage.py showmigrations`
- Reset migrations carefully: Never delete migrations in production

### Template Errors

- Use {% load static %} at top of templates
- Check TEMPLATES DIRS setting
- Verify template names match exactly (case-sensitive)

### Static Files Errors

- Run collectstatic for production
- Check STATIC_URL and STATIC_ROOT
- Verify STATICFILES_DIRS includes your static folder

### Form Errors

- Always use {% csrf_token %} in forms
- Check form.errors in templates
- Validate in forms.py, not views

---

## 📊 ERROR LOG HISTORY

### Week of 2025-09-08

- Total errors encountered: 5
- Critical errors: 1
- Resolved: 3
- Still active: 2

### Error Categories:

- Configuration: 2
- Import/Path: 2
- Dependencies: 1

---

## 🔍 DEBUGGING CHECKLIST

When encountering a new error:

1. **Immediate Actions:**

   - [ ] Copy exact error message
   - [ ] Note file and line number
   - [ ] Run `python manage.py check`
   - [ ] Verify virtual environment is activated
   - [ ] Check if migrations are needed

2. **Investigation:**

   - [ ] Search this file for similar errors
   - [ ] Check recent code changes with `git status`
   - [ ] Verify all apps are in INSTALLED_APPS
   - [ ] Check Django debug toolbar
   - [ ] Review Django logs

3. **Documentation:**
   - [ ] Add error to appropriate section
   - [ ] Document all solution attempts
   - [ ] Update status regularly
   - [ ] Add solution when found
   - [ ] Create snippet if reusable

---

**Last Updated:** 2025-09-08 16:30
**Total Documented Errors:** 5
**Resolution Rate:** 60%
**Most Common Issue:** Import paths and configuration
