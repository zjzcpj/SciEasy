// Interaction test: project lifecycle
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp } from '../fixtures/test-helpers';

test.describe('Project Lifecycle', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
  });

  test.fixme('create new project with name and description', async ({ page }) => {
    // Blocked by #184: project creation flow may not be fully implemented
    // TODO: add data-testid="new-project-button" to WelcomeScreen
    await page.click('text=New');

    // Fill project name
    await page.fill('input[placeholder*="name" i]', 'Test Project');

    // Fill description if input exists
    const descInput = page.locator('textarea[placeholder*="description" i]').or(
      page.locator('input[placeholder*="description" i]')
    );
    if (await descInput.count() > 0) {
      await descInput.first().fill('A test project for E2E testing');
    }

    // Click Create
    // TODO: add data-testid="create-project-button" to ProjectDialog
    await page.click('text=Create');

    // Editor canvas should appear
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 10000 });
  });

  test.fixme('project name appears in toolbar after creation', async ({ page }) => {
    // Blocked by #184: project name display in toolbar may not be implemented
    await page.click('text=New');
    await page.fill('input[placeholder*="name" i]', 'My Science Project');
    await page.click('text=Create');
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 10000 });

    // Project name should be visible somewhere in the toolbar area
    await expect(page.getByText('My Science Project')).toBeVisible();
  });

  test.fixme('save project via Save button', async ({ page }) => {
    // Blocked by #184: save flow may not be fully implemented
    await page.click('text=New');
    await page.fill('input[placeholder*="name" i]', 'Save Test');
    await page.click('text=Create');
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 10000 });

    let saveCalled = false;
    await page.route('**/api/projects/*/save', async (route) => {
      saveCalled = true;
      await route.fulfill({ json: { success: true } });
    });
    await page.route('**/api/workflows/*', async (route) => {
      if (route.request().method() === 'PUT') {
        saveCalled = true;
        await route.fulfill({ json: { success: true } });
      } else {
        await route.continue();
      }
    });

    // Click Save button
    const saveButton = page.getByRole('button', { name: /save/i }).first();
    await saveButton.click();
    await page.waitForTimeout(500);
  });

  test.fixme('save project via Ctrl+S', async ({ page }) => {
    // Blocked by #184: Ctrl+S may not be wired
    await page.click('text=New');
    await page.fill('input[placeholder*="name" i]', 'Shortcut Test');
    await page.click('text=Create');
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 10000 });

    await page.keyboard.press('Control+s');
    await page.waitForTimeout(500);
  });
});
