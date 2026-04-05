// Spec: ARCHITECTURE.md Section 9.3
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject } from '../fixtures/test-helpers';
import { SPEC_TOOLBAR_BUTTONS } from '../fixtures/spec-constants';

test.describe('Section 9.3: Toolbar', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
  });

  test.fixme('Section 9.3: all file operation buttons present (Import, Save, Export)', async ({ page }) => {
    // Blocked by #184: toolbar buttons may not all be present
    // TODO: add data-testid="toolbar" to Toolbar component
    const toolbar = page.locator('[data-testid="toolbar"]').or(
      page.locator('header').or(page.locator('[class*="toolbar"]'))
    ).first();
    await expect(toolbar).toBeVisible();

    for (const label of SPEC_TOOLBAR_BUTTONS.fileOps) {
      const button = toolbar.getByRole('button', { name: new RegExp(label, 'i') }).or(
        toolbar.getByText(label, { exact: false })
      );
      await expect(button.first()).toBeVisible();
    }
  });

  test.fixme('Section 9.3: all execution control buttons present (Run, Pause, Stop, Reset)', async ({ page }) => {
    // Blocked by #184: execution buttons may not all be present
    const toolbar = page.locator('[data-testid="toolbar"]').or(
      page.locator('header').or(page.locator('[class*="toolbar"]'))
    ).first();

    for (const label of SPEC_TOOLBAR_BUTTONS.execution) {
      const button = toolbar.getByRole('button', { name: new RegExp(label, 'i') }).or(
        toolbar.getByText(label, { exact: false })
      );
      await expect(button.first()).toBeVisible();
    }
  });

  test.fixme('Section 9.3: Delete and Reload Blocks buttons present', async ({ page }) => {
    // Blocked by #184: edit buttons may not all be present
    const toolbar = page.locator('[data-testid="toolbar"]').or(
      page.locator('header').or(page.locator('[class*="toolbar"]'))
    ).first();

    for (const label of SPEC_TOOLBAR_BUTTONS.edit) {
      const button = toolbar.getByRole('button', { name: new RegExp(label, 'i') }).or(
        toolbar.getByText(label, { exact: false })
      );
      await expect(button.first()).toBeVisible();
    }
  });

  test.fixme('Section 9.3: visual grouping separators between button groups', async ({ page }) => {
    // Blocked by #184: separators may not be present
    const toolbar = page.locator('[data-testid="toolbar"]').or(
      page.locator('header').or(page.locator('[class*="toolbar"]'))
    ).first();

    // Look for separator elements (radix-ui separators or custom dividers)
    const separators = toolbar.locator('[data-orientation="vertical"]').or(
      toolbar.locator('[role="separator"]').or(
        toolbar.locator('[class*="separator"]')
      )
    );
    // Expect at least 2 separators (between 3 groups: file ops, execution, edit)
    const count = await separators.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });
});
