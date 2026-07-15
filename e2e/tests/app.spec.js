// @ts-check
const { test, expect } = require('@playwright/test');

const USER = 'e2e';
const PASSWORD = 'e2e-password-123';

async function login(page) {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', USER);
  await page.fill('input[name="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  // Django redirects to '/', which loads the SPA.
  await page.waitForURL('http://localhost:3000/');
}

test('unauthenticated visit redirects to the Django login page', async ({ page }) => {
  await page.goto('/');
  await page.waitForURL(/\/accounts\/login\//);
  await expect(page.locator('input[name="username"]')).toBeVisible();
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});

test('login renders the app shell with the seeded folder and connection', async ({ page }) => {
  await login(page);

  // The seeded folder is a root node and should render once the connections
  // tree API responds (this proves auth + /api/connections/tree worked).
  await expect(page.getByText('E2E Folder')).toBeVisible();

  // The folder only holds a connection (no subfolders), so it starts collapsed.
  // Use the "Expand all" toolbar button to reveal the connection.
  await page.locator('[title="Expand all"]').click();
  await expect(page.getByText('E2E Test RDP')).toBeVisible();
});

test('logout returns the user to the login page', async ({ page }) => {
  await login(page);
  await expect(page.getByText('E2E Folder')).toBeVisible();

  // The logout control lives in the settings sidebar; navigating to the logout
  // endpoint exercises the same server logout the UI triggers.
  await page.goto('/accounts/logout/');
  await page.goto('/');
  await page.waitForURL(/\/accounts\/login\//);
  await expect(page.locator('input[name="username"]')).toBeVisible();
});
