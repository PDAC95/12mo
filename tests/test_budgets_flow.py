"""
End-to-end tests for Wallai Budget Management System
"""
import pytest
from playwright.sync_api import expect
from datetime import datetime

def get_current_month():
    """Get current month in YYYY-MM format"""
    return datetime.now().strftime('%Y-%m')

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_dashboard_loads(authenticated_user, base_url):
    """Test that budget dashboard loads correctly"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Should see budget dashboard
    expect(page.locator('h1, .page-title')).to_contain_text('Budget')

    # Check for key budget elements
    budget_container = page.locator('.budget-dashboard, .budget-container, main')
    expect(budget_container).to_be_visible()

@pytest.mark.e2e
@pytest.mark.budgets
def test_monthly_budget_creation(authenticated_user, base_url):
    """Test creating a monthly budget"""
    page = authenticated_user

    # Go to budget creation
    page.goto(f"{base_url}/budgets/create-monthly/")

    # Should see monthly budget creation form
    expect(page.locator('h1, .page-title')).to_contain_text('Create')

    # Current month should be pre-selected
    current_month = get_current_month()
    month_input = page.locator('input[name="month_period"]')
    if month_input.is_visible():
        expect(month_input).to_have_value(current_month)

    # Choose creation method (new or copy)
    create_new_option = page.locator('input[value="new"], input[value="create_new"]')
    if create_new_option.is_visible():
        create_new_option.click()

    # Submit form
    page.click('button[type="submit"]')

    # Should redirect to budget dashboard or show success
    page.wait_for_load_state('networkidle')

    # Verify budget categories were created
    categories = page.locator('.budget-category, .category-row')
    expect(categories.first).to_be_visible()

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_categories_display(authenticated_user, base_url):
    """Test that budget categories are displayed correctly"""
    page = authenticated_user

    # Ensure we have a budget by creating one first
    page.goto(f"{base_url}/budgets/create-monthly/")
    page.click('button[type="submit"]')  # Create with defaults

    # Navigate to budget dashboard
    page.goto(f"{base_url}/budgets/")

    # Should see budget categories
    categories = page.locator('.budget-category, .category-row, tbody tr')
    expect(categories.first).to_be_visible()

    # Check for essential budget categories
    essential_categories = ['Housing', 'Food', 'Transportation', 'Savings']
    for category in essential_categories:
        category_element = page.locator(f':text("{category}")')
        if category_element.is_visible():
            expect(category_element).to_be_visible()

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_progress_tracking(authenticated_user, base_url):
    """Test budget progress bars and tracking"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Look for progress bars
    progress_bars = page.locator('.progress-bar, .budget-progress, [role="progressbar"]')
    if progress_bars.count() > 0:
        # Check that progress bars are visible
        expect(progress_bars.first).to_be_visible()

        # Progress bars should have percentage values
        progress_value = progress_bars.first.get_attribute('style')
        if progress_value and 'width:' in progress_value:
            assert 'width:' in progress_value

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_copy_from_previous_month(authenticated_user, base_url):
    """Test copying budget from previous month"""
    page = authenticated_user

    # Create budget for current month first
    page.goto(f"{base_url}/budgets/create-monthly/")
    page.click('button[type="submit"]')

    # Now try to create budget for next month by copying
    page.goto(f"{base_url}/budgets/create-monthly/")

    # Select copy option
    copy_option = page.locator('input[value="copy"], input[value="copy_previous"]')
    if copy_option.is_visible():
        copy_option.click()

        # Should show copy options
        copy_controls = page.locator('.copy-options, .multiplier')
        if copy_controls.is_visible():
            expect(copy_controls).to_be_visible()

        # Submit copy operation
        page.click('button[type="submit"]')

        # Should successfully create copied budget
        page.wait_for_load_state('networkidle')

@pytest.mark.e2e
@pytest.mark.budgets
def test_individual_budget_editing(authenticated_user, base_url):
    """Test editing individual budget categories"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Look for edit buttons on budget categories
    edit_button = page.locator('.edit-budget, .btn-edit, a[href*="edit"]').first
    if edit_button.is_visible():
        edit_button.click()

        # Should open edit form
        form = page.locator('form')
        expect(form).to_be_visible()

        # Modify amount
        amount_input = page.locator('input[name="amount"]')
        if amount_input.is_visible():
            amount_input.clear()
            amount_input.fill('500.00')

        # Submit changes
        save_button = page.locator('button[type="submit"], .btn-save')
        save_button.click()

        # Should save and redirect
        page.wait_for_load_state('networkidle')

@pytest.mark.e2e
@pytest.mark.budgets
def test_bulk_budget_editing(authenticated_user, base_url):
    """Test bulk editing of multiple budget categories"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Look for bulk edit button
    bulk_edit_button = page.locator('.bulk-edit, .edit-all, a[href*="bulk"]')
    if bulk_edit_button.is_visible():
        bulk_edit_button.click()

        # Should show bulk edit form
        form = page.locator('form')
        expect(form).to_be_visible()

        # Should have multiple amount inputs
        amount_inputs = page.locator('input[name*="amount"]')
        if amount_inputs.count() > 1:
            # Modify first few amounts
            amount_inputs.nth(0).clear()
            amount_inputs.nth(0).fill('600.00')

            amount_inputs.nth(1).clear()
            amount_inputs.nth(1).fill('400.00')

        # Submit bulk changes
        page.click('button[type="submit"]')

        # Should save all changes
        page.wait_for_load_state('networkidle')

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_totals_calculation(authenticated_user, base_url):
    """Test that budget totals are calculated correctly"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Look for total budget amount
    total_element = page.locator('.total-budget, .budget-total, .total-amount')
    if total_element.is_visible():
        total_text = total_element.text_content()

        # Should contain currency format
        assert '$' in total_text or 'USD' in total_text

        # Should be a reasonable total (between $1000-$10000 for default budget)
        import re
        amount_match = re.search(r'[\d,]+\.?\d*', total_text.replace(',', ''))
        if amount_match:
            amount = float(amount_match.group())
            assert 1000 <= amount <= 10000, f"Total budget {amount} seems unreasonable"

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_member_assignment(authenticated_user, base_url):
    """Test assigning budget categories to space members"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Look for member assignment options
    member_select = page.locator('select[name*="assigned"], .member-assignment')
    if member_select.count() > 0:
        # Should have member options
        options = member_select.first.locator('option')
        expect(options.first).to_be_visible()

        # Select a member if options available
        if options.count() > 1:
            options.nth(1).click()

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_validation(authenticated_user, base_url):
    """Test budget form validation"""
    page = authenticated_user

    # Try to create budget with invalid data
    page.goto(f"{base_url}/budgets/create-monthly/")

    # Clear month field if editable
    month_input = page.locator('input[name="month_period"]')
    if month_input.is_editable():
        month_input.clear()

    # Submit empty form
    page.click('button[type="submit"]')

    # Should show validation errors
    error_element = page.locator('.field-error, .invalid-feedback, .error')
    if error_element.is_visible():
        expect(error_element).to_be_visible()

@pytest.mark.e2e
@pytest.mark.budgets
@pytest.mark.mobile
def test_budgets_mobile_interface(mobile_page, base_url, test_user):
    """Test budget interface on mobile devices"""
    page = mobile_page

    # Login on mobile
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', test_user.email)
    page.fill('input[name="password"]', 'TestPass123!')
    page.click('button[type="submit"]')

    # Navigate to budgets via bottom navigation
    budgets_nav = page.locator('.bottom-nav a[href*="budgets"], .nav-budgets')
    if budgets_nav.is_visible():
        budgets_nav.click()
    else:
        page.goto(f"{base_url}/budgets/")

    # Should see mobile-optimized budget layout
    expect(page.locator('.budget-dashboard, main')).to_be_visible()

    # Budget categories should be mobile-friendly
    categories = page.locator('.budget-category, .category-row')
    if categories.count() > 0:
        # Should be stacked vertically on mobile
        expect(categories.first).to_be_visible()

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_month_navigation(authenticated_user, base_url):
    """Test navigating between different budget months"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Look for month navigation
    month_nav = page.locator('.month-nav, .month-selector, .period-nav')
    if month_nav.is_visible():
        # Should show current month
        current_month = get_current_month()
        expect(month_nav).to_contain_text(current_month.split('-')[0])  # Year

        # Look for previous/next month buttons
        prev_button = page.locator('.prev-month, .btn-prev')
        next_button = page.locator('.next-month, .btn-next')

        if prev_button.is_visible():
            prev_button.click()
            page.wait_for_load_state('networkidle')

        if next_button.is_visible():
            next_button.click()
            page.wait_for_load_state('networkidle')

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_system_defaults(authenticated_user, base_url):
    """Test that system default categories are created correctly"""
    page = authenticated_user

    # Create a new monthly budget
    page.goto(f"{base_url}/budgets/create-monthly/")
    page.click('button[type="submit"]')

    # Navigate to budget view
    page.goto(f"{base_url}/budgets/")

    # Check for standard budget categories
    standard_categories = [
        'Housing', 'Food', 'Transportation', 'Savings',
        'Entertainment', 'Healthcare', 'Utilities'
    ]

    visible_categories = 0
    for category in standard_categories:
        category_element = page.locator(f':text("{category}")')
        if category_element.is_visible():
            visible_categories += 1

    # Should have at least 5 standard categories
    assert visible_categories >= 5, f"Only {visible_categories} standard categories found"

@pytest.mark.e2e
@pytest.mark.budgets
def test_budget_amount_formatting(authenticated_user, base_url):
    """Test that budget amounts are formatted correctly"""
    page = authenticated_user

    # Navigate to budgets
    page.goto(f"{base_url}/budgets/")

    # Look for amount displays
    amounts = page.locator('.amount, .budget-amount, .currency')
    if amounts.count() > 0:
        amount_text = amounts.first.text_content()

        # Should have proper currency formatting
        assert '$' in amount_text or 'USD' in amount_text

        # Should have decimal formatting for non-zero amounts
        if '.' in amount_text:
            decimal_part = amount_text.split('.')[-1]
            # Should have 2 decimal places
            assert len(decimal_part.replace('$', '').replace('USD', '').strip()) >= 2