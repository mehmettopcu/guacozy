// @ts-check
// These tests exercise the UI libraries most at risk in the React 18 upgrade:
// FlexLayout (tabs), react-contexify (context menus) and semantic-ui-react
// (modals), plus the ticket/folder APIs (CSRF-protected POSTs).
const { test, expect } = require('@playwright/test');

const USER = 'e2e';
const PASSWORD = 'e2e-password-123';

// The connection tree is scoped to #connectionTree so assertions are not
// confused by the tickets sidebar (which also lists connection names once a
// ticket exists — the E2E backend DB is shared across tests).
function tree(page) {
  return page.locator('#connectionTree');
}

async function loginAndExpand(page) {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', USER);
  await page.fill('input[name="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL('http://localhost:3000/');
  await expect(tree(page).getByText('E2E Folder')).toBeVisible();
  // Reveal the connection nested in the folder.
  await page.locator('[title="Expand all"]').click();
  await expect(tree(page).getByText('E2E Test RDP')).toBeVisible();
}

test('double-clicking a connection opens a FlexLayout session tab', async ({ page }) => {
  await loginAndExpand(page);

  // Double-click creates a ticket (POST /api/tickets/) and opens a tab.
  await tree(page).getByText('E2E Test RDP').dblclick();

  // The FlexLayout tab strip should now contain a tab for the connection.
  await expect(
    page.locator('.flexlayout__tab_button', { hasText: 'E2E Test RDP' })
  ).toBeVisible();
});

test('folder context menu creates a subfolder via the modal', async ({ page }) => {
  await loginAndExpand(page);

  // react-contexify menu on right-click.
  await tree(page).getByText('E2E Folder').click({ button: 'right' });
  const menu = page.locator('.react-contexify');
  await expect(menu).toBeVisible();
  await menu.getByText('New', { exact: true }).click();

  // semantic-ui-react modal.
  const modal = page.locator('.ui.modal');
  await expect(modal.getByText('Create folder under E2E Folder')).toBeVisible();
  // Submit via Enter (the Form's onSubmit); the basic modal's button can be
  // overlapped by the sidebar container, which intercepts pointer events.
  await modal.locator('input').fill('E2E Child');
  await modal.locator('input').press('Enter');

  // The new folder should appear in the tree after it reloads.
  await page.locator('[title="Expand all"]').click();
  await expect(tree(page).getByText('E2E Child')).toBeVisible();
});
