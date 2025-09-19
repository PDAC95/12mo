from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import calendar
from datetime import datetime

User = get_user_model()


class BudgetCategory(models.Model):
    """Budget categories for organizing expenses"""

    # Category types
    TYPE_CHOICES = [
        ('fixed', 'Fixed'),      # Rent, insurance, fixed payments
        ('variable', 'Variable'), # Food, entertainment, flexible expenses
    ]

    # System default categories
    SYSTEM_CATEGORIES = [
        ('housing', 'Housing & Rent', 'fixed'),
        ('utilities', 'Utilities', 'variable'),
        ('food', 'Food & Groceries', 'variable'),
        ('transportation', 'Transportation', 'variable'),
        ('healthcare', 'Healthcare', 'variable'),
        ('entertainment', 'Entertainment', 'variable'),
        ('shopping', 'Shopping', 'variable'),
        ('savings', 'Savings', 'fixed'),
        ('debt', 'Debt Payments', 'fixed'),
        ('other', 'Other', 'variable'),
    ]

    # Icon choices for categories
    ICON_CHOICES = [
        ('home', '🏠 Home'),
        ('zap', '⚡ Utilities'),
        ('shopping-cart', '🛒 Food'),
        ('car', '🚗 Transport'),
        ('heart', '❤️ Health'),
        ('music', '🎵 Entertainment'),
        ('gift', '🎁 Shopping'),
        ('piggy-bank', '🐷 Savings'),
        ('credit-card', '💳 Debt'),
        ('more-horizontal', '📋 Other'),
    ]

    name = models.CharField(
        max_length=50,
        help_text="Category name (max 50 characters)"
    )
    description = models.TextField(
        max_length=200,
        blank=True,
        help_text="Optional description of the category"
    )
    icon = models.CharField(
        max_length=20,
        choices=ICON_CHOICES,
        default='more-horizontal',
        help_text="Icon for this category"
    )
    category_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='variable',
        help_text="Whether this is a fixed or variable expense"
    )
    color = models.CharField(
        max_length=20,
        default='blue',
        help_text="Color theme for this category"
    )
    is_system_default = models.BooleanField(
        default=False,
        help_text="Whether this is a system-provided default category"
    )
    space = models.ForeignKey(
        'spaces.Space',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Space this category belongs to (null for system defaults)"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User who created this custom category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )

    class Meta:
        db_table = 'budget_categories'
        ordering = ['is_system_default', 'name']
        verbose_name = 'Budget Category'
        verbose_name_plural = 'Budget Categories'
        unique_together = [['space', 'name']]  # Unique category names per space

    def __str__(self):
        if self.is_system_default:
            return f"{self.name} (System)"
        elif self.space:
            return f"{self.name} ({self.space.name})"
        else:
            return self.name

    def clean(self):
        """Custom validation"""
        # System defaults can't belong to a specific space
        if self.is_system_default and self.space:
            raise ValidationError('System default categories cannot belong to a specific space')

        # Custom categories must belong to a space
        if not self.is_system_default and not self.space:
            raise ValidationError('Custom categories must belong to a space')

        # Validate name length
        if self.name and len(self.name.strip()) > 50:
            raise ValidationError({'name': 'Category name cannot be longer than 50 characters'})

    @property
    def icon_class(self):
        """Get the icon class mapping for display"""
        icon_map = {
            'home': 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
            'zap': 'M13 10V3L4 14h7v7l9-11h-7z',
            'shopping-cart': 'M3 3h2l.4 2M7 13h10l4-8H5.4m1.6 8L6 5H2m5 8v6a2 2 0 002 2h8a2 2 0 002-2v-6m-10 0h10',
            'car': 'M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z',
            'heart': 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
            'music': 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z',
            'gift': 'M12 3v1m0-1V2a1 1 0 00-1-1H9a1 1 0 00-1 1v1m4 0h2a1 1 0 011 1v1H10V4a1 1 0 011-1h1z',
            'piggy-bank': 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z',
            'credit-card': 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H5a3 3 0 00-3 3v8a3 3 0 003 3z',
            'more-horizontal': 'M5 12h.01M12 12h.01M19 12h.01',
        }
        return icon_map.get(self.icon, icon_map['more-horizontal'])

    @classmethod
    def create_system_defaults(cls):
        """Create system default categories if they don't exist"""
        for code, name, category_type in cls.SYSTEM_CATEGORIES:
            icon_map = {
                'housing': 'home',
                'utilities': 'zap',
                'food': 'shopping-cart',
                'transportation': 'car',
                'healthcare': 'heart',
                'entertainment': 'music',
                'shopping': 'gift',
                'savings': 'piggy-bank',
                'debt': 'credit-card',
                'other': 'more-horizontal',
            }

            cls.objects.get_or_create(
                name=name,
                is_system_default=True,
                defaults={
                    'description': f'System default category for {name.lower()}',
                    'icon': icon_map.get(code, 'more-horizontal'),
                    'category_type': category_type,
                    'color': 'blue',
                }
            )


class Budget(models.Model):
    """Monthly budget allocation for a space"""

    space = models.ForeignKey(
        'spaces.Space',
        on_delete=models.CASCADE,
        related_name='budgets',
        help_text="Space this budget belongs to"
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        related_name='budgets',
        help_text="Budget category"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Budgeted amount for this category"
    )

    # TIMING SYSTEM - New fields for smart budget timing
    timing_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed_date', 'Fixed Date'),      # Rent - specific due date
            ('date_range', 'Date Range'),      # Groceries - within a week
            ('flexible', 'Flexible'),          # Gas - anytime during month
        ],
        default='flexible',
        help_text="When this expense should be paid during the month"
    )

    # For fixed date expenses (rent, bills)
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Exact due date for fixed date expenses"
    )

    # For date range expenses (groceries, entertainment)
    range_start = models.DateField(
        null=True,
        blank=True,
        help_text="Start date for date range expenses"
    )
    range_end = models.DateField(
        null=True,
        blank=True,
        help_text="End date for date range expenses"
    )
    range_description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Human-readable description of the range (e.g., 'First week', 'Weekends')"
    )

    # Smart reminders and preferences
    reminder_days_before = models.IntegerField(
        default=3,
        help_text="How many days before due date/range to send reminder"
    )
    preferred_time_of_day = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
            ('anytime', 'Anytime'),
        ],
        default='anytime',
        help_text="Preferred time of day for this expense"
    )

    # Enhanced recurrence system
    recurrence_pattern = models.CharField(
        max_length=30,
        choices=[
            ('monthly_same_date', 'Same date each month'),      # Rent - always 1st
            ('monthly_same_range', 'Same range each month'),    # Groceries - always week 1
            ('monthly_flexible', 'Flexible each month'),        # Gas - anytime
            ('biweekly_same_day', 'Same day biweekly'),        # Paycheck - every other Friday
        ],
        blank=True,
        null=True,
        help_text="How this recurring expense should repeat"
    )

    # Behavior tracking for smart suggestions
    actual_spend_dates = models.JSONField(
        default=list,
        blank=True,
        help_text="Historical dates when this expense was actually paid (for pattern analysis)"
    )
    last_behavior_analysis = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When behavior analysis was last updated for this budget"
    )

    # Estimation vs Real tracking
    is_estimated = models.BooleanField(
        default=False,
        help_text="Whether this is an estimated amount (like utilities) vs fixed (like rent)"
    )

    # For recurring expenses
    is_recurring = models.BooleanField(
        default=False,
        help_text="Whether this is a recurring expense"
    )

    recurrence_type = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        blank=True,
        null=True,
        help_text="How often this expense recurs"
    )

    expected_day = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month when this expense is expected (1-31)"
    )

    next_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next expected date for this recurring expense"
    )
    month_period = models.CharField(
        max_length=7,
        help_text="Budget month in YYYY-MM format"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User responsible for this budget category (optional)"
    )
    notes = models.TextField(
        max_length=500,
        blank=True,
        help_text="Optional notes about this budget"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_budgets',
        help_text="User who created this budget"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this budget is active"
    )

    class Meta:
        db_table = 'budgets'
        ordering = ['-month_period', 'category__name']
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'
        unique_together = [['space', 'category', 'month_period']]  # One budget per category per month per space

    def __str__(self):
        return f"{self.space.name} - {self.category.name} ({self.month_period}): ${self.amount}"

    def clean(self):
        """Custom validation"""
        # Validate month_period format
        if self.month_period:
            try:
                datetime.strptime(self.month_period, '%Y-%m')
            except ValueError:
                raise ValidationError({'month_period': 'Month period must be in YYYY-MM format'})

        # Validate that assigned user is a member of the space
        if self.assigned_to and self.space:
            from spaces.models import SpaceMember
            if not SpaceMember.objects.filter(
                space=self.space,
                user=self.assigned_to,
                is_active=True
            ).exists():
                raise ValidationError({'assigned_to': 'Assigned user must be a member of the space'})

        # Validate amount is positive
        if self.amount and self.amount <= 0:
            raise ValidationError({'amount': 'Budget amount must be greater than 0'})

        # TIMING VALIDATION - Validate timing fields consistency
        if self.timing_type == 'fixed_date':
            if not self.due_date:
                raise ValidationError({'due_date': 'Due date is required for fixed date expenses'})
            # Clear range fields for fixed date
            self.range_start = None
            self.range_end = None
            self.range_description = ''

        elif self.timing_type == 'date_range':
            if not self.range_start or not self.range_end:
                raise ValidationError({'range_start': 'Both start and end dates are required for date range expenses'})
            if self.range_start >= self.range_end:
                raise ValidationError({'range_start': 'Start date must be before end date'})
            # Clear due_date for range
            self.due_date = None

        elif self.timing_type == 'flexible':
            # Clear all timing fields for flexible
            self.due_date = None
            self.range_start = None
            self.range_end = None
            self.range_description = ''

        # Validate recurrence pattern matches timing type
        if self.is_recurring and self.recurrence_pattern:
            if self.timing_type == 'fixed_date' and self.recurrence_pattern not in ['monthly_same_date', 'biweekly_same_day']:
                raise ValidationError({'recurrence_pattern': 'Fixed date expenses can only use date-based recurrence patterns'})
            elif self.timing_type == 'date_range' and self.recurrence_pattern != 'monthly_same_range':
                raise ValidationError({'recurrence_pattern': 'Date range expenses should use range-based recurrence pattern'})
            elif self.timing_type == 'flexible' and self.recurrence_pattern != 'monthly_flexible':
                raise ValidationError({'recurrence_pattern': 'Flexible expenses should use flexible recurrence pattern'})

    @property
    def is_current_month(self):
        """Check if this budget is for the current month"""
        current_month = timezone.now().strftime('%Y-%m')
        return self.month_period == current_month

    @property
    def month_name(self):
        """Get the month name for display"""
        try:
            year, month = self.month_period.split('-')
            return calendar.month_name[int(month)]
        except (ValueError, IndexError):
            return self.month_period

    @property
    def total_spent(self):
        """Calculate total spent in this category for this month"""
        return self.get_real_spending_current_month()

    @property
    def remaining_amount(self):
        """Calculate remaining budget amount"""
        return self.amount - self.total_spent

    @property
    def spent_percentage(self):
        """Calculate percentage of budget spent"""
        if self.amount > 0:
            return (self.total_spent / self.amount * 100)
        return 0

    @property
    def is_over_budget(self):
        """Check if spending exceeds budget"""
        return self.total_spent > self.amount

    @property
    def is_warning_level(self):
        """Check if spending is at warning level (80% of budget)"""
        return self.spent_percentage >= 80

    @classmethod
    def create_monthly_budget(cls, space, month_period, created_by):
        """Create a complete monthly budget for a space using system defaults"""
        budgets_created = []

        # Get system default categories
        system_categories = BudgetCategory.objects.filter(is_system_default=True, is_active=True)

        for category in system_categories:
            # Set default amounts based on category type
            default_amounts = {
                'housing': Decimal('1200.00'),
                'utilities': Decimal('200.00'),
                'food': Decimal('400.00'),
                'transportation': Decimal('300.00'),
                'healthcare': Decimal('150.00'),
                'entertainment': Decimal('200.00'),
                'shopping': Decimal('250.00'),
                'savings': Decimal('500.00'),
                'debt': Decimal('300.00'),
                'other': Decimal('100.00'),
            }

            # Map category names to default amounts
            category_lower = category.name.lower()
            default_amount = Decimal('100.00')  # Default fallback

            for key, amount in default_amounts.items():
                if key in category_lower:
                    default_amount = amount
                    break

            budget, created = cls.objects.get_or_create(
                space=space,
                category=category,
                month_period=month_period,
                defaults={
                    'amount': default_amount,
                    'created_by': created_by,
                    'notes': f'Auto-generated budget for {category.name}'
                }
            )

            if created:
                budgets_created.append(budget)

        return budgets_created

    @classmethod
    def copy_from_previous_month(cls, space, target_month, created_by):
        """Copy budget from previous month to target month"""
        try:
            # Parse target month
            target_year, target_month_num = map(int, target_month.split('-'))

            # Calculate previous month
            if target_month_num == 1:
                prev_year = target_year - 1
                prev_month_num = 12
            else:
                prev_year = target_year
                prev_month_num = target_month_num - 1

            previous_month = f"{prev_year:04d}-{prev_month_num:02d}"

            # Get budgets from previous month
            previous_budgets = cls.objects.filter(
                space=space,
                month_period=previous_month,
                is_active=True
            )

            budgets_created = []
            for prev_budget in previous_budgets:
                budget, created = cls.objects.get_or_create(
                    space=space,
                    category=prev_budget.category,
                    month_period=target_month,
                    defaults={
                        'amount': prev_budget.amount,
                        'assigned_to': prev_budget.assigned_to,
                        'notes': f'Copied from {previous_month}',
                        'created_by': created_by,
                    }
                )

                if created:
                    budgets_created.append(budget)

            return budgets_created

        except ValueError:
            raise ValidationError('Invalid month format. Use YYYY-MM format.')

    def get_average_real_spending(self, months_back=6):
        """Calculate average real spending for this budget item over last X months"""
        try:
            year, month = map(int, self.month_period.split('-'))
            real_expenses = ActualExpense.objects.filter(
                budget_item=self,
                date_paid__year__gte=year - 1 if month <= months_back else year,
                date_paid__month__lte=month
            )

            if real_expenses.exists():
                total = sum(expense.actual_amount for expense in real_expenses)
                return total / real_expenses.count()
            return self.amount
        except (ValueError, ZeroDivisionError):
            return self.amount

    def get_spending_variance(self):
        """Compare estimated vs real spending, return percentage difference"""
        real_total = self.get_real_spending_current_month()
        if self.amount == 0:
            return 0

        variance = ((real_total - self.amount) / self.amount) * 100
        return round(variance, 1)

    def get_real_spending_current_month(self):
        """Get actual spending for current month"""
        real_expenses = ActualExpense.objects.filter(
            budget_item=self,
            month_period=self.month_period
        )
        return sum(expense.actual_amount for expense in real_expenses)

    # TIMING SYSTEM METHODS
    @property
    def timing_status(self):
        """Get current timing status of this budget"""
        from datetime import datetime, date
        today = date.today()

        if self.timing_type == 'fixed_date' and self.due_date:
            if self.due_date < today:
                return 'overdue'
            elif self.due_date == today:
                return 'due_today'
            elif (self.due_date - today).days <= self.reminder_days_before:
                return 'due_soon'
            else:
                return 'upcoming'

        elif self.timing_type == 'date_range' and self.range_start and self.range_end:
            if today < self.range_start:
                if (self.range_start - today).days <= self.reminder_days_before:
                    return 'range_starting_soon'
                return 'upcoming'
            elif self.range_start <= today <= self.range_end:
                return 'in_range'
            else:
                return 'range_ended'

        return 'flexible'

    @property
    def timing_display(self):
        """Get human-readable timing information"""
        if self.timing_type == 'fixed_date' and self.due_date:
            return f"Due: {self.due_date.strftime('%B %d')}"
        elif self.timing_type == 'date_range' and self.range_start and self.range_end:
            if self.range_description:
                return f"{self.range_description} ({self.range_start.strftime('%m/%d')} - {self.range_end.strftime('%m/%d')})"
            return f"{self.range_start.strftime('%m/%d')} - {self.range_end.strftime('%m/%d')}"
        return "Flexible timing"

    @property
    def days_until_due(self):
        """Get days until due date or range start"""
        from datetime import date
        today = date.today()

        if self.timing_type == 'fixed_date' and self.due_date:
            return (self.due_date - today).days
        elif self.timing_type == 'date_range' and self.range_start:
            if today < self.range_start:
                return (self.range_start - today).days
            elif today <= self.range_end:
                return 0  # In range
        return None

    def record_actual_spend_date(self, spend_date):
        """Record when this budget was actually spent for pattern analysis"""
        if isinstance(spend_date, datetime):
            spend_date = spend_date.date()

        spend_date_str = spend_date.isoformat()
        if spend_date_str not in self.actual_spend_dates:
            self.actual_spend_dates.append(spend_date_str)
            # Keep only last 12 entries for analysis
            if len(self.actual_spend_dates) > 12:
                self.actual_spend_dates = self.actual_spend_dates[-12:]
            self.save(update_fields=['actual_spend_dates'])

    def get_timing_variance_score(self):
        """Calculate how well user follows their timing preferences (0-100 score)"""
        if not self.actual_spend_dates or self.timing_type == 'flexible':
            return 100  # No variance for flexible or no data

        # Implementation will be enhanced with behavior analysis
        # For now, return basic score
        return 85

    def update_next_due_date(self):
        """Calculate and update next due date for recurring expenses"""
        if not self.is_recurring or not self.expected_day:
            return

        from datetime import datetime, timedelta
        import calendar

        try:
            year, month = map(int, self.month_period.split('-'))

            if self.recurrence_type == 'monthly':
                # Next month, same day
                if month == 12:
                    next_year, next_month = year + 1, 1
                else:
                    next_year, next_month = year, month + 1

                # Handle month end dates (e.g., Jan 31 -> Feb 28)
                max_day = calendar.monthrange(next_year, next_month)[1]
                next_day = min(self.expected_day, max_day)

                self.next_due_date = datetime(next_year, next_month, next_day).date()

            # Add other recurrence types as needed

        except (ValueError, TypeError):
            pass

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_recurring:
            self.update_next_due_date()
        super().save(*args, **kwargs)


class ActualExpense(models.Model):
    """Real expenses associated with budget items"""

    budget_item = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='actual_expenses',
        help_text="Budget item this expense belongs to"
    )
    actual_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Actual amount spent"
    )
    date_paid = models.DateField(
        help_text="Date when this expense was paid"
    )
    month_period = models.CharField(
        max_length=7,
        blank=True,
        help_text="Month this expense belongs to (YYYY-MM format)"
    )
    paid_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who paid this expense"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional description of the expense"
    )
    receipt_url = models.URLField(
        blank=True,
        help_text="URL to receipt image (Cloudinary, etc.)"
    )

    # Split expenses support
    is_shared = models.BooleanField(
        default=False,
        help_text="Whether this expense is shared among multiple users"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'actual_expenses'
        ordering = ['-date_paid']
        verbose_name = 'Actual Expense'
        verbose_name_plural = 'Actual Expenses'

    def __str__(self):
        return f"{self.budget_item.category.name}: ${self.actual_amount} on {self.date_paid}"

    def clean(self):
        """Custom validation"""
        # Auto-set month_period from date_paid
        if self.date_paid:
            self.month_period = self.date_paid.strftime('%Y-%m')

        # Validate paid_by is member of space
        if self.paid_by and self.budget_item and self.budget_item.space:
            from spaces.models import SpaceMember
            if not SpaceMember.objects.filter(
                space=self.budget_item.space,
                user=self.paid_by,
                is_active=True
            ).exists():
                raise ValidationError({'paid_by': 'User must be a member of the space'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ExpenseSplit(models.Model):
    """For handling split expenses between multiple users"""

    actual_expense = models.ForeignKey(
        ActualExpense,
        on_delete=models.CASCADE,
        related_name='splits'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User responsible for this portion"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))],
        help_text="Percentage of expense this user is responsible for"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Calculated amount for this user"
    )

    class Meta:
        db_table = 'expense_splits'
        unique_together = [['actual_expense', 'user']]
        verbose_name = 'Expense Split'
        verbose_name_plural = 'Expense Splits'

    def __str__(self):
        return f"{self.user.username}: {self.percentage}% (${self.amount})"

    def clean(self):
        """Custom validation"""
        if self.actual_expense and self.percentage:
            # Calculate amount based on percentage
            self.amount = (self.actual_expense.actual_amount * self.percentage / 100).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class BudgetTemplate(models.Model):
    """Predefined templates for quick budget creation"""

    TEMPLATE_TYPES = [
        ('bill', 'Monthly Bill'),           # Fixed date expenses like rent, utilities
        ('grocery', 'Groceries'),           # Weekly/biweekly groceries
        ('biweekly', 'Biweekly Expense'),   # Paycheck, biweekly bills
        ('flexible', 'Flexible Expense'),   # Gas, coffee, misc
        ('custom', 'Custom Template'),      # User-created templates
    ]

    name = models.CharField(
        max_length=100,
        help_text="Template name (e.g., 'Monthly Rent', 'Weekly Groceries')"
    )
    description = models.TextField(
        max_length=300,
        blank=True,
        help_text="Description of when to use this template"
    )
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        help_text="Type of template for categorization"
    )

    # Default values for budget creation
    default_category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        help_text="Default category for this template"
    )
    suggested_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Suggested default amount (optional)"
    )

    # Default timing configuration
    default_timing_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed_date', 'Fixed Date'),
            ('date_range', 'Date Range'),
            ('flexible', 'Flexible'),
        ],
        help_text="Default timing type for this template"
    )
    default_reminder_days = models.IntegerField(
        default=3,
        help_text="Default reminder days before due"
    )
    default_time_of_day = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
            ('anytime', 'Anytime'),
        ],
        default='anytime',
        help_text="Default preferred time of day"
    )

    # Recurrence defaults
    default_is_recurring = models.BooleanField(
        default=False,
        help_text="Whether expenses from this template should be recurring by default"
    )
    default_recurrence_pattern = models.CharField(
        max_length=30,
        choices=[
            ('monthly_same_date', 'Same date each month'),
            ('monthly_same_range', 'Same range each month'),
            ('monthly_flexible', 'Flexible each month'),
            ('biweekly_same_day', 'Same day biweekly'),
        ],
        blank=True,
        null=True,
        help_text="Default recurrence pattern"
    )

    # Template configuration
    is_system_default = models.BooleanField(
        default=False,
        help_text="Whether this is a system-provided template"
    )
    space = models.ForeignKey(
        'spaces.Space',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Space this template belongs to (null for system templates)"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User who created this template"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is active"
    )

    # Usage tracking
    usage_count = models.IntegerField(
        default=0,
        help_text="How many times this template has been used"
    )

    class Meta:
        db_table = 'budget_templates'
        ordering = ['template_type', 'name']
        verbose_name = 'Budget Template'
        verbose_name_plural = 'Budget Templates'

    def __str__(self):
        if self.is_system_default:
            return f"{self.name} (System)"
        elif self.space:
            return f"{self.name} ({self.space.name})"
        return self.name

    def clean(self):
        """Template validation"""
        if self.is_system_default and self.space:
            raise ValidationError('System templates cannot belong to a specific space')
        if not self.is_system_default and not self.space:
            raise ValidationError('Custom templates must belong to a space')

    @classmethod
    def create_system_defaults(cls):
        """Create system default templates"""
        system_templates = [
            {
                'name': 'Monthly Rent/Mortgage',
                'description': 'Fixed monthly housing payment with specific due date',
                'template_type': 'bill',
                'default_category_name': 'Housing & Rent',
                'suggested_amount': Decimal('1200.00'),
                'default_timing_type': 'fixed_date',
                'default_is_recurring': True,
                'default_recurrence_pattern': 'monthly_same_date',
            },
            {
                'name': 'Weekly Groceries',
                'description': 'Regular grocery shopping during specific week periods',
                'template_type': 'grocery',
                'default_category_name': 'Food & Groceries',
                'suggested_amount': Decimal('100.00'),
                'default_timing_type': 'date_range',
                'default_is_recurring': True,
                'default_recurrence_pattern': 'monthly_same_range',
            },
            {
                'name': 'Biweekly Paycheck Budget',
                'description': 'Budget allocation for biweekly income periods',
                'template_type': 'biweekly',
                'default_category_name': 'Other',
                'suggested_amount': Decimal('500.00'),
                'default_timing_type': 'fixed_date',
                'default_is_recurring': True,
                'default_recurrence_pattern': 'biweekly_same_day',
            },
            {
                'name': 'Flexible Monthly Expense',
                'description': 'Expenses that can be paid anytime during the month',
                'template_type': 'flexible',
                'default_category_name': 'Other',
                'suggested_amount': Decimal('50.00'),
                'default_timing_type': 'flexible',
                'default_is_recurring': True,
                'default_recurrence_pattern': 'monthly_flexible',
            },
            {
                'name': 'Utility Bill',
                'description': 'Monthly utilities with flexible payment date',
                'template_type': 'bill',
                'default_category_name': 'Utilities',
                'suggested_amount': Decimal('150.00'),
                'default_timing_type': 'date_range',
                'default_is_recurring': True,
                'default_recurrence_pattern': 'monthly_same_range',
            },
        ]

        for template_data in system_templates:
            category_name = template_data.pop('default_category_name')
            category = BudgetCategory.objects.filter(
                name=category_name,
                is_system_default=True
            ).first()

            if category:
                cls.objects.get_or_create(
                    name=template_data['name'],
                    is_system_default=True,
                    defaults={
                        **template_data,
                        'default_category': category,
                    }
                )

    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class SpendingBehaviorAnalysis(models.Model):
    """Track and analyze user spending behavior patterns"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User whose behavior is being analyzed"
    )
    space = models.ForeignKey(
        'spaces.Space',
        on_delete=models.CASCADE,
        help_text="Space context for this analysis"
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        help_text="Budget category being analyzed"
    )

    # Timing behavior patterns
    preferred_day_of_week = models.IntegerField(
        null=True,
        blank=True,
        help_text="Most common day of week for spending (1=Monday, 7=Sunday)"
    )
    preferred_time_of_day = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
        ],
        blank=True,
        help_text="Most common time of day for spending"
    )
    average_delay_days = models.IntegerField(
        default=0,
        help_text="Average days late vs planned timing (negative = early)"
    )

    # Pattern confidence and analysis quality
    pattern_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Confidence in pattern accuracy (0-100%)"
    )
    data_points_count = models.IntegerField(
        default=0,
        help_text="Number of expenses used for this analysis"
    )

    # Suggestion preferences learned
    optimal_timing_suggestion = models.CharField(
        max_length=200,
        blank=True,
        help_text="AI-generated optimal timing suggestion"
    )
    user_follows_suggestions = models.BooleanField(
        default=True,
        help_text="Whether user typically follows timing suggestions"
    )

    # Analysis metadata
    last_analysis_date = models.DateTimeField(
        auto_now=True,
        help_text="When this analysis was last updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'spending_behavior_analysis'
        unique_together = [['user', 'space', 'category']]
        ordering = ['-last_analysis_date']
        verbose_name = 'Spending Behavior Analysis'
        verbose_name_plural = 'Spending Behavior Analyses'

    def __str__(self):
        return f"{self.user.username} - {self.category.name} behavior in {self.space.name}"

    def update_from_expenses(self):
        """Update analysis based on recent expense patterns"""
        from datetime import datetime, timedelta
        from collections import Counter

        # Get recent expenses for this user/category/space
        recent_expenses = ActualExpense.objects.filter(
            budget_item__space=self.space,
            budget_item__category=self.category,
            paid_by=self.user,
            date_paid__gte=timezone.now() - timedelta(days=180)  # Last 6 months
        ).order_by('-date_paid')

        if not recent_expenses.exists():
            return

        self.data_points_count = recent_expenses.count()

        # Analyze day of week patterns
        days_of_week = [expense.date_paid.weekday() + 1 for expense in recent_expenses]  # 1=Monday
        if days_of_week:
            day_counter = Counter(days_of_week)
            self.preferred_day_of_week = day_counter.most_common(1)[0][0]

        # Calculate confidence based on data points and consistency
        if self.data_points_count >= 3:
            # Simple confidence calculation - can be enhanced
            consistency_ratio = day_counter.most_common(1)[0][1] / self.data_points_count
            self.pattern_confidence = min(consistency_ratio * 100, 100)
        else:
            self.pattern_confidence = 0

        # Generate optimal timing suggestion
        if self.preferred_day_of_week and self.pattern_confidence > 50:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_name = day_names[self.preferred_day_of_week - 1]
            self.optimal_timing_suggestion = f"You typically spend on {day_name}s"

        self.save()

    def get_smart_suggestion(self):
        """Get personalized timing suggestion for this category"""
        if self.pattern_confidence < 30:
            return "Not enough data for personalized suggestions yet"

        if self.optimal_timing_suggestion:
            disclaimer = " (This is based on your past behavior - feel free to adjust as needed)"
            return self.optimal_timing_suggestion + disclaimer

        return "Continue with your preferred timing"


# Import approval workflow models
from .approval_models import BudgetChangeRequest, BudgetChangeVote, ChangeHistoryLog
