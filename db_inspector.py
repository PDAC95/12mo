#!/usr/bin/env python
"""
Wallai Database Inspector - Quick database introspection tool
Útil para debugging y development con Claude Code
"""

import os
import sys
import django

# Add project to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from spaces.models import Space, SpaceMember
from authentication.models import User
from budgets.models import BudgetCategory, Budget

def db_summary():
    """Get complete database summary for Wallai"""
    print("WALLAI DATABASE SUMMARY")
    print("=" * 50)

    # Database info
    print(f"Database: {connection.vendor} ({connection.settings_dict['NAME']})")
    print()

    # Core models count
    print("MODEL COUNTS:")
    print(f"   Users: {User.objects.count()}")
    print(f"   Spaces: {Space.objects.count()}")
    print(f"   Space Members: {SpaceMember.objects.count()}")
    print(f"   Budget Categories: {BudgetCategory.objects.count()}")
    print(f"   Budgets: {Budget.objects.count()}")
    print()

    # Active spaces detail
    print("ACTIVE SPACES:")
    for space in Space.objects.filter(is_active=True):
        member_count = space.spacemember_set.count()
        budget_count = Budget.objects.filter(space=space).count()
        print(f"   * {space.name} (Members: {member_count}, Budgets: {budget_count})")
    print()

    # Recent budgets
    print("RECENT BUDGETS:")
    recent_budgets = Budget.objects.select_related('space', 'category').order_by('-created_at')[:5]
    for budget in recent_budgets:
        print(f"   * {budget.space.name} - {budget.category.name}: ${budget.amount}")
    print()

def space_detail(space_name=None):
    """Get detailed info about a specific space"""
    if not space_name:
        print("Available spaces:")
        for space in Space.objects.all():
            print(f"   • {space.name} (ID: {space.id})")
        return

    try:
        space = Space.objects.get(name__icontains=space_name)
        print(f"SPACE DETAIL: {space.name}")
        print("=" * 50)
        print(f"   Created: {space.created_at}")
        print(f"   Invite Code: {space.invite_code}")
        print(f"   Owner: {space.created_by.username}")
        print(f"   Active: {space.is_active}")
        print()

        # Members
        print("MEMBERS:")
        for member in space.spacemember_set.select_related('user'):
            role = "Owner" if member.user == space.created_by else "Member"
            print(f"   * {member.user.username} ({role}) - Joined: {member.joined_at}")
        print()

        # Budgets
        print("BUDGETS:")
        budgets = Budget.objects.filter(space=space).select_related('category')
        current_month = budgets.filter(month_period='2025-09').order_by('category__name')

        total_budget = sum(b.amount for b in current_month)
        print(f"   September 2025 Total: ${total_budget}")

        for budget in current_month:
            assigned_to = f" (Assigned: {budget.assigned_to.username})" if budget.assigned_to else ""
            print(f"   * {budget.category.name}: ${budget.amount}{assigned_to}")

    except Space.DoesNotExist:
        print(f"ERROR: Space '{space_name}' not found")

def budget_analysis():
    """Analyze budget data for insights"""
    print("BUDGET ANALYSIS")
    print("=" * 50)

    # Total budgets by month
    from django.db.models import Sum

    budget_by_month = Budget.objects.values('month_period').annotate(
        total=Sum('amount')
    ).order_by('month_period')

    print("TOTAL BUDGETS BY MONTH:")
    for month_data in budget_by_month:
        print(f"   {month_data['month_period']}: ${month_data['total']}")
    print()

    # Most common categories
    from django.db.models import Count

    category_usage = BudgetCategory.objects.annotate(
        budget_count=Count('budget')
    ).order_by('-budget_count')[:5]

    print("TOP BUDGET CATEGORIES:")
    for category in category_usage:
        print(f"   * {category.name}: {category.budget_count} budgets")
    print()

    # Average amounts by category
    category_averages = Budget.objects.values('category__name').annotate(
        avg_amount=Sum('amount')
    ).order_by('-avg_amount')[:5]

    print("HIGHEST BUDGET CATEGORIES (Total):")
    for cat_data in category_averages:
        print(f"   * {cat_data['category__name']}: ${cat_data['avg_amount']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "summary":
            db_summary()
        elif command == "space":
            space_name = sys.argv[2] if len(sys.argv) > 2 else None
            space_detail(space_name)
        elif command == "budget":
            budget_analysis()
        else:
            print("Available commands: summary, space [name], budget")
    else:
        db_summary()