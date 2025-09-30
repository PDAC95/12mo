#!/usr/bin/env python
"""
Test script to verify soft delete functionality for Budget model
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.budgets.models import Budget

def test_soft_delete_functionality():
    """Test the soft delete functionality"""
    print("🧪 Testing Budget Soft Delete Functionality")
    print("=" * 45)

    # Test 1: Check if Budget model has soft delete fields
    print("\n✅ Test 1: Checking model fields...")
    try:
        field_names = [field.name for field in Budget._meta.get_fields()]

        if 'deleted_at' in field_names:
            print("   ✅ deleted_at field exists")
        else:
            print("   ❌ deleted_at field missing")

        if 'deleted_by' in field_names:
            print("   ✅ deleted_by field exists")
        else:
            print("   ❌ deleted_by field missing")

    except Exception as e:
        print(f"   ❌ Error checking fields: {e}")

    # Test 2: Check custom manager methods
    print("\n✅ Test 2: Checking custom manager methods...")
    try:
        manager_methods = dir(Budget.objects)

        required_methods = ['active', 'deleted', 'all_including_deleted', 'soft_delete', 'restore']
        for method in required_methods:
            if method in manager_methods:
                print(f"   ✅ {method}() method exists")
            else:
                print(f"   ❌ {method}() method missing")

    except Exception as e:
        print(f"   ❌ Error checking manager methods: {e}")

    # Test 3: Check instance methods
    print("\n✅ Test 3: Checking instance methods...")
    try:
        # Get any budget instance (or check on the class)
        if hasattr(Budget, 'soft_delete'):
            print("   ✅ soft_delete() instance method exists")
        else:
            print("   ❌ soft_delete() instance method missing")

        if hasattr(Budget, 'restore'):
            print("   ✅ restore() instance method exists")
        else:
            print("   ❌ restore() instance method missing")

        if hasattr(Budget, 'is_deleted'):
            print("   ✅ is_deleted property exists")
        else:
            print("   ❌ is_deleted property missing")

    except Exception as e:
        print(f"   ❌ Error checking instance methods: {e}")

    # Test 4: Check basic queryset functionality
    print("\n✅ Test 4: Testing basic queryset functionality...")
    try:
        active_count = Budget.objects.active().count()
        deleted_count = Budget.objects.deleted().count()
        all_count = Budget.objects.all_including_deleted().count()

        print(f"   ✅ Active budgets: {active_count}")
        print(f"   ✅ Deleted budgets: {deleted_count}")
        print(f"   ✅ Total budgets: {all_count}")

        if all_count == active_count + deleted_count:
            print("   ✅ Queryset counts are consistent")
        else:
            print("   ⚠️  Queryset counts may be inconsistent")

    except Exception as e:
        print(f"   ❌ Error testing querysets: {e}")

    print("\n🎉 Soft Delete Functionality Test Complete!")

if __name__ == "__main__":
    test_soft_delete_functionality()