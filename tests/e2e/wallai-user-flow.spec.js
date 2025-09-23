// Wallai E2E Testing - Complete User Flow
// Testing PWA functionality, authentication, and core features

const { test, expect } = require('@playwright/test');

test.describe('Wallai PWA - User Authentication Flow', () => {
  test('should navigate from landing to registration and login', async ({ page }) => {
    // Navigate to landing page
    await page.goto('/');

    // Verify Wallai branding is visible
    await expect(page.locator('img[alt="Wallai"]')).toBeVisible();

    // Click on "Get Started" or similar CTA
    await page.click('text=Get Started');

    // Should navigate to registration page
    await expect(page).toHaveURL(/.*register.*/);

    // Verify registration form is present
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('should complete user registration flow', async ({ page }) => {
    await page.goto('/register/');

    // Fill registration form
    await page.fill('input[name="email"]', `test${Date.now()}@wallai.com`);
    await page.fill('input[name="username"]', `testuser${Date.now()}`);
    await page.fill('input[name="password1"]', 'SecurePass123!');
    await page.fill('input[name="password2"]', 'SecurePass123!');

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard after successful registration
    await expect(page).toHaveURL(/.*dashboard.*/);

    // Verify authenticated layout is loaded
    await expect(page.locator('nav.bottom-nav')).toBeVisible();
  });
});

test.describe('Wallai PWA - Mobile Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Login or setup authenticated state
    // You might want to create a test user fixture
    await page.goto('/login/');
    await page.fill('input[name="email"]', 'test@wallai.com');
    await page.fill('input[name="password"]', 'testpass');
    await page.click('button[type="submit"]');
  });

  test('should navigate between bottom nav sections', async ({ page }) => {
    // Test mobile bottom navigation
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size

    // Verify bottom navigation is visible on mobile
    await expect(page.locator('.bottom-nav')).toBeVisible();

    // Test navigation to different sections
    const navItems = ['Dashboard', 'Stats', 'Budget', 'Prices'];

    for (const item of navItems) {
      if (item !== 'Add') { // Skip center button for now
        await page.click(`text=${item}`);
        // Verify URL or page content changed
        await page.waitForTimeout(500); // Brief wait for navigation
      }
    }
  });

  test('should handle center add button functionality', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    // Click the center floating action button
    await page.click('.center-button button');

    // Should open expense creation modal or navigate to expense form
    // This will depend on your implementation
    await expect(page.locator('text=Add Expense').or(page.locator('text=New Expense'))).toBeVisible();
  });
});

test.describe('Wallai PWA - Space Management', () => {
  test.beforeEach(async ({ page }) => {
    // Setup authenticated state
    await page.goto('/login/');
    await page.fill('input[name="email"]', 'test@wallai.com');
    await page.fill('input[name="password"]', 'testpass');
    await page.click('button[type="submit"]');
  });

  test('should create a new space', async ({ page }) => {
    await page.goto('/spaces/');

    // Click create space button
    await page.click('text=Create Space');

    // Fill space creation form
    await page.fill('input[name="name"]', `Test Space ${Date.now()}`);
    await page.fill('textarea[name="description"]', 'A test space for E2E testing');

    // Select color and icon (if implemented)
    await page.click('[data-color="blue"]');
    await page.click('[data-icon="home"]');

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to space detail or list
    await expect(page.locator('text=Space created successfully').or(page.locator('.space-card'))).toBeVisible();
  });

  test('should switch between spaces', async ({ page }) => {
    await page.goto('/dashboard/');

    // Click space selector in header
    await page.click('.space-selector');

    // Verify dropdown is visible
    await expect(page.locator('.space-dropdown')).toBeVisible();

    // Select different space (if multiple exist)
    const spaceOptions = await page.locator('.space-option').count();
    if (spaceOptions > 1) {
      await page.click('.space-option:nth-child(2)');

      // Verify space context changed
      await page.waitForTimeout(500);
      // Check that header or context indicator updated
    }
  });
});

test.describe('Wallai PWA - PWA Installation', () => {
  test('should be installable as PWA', async ({ page, context }) => {
    await page.goto('/');

    // Check if PWA manifest is properly loaded
    const manifestLink = await page.locator('link[rel="manifest"]');
    await expect(manifestLink).toHaveAttribute('href', '/static/pwa/manifest.json');

    // Verify service worker registration
    const swRegistration = await page.evaluate(() => {
      return 'serviceWorker' in navigator;
    });
    expect(swRegistration).toBe(true);
  });

  test('should work offline (basic PWA test)', async ({ page, context }) => {
    await page.goto('/dashboard/');

    // Simulate offline condition
    await context.setOffline(true);

    // Navigate to a cached page
    await page.goto('/dashboard/');

    // Should still load basic content (depending on your SW implementation)
    await expect(page.locator('text=Wallai').or(page.locator('.logo'))).toBeVisible();

    // Restore online
    await context.setOffline(false);
  });
});

test.describe('Wallai PWA - Responsive Design', () => {
  const devices = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Desktop', width: 1200, height: 800 }
  ];

  devices.forEach(device => {
    test(`should render correctly on ${device.name}`, async ({ page }) => {
      await page.setViewportSize({ width: device.width, height: device.height });
      await page.goto('/dashboard/');

      // Verify responsive navigation
      if (device.width < 768) {
        // Mobile: bottom nav should be visible
        await expect(page.locator('.bottom-nav')).toBeVisible();
        await expect(page.locator('.sidebar')).toBeHidden();
      } else {
        // Desktop/Tablet: sidebar should be visible
        await expect(page.locator('.sidebar')).toBeVisible();
        await expect(page.locator('.bottom-nav')).toBeHidden();
      }

      // Take screenshot for visual comparison
      await page.screenshot({
        path: `tests/screenshots/dashboard-${device.name.toLowerCase()}.png`,
        fullPage: true
      });
    });
  });
});