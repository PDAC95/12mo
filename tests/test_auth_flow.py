"""
End-to-end tests for Wallai authentication flow
"""
import pytest
from playwright.sync_api import expect

@pytest.mark.e2e
@pytest.mark.auth
def test_landing_page_loads(page, base_url):
    """Test that the landing page loads correctly"""
    page.goto(base_url)

    # Check that we're on the landing page
    expect(page).to_have_title("Wallai - Collaborative Personal Finance")

    # Check for key elements
    expect(page.locator("h1")).to_contain_text("Wallai")
    expect(page.locator('a[href="/login/"]')).to_be_visible()
    expect(page.locator('a[href="/register/"]')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.auth
def test_user_registration_flow(page, base_url):
    """Test complete user registration process"""
    page.goto(f"{base_url}/register/")

    # Fill registration form
    page.fill('input[name="email"]', 'newuser@wallai.com')
    page.fill('input[name="username"]', 'newuser')
    page.fill('input[name="password1"]', 'SecurePass123!')
    page.fill('input[name="password2"]', 'SecurePass123!')

    # Submit form
    page.click('button[type="submit"]')

    # Should redirect to login or dashboard
    page.wait_for_url(f"{base_url}/login/")
    expect(page.locator('.alert-success, .success-message')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.auth
def test_user_login_flow(page, base_url, test_user):
    """Test user login process"""
    page.goto(f"{base_url}/login/")

    # Fill login form
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')

    # Submit form
    page.click('button[type="submit"]')

    # Should redirect to dashboard
    page.wait_for_url(f"{base_url}/dashboard/")
    expect(page.locator('h1, .welcome-message')).to_contain_text("Welcome")

@pytest.mark.e2e
@pytest.mark.auth
def test_invalid_login(page, base_url):
    """Test login with invalid credentials"""
    page.goto(f"{base_url}/login/")

    # Fill with invalid credentials
    page.fill('input[name="email"]', 'invalid@wallai.com')
    page.fill('input[name="password"]', 'wrongpassword')

    # Submit form
    page.click('button[type="submit"]')

    # Should stay on login page with error
    expect(page).to_have_url(f"{base_url}/login/")
    expect(page.locator('.alert-danger, .error-message')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.auth
def test_logout_flow(page, base_url, authenticated_user):
    """Test user logout process"""
    # User should be logged in from fixture
    expect(page).to_have_url(f"{base_url}/dashboard/")

    # Find and click logout button/link
    logout_button = page.locator('a[href="/logout/"], button:has-text("Logout"), .logout-link')
    logout_button.first.click()

    # Should redirect to landing page
    page.wait_for_url(base_url)
    expect(page.locator('a[href="/login/"]')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.auth
@pytest.mark.mobile
def test_mobile_authentication(mobile_page, base_url, test_user):
    """Test authentication flow on mobile"""
    mobile_page.goto(f"{base_url}/login/")

    # Check mobile layout
    expect(mobile_page.locator('.mobile-header, .header')).to_be_visible()

    # Login on mobile
    mobile_page.fill('input[name="email"]', test_user.email)
    mobile_page.fill('input[name="password"]', 'TestPass123!')
    mobile_page.click('button[type="submit"]')

    # Should see mobile dashboard
    mobile_page.wait_for_url(f"{base_url}/dashboard/")
    expect(mobile_page.locator('.bottom-nav, .mobile-nav')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.auth
def test_protected_page_redirect(page, base_url):
    """Test that protected pages redirect to login"""
    # Try to access dashboard without authentication
    page.goto(f"{base_url}/dashboard/")

    # Should redirect to login
    page.wait_for_url(f"{base_url}/login/")
    expect(page.locator('form')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.auth
def test_form_validation(page, base_url):
    """Test form validation on registration"""
    page.goto(f"{base_url}/register/")

    # Try to submit empty form
    page.click('button[type="submit"]')

    # Should show validation errors
    expect(page.locator('.field-error, .invalid-feedback')).to_be_visible()

    # Test password mismatch
    page.fill('input[name="email"]', 'test@wallai.com')
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password1"]', 'password123')
    page.fill('input[name="password2"]', 'differentpassword')
    page.click('button[type="submit"]')

    # Should show password mismatch error
    expect(page.locator(':text("password")')).to_be_visible()