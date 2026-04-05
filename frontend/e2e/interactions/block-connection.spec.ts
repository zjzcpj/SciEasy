// Interaction test: block connections
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, dragBlockToCanvas, connectPorts } from '../fixtures/test-helpers';

test.describe('Block Connection', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
  });

  test.fixme('drag two blocks and connect output to input', async ({ page }) => {
    // Blocked by #184: connection flow may not be fully functional
    await dragBlockToCanvas(page, 'IO Block', { x: 200, y: 200 });
    await dragBlockToCanvas(page, 'Process Block', { x: 500, y: 200 });

    // Connect IO Block output to Process Block input
    await connectPorts(page, 0, 1);

    // Edge should appear
    const edges = page.locator('.react-flow__edge');
    await expect(edges).toHaveCount(1);
  });

  test.fixme('edge appears between connected blocks', async ({ page }) => {
    // Blocked by #184: edge rendering may have issues
    await dragBlockToCanvas(page, 'IO Block', { x: 200, y: 200 });
    await dragBlockToCanvas(page, 'Process Block', { x: 500, y: 200 });

    await connectPorts(page, 0, 1);

    const edge = page.locator('.react-flow__edge').first();
    await expect(edge).toBeVisible();

    // Edge path should exist and have non-zero dimensions
    const edgePath = edge.locator('path').first();
    await expect(edgePath).toBeVisible();
  });

  test.fixme('edge is visible (not zero-opacity or hidden)', async ({ page }) => {
    // Blocked by #184: edge visibility may have issues
    await dragBlockToCanvas(page, 'IO Block', { x: 200, y: 200 });
    await dragBlockToCanvas(page, 'Process Block', { x: 500, y: 200 });

    await connectPorts(page, 0, 1);

    const edge = page.locator('.react-flow__edge').first();
    const path = edge.locator('path').first();

    const opacity = await path.evaluate((el) => {
      return window.getComputedStyle(el).opacity;
    });
    expect(parseFloat(opacity)).toBeGreaterThan(0);

    const visibility = await path.evaluate((el) => {
      return window.getComputedStyle(el).visibility;
    });
    expect(visibility).not.toBe('hidden');
  });
});
