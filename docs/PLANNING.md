# PLANNING.md - Wallai Technical Architecture

## Project Vision

Wallai is a Progressive Web Application for collaborative personal finance management, enabling multiple users to share and manage budgets within defined spaces. Currently in Sprint 0, the project focuses on replacing manual Excel-based expense tracking with an automated, mobile-first solution that provides real-time visibility of shared finances.

**MVP Scope:** User authentication, space management, budget planning, expense tracking, and basic dashboard with PWA capabilities
**Current Status:** Sprint 0 - Foundation setup (Authentication + Base Apps completed)
**Target Launch:** October 2025 (6 weeks)

## Technical Architecture

### System Architecture Diagram

```
┌───────────────────────────────────────────────────────────┐
│                    CloudFlare CDN                          │
└───────────────┬───────────────────────────────────────────┘
                │
    ┌───────────▼──────────┐
    │    Django Server     │
    │  (Templates + API)   │
    │    Railway/Render    │
    └───────────┬──────────┘
                │
    ┌───────────▼───────────────────────────┬──────────────┐
    │         Django Application            │              │
    │  ┌──────────────────────────────┐    │              │
    │  │     Authentication (JWT)      │    │              │
    │  └──────────────────────────────┘    │              │
    │  ┌──────────────────────────────┐    │    Redis     │
    │  │      Business Logic          │◄───┼─► (Cache/    │
    │  │  (Spaces/Budgets/Expenses)   │    │   Sessions)  │
    │  └──────────────────────────────┘    │              │
    │  ┌──────────────────────────────┐    │              │
    │  │    Template Rendering        │    │              │
    │  │      (Django Templates)      │    │              │
    │  └──────────────────────────────┘    │              │
    └───────────┬───────────────────────────┼──────────────┘
                │                           │
    ┌───────────▼──────────┐    ┌──────────▼──────────┐
    │   PostgreSQL DB      │    │   Celery Workers    │
    │   (Production)       │    │  (Monthly tasks)    │
    └──────────────────────┘    └─────────────────────┘
                │                           │
    ┌───────────▼──────────┐    ┌──────────▼──────────┐
    │   Cloudinary         │    │   SendGrid          │
    │   (Media Storage)    │    │   (Email Service)   │
    └──────────────────────┘    └─────────────────────┘
```

### Frontend Architecture (PWA)

- **Framework:** Django Templates + Progressive Enhancement
- **Component Structure:**

  ```
  templates/
  ├── public/              # Public pages (no auth required)
  │   ├── base_public.html # Base for public pages
  │   ├── landing.html     # Homepage with hero section
  │   ├── login.html       # Login form
  │   └── register.html    # Registration form
  ├── authenticated/       # Authenticated layout
  │   └── base_authenticated.html # Base with nav/sidebar
  ├── dashboard/           # Dashboard views
  │   └── home.html       # Main dashboard page
  ├── components/          # Reusable components
  │   ├── navbar.html     # Bottom navigation (mobile)
  │   ├── sidebar.html    # Sidebar navigation (desktop)
  │   ├── header.html     # Top header with user menu
  │   ├── modals/         # Modal components
  │   └── forms/          # Form components
  ├── spaces/             # Space management
  ├── budgets/            # Budget views
  ├── expenses/           # Expense tracking
  └── errors/             # Error pages (404, 500)

  static/
  ├── css/
  │   ├── main.css        # Tailwind output
  │   └── components/     # Component styles
  ├── js/
  │   ├── main.js         # Core JavaScript
  │   ├── sw.js           # Service Worker
  │   └── modules/        # JS modules
  └── pwa/
      ├── manifest.json   # PWA manifest
      └── icons/         # App icons
  ```

- **State Management:** Alpine.js for reactive UI
- **Routing:** Django URL patterns
- **Build Optimization:** Tailwind CSS purge, JS minification

#### Navigation Architecture

**Responsive Navigation System:**
- **Mobile (<768px):** Bottom navigation bar + hamburger header
- **Tablet (768-1024px):** Both bottom nav and collapsible sidebar
- **Desktop (>1024px):** Fixed sidebar + header, no bottom nav

**Navigation Components:**
```html
<!-- Header (all screens) -->
<header class="fixed top-0 w-full">
  <div class="mobile-header md:hidden">
    <button class="hamburger">☰</button>
    <h1>MonAI</h1>
    <div class="user-avatar">{{ user.username.0 }}</div>
  </div>
</header>

<!-- Sidebar (desktop + tablet) -->
<nav class="sidebar hidden md:block fixed left-0 w-64">
  <div class="logo">MonAI</div>
  <ul class="nav-links">
    <li><a href="/dashboard/">Dashboard</a></li>
    <li><a href="#" disabled>Espacios</a></li>
    <li><a href="#" disabled>Presupuestos</a></li>
    <li><a href="#" disabled>Gastos</a></li>
  </ul>
  <div class="user-profile">...</div>
</nav>

<!-- Bottom Navigation (mobile only) -->
<nav class="bottom-nav md:hidden fixed bottom-0 w-full">
  <a href="/dashboard/">Dashboard</a>
  <a href="#" disabled>Espacios</a>
  <a href="#" disabled>Presupuestos</a>
  <a href="#" disabled>Gastos</a>
</nav>
```

**Authentication Flow:**
1. Landing page (/) → Clean design, no navigation
2. Login/Register → Minimal header with back to home
3. Dashboard → Full authenticated layout with nav
4. All protected pages use authenticated layout

**User Experience:**
- Smooth transitions between public and authenticated areas
- Consistent navigation patterns across screen sizes
- Visual feedback for disabled features (coming soon)
- User context always visible in header/sidebar

### Backend Architecture

- **Framework:** Django 5.0
- **Folder Structure:**
  ```
  apps/
  ├── authentication/    # User management & JWT
  │   ├── models.py     # Extended User model
  │   ├── serializers.py # API serializers
  │   ├── views.py      # Auth endpoints
  │   └── urls.py       # Auth routes
  ├── spaces/           # Space management
  │   ├── models.py     # Space, SpaceMember
  │   ├── services.py   # Business logic
  │   └── views.py      # Space views
  ├── budgets/          # Budget planning
  │   ├── models.py     # Budget, BudgetCategory
  │   ├── tasks.py      # Celery tasks
  │   └── views.py      # Budget management
  ├── expenses/         # Expense tracking
  │   ├── models.py     # Expense, ExpenseSplit
  │   ├── services.py   # Calculation logic
  │   └── views.py      # Expense CRUD
  └── dashboard/        # Analytics & reports
      ├── services.py   # Dashboard logic
      └── views.py      # Dashboard views
  ```
- **API Design:** RESTful with DRF for mobile endpoints
- **Authentication:** JWT (simplejwt)
- **Database ORM:** Django ORM

### Database Design

- **Type:** PostgreSQL (Production) / SQLite (Development)
- **Tables:**
  - `users`: Extended Django User model
  - `spaces`: Shared financial spaces
  - `space_members`: User-Space relationships
  - `budget_categories`: System and custom categories
  - `budgets`: Monthly budget allocations
  - `expenses`: Actual transactions
  - `expense_splits`: Split expense details
  - `incomes`: Income records
  - `monthly_closes`: Historical snapshots
- **Indexes:**
  - `space_id, month_period`: Frequent filtering
  - `user_id, space_id`: Member queries
  - `created_at DESC`: Timeline queries
- **Relationships:**
  - User ←→ Space (M2M through SpaceMember)
  - Space → Budget/Expense (One to Many)
  - Expense → ExpenseSplit (One to Many)

## Technology Stack

### Frontend

```yaml
Framework: Django Templates
Version: 5.0.1
UI Library: Tailwind CSS (CDN)
JavaScript: Vanilla JS + Alpine.js
PWA: Service Workers + Web App Manifest
Charts: Chart.js
Icons: Heroicons
Forms: Django Forms + Crispy Forms
Testing: Django TestCase
Build Tool: Django Collectstatic
```

### Backend

```yaml
Language: Python 3.11+
Framework: Django 5.0.1
API: Django REST Framework 3.14.0
Database: PostgreSQL 15 / SQLite3
Authentication: djangorestframework-simplejwt 5.3.1
File Storage: Cloudinary
Email Service: SendGrid
Queue/Jobs: Celery + Redis
Logging: Django Logging
Validation: Django Forms + DRF Serializers
Testing: pytest-django
API Docs: drf-spectacular (Swagger)
```

### DevOps & Tools

```yaml
Version Control: Git/GitHub
CI/CD: GitHub Actions (planned)
Container: Docker (future)
Hosting: Railway.app → AWS
Monitoring: Sentry
Analytics: Google Analytics 4
Package Manager: pip + venv
Linting: Black + isort
Pre-commit: pre-commit hooks
```

## Code Conventions

### Naming Conventions

```python
# Django Models
class SpaceMember(models.Model):  # PascalCase
    space = models.ForeignKey()   # snake_case fields

# Views
def expense_list(request):        # snake_case

# URLs
path('api/auth/', include())      # kebab-case endpoints

# Templates
templates/dashboard/index.html    # kebab-case files

# Static files
static/js/expense-tracker.js      # kebab-case
static/css/dashboard.css

# Constants
MAX_MEMBERS_PER_SPACE = 10       # UPPER_SNAKE_CASE
```

### Git Commit Format

```
type(scope): subject

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

Example:
feat(spaces): add member invitation system
fix(auth): resolve JWT refresh token issue
```

### API Response Format

```python
# Success Response
{
    "success": True,
    "data": {
        "user": {...},
        "tokens": {...}
    },
    "message": "Login successful"
}

# Error Response
{
    "success": False,
    "error": {
        "message": "Invalid credentials",
        "code": "AUTH_FAILED",
        "field_errors": {...}
    }
}
```

### Error Handling Pattern

```python
# Django Views
def expense_create(request):
    try:
        expense = ExpenseService.create(request.data)
        return JsonResponse({
            'success': True,
            'data': expense.to_dict()
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': {'message': str(e)}
        }, status=400)
    except Exception as e:
        logger.error(f"Expense creation failed: {e}")
        return JsonResponse({
            'success': False,
            'error': {'message': 'Internal server error'}
        }, status=500)
```

## Folder Structure

### Complete Project Structure

```
12mo/
├── apps/
│   ├── __init__.py
│   ├── authentication/
│   ├── spaces/
│   ├── budgets/
│   ├── expenses/
│   └── dashboard/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── static/
│   ├── css/
│   ├── js/
│   └── pwa/
├── templates/
│   ├── base.html
│   └── [app_templates]/
├── media/
│   └── uploads/
├── locale/
│   ├── es/
│   └── en/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── docs/
│   ├── prd-monai.md
│   ├── planning.md
│   ├── api-docs.md
│   └── deployment.md
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```

## Environment Configuration

### Backend Environment Variables (.env)

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/monai_db
# Development uses SQLite by default

# JWT
JWT_SECRET_KEY=jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (SendGrid)
SENDGRID_API_KEY=your-sendgrid-key
DEFAULT_FROM_EMAIL=noreply@monai.app

# Cloudinary
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Sentry
SENTRY_DSN=https://key@sentry.io/project

# Google Analytics
GA_MEASUREMENT_ID=G-XXXXXXXXXX

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Frontend Environment Variables

```javascript
// static/js/config.js
const config = {
  API_URL: "http://localhost:8000/api",
  WS_URL: "ws://localhost:8000/ws",
  GA_ID: "G-XXXXXXXXXX",
  SENTRY_DSN: "https://key@sentry.io/project",
  VERSION: "1.0.0",
};
```

## API Design Patterns

### RESTful Endpoints Structure

```
# Authentication
POST   /api/auth/register/          # User registration
POST   /api/auth/login/             # User login
POST   /api/auth/token/refresh/     # Refresh JWT token
GET    /api/auth/profile/           # Get current user

# Spaces
GET    /api/spaces/                 # List user's spaces
POST   /api/spaces/                 # Create new space
GET    /api/spaces/:id/             # Get space details
PUT    /api/spaces/:id/             # Update space
DELETE /api/spaces/:id/             # Delete space
POST   /api/spaces/join/            # Join space with code
POST   /api/spaces/:id/invite/      # Generate invite code
GET    /api/spaces/:id/members/     # List space members

# Budgets
GET    /api/budgets/                # List budgets (filtered by space/month)
POST   /api/budgets/                # Create budget
PUT    /api/budgets/:id/            # Update budget
DELETE /api/budgets/:id/            # Delete budget
POST   /api/budgets/copy-month/     # Copy from previous month

# Expenses
GET    /api/expenses/               # List expenses (filtered)
POST   /api/expenses/               # Create expense
PUT    /api/expenses/:id/           # Update expense
DELETE /api/expenses/:id/           # Delete expense
GET    /api/expenses/summary/       # Monthly summary

# Dashboard
GET    /api/dashboard/overview/     # Current month overview
GET    /api/dashboard/balances/     # Member balances
GET    /api/dashboard/trends/       # Spending trends
GET    /api/dashboard/history/      # Historical data
```

## Security Standards

### Authentication & Authorization

- JWT with refresh token rotation
- Email-based authentication
- Space-based permissions
- Member role validation

### Data Protection

- Django CSRF protection
- Input validation with Django Forms
- SQL injection prevention (ORM)
- XSS protection (template escaping)
- Rate limiting with django-ratelimit
- Secure password hashing (bcrypt)

### Security Headers

```python
# settings/production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Performance Optimization

### Backend Optimization

- Database query optimization with select_related()
- QuerySet pagination
- Redis caching for sessions
- Celery for async tasks
- Database connection pooling
- Efficient ORM queries

### Frontend Optimization

- PWA with offline support
- Service Worker caching
- Lazy loading images
- Minified CSS/JS
- CDN for static assets
- Browser caching headers
- Compressed responses (gzip)

### Monitoring Metrics

- Response time < 200ms (API)
- Page load time < 2s
- Time to interactive < 3s
- Error rate < 0.1%
- Uptime > 99.9%

## Testing Strategy

### Unit Testing

```python
# Coverage targets
- Statements: > 80%
- Branches: > 75%
- Functions: > 80%
- Lines: > 80%

# Test structure
tests/
├── test_models.py
├── test_views.py
├── test_services.py
└── test_api.py
```

### Integration Testing

- API endpoint testing
- Database operations
- Authentication flows
- Space operations
- Budget calculations

### E2E Testing

- User registration flow
- Space creation and invitation
- Expense entry and splitting
- Monthly budget cycle
- Dashboard viewing

### Testing Tools

```yaml
Unit: pytest, Django TestCase
Integration: Django Test Client
API: Django REST Framework Test
E2E: Selenium (future)
Coverage: pytest-cov
```

## Deployment Architecture

### Development Environment

- SQLite database
- Django Debug Toolbar
- Hot reload enabled
- Mock data fixtures

### Staging Environment

- PostgreSQL database
- Redis cache
- Production settings
- Test data

### Production Environment

- Railway.app / Render.com
- PostgreSQL managed database
- Redis for cache
- Cloudinary CDN
- SSL/TLS enabled
- Automated backups

### CI/CD Pipeline

```yaml
1. Push to GitHub
2. Run Black formatter check
3. Run isort import check
4. Run pytest unit tests
5. Run integration tests
6. Check coverage (>80%)
7. Build static assets
8. Deploy to staging (auto)
9. Run smoke tests
10. Deploy to production (manual)
```

## Scaling Strategy

### Phase 1: MVP (0-100 users)

- Single server deployment
- SQLite/PostgreSQL
- Local Redis

### Phase 2: Growth (100-1000 users)

- Load balancer
- Separate database server
- CDN for all static assets
- Dedicated Redis instance

### Phase 3: Scale (1000+ users)

- Multiple app servers
- Read replicas for database
- Elasticsearch for search
- Dedicated queue workers
- Monitoring and alerting

### Caching Strategy

- Session data in Redis
- Static assets in CDN
- Database query caching
- Template fragment caching
- API response caching (future)

---

## Wallai Design System Architecture

### Brand Identity & Color System

**Primary Brand Colors:**
```css
:root {
  --wallai-green: #4ADE80;    /* Primary CTA buttons, highlights */
  --wallai-teal: #5EEAD4;     /* Secondary accents, hover states */
  --wallai-blue: #3B82A6;     /* Links, active states */
  --wallai-dark: #1E293B;     /* Text, borders */
  
  /* Gradient System */
  --gradient-primary: linear-gradient(135deg, #4ADE80 0%, #5EEAD4 50%, #3B82A6 100%);
  --gradient-secondary: linear-gradient(135deg, #5EEAD4 0%, #3B82A6 100%);
  --gradient-accent: linear-gradient(135deg, #4ADE80 0%, #5EEAD4 100%);
}
```

**Logo Assets (Cloudinary CDN):**
- Horizontal: `logo-horizontal_az18yr.png` (Navigation, h-12/h-16)
- Vertical: `logo-vertical_nioobl.png` (Hero sections, h-32)  
- Compact: `logo_zp2pxq.png` (Mobile, favicons, h-8)

### Component Architecture

**CSS Structure:**
```
static/css/
├── wallai.css                 # Brand-specific utilities and components
└── wallai-design-system.css   # Comprehensive component system
```

**Core Component Classes:**
```css
/* Buttons */
.wallai-btn {
  @apply px-6 py-3 rounded-xl font-semibold text-white shadow-lg;
  background: var(--gradient-primary);
  transition: all 0.2s ease;
}

.wallai-btn-outline {
  @apply px-6 py-3 rounded-xl font-semibold border-2;
  border-color: var(--wallai-green);
  color: var(--wallai-green);
}

/* Cards & Containers */
.wallai-card {
  @apply bg-white rounded-2xl p-6 shadow-lg border border-gray-100;
}

/* Form Elements */
.wallai-input {
  @apply w-full px-4 py-3 rounded-xl border-2 border-gray-200;
  @apply focus:border-wallai-green focus:outline-none;
  transition: border-color 0.2s ease;
}

/* Brand Text Effects */
.wallai-gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### Navigation System Architecture

**Mobile-First Navigation (Updated Implementation):**

```html
<!-- Enhanced Header (80px height, h-16 logo) -->
<header class="h-20 bg-white border-b border-gray-200">
  <div class="flex items-center justify-between h-full px-6">
    <img src="logo-horizontal.png" alt="Wallai" class="h-16">
    <div class="user-menu">{{ user.first_name }}</div>
  </div>
</header>

<!-- Modern Curved Bottom Navigation (Mobile Only) -->
<nav class="md:hidden fixed bottom-0 left-0 right-0 z-50">
  <div class="bottom-nav h-18 bg-white border-t border-gray-200">
    <div class="grid grid-cols-5 h-full relative">
      <!-- Home, Stats, Center (+), Budget, Prices -->
      <div class="center-button absolute top-[-30px] left-1/2 transform -translate-x-1/2">
        <button class="w-17 h-17 bg-wallai-gradient rounded-full">
          <svg class="w-8 h-8 text-white"><!-- Plus icon --></svg>
        </button>
      </div>
    </div>
  </div>
</nav>
```

**Navigation Features:**
- **Mobile**: Curved bottom nav with floating center button
- **Desktop**: Enhanced sidebar with larger logo
- **Responsive**: Seamless experience across all screen sizes
- **Touch Optimized**: 44px+ touch targets, proper spacing

### Template Architecture

**Template Hierarchy:**
```
templates/
├── public/                    # No authentication required
│   ├── base_public.html      # PWA config, landing pages
│   ├── landing.html          # Hero + features with Wallai branding
│   ├── login.html            # Wallai-styled authentication
│   └── register.html         # Consistent branding
├── authenticated/            # Authentication required  
│   └── base_authenticated.html # Modern navigation + Wallai design
├── dashboard/
│   └── home.html            # Dashboard with metrics cards
└── components/              # Reusable components
    ├── mobile_navigation.html # Bottom nav component
    └── modals.html          # Glassmorphism modals
```

### Responsive Design Standards

**Breakpoint System:**
- **Mobile**: 375px-767px (Bottom navigation primary)
- **Tablet**: 768px-1023px (Both nav systems)
- **Desktop**: 1024px+ (Sidebar primary)

**Typography Scale:**
```css
/* Mobile-first with responsive scaling */
.hero-title { @apply text-3xl md:text-4xl lg:text-5xl; }
.section-title { @apply text-2xl md:text-3xl; }
.body-text { @apply text-base md:text-lg; }
```

**Spacing System (Tailwind-based):**
- Base unit: 4px
- Common spacings: 12px (p-3), 24px (p-6), 32px (p-8), 48px (p-12)
- Touch targets: Minimum 44px for mobile interactions

### Animation & Interaction Patterns

**Micro-Animations:**
```css
/* Floating elements */
@keyframes wallai-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

/* Hover effects */
.hover\:scale-105:hover { transform: scale(1.05); }
.transition-all { transition: all 0.2s ease; }
```

**Glassmorphism Effects:**
```css
.glassmorphism {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
```

### Performance & Optimization

**CSS Optimization:**
- Critical CSS inlined for above-the-fold content
- Non-critical CSS loaded asynchronously
- Tailwind purging for production builds

**Asset Optimization:**
- Logo assets served via Cloudinary CDN
- Automatic WebP conversion and responsive images
- Lazy loading for below-fold images

**Bundle Strategy:**
- Component-based CSS architecture
- Modular JavaScript with ES6 modules
- Service worker caching for offline experience

---

**Document Status:**

- Created: September 8, 2025
- Last Updated: September 11, 2025 (Wallai rebrand + modern navigation)
- Version: 2.0
- Maintained by: PDAC95 Engineering Team
