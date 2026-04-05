import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'html',

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Auto-start dev servers for local development
  webServer: [
    {
      command: 'cd .. && python -m uvicorn scieasy.api.app:create_app --factory --port 8000',
      port: 8000,
      timeout: 30000,
      reuseExistingServer: !process.env.CI,
      cwd: '..',
    },
    {
      command: 'npm run dev',
      port: 5173,
      timeout: 15000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
