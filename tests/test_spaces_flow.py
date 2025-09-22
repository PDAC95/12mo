"""
End-to-end tests for Wallai Spaces management
"""
import pytest
from playwright.sync_api import expect
import string
import random

def generate_space_name():
    """Generate a unique space name for testing"""
    return f"Test Space {random.randint(1000, 9999)}"

@pytest.mark.e2e
@pytest.mark.spaces
def test_create_space_flow(authenticated_user, base_url):
    """Test complete space creation process"""
    page = authenticated_user

    # Navigate to spaces
    page.goto(f"{base_url}/spaces/")

    # Click create space button
    create_button = page.locator('a[href="/spaces/create/"], .create-space-btn')
    create_button.first.click()

    # Fill space creation form
    space_name = generate_space_name()
    page.fill('input[name="name"]', space_name)
    page.fill('textarea[name="description"]', 'Test space for E2E testing')

    # Select color (if available)
    color_option = page.locator('input[name="color"][value="blue"]')
    if color_option.is_visible():
        color_option.click()

    # Select icon (if available)
    icon_option = page.locator('input[name="icon"][value="home"]')
    if icon_option.is_visible():
        icon_option.click()

    # Submit form
    page.click('button[type="submit"]')

    # Should redirect to space detail or list
    expect(page.locator(f':text("{space_name}")')).to_be_visible()

    # Check for invite code generation
    invite_code = page.locator('.invite-code, [data-testid="invite-code"]')
    if invite_code.is_visible():
        code_text = invite_code.text_content()
        assert len(code_text.strip()) == 6, "Invite code should be 6 characters"

@pytest.mark.e2e
@pytest.mark.spaces
def test_space_list_display(authenticated_user, base_url):
    """Test that spaces are displayed correctly in the list"""
    page = authenticated_user

    # Go to spaces page
    page.goto(f"{base_url}/spaces/")

    # Should see spaces list or empty state
    spaces_container = page.locator('.spaces-list, .space-cards, main')
    expect(spaces_container).to_be_visible()

    # Check for personal space (auto-created)
    personal_space = page.locator(':text("Personal")')
    expect(personal_space).to_be_visible()

@pytest.mark.e2e
@pytest.mark.spaces
def test_join_space_with_code(authenticated_user, base_url):
    """Test joining a space using invite code"""
    page = authenticated_user

    # First, create a space to get an invite code
    page.goto(f"{base_url}/spaces/create/")
    space_name = generate_space_name()
    page.fill('input[name="name"]', space_name)
    page.click('button[type="submit"]')

    # Get the invite code
    invite_code_element = page.locator('.invite-code, [data-testid="invite-code"]')
    if invite_code_element.is_visible():
        invite_code = invite_code_element.text_content().strip()

        # Now test joining with this code (simulate different user)
        # For testing, we'll use the join form if available
        join_button = page.locator('a[href*="join"], .join-space-btn')
        if join_button.is_visible():
            join_button.first.click()
            page.fill('input[name="invite_code"]', invite_code)
            page.click('button[type="submit"]')

            # Should show success or redirect
            expect(page.locator('.success, .alert-success')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.spaces
def test_space_context_switching(authenticated_user, base_url):
    """Test switching between spaces"""
    page = authenticated_user

    # Go to dashboard
    page.goto(f"{base_url}/dashboard/")

    # Look for space selector in header
    space_selector = page.locator('.space-selector, .current-space, .space-dropdown')
    if space_selector.is_visible():
        space_selector.click()

        # Should show dropdown with available spaces
        dropdown = page.locator('.space-options, .dropdown-menu')
        expect(dropdown).to_be_visible()

        # Try to select a different space
        space_option = dropdown.locator('a, button').first
        if space_option.is_visible():
            space_option.click()

            # Page should reload or update with new context
            page.wait_for_load_state('networkidle')

@pytest.mark.e2e
@pytest.mark.spaces
def test_space_member_management(authenticated_user, base_url):
    """Test space member management features"""
    page = authenticated_user

    # Create or navigate to a space
    page.goto(f"{base_url}/spaces/")

    # Click on first space to view details
    space_link = page.locator('.space-card a, .space-item a').first
    if space_link.is_visible():
        space_link.click()

        # Should see space details page
        expect(page.locator('h1, .space-name')).to_be_visible()

        # Check for members section
        members_section = page.locator('.members, .space-members')
        if members_section.is_visible():
            expect(members_section).to_contain_text('Member')

        # Check for invite code regeneration
        regenerate_button = page.locator('.regenerate-code, button:has-text("Regenerate")')
        if regenerate_button.is_visible():
            old_code = page.locator('.invite-code').text_content()
            regenerate_button.click()
            page.wait_for_load_state('networkidle')
            new_code = page.locator('.invite-code').text_content()
            assert old_code != new_code, "Invite code should change after regeneration"

@pytest.mark.e2e
@pytest.mark.spaces
def test_space_customization(authenticated_user, base_url):
    """Test space customization features"""
    page = authenticated_user

    # Create a new space with customization
    page.goto(f"{base_url}/spaces/create/")

    space_name = generate_space_name()
    page.fill('input[name="name"]', space_name)

    # Test color selection
    colors = page.locator('input[name="color"]')
    if colors.count() > 0:
        colors.nth(1).click()  # Select second color option

    # Test icon selection
    icons = page.locator('input[name="icon"]')
    if icons.count() > 0:
        icons.nth(2).click()  # Select third icon option

    # Submit and verify
    page.click('button[type="submit"]')

    # Check that customization is applied
    space_card = page.locator(f':text("{space_name}")').locator('..').first
    expect(space_card).to_be_visible()

@pytest.mark.e2e
@pytest.mark.spaces
def test_space_archive_restore(authenticated_user, base_url):
    """Test space archive and restore functionality"""
    page = authenticated_user

    # Create a space first
    page.goto(f"{base_url}/spaces/create/")
    space_name = generate_space_name()
    page.fill('input[name="name"]', space_name)
    page.click('button[type="submit"]')

    # Navigate to space details
    page.goto(f"{base_url}/spaces/")
    space_link = page.locator(f':text("{space_name}")').locator('..').locator('a').first
    space_link.click()

    # Look for archive button
    archive_button = page.locator('.archive-space, button:has-text("Archive")')
    if archive_button.is_visible():
        archive_button.click()

        # Confirm archiving if confirmation is required
        confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Archive")')
        if confirm_button.is_visible():
            confirm_button.click()

        # Should redirect to spaces list
        page.wait_for_url(f"{base_url}/spaces/")

        # Space should not be visible in active list
        expect(page.locator(f':text("{space_name}")')).not_to_be_visible()

        # Check archived spaces if available
        archived_link = page.locator('a:has-text("Archived"), .archived-spaces')
        if archived_link.is_visible():
            archived_link.click()
            expect(page.locator(f':text("{space_name}")')).to_be_visible()

@pytest.mark.e2e
@pytest.mark.spaces
@pytest.mark.mobile
def test_spaces_mobile_interface(mobile_page, base_url, test_user):
    """Test spaces interface on mobile devices"""
    page = mobile_page

    # Login on mobile
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Navigate to spaces via bottom navigation
    spaces_nav = page.locator('.bottom-nav a[href*="spaces"], .nav-spaces')
    if spaces_nav.is_visible():
        spaces_nav.click()
    else:
        page.goto(f"{base_url}/spaces/")

    # Check mobile layout
    expect(page.locator('.spaces-list, main')).to_be_visible()

    # Test mobile space creation
    create_button = page.locator('.create-space, .floating-action-button, a[href="/spaces/create/"]')
    if create_button.is_visible():
        create_button.click()

        # Mobile form should be responsive
        form = page.locator('form')
        expect(form).to_be_visible()

        # Test mobile form interaction
        page.fill('input[name="name"]', 'Mobile Test Space')
        page.click('button[type="submit"]')

@pytest.mark.e2e
@pytest.mark.spaces
def test_space_limits_validation(authenticated_user, base_url):
    """Test space creation limits and validation"""
    page = authenticated_user

    # Test empty space name
    page.goto(f"{base_url}/spaces/create/")
    page.click('button[type="submit"]')

    # Should show validation error
    error_message = page.locator('.field-error, .invalid-feedback, .error')
    expect(error_message).to_be_visible()

    # Test very long space name
    long_name = 'A' * 100  # Assuming max length is less than 100
    page.fill('input[name="name"]', long_name)
    page.click('button[type="submit"]')

    # Should show length validation error if enforced
    if page.locator('.field-error, .invalid-feedback').is_visible():
        expect(page.locator('.field-error, .invalid-feedback')).to_contain_text('length')

@pytest.mark.e2e
@pytest.mark.spaces
def test_space_navigation_integration(authenticated_user, base_url):
    """Test that spaces integrate properly with navigation"""
    page = authenticated_user

    # Start at dashboard
    page.goto(f"{base_url}/dashboard/")

    # Check that current space is displayed in header
    current_space = page.locator('.current-space, .space-selector')
    expect(current_space).to_be_visible()

    # Navigate to different sections and ensure space context is maintained
    sections = ['/budgets/', '/dashboard/']
    for section in sections:
        page.goto(f"{base_url}{section}")
        expect(current_space).to_be_visible()
        expect(current_space).to_have_text(lambda text: len(text.strip()) > 0)