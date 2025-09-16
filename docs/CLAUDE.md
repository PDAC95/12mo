# CLAUDE.md - Wallai Framework Rules

## MANDATORY RULES FOR CLAUDE CODE

### 🚀 START OF EACH SESSION

1. **ALWAYS read files in this exact order:**

   ```
   1. CLAUDE.md (this file - project rules)
   2. docs/planning-monai.md (technical architecture)
   3. docs/prd-monai.md (product requirements)
   4. TASKS.md (find next P0 task)
   5. ERRORS.md (check active blockers)
   6. PROGRESS.md (review last session)
   ```

2. **Announce work plan:**

   ```
   "Files loaded. Working on: [Task #X - Description]
   Priority: P0
   Sprint: [Current Sprint]
   Estimated time: [X hours]"
   ```

3. **Environment verification checklist:**
   - [ ] Virtual environment activated (venv)
   - [ ] All pip packages installed
   - [ ] Environment variables configured (.env)
   - [ ] Django server running (port: 8000)
   - [ ] Database migrations applied
   - [ ] No conflicting processes on ports

### 💻 DURING DEVELOPMENT

#### Code Standards Enforcement

**Technology Stack Compliance:**

- Django 5.0.1 with Django Templates
- PostgreSQL for production, SQLite for development
- JWT authentication (djangorestframework-simplejwt)
- PWA with Service Workers
- Tailwind CSS via CDN
- Alpine.js for reactivity

**File Naming Conventions:**

```
Django Apps:
- Models: models.py (class SpaceMember)
- Views: views.py (def expense_list)
- Forms: forms.py (class ExpenseForm)
- Services: services.py (class BudgetService)
- Serializers: serializers.py (class UserSerializer)

Templates:
- templates/public/landing.html (public pages)
- templates/authenticated/base_authenticated.html (auth required)
- templates/dashboard/home.html (specific features)
- templates/components/component_name.html (reusable)

Static Files:
- static/js/module-name.js
- static/css/component-name.css
- static/pwa/manifest.json
```

**API Response Consistency:**

```python
# All API responses must follow this format
{
    "success": True,
    "data": {},
    "message": "Operation successful"
}

# Error responses
{
    "success": False,
    "error": {
        "message": "Error description",
        "code": "ERROR_CODE",
        "field_errors": {}
    }
}
```

#### Before Writing Any Code

1. **Announce specific changes:**

   ```
   "Modifying: apps/spaces/models.py
   Class/Function: SpaceMember model
   Purpose: Add invitation status field
   Dependencies: No new imports"
   ```

2. **Check ERRORS.md for related issues:**

   - Search for file name
   - Check for similar error patterns
   - Apply documented solutions
   - Avoid repeating fixed errors

3. **Verify against planning-monai.md:**
   - Follows folder structure?
   - Uses correct naming?
   - Implements security standards?
   - Matches API patterns?

#### After Each Code Change

1. **Test immediately:**

   ```bash
   python manage.py check
   python manage.py test apps.app_name
   python manage.py runserver
   ```

2. **Update documentation:**
   - Docstrings for new functions
   - Update API documentation if changed
   - Note breaking changes

#### Task Completion Protocol

1. **Update TASKS.md immediately:**

   ```markdown
   - [x] [2025-09-08 14:30] [P0] Implement space invitation system
   ```

2. **Add to PROGRESS.md:**

   ```markdown
   ## 2025-09-08

   ✅ Completed: Space invitation system

   - Details: 6-character code generation, join endpoint
   - Files modified: apps/spaces/models.py, views.py, urls.py
   - Testing: Created and joined test space
     ⚠️ Issues: None
   ```

3. **Document any errors in ERRORS.md:**
   ```markdown
   - [ ] [2025-09-08 14:30] ImportError in spaces app
     - File: apps/spaces/views.py:15
     - Error: No module named 'spaces'
     - Context: Missing **init**.py in apps folder
     - Solution: Added **init**.py file
     - Status: Resolved
   ```

### 📝 TASK PRIORITY SYSTEM

**P0 - CRITICAL (Do immediately):**

- Authentication broken
- Database connection issues
- Security vulnerabilities
- Production bugs
- Data loss risks

**P1 - IMPORTANT (Do after all P0):**

- Core features (spaces, budgets, expenses)
- User-facing functionality
- Performance issues
- PWA functionality
- i18n implementation

**P2 - NICE TO HAVE (Only if no P0/P1):**

- UI enhancements
- Code refactoring
- Documentation updates
- Test coverage improvements
- Minor optimizations

### 🚫 FORBIDDEN ACTIONS

**NEVER do these:**

1. Skip reading documentation files
2. Use apps.\* imports (use direct imports)
3. Commit .env file or secrets
4. Delete migrations without backup
5. Use print() instead of logging
6. Skip input validation
7. Ignore Django security middleware
8. Make DB changes without migrations
9. Use inline styles instead of CSS files
10. Forget to update TASKS.md

**ALWAYS do these:**

1. Use Django's ORM for database queries
2. Validate with Django Forms/Serializers
3. Use Django's built-in authentication
4. Follow REST conventions for APIs
5. Test with different user roles
6. Use Django messages for user feedback
7. Implement proper error pages (404, 500)
8. Use Django's CSRF protection
9. Update requirements.txt for new packages
10. Run migrations after model changes

### 📄 SESSION MANAGEMENT

#### Starting a Session

```markdown
## Session Start: 2025-09-08 14:00

- Previous session: Completed authentication system
- Current task: Implement spaces CRUD
- Blockers: None
- Environment ready: Yes
```

#### During the Session

- Commit code every 30 minutes:
  ```bash
  git add .
  git commit -m "feat(spaces): add member invitation"
  git push origin main
  ```
- Update TASKS.md after each completion
- Document errors immediately
- Run tests frequently

#### Ending a Session

1. **Create session summary in PROGRESS.md:**

   ```markdown
   ## Session Summary - 2025-09-08 18:00

   Duration: 4 hours

   Completed Tasks:

   - Space model with invitation codes
   - Member join functionality

   In Progress:

   - Budget category CRUD (60% complete)

   Blockers:

   - None

   Next Session Priority:

   1. Complete budget categories
   2. Start expense models
   3. Create dashboard views

   Notes:

   - Remember to add index on space_id
   - Consider caching for dashboard
   ```

2. **Cleanup:**
   ```bash
   python manage.py check
   git status
   git add .
   git commit -m "chore: end of session cleanup"
   ```

### 📱 NAVIGATION PATTERNS (From US-0 Implementation)

#### Template Hierarchy Pattern

```python
# Base template structure discovered in US-0
templates/
├── public/                  # No authentication required
│   ├── base_public.html    # PWA config, landing pages
│   ├── landing.html        # Hero + features
│   ├── login.html          # Login form
│   └── register.html       # Registration form
├── authenticated/          # Authentication required  
│   └── base_authenticated.html # Sidebar + bottom nav
└── dashboard/
    └── home.html          # Main dashboard
```

#### Responsive Navigation Pattern

```html
<!-- Mobile-first responsive navigation -->
<div x-data="{ sidebarOpen: false }">
  <!-- Mobile header -->
  <header class="md:hidden">
    <button @click="sidebarOpen = true">☰</button>
  </header>
  
  <!-- Desktop sidebar -->
  <nav class="hidden md:block fixed w-64">
    <!-- Navigation links with active states -->
  </nav>
  
  <!-- Mobile bottom navigation -->
  <nav class="md:hidden fixed bottom-0 w-full">
    <!-- Bottom nav items -->
  </nav>
</div>
```

#### Authentication Layout Pattern

```python
# Separate public and authenticated base templates
class LoginView(FormView):
    template_name = 'public/login.html'  # Uses base_public.html
    
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'  # Uses base_authenticated.html
```

#### Form Integration Pattern

```python
# Consistent form styling with Tailwind
class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full px-3 py-2 border border-gray-300',
            'placeholder': 'correo@ejemplo.com'
        })
    )
```

### 🔧 DJANGO-SPECIFIC PATTERNS

#### Model Pattern

```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Space(models.Model):
    """Shared financial space between users"""
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=6, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'spaces'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
```

#### View Pattern (Function-Based)

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

@login_required
@transaction.atomic
def create_space(request):
    """Create a new financial space"""
    if request.method == 'POST':
        form = SpaceForm(request.POST)
        if form.is_valid():
            space = form.save(commit=False)
            space.created_by = request.user
            space.save()
            messages.success(request, 'Space created successfully')
            return redirect('spaces:detail', pk=space.pk)
    else:
        form = SpaceForm()

    return render(request, 'spaces/create.html', {'form': form})
```

#### API View Pattern (DRF)

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_space(request):
    """Join a space using invitation code"""
    code = request.data.get('invite_code')

    if not code:
        return Response({
            'success': False,
            'error': {'message': 'Invitation code required'}
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        space = Space.objects.get(invite_code=code, is_active=True)
        SpaceMember.objects.get_or_create(
            space=space,
            user=request.user
        )
        return Response({
            'success': True,
            'data': SpaceSerializer(space).data,
            'message': 'Successfully joined space'
        })
    except Space.DoesNotExist:
        return Response({
            'success': False,
            'error': {'message': 'Invalid invitation code'}
        }, status=status.HTTP_404_NOT_FOUND)
```

#### Service Pattern

```python
from decimal import Decimal
from django.db.models import Sum, Q
from datetime import datetime

class BudgetService:
    """Business logic for budget operations"""

    @staticmethod
    def calculate_monthly_balance(space, month_period):
        """Calculate balance for a specific month"""
        incomes = Income.objects.filter(
            space=space,
            month_period=month_period
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        expenses = Expense.objects.filter(
            space=space,
            month_period=month_period
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return {
            'income': incomes,
            'expenses': expenses,
            'balance': incomes - expenses,
            'percentage_used': (expenses / incomes * 100) if incomes > 0 else 0
        }

    @staticmethod
    def replicate_monthly_budget(space):
        """Auto-replicate budget for new month"""
        current_month = datetime.now().strftime('%Y-%m')
        # Implementation here
        pass
```

### 🎯 PROJECT-SPECIFIC FOCUS AREAS

1. **Core Feature Priority:**

   - Spaces: Multi-user collaboration
   - Budgets: Monthly planning and replication
   - Expenses: Real-time tracking and splitting
   - Dashboard: Clear financial visibility

2. **Technical Excellence:**

   - Mobile-first responsive design
   - PWA offline functionality
   - JWT token security
   - i18n Spanish/English support

3. **User Experience:**
   - Quick expense entry
   - Clear balance visibility
   - Intuitive navigation (bottom navbar)
   - Fast page loads (<2s)

### 📊 CURRENT SPRINT STATUS

**Sprint 0: Foundation** ✅ COMPLETED

- ✅ Project setup
- ✅ Authentication system  
- ✅ Base apps created
- ✅ PWA configuration (manifest + service worker)
- ✅ i18n setup (Spanish/English)
- ✅ Base templates (mobile-first)

**Current Sprint: Sprint 1 - Spaces & Members**

- Space model and CRUD operations
- Member invitation system (6-char codes)
- Space switching UI
- Member management features
- Bottom navigation component
- Tailwind CSS integration

### 🔍 COMMON DJANGO ISSUES TO AVOID

1. **Import Issues:**

   ```python
   # Wrong
   from apps.authentication.models import User

   # Correct
   from authentication.models import User
   # or
   from django.contrib.auth import get_user_model
   User = get_user_model()
   ```

2. **Settings Import:**

   ```python
   # Always use
   from django.conf import settings
   # Never import directly from config.settings.base
   ```

3. **Migration Issues:**

   ```bash
   # Always make migrations for specific app
   python manage.py makemigrations app_name

   # Check migrations before applying
   python manage.py showmigrations
   ```

4. **Static Files:**

   ```python
   # In templates
   {% load static %}
   <link href="{% static 'css/style.css' %}" rel="stylesheet">

   # In settings
   STATIC_URL = '/static/'
   STATICFILES_DIRS = [BASE_DIR / 'static']
   ```

### 🚀 QUICK COMMANDS REFERENCE

```bash
# Development
python manage.py runserver
python manage.py shell_plus
python manage.py dbshell

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Testing
python manage.py test
python manage.py test apps.spaces
pytest --cov=apps

# Static Files
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser

# Code Quality
black apps/
isort apps/
python manage.py check
```

---

## REMEMBER

**The framework exists to:**

1. Maintain Django best practices
2. Track progress accurately
3. Ensure PWA functionality
4. Facilitate multi-user collaboration
5. Deliver a production-ready MVP

**Never compromise on:**

1. Django security middleware
2. Input validation
3. Database migrations
4. JWT authentication
5. Task documentation

**Current Sprint:** Sprint 3 - Expense Tracking
**Sprint Goal:** Real-time expense tracking with budget integration
**Sprint Start Date:** September 17, 2025
**Sprint End Date:** September 24, 2025

**Sprint 0 Status:** ✅ COMPLETED (September 10, 2025)
**Sprint 1 Status:** ✅ COMPLETED (September 16, 2025) - Spaces & Members
**Sprint 2 Status:** ✅ COMPLETED (September 16, 2025) - Budget Management

---

_This document is the source of truth for Wallai development. Follow it strictly._
