"""
Pytest configuration and fixtures for Wallai E2E testing
"""
import pytest
import django
from django.conf import settings
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core.management import execute_from_command_line
import os
import subprocess
import time
import threading
from django.contrib.auth import get_user_model

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

User = get_user_model()

@pytest.fixture(scope="session")
def django_server():
    """Start Django development server for testing"""
    # Use a different port to avoid conflicts
    port = "8001"
    server_url = f"http://localhost:{port}"

    # Start the server in a subprocess
    server_process = subprocess.Popen([
        "python", "manage.py", "runserver", f"localhost:{port}", "--noreload"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for server to start
    time.sleep(3)

    yield server_url

    # Cleanup: terminate the server
    server_process.terminate()
    server_process.wait()

@pytest.fixture(scope="session")
def base_url(django_server):
    """Base URL for the application"""
    return django_server

@pytest.fixture
def test_user():
    """Create a test user for authentication tests"""
    user = User.objects.create_user(
        email='test@wallai.com',
        username='testuser',
        password='TestPass123!'
    )
    yield user
    user.delete()

@pytest.fixture
def authenticated_user(page, base_url, test_user):
    """Log in a user and return the authenticated page"""
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard/")
    return page

@pytest.fixture
def mobile_page(page):
    """Configure page for mobile testing"""
    page.set_viewport_size({"width": 375, "height": 667})  # iPhone size
    return page