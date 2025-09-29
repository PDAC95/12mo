from django.db import models
from django.utils import timezone


class BudgetManager(models.Manager):
    """Custom manager for Budget model with soft delete functionality"""

    def active(self):
        """Get only active (non-deleted) budgets"""
        return self.filter(deleted_at__isnull=True, is_active=True)

    def deleted(self):
        """Get only soft-deleted budgets"""
        return self.filter(deleted_at__isnull=False)

    def all_including_deleted(self):
        """Get all budgets including soft-deleted ones"""
        return self.get_queryset()

    def hard_delete(self, pk):
        """Permanently delete a budget (use with caution)"""
        return self.filter(pk=pk).delete()

    def restore(self, pk, restored_by=None):
        """Restore a soft-deleted budget"""
        budget = self.filter(pk=pk, deleted_at__isnull=False).first()
        if budget:
            budget.deleted_at = None
            budget.deleted_by = None
            budget.is_active = True
            budget.save(update_fields=['deleted_at', 'deleted_by', 'is_active'])
            return budget
        return None

    def soft_delete(self, pk, deleted_by=None):
        """Soft delete a budget"""
        budget = self.filter(pk=pk, deleted_at__isnull=True).first()
        if budget:
            budget.deleted_at = timezone.now()
            budget.deleted_by = deleted_by
            budget.is_active = False
            budget.save(update_fields=['deleted_at', 'deleted_by', 'is_active'])
            return budget
        return None

    def get_with_deleted(self, pk):
        """Get a budget by pk including soft-deleted ones"""
        return self.all_including_deleted().filter(pk=pk).first()