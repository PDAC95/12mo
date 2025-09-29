import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ..models import Budget, BudgetCategory, BudgetSplit, ActualExpense
from ..utils.deletion_utils import BudgetDeletionUtils
from spaces.models import Space, SpaceMember

User = get_user_model()


class BudgetDeletionPermissionsTest(TestCase):
    """Test suite for budget deletion permissions and security"""

    def setUp(self):
        """Set up test data"""
        # Create users with different roles
        self.space_owner = User.objects.create_user(
            username='space_owner',
            email='owner@test.com',
            password='testpass123'
        )
        self.space_admin = User.objects.create_user(
            username='space_admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.budget_creator = User.objects.create_user(
            username='budget_creator',
            email='creator@test.com',
            password='testpass123'
        )
        self.assigned_user = User.objects.create_user(
            username='assigned_user',
            email='assigned@test.com',
            password='testpass123'
        )
        self.regular_member = User.objects.create_user(
            username='regular_member',
            email='member@test.com',
            password='testpass123'
        )
        self.inactive_member = User.objects.create_user(
            username='inactive_member',
            email='inactive@test.com',
            password='testpass123'
        )
        self.non_member = User.objects.create_user(
            username='non_member',
            email='nonmember@test.com',
            password='testpass123'
        )

        # Create space
        self.space = Space.objects.create(
            name='Test Space',
            description='Test space for permission testing',
            created_by=self.space_owner
        )

        # Create space members with different roles
        SpaceMember.objects.create(
            space=self.space,
            user=self.space_owner,
            role='owner',
            is_active=True
        )
        SpaceMember.objects.create(
            space=self.space,
            user=self.space_admin,
            role='admin',
            is_active=True
        )
        SpaceMember.objects.create(
            space=self.space,
            user=self.budget_creator,
            role='member',
            is_active=True
        )
        SpaceMember.objects.create(
            space=self.space,
            user=self.assigned_user,
            role='member',
            is_active=True
        )
        SpaceMember.objects.create(
            space=self.space,
            user=self.regular_member,
            role='member',
            is_active=True
        )
        SpaceMember.objects.create(
            space=self.space,
            user=self.inactive_member,
            role='member',
            is_active=False  # Inactive member
        )
        # non_member is not added to the space

        # Create budget category
        self.category = BudgetCategory.objects.create(
            name='Test Category',
            space=self.space,
            created_by=self.space_owner
        )

        # Create budget created by budget_creator and assigned to assigned_user
        self.budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('500.00'),
            month_period='2024-09',
            created_by=self.budget_creator,
            assigned_to=self.assigned_user
        )

    def test_space_owner_can_delete_any_budget(self):
        """Test that space owner can delete any budget in their space"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.space_owner
        )
        self.assertTrue(has_permission)
        self.assertIn('owner', message.lower())

    def test_space_admin_can_delete_any_budget(self):
        """Test that space admin can delete any budget in their space"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.space_admin
        )
        self.assertTrue(has_permission)
        self.assertIn('admin', message.lower())

    def test_budget_creator_can_delete_own_budget(self):
        """Test that budget creator can delete their own budget"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.budget_creator
        )
        self.assertTrue(has_permission)
        self.assertIn('creator', message.lower())

    def test_assigned_user_can_delete_assigned_budget(self):
        """Test that user assigned to budget can delete it"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.assigned_user
        )
        self.assertTrue(has_permission)
        self.assertIn('assigned', message.lower())

    def test_regular_member_cannot_delete_unrelated_budget(self):
        """Test that regular member cannot delete budget they didn't create and aren't assigned to"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.regular_member
        )
        self.assertFalse(has_permission)
        self.assertIn('permission', message.lower())

    def test_inactive_member_cannot_delete_budget(self):
        """Test that inactive space member cannot delete budget"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.inactive_member
        )
        self.assertFalse(has_permission)
        self.assertIn('not a member', message.lower())

    def test_non_member_cannot_delete_budget(self):
        """Test that non-space member cannot delete budget"""
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.non_member
        )
        self.assertFalse(has_permission)
        self.assertIn('not a member', message.lower())

    def test_api_deletion_permission_enforcement_non_member(self):
        """Test API enforces permissions for non-members"""
        self.client.login(username='non_member', password='testpass123')

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

    def test_api_deletion_permission_enforcement_regular_member(self):
        """Test API enforces permissions for regular members"""
        self.client.login(username='regular_member', password='testpass123')

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

    def test_api_deletion_success_for_owner(self):
        """Test API allows deletion for space owner"""
        self.client.login(username='space_owner', password='testpass123')

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

    def test_api_deletion_success_for_admin(self):
        """Test API allows deletion for space admin"""
        self.client.login(username='space_admin', password='testpass123')

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

    def test_api_deletion_success_for_creator(self):
        """Test API allows deletion for budget creator"""
        self.client.login(username='budget_creator', password='testpass123')

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

    def test_api_deletion_success_for_assigned_user(self):
        """Test API allows deletion for assigned user"""
        self.client.login(username='assigned_user', password='testpass123')

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

    def test_summary_view_permission_check(self):
        """Test deletion summary view includes permission check"""
        # Test for authorized user
        self.client.login(username='space_owner', password='testpass123')
        url = reverse('budgets:deletion_summary', kwargs={'budget_id': self.budget.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['summary']['can_delete'])

        # Test for unauthorized user
        self.client.login(username='non_member', password='testpass123')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['summary']['can_delete'])
        self.assertIn('permission_error', data['summary'])

    def test_permission_validation_with_budget_splits(self):
        """Test permission validation when user has budget split but isn't creator/assigned"""
        # Create budget split for regular member
        BudgetSplit.objects.create(
            budget=self.budget,
            user=self.regular_member,
            percentage=Decimal('25.00'),
            calculated_amount=Decimal('125.00')
        )

        # Regular member still shouldn't be able to delete
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.regular_member
        )
        self.assertFalse(has_permission)

    def test_permission_validation_with_expenses(self):
        """Test permission validation when user has paid expenses but isn't creator/assigned"""
        # Create expense paid by regular member
        ActualExpense.objects.create(
            budget_item=self.budget,
            actual_amount=Decimal('100.00'),
            date_paid=timezone.now().date(),
            paid_by=self.regular_member,
            description='Test expense'
        )

        # Regular member still shouldn't be able to delete
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            self.budget, self.regular_member
        )
        self.assertFalse(has_permission)

    def test_cross_space_permission_isolation(self):
        """Test that users cannot delete budgets from spaces they don't belong to"""
        # Create another space and user
        other_space = Space.objects.create(
            name='Other Space',
            description='Another space',
            created_by=self.space_owner
        )

        other_user = User.objects.create_user(
            username='other_user',
            email='other@test.com',
            password='testpass123'
        )

        SpaceMember.objects.create(
            space=other_space,
            user=other_user,
            role='owner',
            is_active=True
        )

        other_category = BudgetCategory.objects.create(
            name='Other Category',
            space=other_space,
            created_by=other_user
        )

        other_budget = Budget.objects.create(
            space=other_space,
            category=other_category,
            amount=Decimal('300.00'),
            month_period='2024-09',
            created_by=other_user
        )

        # space_owner should not be able to delete budget from other_space
        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            other_budget, self.space_owner
        )
        self.assertFalse(has_permission)
        self.assertIn('not a member', message.lower())

    def test_deleted_budget_permission_validation(self):
        """Test permission validation for already deleted budget"""
        # Soft delete the budget
        self.budget.soft_delete(deleted_by=self.space_owner)

        # Even owner should not be able to delete again (handled by safety validation)
        is_safe, errors = BudgetDeletionUtils.validate_deletion_safety(self.budget)
        self.assertFalse(is_safe)
        self.assertTrue(any('already deleted' in error for error in errors))

    def test_permission_validation_exception_handling(self):
        """Test permission validation handles exceptions gracefully"""
        # Create a mock budget with invalid space reference
        mock_budget = Budget(
            id=999,
            space_id=999,  # Non-existent space
            category=self.category,
            amount=Decimal('100.00'),
            month_period='2024-09',
            created_by=self.space_owner
        )

        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            mock_budget, self.space_owner
        )
        self.assertFalse(has_permission)
        self.assertIn('validation failed', message.lower())

    def test_multiple_role_hierarchy(self):
        """Test permission hierarchy when user has multiple potential permissions"""
        # Create a budget where user is both creator and assigned
        multi_role_budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('400.00'),
            month_period='2024-10',
            created_by=self.assigned_user,  # User is creator
            assigned_to=self.assigned_user  # User is also assigned
        )

        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            multi_role_budget, self.assigned_user
        )
        self.assertTrue(has_permission)
        # Should return the first valid reason (creator in this case)
        self.assertIn('creator', message.lower())

    def test_space_role_vs_budget_role_priority(self):
        """Test that space admin role takes priority over other permissions"""
        # Create budget where admin is neither creator nor assigned
        admin_test_budget = Budget.objects.create(
            space=self.space,
            category=self.category,
            amount=Decimal('600.00'),
            month_period='2024-11',
            created_by=self.regular_member,
            assigned_to=self.regular_member
        )

        has_permission, message = BudgetDeletionUtils.validate_user_permission(
            admin_test_budget, self.space_admin
        )
        self.assertTrue(has_permission)
        self.assertIn('admin', message.lower())

    def test_unauthenticated_api_access(self):
        """Test that unauthenticated users cannot access deletion APIs"""
        # Don't log in
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

        # Should redirect to login or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])

        # Test summary endpoint
        url = reverse('budgets:deletion_summary', kwargs={'budget_id': self.budget.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 401, 403])