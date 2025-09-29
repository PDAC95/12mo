import json
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from unittest.mock import patch, MagicMock

from ..models import Budget, BudgetCategory, BudgetSplit, ActualExpense
from ..utils.deletion_utils import BudgetDeletionUtils
from ..serializers.delete_serializers import (
    BudgetDeleteRequestSerializer,
    BudgetDeleteResponseSerializer,
    BudgetDeletionSummarySerializer
)
from spaces.models import Space, SpaceMember

User = get_user_model()


class BudgetDeletionUtilsTest(TestCase):
    """Test suite for BudgetDeletionUtils functionality"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='testpass123'
        )
        self.outsider = User.objects.create_user(
            username='outsider',
            email='outsider@test.com',
            password='testpass123'
        )

        # Create space
        self.space = Space.objects.create(
            name='Test Space',
            description='Test space for budget deletion',
            created_by=self.owner
        )

        # Create space members
        SpaceMember.objects.create(
            space=self.space,
            user=self.owner,
            role='owner',
            is_active=True
        )
        SpaceMember.objects.create(
            space=self.space,
            user=self.member,
            role='member',
            is_active=True
        )

        # Create budget category
        self.category = BudgetCategory.objects.create(
            name='Test Category',
            space=self.space,
            created_by=self.owner
        )

        # Create budget
        self.budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('500.00'),
            month_period='2024-09',
            created_by=self.owner
        )

    def test_validate_user_permission_owner(self):
        """Test permission validation for space owner"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.owner
        )
        self.assertTrue(has_permission)
        self.assertIn('owner', message.lower())

    def test_validate_user_permission_member_creator(self):
        """Test permission validation for budget creator"""
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('300.00'),
            month_period='2024-10',
            created_by=self.member
        )

        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            budget, self.member
        )
        self.assertTrue(has_permission)
        self.assertIn('creator', message.lower())

    def test_validate_user_permission_outsider(self):
        """Test permission validation for non-member"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.outsider
        )
        self.assertFalse(has_permission)
        self.assertIn('not a member', message.lower())

    def test_validate_user_permission_assigned_user(self):
        """Test permission validation for assigned user"""
        self.budget.assigned_to = self.member
        self.budget.save()

        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.member
        )
        self.assertTrue(has_permission)
        self.assertIn('assigned', message.lower())

    def test_get_deletion_summary_empty_budget(self):
        """Test deletion summary for budget with no splits or expenses"""
        summary = BudgetDeletionUtils.get_deletion_summary(self.budget)

        self.assertEqual(summary['budget_id'], self.budget.id)
        self.assertEqual(summary['total_splits'], 0)
        self.assertEqual(summary['total_expenses'], 0)
        self.assertEqual(summary['total_expense_amount'], Decimal('0.00'))
        self.assertEqual(summary['affected_users'], [])

    def test_get_deletion_summary_with_splits_and_expenses(self):
        """Test deletion summary for budget with splits and expenses"""
        # Create budget splits
        BudgetSplit.objects.create(
            budget=self.budget,
            user=self.owner,
            percentage=Decimal('60.00'),
            calculated_amount=Decimal('300.00')
        )
        BudgetSplit.objects.create(
            budget=self.budget,
            user=self.member,
            percentage=Decimal('40.00'),
            calculated_amount=Decimal('200.00')
        )

        # Create actual expenses
        ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('150.00'),
            date_paid=timezone.now().date(),
            paid_by=self.owner,
            description='Test expense 1'
        )
        ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('75.00'),
            date_paid=timezone.now().date(),
            paid_by=self.member,
            description='Test expense 2'
        )

        summary = BudgetDeletionUtils.get_deletion_summary(self.budget)

        self.assertEqual(summary['total_splits'], 2)
        self.assertEqual(summary['total_expenses'], 2)
        self.assertEqual(summary['total_expense_amount'], Decimal('225.00'))
        self.assertIn(self.owner.username, summary['affected_users'])
        self.assertIn(self.member.username, summary['affected_users'])
        self.assertTrue(len(summary['warning_messages']) > 0)

    def test_validate_deletion_safety_with_high_expenses(self):
        """Test deletion safety validation with high-value expenses"""
        # Create high-value expense
        ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('1500.00'),
            date_paid=timezone.now().date(),
            paid_by=self.owner,
            description='High value expense'
        )

        is_safe, errors = BudgetDeletionUtils.validate_deletion_safety(self.budget)

        self.assertFalse(is_safe)
        self.assertTrue(any('significant expenses' in error for error in errors))

    def test_validate_deletion_safety_with_recent_activity(self):
        """Test deletion safety validation with recent expenses"""
        # Create recent expense
        ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('100.00'),
            date_paid=timezone.now().date(),
            paid_by=self.owner,
            description='Recent expense'
        )

        is_safe, errors = BudgetDeletionUtils.validate_deletion_safety(self.budget)

        self.assertFalse(is_safe)
        self.assertTrue(any('recent activity' in error for error in errors))

    def test_get_affected_users_detail(self):
        """Test detailed affected users information"""
        # Create splits and expenses
        BudgetSplit.objects.create(
            budget=self.budget,
            user=self.owner,
            percentage=Decimal('60.00'),
            calculated_amount=Decimal('300.00')
        )
        ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('150.00'),
            date_paid=timezone.now().date(),
            paid_by=self.member,
            description='Test expense'
        )

        affected_users = BudgetDeletionUtils.get_affected_users_detail(self.budget)

        # Should have 2 users
        self.assertEqual(len(affected_users), 2)

        # Find owner and member in results
        owner_data = next((u for u in affected_users if u['user_id'] == self.owner.id), None)
        member_data = next((u for u in affected_users if u['user_id'] == self.member.id), None)

        self.assertIsNotNone(owner_data)
        self.assertIsNotNone(member_data)

        # Check owner data
        self.assertEqual(owner_data['split_amount'], Decimal('300.00'))
        self.assertEqual(owner_data['expense_count'], 0)

        # Check member data
        self.assertEqual(member_data['expense_count'], 1)
        self.assertEqual(member_data['expense_amount'], Decimal('150.00'))


class BudgetDeletionTransactionTest(TransactionTestCase):
    """Test suite for budget deletion with transaction handling"""

    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123'
        )

        self.space = Space.objects.create(
            name='Test Space',
            description='Test space',
            created_by=self.owner
        )

        SpaceMember.objects.create(
            space=self.space,
            user=self.owner,
            role='owner',
            is_active=True
        )

        self.category = BudgetCategory.objects.create(
            name='Test Category',
            space=self.space,
            created_by=self.owner
        )

        self.budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('500.00'),
            month_period='2024-09',
            created_by=self.owner
        )

    def test_perform_soft_deletion(self):
        """Test soft deletion functionality"""
        # Create related objects
        budget_split = BudgetSplit.objects.create(
            budget=self.budget,
            user=self.owner,
            percentage=Decimal('100.00'),
            calculated_amount=Decimal('500.00')
        )
        expense = ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('200.00'),
            date_paid=timezone.now().date(),
            paid_by=self.owner
        )

        # Perform soft deletion
        result = BudgetDeletionUtils.perform_deletion(
            budget=self.budget,
            user=self.owner,
            soft_delete=True,
            notify_members=True
        )

        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['deleted_splits'], 1)
        self.assertEqual(result['deleted_expenses'], 1)

        # Refresh budget from database
        self.budget.refresh_from_db()
        self.assertTrue(self.budget.is_deleted)
        self.assertIsNotNone(self.budget.deleted_at)
        self.assertEqual(self.budget.deleted_by, self.owner)

        # Related objects should still exist
        self.assertTrue(BudgetSplit.objects.filter(budget=self.budget).exists())
        self.assertTrue(ActualExpense.objects.filter(budget_item=self.budget).exists())

    def test_perform_hard_deletion(self):
        """Test hard deletion functionality"""
        # Create related objects
        budget_split = BudgetSplit.objects.create(
            budget=self.budget,
            user=self.owner,
            percentage=Decimal('100.00'),
            calculated_amount=Decimal('500.00')
        )
        expense = ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('200.00'),
            date_paid=timezone.now().date(),
            paid_by=self.owner
        )

        budget_id = self.budget.id

        # Perform hard deletion
        result = BudgetDeletionUtils.perform_deletion(
            budget=self.budget,
            user=self.owner,
            soft_delete=False,
            notify_members=True
        )

        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['deleted_splits'], 1)
        self.assertEqual(result['deleted_expenses'], 1)

        # Budget should be completely deleted
        self.assertFalse(Budget.objects.filter(id=budget_id).exists())

        # Related objects should also be deleted (cascade)
        self.assertFalse(BudgetSplit.objects.filter(budget_id=budget_id).exists())
        self.assertFalse(ActualExpense.objects.filter(budget_item_id=budget_id).exists())

    @patch('apps.budgets.utils.deletion_utils.logger')
    def test_deletion_with_exception(self, mock_logger):
        """Test deletion behavior when exception occurs"""
        with patch.object(Budget, 'delete', side_effect=Exception('Database error')):
            result = BudgetDeletionUtils.perform_deletion(
                budget=self.budget,
                user=self.owner,
                soft_delete=False,
                notify_members=True
            )

            self.assertFalse(result['success'])
            self.assertIn('Database error', result['message'])
            mock_logger.error.assert_called()


class BudgetDeleteSerializerTest(TestCase):
    """Test suite for budget deletion serializers"""

    def test_budget_delete_request_serializer_valid(self):
        """Test valid budget delete request serialization"""
        data = {
            'confirmation_text': 'ELIMINAR',
            'notify_members': True,
            'soft_delete': False
        }

        serializer = BudgetDeleteRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['confirmation_text'], 'ELIMINAR')

    def test_budget_delete_request_serializer_invalid_confirmation(self):
        """Test invalid confirmation text"""
        data = {
            'confirmation_text': 'DELETE',
            'notify_members': True,
            'soft_delete': False
        }

        serializer = BudgetDeleteRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirmation_text', serializer.errors)

    def test_budget_delete_response_serializer(self):
        """Test budget delete response serialization"""
        data = {
            'success': True,
            'message': 'Budget deleted successfully',
            'deleted_splits': 2,
            'deleted_expenses': 3,
            'budget_id': 123,
            'space_id': 456,
            'category_name': 'Food',
            'month_period': '2024-09',
            'deleted_at': timezone.now(),
            'audit_log_id': 789
        }

        serializer = BudgetDeleteResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_budget_deletion_summary_serializer(self):
        """Test budget deletion summary serialization"""
        data = {
            'budget_id': 123,
            'budget_amount': Decimal('500.00'),
            'category_name': 'Food',
            'month_period': '2024-09',
            'space_name': 'Test Space',
            'total_splits': 2,
            'total_expenses': 3,
            'total_expense_amount': Decimal('250.00'),
            'affected_users': ['user1', 'user2'],
            'can_delete': True,
            'warning_messages': ['Warning message']
        }

        serializer = BudgetDeletionSummarySerializer(data=data)
        self.assertTrue(serializer.is_valid())


class BudgetDeleteViewTest(TestCase):
    """Test suite for budget deletion views"""

    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123'
        )

        self.space = Space.objects.create(
            name='Test Space',
            description='Test space',
            created_by=self.owner
        )

        SpaceMember.objects.create(
            space=self.space,
            user=self.owner,
            role='owner',
            is_active=True
        )

        self.category = BudgetCategory.objects.create(
            name='Test Category',
            space=self.space,
            created_by=self.owner
        )

        self.budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('500.00'),
            month_period='2024-09',
            created_by=self.owner
        )

    def test_budget_deletion_summary_view_success(self):
        """Test successful budget deletion summary retrieval"""
        self.client.login(username='owner', password='testpass123')

        url = reverse('budgets:deletion_summary', kwargs={'budget_id': self.budget.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('summary', data)
        self.assertEqual(data['summary']['budget_id'], self.budget.id)

    def test_budget_deletion_summary_view_not_found(self):
        """Test budget deletion summary for non-existent budget"""
        self.client.login(username='owner', password='testpass123')

        url = reverse('budgets:deletion_summary', kwargs={'budget_id': 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_budget_delete_api_view_success(self):
        """Test successful budget deletion via API"""
        self.client.login(username='owner', password='testpass123')

        url = reverse('budgets:delete_api', kwargs={'budget_id': self.budget.id})
        data = {
            'confirmation_text': 'ELIMINAR',
            'notify_members': True,
            'soft_delete': True
        }

        response = self.client.delete(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertTrue(response_data['success'])

        # Check that budget was soft deleted
        self.budget.refresh_from_db()
        self.assertTrue(self.budget.is_deleted)

    def test_budget_delete_api_view_invalid_confirmation(self):
        """Test budget deletion with invalid confirmation text"""
        self.client.login(username='owner', password='testpass123')

        url = reverse('budgets:delete_api', kwargs={'budget_id': self.budget.id})
        data = {
            'confirmation_text': 'DELETE',
            'notify_members': True,
            'soft_delete': True
        }

        response = self.client.delete(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('errors', response_data)

    def test_budget_delete_api_view_unauthorized(self):
        """Test budget deletion by unauthorized user"""
        outsider = User.objects.create_user(
            username='outsider',
            email='outsider@test.com',
            password='testpass123'
        )

        self.client.login(username='outsider', password='testpass123')

        url = reverse('budgets:delete_api', kwargs={'budget_id': self.budget.id})
        data = {
            'confirmation_text': 'ELIMINAR',
            'notify_members': True,
            'soft_delete': True
        }

        response = self.client.delete(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)

        response_data = response.json()
        self.assertFalse(response_data['success'])

    def test_budget_delete_api_view_not_found(self):
        """Test budget deletion for non-existent budget"""
        self.client.login(username='owner', password='testpass123')

        url = reverse('budgets:delete_api', kwargs={'budget_id': 99999})
        data = {
            'confirmation_text': 'ELIMINAR',
            'notify_members': True,
            'soft_delete': True
        }

        response = self.client.delete(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    @patch('apps.budgets.views.delete_views.BudgetDeletionUtils.perform_deletion')
    def test_budget_delete_api_view_server_error(self, mock_perform_deletion):
        """Test budget deletion with server error"""
        mock_perform_deletion.return_value = {
            'success': False,
            'message': 'Database connection failed'
        }

        self.client.login(username='owner', password='testpass123')

        url = reverse('budgets:delete_api', kwargs={'budget_id': self.budget.id})
        data = {
            'confirmation_text': 'ELIMINAR',
            'notify_members': True,
            'soft_delete': True
        }

        response = self.client.delete(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)

        response_data = response.json()
        self.assertFalse(response_data['success'])


class BudgetDeletionEdgeCasesTest(TestCase):
    """Test suite for budget deletion edge cases"""

    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123'
        )

        self.space = Space.objects.create(
            name='Test Space',
            description='Test space',
            created_by=self.owner
        )

        SpaceMember.objects.create(
            space=self.space,
            user=self.owner,
            role='owner',
            is_active=True
        )

        self.category = BudgetCategory.objects.create(
            name='Test Category',
            space=self.space,
            created_by=self.owner
        )

    def test_delete_already_soft_deleted_budget(self):
        """Test deletion of already soft-deleted budget"""
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('500.00'),
            month_period='2024-09',
            created_by=self.owner
        )

        # First soft delete
        budget.soft_delete(deleted_by=self.owner)

        # Try to delete again
        is_safe, errors = BudgetDeletionUtils.validate_deletion_safety(budget)
        self.assertFalse(is_safe)
        self.assertTrue(any('already deleted' in error for error in errors))

    def test_delete_budget_with_large_number_of_splits(self):
        """Test deletion of budget with many splits"""
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('1000.00'),
            month_period='2024-09',
            created_by=self.owner
        )

        # Create multiple users and splits
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            users.append(user)

            SpaceMember.objects.create(
                space=self.space,
                user=user,
                role='member',
                is_active=True
            )

            BudgetSplit.objects.create(
                budget=budget,
                user=user,
                percentage=Decimal('10.00'),
                calculated_amount=Decimal('100.00')
            )

        summary = BudgetDeletionUtils.get_deletion_summary(budget)
        self.assertEqual(summary['total_splits'], 10)
        self.assertEqual(len(summary['affected_users']), 10)

        # Test deletion
        result = BudgetDeletionUtils.perform_deletion(
            budget=budget,
            user=self.owner,
            soft_delete=False,
            notify_members=True
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['deleted_splits'], 10)

    def test_concurrent_deletion_attempt(self):
        """Test concurrent deletion attempts"""
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('500.00'),
            month_period='2024-09',
            created_by=self.owner
        )

        # Simulate first deletion in progress
        with transaction.atomic():
            # Start deletion process
            result1 = BudgetDeletionUtils.perform_deletion(
                budget=budget,
                user=self.owner,
                soft_delete=False,
                notify_members=True
            )

            # Budget should be deleted
            self.assertTrue(result1['success'])

        # Try to delete the already deleted budget
        with self.assertRaises(Budget.DoesNotExist):
            Budget.objects.get(id=budget.id)

    def test_deletion_with_complex_expense_structure(self):
        """Test deletion with complex expense and split structure"""
        budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('1000.00'),
            month_period='2024-09',
            created_by=self.owner
        )

        # Create multiple users
        user1 = User.objects.create_user(username='user1', email='user1@test.com', password='pass')
        user2 = User.objects.create_user(username='user2', email='user2@test.com', password='pass')

        for user in [user1, user2]:
            SpaceMember.objects.create(
                space=self.space,
                user=user,
                role='member',
                is_active=True
            )

        # Create budget splits
        BudgetSplit.objects.create(
            budget=budget,
            user=self.owner,
            percentage=Decimal('50.00'),
            calculated_amount=Decimal('500.00')
        )
        BudgetSplit.objects.create(
            budget=budget,
            user=user1,
            percentage=Decimal('30.00'),
            calculated_amount=Decimal('300.00')
        )
        BudgetSplit.objects.create(
            budget=budget,
            user=user2,
            percentage=Decimal('20.00'),
            calculated_amount=Decimal('200.00')
        )

        # Create expenses with split information
        expense1 = ActualExpense.objects.create(
            budget_item=budget,
            actual_amount=Decimal('400.00'),
            date_paid=timezone.now().date(),
            paid_by=self.owner,
            is_shared=True
        )
        expense2 = ActualExpense.objects.create(
            budget_item=budget,
            actual_amount=Decimal('200.00'),
            date_paid=timezone.now().date(),
            paid_by=user1,
            is_shared=False
        )

        # Test deletion summary
        summary = BudgetDeletionUtils.get_deletion_summary(budget)
        self.assertEqual(summary['total_splits'], 3)
        self.assertEqual(summary['total_expenses'], 2)
        self.assertEqual(summary['total_expense_amount'], Decimal('600.00'))
        self.assertEqual(len(summary['affected_users']), 3)

        # Test affected users detail
        affected_users = BudgetDeletionUtils.get_affected_users_detail(budget)
        self.assertEqual(len(affected_users), 3)

        # Find owner data
        owner_data = next((u for u in affected_users if u['user_id'] == self.owner.id), None)
        self.assertIsNotNone(owner_data)
        self.assertEqual(owner_data['split_amount'], Decimal('500.00'))
        self.assertEqual(owner_data['expense_count'], 1)
        self.assertEqual(owner_data['expense_amount'], Decimal('400.00'))

        # Test deletion
        result = BudgetDeletionUtils.perform_deletion(
            budget=budget,
            user=self.owner,
            soft_delete=False,
            notify_members=True
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['deleted_splits'], 3)
        self.assertEqual(result['deleted_expenses'], 2)