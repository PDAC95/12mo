#!/usr/bin/env python
"""
Debug script for template view issues
"""
import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from spaces.models import Space, SpaceMember
from spaces.utils import SpaceContextManager

User = get_user_model()

def test_space_context_manager():
    print("=== DEBUGGING SPACE CONTEXT MANAGER ===")

    # Get specific user dumck@hotmail.com
    try:
        user = User.objects.get(email='dumck@hotmail.com')
        print(f"Testing with user: {user.email}")
    except User.DoesNotExist:
        print("ERROR: User dumck@hotmail.com not found")
        return

    # Check spaces
    spaces = Space.objects.filter(spacemember__user=user, spacemember__is_active=True)
    print(f"User has {spaces.count()} spaces:")
    for space in spaces:
        print(f"  - {space.name} (ID: {space.id})")

    # Create request
    factory = RequestFactory()
    request = factory.get('/budgets/templates/')
    request.user = user

    # Create session
    session = SessionStore()
    session.create()
    request.session = session

    print("\n=== Testing SpaceContextManager ===")

    try:
        # Test get_current_space_id
        space_id = SpaceContextManager.get_current_space_id(request)
        print(f"Current space ID: {space_id}")

        # Test get_current_space
        current_space = SpaceContextManager.get_current_space(request)
        print(f"Current space: {current_space}")

        if current_space:
            print(f"  Name: {current_space.name}")
            print(f"  ID: {current_space.id}")
            print("SUCCESS: SpaceContextManager working correctly")
        else:
            print("WARNING: No current space found")

    except Exception as e:
        print(f"ERROR in SpaceContextManager: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Testing template_list view ===")

    try:
        from budgets.views import template_list
        response = template_list(request)
        print(f"SUCCESS: template_list executed, status: {response.status_code if hasattr(response, 'status_code') else 'redirect'}")
    except Exception as e:
        print(f"ERROR in template_list: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_space_context_manager()