"""
Simple demo test to validate Playwright setup
"""
import pytest
from playwright.sync_api import Page, expect

def test_basic_browser_functionality(page: Page):
    """Test basic browser functionality without Django"""
    # Navigate to a simple website
    page.goto("https://httpbin.org/")

    # Verify we can see the page
    expect(page).to_have_title("httpbin.org")

    # Check for content
    expect(page.locator("h1")).to_contain_text("httpbin")

    print("✓ Basic browser test passed!")

def test_mobile_viewport(page: Page):
    """Test mobile viewport functionality"""
    # Set mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})

    # Navigate to a responsive site
    page.goto("https://httpbin.org/")

    # Should still work on mobile
    expect(page.locator("h1")).to_be_visible()

    print("✓ Mobile viewport test passed!")

def test_form_interaction(page: Page):
    """Test form interaction capabilities"""
    # Go to httpbin forms page
    page.goto("https://httpbin.org/forms/post")

    # Fill out form
    page.fill('input[name="custname"]', 'Test User')
    page.fill('input[name="custtel"]', '123-456-7890')
    page.fill('input[name="custemail"]', 'test@wallai.com')

    # Check form was filled
    expect(page.locator('input[name="custname"]')).to_have_value('Test User')

    print("✓ Form interaction test passed!")

if __name__ == "__main__":
    print("Running Playwright demo tests...")
    pytest.main([__file__, "-v"])