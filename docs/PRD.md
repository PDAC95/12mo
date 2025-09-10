# Product Requirements Document (PRD)

## MonAI - Personal Finance Tracker

**Version:** 1.0  
**Date:** September 8, 2025  
**Author:** PDAC95 Product Team  
**Status:** Active Development - Sprint 0

---

## Executive Summary

MonAI is a Progressive Web Application (PWA) designed for collaborative personal finance management, enabling multiple users to share and manage budgets within defined spaces. The application addresses the complexity of shared household expenses through an intuitive mobile-first interface that tracks planned budgets versus actual expenses.

The core problem MonAI solves is the difficulty couples, roommates, and families face when managing shared finances. Traditional spreadsheets are cumbersome, while existing finance apps focus on individual users rather than collaborative spaces. MonAI bridges this gap by providing real-time expense tracking, automatic budget replication, and clear visibility of who owes what.

The target market includes young professionals, couples, and shared living arrangements in urban areas, particularly in North America where split expenses are common. The key differentiating feature is the "Spaces" concept, allowing users to maintain multiple financial contexts (personal, shared household, business) within a single account.

Currently in Sprint 0 of development, MonAI aims to replace manual Excel-based tracking systems with an automated, accessible solution. The vision extends to incorporating AI-powered insights for expense categorization and budget optimization, positioning MonAI as the foundation for intelligent personal finance management.

## Problem Statement

### Identified Problems

- **Problem 1:** Manual tracking of shared expenses in spreadsheets is time-consuming and error-prone, requiring constant updates and reconciliation between parties
- **Problem 2:** Existing finance apps focus on individual users, lacking collaborative features for couples or roommates who need to split expenses and track who pays for what
- **Problem 3:** Monthly budget planning requires manual copying of categories and amounts, with no automatic tracking of planned versus actual spending

### Problem Impact

- Users spend 2-3 hours monthly updating and reconciling shared expense spreadsheets
- 68% of couples report money as a primary source of stress in relationships
- Average household loses $1,200 annually due to poor expense tracking and missed budget goals
- Current manual methods lead to disputes about who paid for what and who owes whom

## Target Users

### Primary User: Young Couples (Diana & Patricio)

**Profile:** 25-35 years old, dual income, living together, tech-savvy

- **Needs:** Clear visibility of shared expenses, fair expense splitting, automated tracking
- **Frustrations:** Manual Excel updates, remembering who paid last, calculating monthly balances
- **Technology:** Comfortable with mobile apps, prefer mobile over desktop
- **Behavior:** Check finances weekly, pay bills monthly, review expenses together

### Secondary User: Roommates/Shared Living

**Profile:** 22-30 years old, students or young professionals, 2-4 people per space

- **Needs:** Transparent expense sharing, individual tracking within group context
- **Frustrations:** Chasing roommates for payments, unclear expense responsibilities
- **Technology:** Mobile-first users, familiar with payment apps
- **Behavior:** Frequent small shared expenses, monthly rent/utilities

### Tertiary User: Individual Budget Trackers

**Profile:** Any age, single or managing personal finances separately

- **Needs:** Simple budget tracking, expense categorization, monthly insights
- **Frustrations:** Overcomplicated finance apps, subscription fees
- **Technology:** Varies, but prefer simple interfaces
- **Behavior:** Monthly budget reviews, occasional expense entry

## User Stories

### Authentication & Spaces

1. **As a new user**, I want to register with my email so that I can create my account quickly
2. **As a user**, I want to create a shared space so that I can invite my partner/roommates
3. **As a space member**, I want to switch between spaces so that I can manage personal and shared finances separately
4. **As a space owner**, I want to invite members via code so that they can join easily

### Budget Management

5. **As a space member**, I want to set monthly budgets by category so that I can plan my expenses
6. **As a user**, I want budgets to automatically copy each month so that I don't have to recreate them
7. **As a user**, I want to assign budget categories to specific people so that we know who's responsible
8. **As a user**, I want to receive alerts at 80% budget usage so that I can control spending

### Expense Tracking

9. **As a user**, I want to quickly add expenses so that I can track in real-time
10. **As a user**, I want to split expenses between members so that we can share costs fairly
11. **As a user**, I want to see who paid for what so that we can balance accounts
12. **As a user**, I want to categorize expenses so that I can track spending patterns

### Dashboard & Reports

13. **As a user**, I want to see budget vs actual spending so that I know my financial status
14. **As a user**, I want to see who owes whom so that we can settle balances
15. **As a user**, I want to view previous months so that I can track progress
16. **As a user**, I want to identify unplanned expenses so that I can improve budgeting

## Functional Requirements

### User Management

- Email-based authentication with JWT tokens
- Multi-language support (Spanish/English initially)
- Profile management with preferred language setting
- Password reset functionality
- Session management with refresh tokens

### Space Management

- Create multiple spaces per user (max 10 spaces per user)
- Invite members via 6-character alphanumeric code
- Maximum 10 members per space
- Role-based permissions (owner/member)
- Leave space functionality (except owner)

### Budget System

- Create budget categories with monthly amounts
- Assign categories to specific members or shared
- Automatic monthly budget replication at 23:59 last day
- Edit budgets during current month only
- Fixed vs variable expense categories
- Budget templates for quick setup

### Expense Tracking

- Add expenses with amount, category, date, description
- Assign payer (who paid)
- Split expenses (50/50 or custom amounts)
- Edit/delete expenses in current month only
- Attach receipts (image upload)
- Recurring expense support

### Dashboard Features

- Current month overview with balance
- Budget progress bars with color coding
- Expense breakdown by category
- Member balance calculation
- Monthly comparison charts
- Export data to CSV

## Non-Functional Requirements

### Performance

- Page load time < 2 seconds on 3G connection
- API response < 200ms for read operations
- Support for 1000 concurrent users
- Offline capability for core features

### Security

- HTTPS encryption for all communications
- JWT token-based authentication
- Password hashing with bcrypt
- CORS configuration for API protection
- Rate limiting on authentication endpoints

### Scalability

- Modular Django app architecture
- PostgreSQL for production database
- Redis for caching and sessions
- Horizontal scaling capability
- CDN for static assets

### Usability

- Mobile-first responsive design
- PWA installable on devices
- WCAG 2.1 AA accessibility standards
- Multi-language interface (ES/EN/FR planned)
- Intuitive navigation with bottom navbar

### Availability

- 99.9% uptime requirement
- Daily automated backups
- 30-day data retention for deleted items
- Maintenance window: Sunday 2-4 AM EST
- Disaster recovery within 4 hours

## Technology Stack

### Frontend

- **Framework:** Django Templates (Server-side rendering)
- **Styling:** Tailwind CSS
- **JavaScript:** Vanilla JS + Alpine.js for reactivity
- **PWA:** Service Workers + Web App Manifest
- **Charts:** Chart.js for visualizations

### Backend

- **Runtime:** Python 3.11+
- **Framework:** Django 5.0
- **API:** Django REST Framework
- **Database:** PostgreSQL (SQLite for development)
- **Authentication:** JWT (djangorestframework-simplejwt)

### Infrastructure

- **Hosting:** Railway.app (initial) → AWS (production)
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry for error tracking
- **CDN:** Cloudflare for static assets
- **Storage:** Cloudinary for images

### External Integrations

- **Email:** SendGrid for notifications
- **Analytics:** Google Analytics 4
- **Payment:** Stripe (future premium features)
- **Banking:** Plaid API (future MonAI evolution)

## Success Metrics

### Adoption Metrics

- **Target Users:** 100 active spaces in 3 months
- **Registration Rate:** 40% of landing page visitors
- **Space Creation:** 60% of users create/join a space

### Engagement Metrics

- **Session Duration:** Average 3+ minutes
- **Return Rate:** 70% weekly active users
- **Actions per Session:** 5+ (view dashboard, add expense, etc.)

### Business Metrics

- **Excel Replacement:** 80% of users stop using spreadsheets
- **Time Saved:** 2+ hours per month per user
- **User Satisfaction:** NPS score > 40

### Technical Metrics

- **Performance:** 95% of requests < 200ms
- **Error Rate:** < 0.1% of requests
- **Uptime:** 99.9% monthly

## MVP vs Full Version

### MVP (Minimum Viable Product)

**Timeline:** 6 weeks (Sprint 0-5)

**Included Features:**

- User registration/login with JWT
- Create and join spaces
- Basic budget categories
- Manual expense entry
- Simple dashboard with balance
- PWA installation
- Spanish/English support

**Excluded Features:**

- Receipt scanning
- Recurring expenses
- Advanced analytics
- Email notifications
- Data export
- Payment integration

### Full Version (MonAI)

**Timeline:** 6 months

**Additional Features:**

- AI-powered expense categorization
- Bank account integration (Plaid)
- Predictive budgeting
- Bill reminders and notifications
- Detailed analytics and reports
- Premium features with subscription
- Mobile app (React Native)

## Data Model Specification

### User Schema

```python
{
  id: UUID,
  email: String (unique),
  username: String,
  password: String (hashed),
  preferred_language: Enum['es', 'en'],
  created_at: DateTime,
  updated_at: DateTime
}
```

### Space Schema

```python
{
  id: UUID,
  name: String,
  invite_code: String (6 chars),
  created_by: User (FK),
  created_at: DateTime,
  is_active: Boolean
}
```

### Budget Schema

```python
{
  id: UUID,
  space: Space (FK),
  category: BudgetCategory (FK),
  amount: Decimal,
  assigned_to: User (FK, nullable),
  month_year: String (YYYY-MM),
  is_active: Boolean
}
```

### Expense Schema

```python
{
  id: UUID,
  space: Space (FK),
  category: BudgetCategory (FK),
  amount: Decimal,
  paid_by: User (FK),
  description: String,
  date: Date,
  month_period: String (YYYY-MM),
  splits: [ExpenseSplit]
}
```

## System Architecture

### High-Level Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   PWA       │◄──►│   Django    │◄──►│ PostgreSQL  │
│   Client    │    │   Backend   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Service   │    │   Redis     │    │  Celery     │
│   Worker    │    │   Cache     │    │  Workers    │
└─────────────┘    └─────────────┘    └─────────────┘
```

## API Specification

### Authentication Endpoints

#### POST /api/auth/register

**Request:**

```json
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "preferred_language": "es"
}
```

**Response (201):**

```json
{
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    "username": "testuser"
  },
  "tokens": {
    "access": "jwt_token",
    "refresh": "refresh_token"
  }
}
```

#### POST /api/auth/login

**Request:**

```json
{
  "email": "test@example.com",
  "password": "SecurePass123!"
}
```

## Risks and Mitigations

### Technical Risks

**Risk:** Data loss due to synchronization issues

- **Probability:** Medium
- **Impact:** High
- **Mitigation:** Implement optimistic UI updates with conflict resolution

**Risk:** Poor mobile performance

- **Probability:** Low
- **Impact:** High
- **Mitigation:** PWA with offline-first architecture

### Business Risks

**Risk:** Low user adoption due to manual entry

- **Probability:** Medium
- **Impact:** High
- **Mitigation:** Focus on UX simplicity, quick entry methods

### Security Risks

**Risk:** Unauthorized access to financial data

- **Probability:** Low
- **Impact:** High
- **Mitigation:** JWT authentication, encrypted connections, rate limiting

## Timeline

### Sprint 0: Foundation (Week 1)

- Project setup and configuration
- Authentication system
- Base app structure
- PWA basic setup

### Sprint 1: Spaces (Week 2)

- Space model and CRUD
- Member invitation system
- Space switching UI

### Sprint 2: Budgets (Week 3)

- Budget categories
- Monthly budget management
- Auto-replication system

### Sprint 3: Expenses (Week 4)

- Expense entry and editing
- Expense splitting logic
- Category assignment

### Sprint 4: Dashboard (Week 5)

- Dashboard views
- Balance calculations
- Charts and visualizations

### Sprint 5: Polish (Week 6)

- PWA optimization
- Testing and bug fixes
- Deployment preparation

## Next Steps

1. **Complete Sprint 0**

   - Finish PWA setup
   - Configure i18n
   - Set up testing framework
   - Timeline: 2 days
   - Owner: Development Team

2. **Begin Sprint 1**

   - Design Space models
   - Create invitation system
   - Build UI components
   - Timeline: 1 week
   - Owner: Full Stack Team

3. **User Testing Prep**
   - Recruit beta testers
   - Prepare feedback forms
   - Set up analytics
   - Timeline: Ongoing
   - Owner: Product Team

---

**Document Control:**

- Last Updated: September 8, 2025
- Next Review: September 15, 2025
- Owner: PDAC95 Team
- Stakeholders: Development Team, End Users (Diana & Patricio)
