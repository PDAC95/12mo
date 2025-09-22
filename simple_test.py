"""
Simple offline test to demonstrate Playwright functionality
"""
import pytest
from playwright.sync_api import Page, expect

def test_playwright_basics(page: Page):
    """Test basic Playwright functionality with local content"""
    # Create a simple HTML page in memory
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wallai Test Page</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .wallai-button {
                background: linear-gradient(135deg, #4ADE80, #5EEAD4);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>Wallai - E2E Testing Demo</h1>
        <p>This demonstrates Playwright working with Wallai!</p>
        <button class="wallai-button" onclick="this.textContent='Clicked!'">
            Click Me
        </button>
        <input type="text" id="test-input" placeholder="Type here...">
    </body>
    </html>
    """

    # Load the HTML directly
    page.set_content(html_content)

    # Test basic elements
    expect(page).to_have_title("Wallai Test Page")
    expect(page.locator("h1")).to_contain_text("Wallai")

    # Test button interaction
    button = page.locator(".wallai-button")
    expect(button).to_be_visible()
    button.click()
    expect(button).to_contain_text("Clicked!")

    # Test input interaction
    input_field = page.locator("#test-input")
    input_field.fill("Wallai Testing!")
    expect(input_field).to_have_value("Wallai Testing!")

    print("✓ All Playwright functionality tests passed!")

def test_mobile_responsiveness(page: Page):
    """Test mobile responsiveness"""
    # Set mobile viewport (iPhone size)
    page.set_viewport_size({"width": 375, "height": 667})

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mobile Test</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            .mobile-test {
                width: 100%;
                max-width: 350px;
                background: #4ADE80;
                color: white;
                padding: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="mobile-test">
            <h2>Mobile Testing</h2>
            <p>This should fit on mobile screens</p>
        </div>
    </body>
    </html>
    """

    page.set_content(html_content)

    # Check mobile layout
    mobile_div = page.locator(".mobile-test")
    expect(mobile_div).to_be_visible()

    # Get viewport dimensions
    viewport = page.viewport_size
    assert viewport['width'] == 375, "Mobile viewport width should be 375px"

    print("✓ Mobile responsiveness test passed!")

if __name__ == "__main__":
    print("🎭 Running Wallai Playwright Demo...")
    pytest.main([__file__, "-v", "--tb=short"])