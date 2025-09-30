#!/usr/bin/env python
"""
Rollback script for Budget soft delete implementation

This script helps rollback the soft delete changes if needed.
Run this in case of issues with the soft delete implementation.

Usage:
    python rollback_soft_delete.py

Prerequisites:
    - Django environment must be properly configured
    - Database backup recommended before running
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()


def rollback_migration():
    """Rollback the soft delete migration"""
    print("🔄 Rolling back Budget soft delete migration...")

    try:
        # Rollback to migration 0009 (before soft delete)
        execute_from_command_line(['manage.py', 'migrate', 'budgets', '0009'])
        print("✅ Migration rollback completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration rollback failed: {e}")
        return False


def remove_indexes():
    """Remove soft delete optimization indexes if they exist"""
    print("🗑️  Removing soft delete indexes...")

    with connection.cursor() as cursor:
        try:
            # Remove indexes that were created for soft delete
            cursor.execute("DROP INDEX IF EXISTS idx_budget_deleted_at;")
            cursor.execute("DROP INDEX IF EXISTS idx_budget_active_lookup;")
            print("✅ Indexes removed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to remove indexes: {e}")
            return False


def restore_model_file():
    """Instructions to restore the model file"""
    print("\n📝 Manual steps required:")
    print("1. Remove the soft delete fields from apps/budgets/models.py:")
    print("   - Remove: deleted_at field")
    print("   - Remove: deleted_by field")
    print("   - Remove: objects = BudgetManager() line")
    print("   - Remove: soft_delete(), restore(), is_deleted methods")
    print("\n2. Remove the managers.py file:")
    print("   - Delete: apps/budgets/managers.py")
    print("\n3. Remove the import in models.py:")
    print("   - Remove: from .managers import BudgetManager")


def check_soft_deleted_data():
    """Check if there are any soft-deleted budgets"""
    from apps.budgets.models import Budget

    try:
        deleted_count = Budget.objects.filter(deleted_at__isnull=False).count()
        if deleted_count > 0:
            print(f"⚠️  WARNING: {deleted_count} soft-deleted budgets found!")
            print("   These records will be lost if you proceed with rollback.")

            response = input("Do you want to restore all soft-deleted budgets first? (y/n): ")
            if response.lower() == 'y':
                restored = Budget.objects.filter(deleted_at__isnull=False).update(
                    deleted_at=None,
                    deleted_by=None,
                    is_active=True
                )
                print(f"✅ Restored {restored} soft-deleted budgets")
        else:
            print("✅ No soft-deleted budgets found")
        return True
    except Exception as e:
        print(f"❌ Failed to check soft-deleted data: {e}")
        return False


def main():
    """Main rollback process"""
    print("🚨 Budget Soft Delete Rollback Script")
    print("=====================================")

    print("\n⚠️  WARNING: This will remove soft delete functionality!")
    print("Make sure you have a database backup before proceeding.")

    response = input("\nDo you want to continue? (y/n): ")
    if response.lower() != 'y':
        print("❌ Rollback cancelled")
        return

    # Step 1: Check for soft-deleted data
    print("\n🔍 Step 1: Checking for soft-deleted data...")
    if not check_soft_deleted_data():
        return

    # Step 2: Remove indexes
    print("\n🗑️  Step 2: Removing optimization indexes...")
    if not remove_indexes():
        print("⚠️  Index removal failed, but continuing...")

    # Step 3: Rollback migration
    print("\n🔄 Step 3: Rolling back migration...")
    if not rollback_migration():
        print("❌ Migration rollback failed. Manual intervention required.")
        return

    # Step 4: Manual model cleanup instructions
    print("\n📝 Step 4: Manual cleanup required...")
    restore_model_file()

    print("\n✅ Rollback process completed!")
    print("   Don't forget to complete the manual steps above.")


if __name__ == "__main__":
    main()