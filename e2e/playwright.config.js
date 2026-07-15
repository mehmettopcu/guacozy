// @ts-check
const { defineConfig, devices } = require('@playwright/test');

// The E2E stack mirrors the documented dev setup: Django on :8000 and the
// Create React App dev server on :3000 (which proxies /api, /accounts, /tunnelws
// to Django). Tests drive the app through :3000.
module.exports = defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      command: 'bash scripts/start-backend.sh',
      url: 'http://127.0.0.1:8000/accounts/login/',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: 'npm --prefix ../frontend start',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      env: { BROWSER: 'none' },
    },
  ],
});
