# Wallai E2E Testing with Playwright

## 🎭 Overview

This directory contains end-to-end tests for Wallai using Playwright. These tests simulate real user interactions and validate the complete user experience across different devices and scenarios.

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── test_auth_flow.py          # Authentication tests
├── test_spaces_flow.py        # Space management tests
├── test_budgets_flow.py       # Budget system tests
├── test_mobile_navigation.py  # Mobile/responsive tests
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install playwright pytest-playwright
playwright install chromium
```

### 2. Run All Tests
```bash
python run_tests.py
```

### 3. Run Specific Test Categories
```bash
# Authentication tests only
python run_tests.py --auth

# Space management tests only
python run_tests.py --spaces

# Budget system tests only
python run_tests.py --budgets

# Mobile tests only
python run_tests.py --mobile
```

### 4. Run Tests in Headed Mode (Visible Browser)
```bash
python run_tests.py --headed
```

## 📱 Test Categories

### Authentication Tests (`test_auth_flow.py`)
- **Landing page load**: Verify homepage loads correctly
- **User registration**: Complete registration flow
- **User login/logout**: Authentication process
- **Form validation**: Input validation and error handling
- **Protected routes**: Redirect behavior for unauthenticated users

### Space Management Tests (`test_spaces_flow.py`)
- **Space creation**: Create spaces with customization
- **Invite system**: Generate and use invite codes
- **Member management**: Add, remove, transfer ownership
- **Space switching**: Context switching between spaces
- **Archive/restore**: Data preservation functionality

### Budget System Tests (`test_budgets_flow.py`)
- **Budget creation**: Monthly budget setup
- **Category management**: System and custom categories
- **Budget tracking**: Progress bars and alerts
- **Bulk operations**: Multi-category editing
- **Copy functionality**: Replicate budgets across months

### Mobile Navigation Tests (`test_mobile_navigation.py`)
- **Responsive design**: Multiple screen sizes
- **Bottom navigation**: Mobile navigation bar
- **Touch interactions**: Mobile-friendly UI
- **Performance**: Loading times and responsiveness
- **Accessibility**: Focus management and labels

## 🔧 Test Configuration

### Fixtures Available

- **`base_url`**: Application base URL
- **`test_user`**: Pre-created test user
- **`authenticated_user`**: Logged-in user page
- **`mobile_page`**: Mobile viewport configuration

### Markers

Use pytest markers to run specific test types:

```bash
# Run only E2E tests
pytest -m e2e

# Run only mobile tests
pytest -m mobile

# Run only authentication tests
pytest -m auth

# Run only space tests
pytest -m spaces

# Run only budget tests
pytest -m budgets
```

## 📊 Test Reports

### Running with Verbose Output
```bash
python run_tests.py --headed -v
```

### Generate HTML Report
```bash
pytest tests/ --html=test_report.html --self-contained-html
```

## 🐛 Debugging Tests

### 1. Run Single Test
```bash
pytest tests/test_auth_flow.py::test_user_login_flow -v --headed
```

### 2. Add Debug Breakpoint
```python
def test_my_feature(page, base_url):
    page.goto(base_url)
    page.pause()  # Opens browser dev tools
    # ... rest of test
```

### 3. Screenshot on Failure
Tests automatically capture screenshots on failure in `test-results/` directory.

## 🎯 Best Practices

### 1. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 2. Robust Selectors
```python
# Good: Semantic selectors
page.locator('button[type="submit"]')
page.locator('[data-testid="expense-form"]')

# Avoid: Fragile selectors
page.locator('.btn.btn-primary.mt-3')
```

### 3. Explicit Waits
```python
# Wait for elements
page.wait_for_selector('.budget-list')

# Wait for navigation
page.wait_for_url('/dashboard/')

# Wait for network
page.wait_for_load_state('networkidle')
```

### 4. Mobile Testing
```python
# Always test mobile viewports
@pytest.mark.mobile
def test_mobile_feature(mobile_page, base_url):
    page = mobile_page  # Pre-configured mobile viewport
    # ... test mobile-specific behavior
```

## 🚨 Common Issues

### 1. Django Server Not Starting
- Check if port 8001 is available
- Verify Django settings configuration
- Ensure database migrations are applied

### 2. Tests Timing Out
- Increase timeout in `conftest.py`
- Check for slow network requests
- Verify test server performance

### 3. Element Not Found
- Use `page.wait_for_selector()` before interactions
- Check element visibility with conditional logic
- Verify CSS selectors match actual HTML

### 4. Mobile Tests Failing
- Ensure responsive CSS is loaded
- Check viewport meta tag
- Verify touch targets are adequate size

## 📈 Performance Benchmarks

### Target Performance Metrics
- **Page Load**: < 2 seconds
- **Navigation**: < 1 second
- **Form Submission**: < 3 seconds
- **Mobile Responsiveness**: Immediate

### Monitoring Performance
```python
def test_performance(page, base_url):
    start = page.evaluate('() => performance.now()')
    page.goto(base_url)
    page.wait_for_load_state('networkidle')
    end = page.evaluate('() => performance.now()')

    load_time = end - start
    assert load_time < 2000, f"Page loaded in {load_time}ms"
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements/development.txt
      - run: playwright install chromium
      - run: python run_tests.py
```

## 📞 Support

For issues with E2E testing:

1. Check test output for specific error messages
2. Review test screenshots in `test-results/`
3. Run single tests in headed mode for debugging
4. Verify Django server is running correctly

## 🎉 Contributing

When adding new tests:

1. Follow existing test patterns
2. Use appropriate markers (`@pytest.mark.e2e`, `@pytest.mark.mobile`)
3. Include both positive and negative test cases
4. Test mobile responsiveness
5. Add performance checks for critical flows

---

**Last Updated**: September 22, 2025
**Test Coverage**: Authentication, Spaces, Budgets, Mobile Navigation
**Status**: ✅ Production Ready