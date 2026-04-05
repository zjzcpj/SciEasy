// Interaction test: block drag and drop
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, dragBlockToCanvas, getBlockNode } from '../fixtures/test-helpers';

test.describe('Block Drag and Drop', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
  });

  test.fixme('drag IO Block from palette to canvas', async ({ page }) => {
    // Blocked by #184: drag-drop from palette may not be fully functional
    await dragBlockToCanvas(page, 'IO Block', { x: 300, y: 200 });

    // Block should appear on canvas
    const nodes = page.locator('.react-flow__node');
    await expect(nodes).toHaveCount(1);
  });

  test.fixme('block appears on canvas after drop', async ({ page }) => {
    // Blocked by #184: block rendering after drop may have issues
    await dragBlockToCanvas(page, 'IO Block', { x: 300, y: 200 });

    const node = getBlockNode(page, 0);
    await expect(node).toBeVisible();

    // Block should display its name
    await expect(node.getByText(/IO Block/i)).toBeVisible();
  });

  test.fixme('drag Process Block, verify two blocks on canvas', async ({ page }) => {
    // Blocked by #184: multiple blocks on canvas may not work correctly
    await dragBlockToCanvas(page, 'IO Block', { x: 200, y: 200 });
    await dragBlockToCanvas(page, 'Process Block', { x: 500, y: 200 });

    const nodes = page.locator('.react-flow__node');
    await expect(nodes).toHaveCount(2);
  });

  test.fixme('block position is near the drop point (within 100px tolerance)', async ({ page }) => {
    // Blocked by #184: block positioning after drop may be off
    const dropX = 350;
    const dropY = 250;
    await dragBlockToCanvas(page, 'IO Block', { x: dropX, y: dropY });

    const node = getBlockNode(page, 0);
    const box = await node.boundingBox();
    expect(box).toBeTruthy();

    if (box) {
      const canvas = page.locator('.react-flow');
      const canvasBox = await canvas.boundingBox();
      if (canvasBox) {
        // Position relative to canvas
        const relativeX = box.x - canvasBox.x;
        const relativeY = box.y - canvasBox.y;
        // Allow 100px tolerance for position
        expect(Math.abs(relativeX - dropX)).toBeLessThan(100);
        expect(Math.abs(relativeY - dropY)).toBeLessThan(100);
      }
    }
  });
});
