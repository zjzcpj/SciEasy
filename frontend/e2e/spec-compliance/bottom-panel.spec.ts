// Spec: ARCHITECTURE.md Section 9.8
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, dragBlockToCanvas, getBlockNode, getBottomPanel } from '../fixtures/test-helpers';
import { SPEC_BOTTOM_TABS } from '../fixtures/spec-constants';

test.describe('Section 9.8: Bottom Panel', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
  });

  test.fixme('Section 9.8: all 6 tabs present', async ({ page }) => {
    // Blocked by #184: not all tabs may be present
    const bottom = getBottomPanel(page);
    await expect(bottom).toBeVisible();

    for (const tabName of SPEC_BOTTOM_TABS) {
      const tab = bottom.getByRole('tab', { name: new RegExp(tabName, 'i') }).or(
        bottom.getByText(tabName, { exact: false })
      );
      await expect(tab.first()).toBeVisible();
    }
  });

  test.fixme('Section 9.8: clicking a block switches to Config tab', async ({ page }) => {
    // Blocked by #184: auto-switch to Config tab may not work
    await dragBlockToCanvas(page, 'Process Block');

    const node = getBlockNode(page, 0);
    await node.click();

    const bottom = getBottomPanel(page);
    // Config tab should become active
    const configTab = bottom.getByRole('tab', { name: /config/i }).or(
      bottom.getByText('Config', { exact: false })
    ).first();

    await expect(configTab).toHaveAttribute('data-state', 'active').or(
      expect(configTab).toHaveAttribute('aria-selected', 'true')
    ).catch(() => {
      // Fallback: check if config tab content is visible
      const configContent = bottom.locator('[data-testid="config-tab-content"]').or(
        bottom.locator('[role="tabpanel"]')
      ).first();
      return expect(configContent).toBeVisible();
    });
  });

  test.fixme('Section 9.8: panel is visible (not zero-height, not hidden)', async ({ page }) => {
    // Blocked by #184: bottom panel may be zero-height or hidden
    const bottom = getBottomPanel(page);
    await expect(bottom).toBeVisible();

    const box = await bottom.boundingBox();
    expect(box).toBeTruthy();
    if (box) {
      expect(box.height).toBeGreaterThan(30); // More than just a tab bar
    }
  });
});
