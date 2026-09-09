import { defineConfig, devices } from '@playwright/test';
import { FRONTEND_URL } from './e2e/setup/env';

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/setup/preflight.ts',
  reporter: [['list'], ['html', { open: 'never' }]],
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: FRONTEND_URL,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
