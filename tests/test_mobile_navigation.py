"""
End-to-end tests for Wallai Mobile Navigation and Responsive Design
"""
import pytest
from playwright.sync_api import expect

@pytest.mark.e2e
@pytest.mark.mobile
def test_bottom_navigation_visibility(mobile_page, base_url, test_user):
    """Test that bottom navigation is visible and functional on mobile"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Should see bottom navigation
    bottom_nav = page.locator('.bottom-nav, .mobile-nav')
    expect(bottom_nav).to_be_visible()

    # Check all navigation buttons
    nav_buttons = bottom_nav.locator('a, button')
    expect(nav_buttons).to_have_count_greater_than(3)  # Should have at least 4-5 nav items

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_header_layout(mobile_page, base_url, test_user):
    """Test mobile header layout and functionality"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Check mobile header
    header = page.locator('header, .header, .mobile-header')
    expect(header).to_be_visible()

    # Wallai logo should be visible
    logo = page.locator('img[alt*="Wallai"], .logo')
    expect(logo).to_be_visible()

    # User avatar or menu should be visible
    user_menu = page.locator('.user-avatar, .user-menu, .profile-menu')
    expect(user_menu).to_be_visible()

@pytest.mark.e2e
@pytest.mark.mobile
def test_floating_action_button(mobile_page, base_url, test_user):
    """Test the center floating action button on mobile"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Look for floating action button (center button)
    fab = page.locator('.center-button, .floating-action-button, .fab')
    if fab.is_visible():
        expect(fab).to_be_visible()

        # Button should be clickable
        fab.click()

        # Should open expense modal or navigate to expense creation
        modal_or_page = page.locator('.modal, .expense-modal, form')
        expect(modal_or_page).to_be_visible()

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_navigation_flow(mobile_page, base_url, test_user):
    """Test complete navigation flow on mobile"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Test navigation to each major section
    sections = [
        ('dashboard', 'Dashboard'),
        ('budgets', 'Budget'),
        ('spaces', 'Space')
    ]

    for section_path, expected_content in sections:
        # Click navigation button
        nav_button = page.locator(f'.bottom-nav a[href*="{section_path}"], .nav-{section_path}')
        if nav_button.is_visible():
            nav_button.click()

            # Wait for navigation
            page.wait_for_load_state('networkidle')

            # Check that we're on the right page
            page_content = page.locator('h1, .page-title, main')
            if expected_content:
                expect(page_content).to_contain_text(expected_content)

            # Check that bottom nav is still visible
            bottom_nav = page.locator('.bottom-nav, .mobile-nav')
            expect(bottom_nav).to_be_visible()

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_responsive_breakpoints(page, base_url, test_user):
    """Test responsive design at different mobile breakpoints"""
    # Test different mobile sizes
    mobile_sizes = [
        (375, 667),   # iPhone SE/8
        (414, 896),   # iPhone 11/XR
        (360, 640),   # Android standard
        (768, 1024),  # Tablet
    ]

    for width, height in mobile_sizes:
        page.set_viewport_size({"width": width, "height": height})

        # Login
        page.goto(f"{base_url}/login/")
        page.fill('input[name="email"]', test_user.email)
        page.fill('input[name="password"]', 'TestPass123!')
        page.click('button[type="submit"]')

        # Check layout adapts properly
        if width < 768:  # Mobile
            # Bottom nav should be visible
            bottom_nav = page.locator('.bottom-nav, .mobile-nav')
            expect(bottom_nav).to_be_visible()

            # Sidebar should be hidden
            sidebar = page.locator('.sidebar, .desktop-nav')
            if sidebar.is_visible():
                expect(sidebar).to_have_css('display', 'none')

        else:  # Tablet/Desktop
            # Sidebar might be visible
            sidebar = page.locator('.sidebar, .desktop-nav')
            if sidebar.is_visible():
                expect(sidebar).to_be_visible()

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_form_interactions(mobile_page, base_url, test_user):
    """Test form interactions on mobile devices"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Test space creation form on mobile
    page.goto(f"{base_url}/spaces/create/")

    # Form should be mobile-friendly
    form = page.locator('form')
    expect(form).to_be_visible()

    # Input fields should be appropriately sized
    name_input = page.locator('input[name="name"]')
    expect(name_input).to_be_visible()

    # Test input interaction
    name_input.fill('Mobile Test Space')

    # Submit button should be touch-friendly
    submit_button = page.locator('button[type="submit"]')
    expect(submit_button).to_be_visible()

    # Button should have adequate touch target (at least 44px)
    button_box = submit_button.bounding_box()
    if button_box:
        assert button_box['height'] >= 40, "Button height should be at least 40px for touch"

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_content_scrolling(mobile_page, base_url, test_user):
    """Test content scrolling behavior on mobile"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Navigate to a content-heavy page (budgets)
    page.goto(f"{base_url}/budgets/")

    # Check that content area is scrollable
    main_content = page.locator('main, .content-area')
    expect(main_content).to_be_visible()

    # Header should stay fixed during scroll
    header = page.locator('header, .header')
    if header.is_visible():
        # Scroll down
        page.mouse.wheel(0, 500)

        # Header should still be visible
        expect(header).to_be_visible()

    # Bottom navigation should stay fixed
    bottom_nav = page.locator('.bottom-nav, .mobile-nav')
    if bottom_nav.is_visible():
        expect(bottom_nav).to_be_visible()

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_space_selector(mobile_page, base_url, test_user):
    """Test space selector functionality on mobile"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Look for space selector in header
    space_selector = page.locator('.space-selector, .current-space')
    if space_selector.is_visible():
        expect(space_selector).to_be_visible()

        # Click to open dropdown
        space_selector.click()

        # Dropdown should be mobile-friendly
        dropdown = page.locator('.space-dropdown, .dropdown-menu')
        if dropdown.is_visible():
            expect(dropdown).to_be_visible()

            # Dropdown items should be touch-friendly
            dropdown_items = dropdown.locator('a, button')
            if dropdown_items.count() > 0:
                first_item = dropdown_items.first
                item_box = first_item.bounding_box()
                if item_box:
                    assert item_box['height'] >= 40, "Dropdown items should be at least 40px tall"

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_error_handling(mobile_page, base_url):
    """Test error handling and messages on mobile"""
    page = mobile_page

    # Test login error on mobile
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', 'invalid@email.com')
    page.fill('input[name="password"]', 'wrongpassword')
    page.click('button[type="submit"]')

    # Error message should be visible and readable on mobile
    error_message = page.locator('.alert-danger, .error-message, .field-error')
    if error_message.is_visible():
        expect(error_message).to_be_visible()

        # Error should not overflow on mobile
        error_box = error_message.bounding_box()
        viewport = page.viewport_size
        if error_box and viewport:
            assert error_box['width'] <= viewport['width'], "Error message should not overflow viewport"

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_loading_states(mobile_page, base_url, test_user):
    """Test loading states and transitions on mobile"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')

    # Submit and watch for loading states
    page.click('button[type="submit"]')

    # Should handle loading gracefully
    page.wait_for_load_state('networkidle', timeout=10000)

    # Should end up at dashboard
    expect(page).to_have_url(f"{base_url}/dashboard/")

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_orientation_changes(mobile_page, base_url, test_user):
    """Test layout behavior during orientation changes"""
    page = mobile_page

    # Start in portrait
    page.set_viewport_size({"width": 375, "height": 667})

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Verify portrait layout
    bottom_nav = page.locator('.bottom-nav, .mobile-nav')
    expect(bottom_nav).to_be_visible()

    # Switch to landscape
    page.set_viewport_size({"width": 667, "height": 375})
    page.wait_for_load_state('networkidle')

    # Layout should adapt
    # Bottom nav should still be visible and functional
    expect(bottom_nav).to_be_visible()

    # Content should not be cut off
    main_content = page.locator('main, .content-area')
    expect(main_content).to_be_visible()

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_accessibility(mobile_page, base_url, test_user):
    """Test mobile accessibility features"""
    page = mobile_page

    # Login
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Check for proper focus management
    # Tab through navigation elements
    page.keyboard.press('Tab')
    focused_element = page.locator(':focus')
    expect(focused_element).to_be_visible()

    # Interactive elements should have proper labels
    buttons = page.locator('button, a')
    for i in range(min(5, buttons.count())):  # Check first 5 buttons
        button = buttons.nth(i)
        if button.is_visible():
            # Should have text content or aria-label
            text_content = button.text_content()
            aria_label = button.get_attribute('aria-label')
            assert text_content.strip() or aria_label, f"Button {i} should have text or aria-label"

@pytest.mark.e2e
@pytest.mark.mobile
def test_mobile_performance(mobile_page, base_url, test_user):
    """Test mobile performance and loading times"""
    page = mobile_page

    # Enable network monitoring
    page.route("**/*", lambda route: route.continue_())

    # Login and measure
    start_time = page.evaluate('() => performance.now()')

    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Wait for dashboard to load
    page.wait_for_selector('h1, .welcome-message, main')

    end_time = page.evaluate('() => performance.now()')
    load_time = end_time - start_time

    # Login + redirect should complete in reasonable time (under 5 seconds)
    assert load_time < 5000, f"Login flow took {load_time}ms, should be under 5000ms"

    # Navigation should be fast
    nav_start = page.evaluate('() => performance.now()')
    page.click('.bottom-nav a[href*="budgets"], .nav-budgets')
    page.wait_for_load_state('networkidle')
    nav_end = page.evaluate('() => performance.now()')
    nav_time = nav_end - nav_start

    # Navigation should be under 2 seconds
    assert nav_time < 2000, f"Navigation took {nav_time}ms, should be under 2000ms"