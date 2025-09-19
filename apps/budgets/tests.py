from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from spaces.models import Space, SpaceMember
from .models import Budget, BudgetCategory, BudgetTemplate, SpendingBehaviorAnalysis, ActualExpense

User = get_user_model()


class TimingSystemTestCase(TestCase):
    """Test cases for the new timing system in budgets"""

    def setUp(self):
        """Set up test data"""
        # Create test user and space
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.space = Space.objects.create(
            name='Test Family',
            description='Test space for timing system',
            created_by=self.user
        )
        SpaceMember.objects.create(
            space=self.space,
            user=self.user,
            role='owner',
            is_active=True
        )

        # Create test category
        self.category = BudgetCategory.objects.create(
            name='Test Category',
            description='Test category for timing',
            icon='home',
            category_type='fixed',
            is_system_default=True
        )

    def test_fixed_date_budget_creation(self):
        """Test creating a budget with fixed date timing"""
        due_date = date.today() + timedelta(days=15)

        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('1200.00'),
            month_period='2025-09',
            timing_type='fixed_date',
            due_date=due_date,
            is_recurring=True,
            recurrence_pattern='monthly_same_date',
            created_by=self.user
        )

        self.assertEqual(budget.timing_type, 'fixed_date')
        self.assertEqual(budget.due_date, due_date)
        self.assertEqual(budget.timing_display, f"Due: {due_date.strftime('%B %d')}")
        self.assertIsNotNone(budget.days_until_due)

    def test_date_range_budget_creation(self):
        """Test creating a budget with date range timing"""
        start_date = date.today() + timedelta(days=5)
        end_date = date.today() + timedelta(days=12)

        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('400.00'),
            month_period='2025-09',
            timing_type='date_range',
            range_start=start_date,
            range_end=end_date,
            range_description='First week of month',
            is_recurring=True,
            recurrence_pattern='monthly_same_range',
            created_by=self.user
        )

        self.assertEqual(budget.timing_type, 'date_range')
        self.assertEqual(budget.range_start, start_date)
        self.assertEqual(budget.range_end, end_date)
        self.assertIn('First week of month', budget.timing_display)

    def test_flexible_budget_creation(self):
        """Test creating a budget with flexible timing"""
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('200.00'),
            month_period='2025-09',
            timing_type='flexible',
            is_recurring=True,
            recurrence_pattern='monthly_flexible',
            created_by=self.user
        )

        self.assertEqual(budget.timing_type, 'flexible')
        self.assertEqual(budget.timing_display, 'Flexible timing')
        self.assertEqual(budget.timing_status, 'flexible')

    def test_timing_validation(self):
        """Test timing field validation"""
        # Test fixed_date without due_date should fail
        with self.assertRaises(ValidationError):
            budget = Budget(
                space=self.space,
                category=self.category,
                amount=Decimal('100.00'),
                month_period='2025-09',
                timing_type='fixed_date',
                created_by=self.user
            )
            budget.full_clean()

        # Test date_range without proper dates should fail
        with self.assertRaises(ValidationError):
            budget = Budget(
                space=self.space,
                category=self.category,
                amount=Decimal('100.00'),
                month_period='2025-09',
                timing_type='date_range',
                range_start=date.today(),
                created_by=self.user
            )
            budget.full_clean()

    def test_timing_status_calculation(self):
        """Test timing status calculation"""
        # Create another category to avoid unique constraint
        overdue_category = BudgetCategory.objects.create(
            name='Overdue Test Category',
            description='Test category for overdue',
            icon='home',
            category_type='fixed',
            is_system_default=True
        )

        # Test overdue status
        overdue_budget = Budget.objects.create(
            space=self.space,
            category=overdue_category,
            amount=Decimal('100.00'),
            month_period='2025-09',
            timing_type='fixed_date',
            due_date=date.today() - timedelta(days=1),
            created_by=self.user
        )
        self.assertEqual(overdue_budget.timing_status, 'overdue')

        # Create another category for due today test
        due_today_category = BudgetCategory.objects.create(
            name='Due Today Test Category',
            description='Test category for due today',
            icon='home',
            category_type='fixed',
            is_system_default=True
        )

        # Test due today status
        due_today_budget = Budget.objects.create(
            space=self.space,
            category=due_today_category,
            amount=Decimal('100.00'),
            month_period='2025-09',
            timing_type='fixed_date',
            due_date=date.today(),
            created_by=self.user
        )
        self.assertEqual(due_today_budget.timing_status, 'due_today')

    def test_actual_spend_date_recording(self):
        """Test recording actual spend dates for pattern analysis"""
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('100.00'),
            month_period='2025-09',
            timing_type='flexible',
            created_by=self.user
        )

        spend_date = date.today()
        budget.record_actual_spend_date(spend_date)

        self.assertIn(spend_date.isoformat(), budget.actual_spend_dates)


class BudgetTemplateTestCase(TestCase):
    """Test cases for BudgetTemplate model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.space = Space.objects.create(
            name='Test Space',
            created_by=self.user
        )
        self.category = BudgetCategory.objects.create(
            name='Housing & Rent',
            is_system_default=True
        )

    def test_system_template_creation(self):
        """Test creating system default templates"""
        template = BudgetTemplate.objects.create(
            name='Monthly Rent Template',
            description='Template for monthly rent payments',
            template_type='bill',
            default_category=self.category,
            suggested_amount=Decimal('1200.00'),
            default_timing_type='fixed_date',
            default_is_recurring=True,
            default_recurrence_pattern='monthly_same_date',
            is_system_default=True
        )

        self.assertTrue(template.is_system_default)
        self.assertEqual(template.template_type, 'bill')
        self.assertEqual(template.usage_count, 0)

    def test_custom_template_creation(self):
        """Test creating custom space templates"""
        template = BudgetTemplate.objects.create(
            name='Custom Grocery Template',
            description='Our family grocery budget',
            template_type='grocery',
            default_category=self.category,
            suggested_amount=Decimal('150.00'),
            default_timing_type='date_range',
            space=self.space,
            created_by=self.user
        )

        self.assertFalse(template.is_system_default)
        self.assertEqual(template.space, self.space)
        self.assertEqual(template.created_by, self.user)

    def test_template_validation(self):
        """Test template validation rules"""
        # System template with space should fail
        with self.assertRaises(ValidationError):
            template = BudgetTemplate(
                name='Invalid Template',
                template_type='bill',
                default_category=self.category,
                default_timing_type='fixed_date',
                is_system_default=True,
                space=self.space
            )
            template.full_clean()

        # Custom template without space should fail
        with self.assertRaises(ValidationError):
            template = BudgetTemplate(
                name='Invalid Template',
                template_type='bill',
                default_category=self.category,
                default_timing_type='fixed_date',
                is_system_default=False
            )
            template.full_clean()

    def test_template_usage_tracking(self):
        """Test template usage counter"""
        template = BudgetTemplate.objects.create(
            name='Test Template',
            template_type='bill',
            default_category=self.category,
            default_timing_type='fixed_date',
            is_system_default=True
        )

        initial_count = template.usage_count
        template.increment_usage()
        template.refresh_from_db()

        self.assertEqual(template.usage_count, initial_count + 1)

    def test_create_system_defaults(self):
        """Test creating system default templates"""
        # Ensure we have the required categories
        BudgetCategory.objects.get_or_create(
            name='Food & Groceries',
            defaults={'is_system_default': True}
        )
        BudgetCategory.objects.get_or_create(
            name='Utilities',
            defaults={'is_system_default': True}
        )
        BudgetCategory.objects.get_or_create(
            name='Other',
            defaults={'is_system_default': True}
        )

        initial_count = BudgetTemplate.objects.count()
        BudgetTemplate.create_system_defaults()
        final_count = BudgetTemplate.objects.count()

        self.assertGreater(final_count, initial_count)
        self.assertTrue(
            BudgetTemplate.objects.filter(
                name='Monthly Rent/Mortgage',
                is_system_default=True
            ).exists()
        )


class SpendingBehaviorAnalysisTestCase(TestCase):
    """Test cases for SpendingBehaviorAnalysis model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.space = Space.objects.create(
            name='Test Space',
            created_by=self.user
        )
        self.category = BudgetCategory.objects.create(
            name='Test Category',
            is_system_default=True
        )
        self.budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('100.00'),
            month_period='2025-09',
            created_by=self.user
        )

    def test_behavior_analysis_creation(self):
        """Test creating spending behavior analysis"""
        analysis = SpendingBehaviorAnalysis.objects.create(
            user=self.user,
            space=self.space,
            category=self.category,
            preferred_day_of_week=3,  # Wednesday
            pattern_confidence=75.5,
            data_points_count=10
        )

        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.preferred_day_of_week, 3)
        self.assertEqual(analysis.pattern_confidence, Decimal('75.5'))

    def test_smart_suggestion_generation(self):
        """Test smart suggestion generation"""
        # Create separate categories for each test to avoid unique constraint
        low_confidence_category = BudgetCategory.objects.create(
            name='Low Confidence Category',
            is_system_default=True
        )
        high_confidence_category = BudgetCategory.objects.create(
            name='High Confidence Category',
            is_system_default=True
        )

        # Low confidence analysis
        low_confidence_analysis = SpendingBehaviorAnalysis.objects.create(
            user=self.user,
            space=self.space,
            category=low_confidence_category,
            pattern_confidence=20.0
        )
        suggestion = low_confidence_analysis.get_smart_suggestion()
        self.assertIn('Not enough data', suggestion)

        # High confidence analysis
        high_confidence_analysis = SpendingBehaviorAnalysis.objects.create(
            user=self.user,
            space=self.space,
            category=high_confidence_category,
            pattern_confidence=80.0,
            optimal_timing_suggestion='You typically spend on Wednesdays'
        )
        suggestion = high_confidence_analysis.get_smart_suggestion()
        self.assertIn('Wednesdays', suggestion)
        self.assertIn('based on your past behavior', suggestion)

    def test_unique_constraint(self):
        """Test unique constraint on user/space/category"""
        SpendingBehaviorAnalysis.objects.create(
            user=self.user,
            space=self.space,
            category=self.category
        )

        # Creating another analysis for same user/space/category should fail
        with self.assertRaises(Exception):  # IntegrityError or similar
            SpendingBehaviorAnalysis.objects.create(
                user=self.user,
                space=self.space,
                category=self.category
            )


class IntegrationTestCase(TestCase):
    """Integration tests for timing system"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.space = Space.objects.create(
            name='Test Space',
            created_by=self.user
        )
        self.category = BudgetCategory.objects.create(
            name='Test Category',
            is_system_default=True
        )

    def test_complete_budget_timing_workflow(self):
        """Test complete workflow from template to budget with timing"""
        # 1. Create template
        template = BudgetTemplate.objects.create(
            name='Test Bill Template',
            template_type='bill',
            default_category=self.category,
            suggested_amount=Decimal('500.00'),
            default_timing_type='fixed_date',
            default_is_recurring=True,
            default_recurrence_pattern='monthly_same_date',
            is_system_default=True
        )

        # 2. Create budget using template defaults
        due_date = date.today() + timedelta(days=10)
        budget = Budget.objects.create(
            space=self.space,
            category=template.default_category,
            amount=template.suggested_amount,
            month_period='2025-09',
            timing_type=template.default_timing_type,
            due_date=due_date,
            is_recurring=template.default_is_recurring,
            recurrence_pattern=template.default_recurrence_pattern,
            created_by=self.user
        )

        # 3. Track template usage
        template.increment_usage()

        # 4. Add user to space as member
        from spaces.models import SpaceMember
        SpaceMember.objects.create(
            space=self.space,
            user=self.user,
            role='owner',
            is_active=True
        )

        # 5. Create actual expense
        expense = ActualExpense.objects.create(
            budget_item=budget,
            actual_amount=Decimal('500.00'),
            date_paid=date.today(),
            paid_by=self.user,
            description='Test payment'
        )

        # 5. Record spend date for behavior analysis
        budget.record_actual_spend_date(expense.date_paid)

        # Verify everything works together
        self.assertEqual(template.usage_count, 1)
        self.assertEqual(budget.timing_type, 'fixed_date')
        self.assertIn(expense.date_paid.isoformat(), budget.actual_spend_dates)
        self.assertEqual(budget.total_spent, Decimal('500.00'))

    def test_budget_timing_status_progression(self):
        """Test timing status changes over time"""
        # Create budget due in 5 days
        future_date = date.today() + timedelta(days=5)
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('100.00'),
            month_period='2025-09',
            timing_type='fixed_date',
            due_date=future_date,
            reminder_days_before=3,
            created_by=self.user
        )

        # Should be upcoming (more than 3 days away)
        # Note: This test assumes the budget is created more than 3 days before due date
        if budget.days_until_due > 3:
            self.assertEqual(budget.timing_status, 'upcoming')
        elif budget.days_until_due <= 3:
            self.assertEqual(budget.timing_status, 'due_soon')

        # Test days until due calculation
        self.assertEqual(budget.days_until_due, (future_date - date.today()).days)
