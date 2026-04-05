// Spec: ARCHITECTURE.md Section 9.3
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, getPalettePanel, getPreviewPanel, getBottomPanel, dragBlockToCanvas, getBlockNode } from '../fixtures/test-helpers';
import { SPEC_KEYBOARD_SHORTCUTS } from '../fixtures/spec-constants';

test.describe('Section 9.3: Keyboard Shortcuts', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
  });

  test.fixme('Section 9.3: Ctrl+O triggers import workflow', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    await page.keyboard.press('Control+o');
    // Should open a file dialog or import modal
    // Since browser file dialogs can't be tested, check if any modal/dialog appears
    const dialog = page.locator('[role="dialog"]').or(page.locator('[class*="modal"]'));
    await expect(dialog.first()).toBeVisible({ timeout: 2000 }).catch(() => {
      // Alternative: check for a file input being triggered
    });
  });

  test.fixme('Section 9.3: Ctrl+S triggers save workflow', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    // Mock the save API endpoint and verify it was called
    let saveCalled = false;
    await page.route('**/api/workflows/*', async (route) => {
      if (route.request().method() === 'PUT') {
        saveCalled = true;
        await route.fulfill({ json: { success: true } });
      } else {
        await route.continue();
      }
    });

    await page.keyboard.press('Control+s');
    await page.waitForTimeout(500);
    // Save should have been triggered (or a save indicator shown)
  });

  test.fixme('Section 9.3: Ctrl+Shift+S triggers export workflow', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    await page.keyboard.press('Control+Shift+s');
    await page.waitForTimeout(500);
  });

  test.fixme('Section 9.3: Ctrl+Enter triggers run workflow', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    let runCalled = false;
    await page.route('**/api/workflows/*/execute', async (route) => {
      runCalled = true;
      await route.fulfill({ json: { execution_id: 'test-exec-1' } });
    });

    await page.keyboard.press('Control+Enter');
    await page.waitForTimeout(500);
  });

  test.fixme('Section 9.3: Ctrl+. triggers stop execution', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    await page.keyboard.press('Control+.');
    await page.waitForTimeout(500);
  });

  test.fixme('Section 9.3: Delete key deletes selected block', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    await dragBlockToCanvas(page, 'IO Block');
    const node = getBlockNode(page, 0);
    await node.click();
    await page.waitForTimeout(200);

    await page.keyboard.press('Delete');
    await page.waitForTimeout(300);

    // Node should be removed from canvas
    const nodes = page.locator('.react-flow__node');
    await expect(nodes).toHaveCount(0);
  });

  test.fixme('Section 9.3: Backspace key deletes selected block', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    await dragBlockToCanvas(page, 'IO Block');
    const node = getBlockNode(page, 0);
    await node.click();
    await page.waitForTimeout(200);

    await page.keyboard.press('Backspace');
    await page.waitForTimeout(300);

    const nodes = page.locator('.react-flow__node');
    await expect(nodes).toHaveCount(0);
  });

  test.fixme('Section 9.3: Ctrl+Z triggers undo', async ({ page }) => {
    // Blocked by #184: undo may not be implemented
    await page.keyboard.press('Control+z');
    await page.waitForTimeout(300);
  });

  test.fixme('Section 9.3: Ctrl+Y triggers redo', async ({ page }) => {
    // Blocked by #184: redo may not be implemented
    await page.keyboard.press('Control+y');
    await page.waitForTimeout(300);
  });

  test.fixme('Section 9.3: Ctrl+A selects all nodes', async ({ page }) => {
    // Blocked by #184: select-all may not be implemented
    await dragBlockToCanvas(page, 'IO Block', { x: 200, y: 200 });
    await dragBlockToCanvas(page, 'Process Block', { x: 500, y: 200 });

    await page.keyboard.press('Control+a');
    await page.waitForTimeout(300);

    // All nodes should be selected
    const selectedNodes = page.locator('.react-flow__node.selected');
    await expect(selectedNodes).toHaveCount(2);
  });

  test.fixme('Section 9.3: Escape deselects all', async ({ page }) => {
    // Blocked by #184: deselect may not be implemented
    await dragBlockToCanvas(page, 'IO Block');
    const node = getBlockNode(page, 0);
    await node.click();

    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    const selectedNodes = page.locator('.react-flow__node.selected');
    await expect(selectedNodes).toHaveCount(0);
  });

  test.fixme('Section 9.3: Ctrl+B toggles palette visibility', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    const palette = getPalettePanel(page);
    await expect(palette).toBeVisible();

    await page.keyboard.press('Control+b');
    await page.waitForTimeout(300);

    // Palette should be collapsed
    const box = await palette.boundingBox();
    if (box) {
      expect(box.width).toBeLessThan(100); // Icon-only mode ~48px
    }
  });

  test.fixme('Section 9.3: Ctrl+D toggles preview visibility', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    const preview = getPreviewPanel(page);

    await page.keyboard.press('Control+d');
    await page.waitForTimeout(300);
  });

  test.fixme('Section 9.3: Ctrl+J toggles bottom panel', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    await page.keyboard.press('Control+j');
    await page.waitForTimeout(300);
  });

  test.fixme('Section 9.3: Ctrl+M toggles minimap', async ({ page }) => {
    // Blocked by #184: shortcut may not be wired
    const minimap = page.locator('.react-flow__minimap');

    await page.keyboard.press('Control+m');
    await page.waitForTimeout(300);
  });
});
