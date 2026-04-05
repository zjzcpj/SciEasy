// Spec: ARCHITECTURE.md Section 9.6
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, dragBlockToCanvas } from '../fixtures/test-helpers';
import { SPEC_TYPE_COLORS } from '../fixtures/spec-constants';

test.describe('Section 9.6: Port Type Colour System', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
    // Add blocks that have different port types
    await dragBlockToCanvas(page, 'IO Block', { x: 200, y: 200 });
    await dragBlockToCanvas(page, 'Process Block', { x: 500, y: 200 });
  });

  test.fixme('Section 9.6: each port coloured individually by data type', async ({ page }) => {
    // Blocked by #184: ports may not be individually coloured
    const handles = page.locator('.react-flow__handle');
    const count = await handles.count();
    expect(count).toBeGreaterThanOrEqual(2);

    // Collect colors of all handles
    const colors: string[] = [];
    for (let i = 0; i < count; i++) {
      const handle = handles.nth(i);
      const bgColor = await handle.evaluate((el) => {
        return window.getComputedStyle(el).backgroundColor;
      });
      colors.push(bgColor);
    }

    // Not all ports should share the same color
    const uniqueColors = new Set(colors);
    expect(uniqueColors.size).toBeGreaterThan(1);
  });

  test.fixme('Section 9.6: Array port colour matches spec (#3B82F6)', async ({ page }) => {
    // Blocked by #184: port colours may not match spec hex values
    // IO Block has output of type Array
    const outputHandle = page.locator('.react-flow__handle.source').first();
    const bgColor = await outputHandle.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.backgroundColor;
    });

    // Convert hex #3B82F6 to rgb(59, 130, 246)
    expect(bgColor).toBe('rgb(59, 130, 246)');
  });

  test.fixme('Section 9.6: DataFrame port colour matches spec (#F97316)', async ({ page }) => {
    // Blocked by #184: port colours may not match spec hex values
    // Process Block has output of type DataFrame
    const processOutputHandle = page.locator('.react-flow__node').nth(1)
      .locator('.react-flow__handle.source').first();
    const bgColor = await processOutputHandle.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.backgroundColor;
    });

    // Convert hex #F97316 to rgb(249, 115, 22)
    expect(bgColor).toBe('rgb(249, 115, 22)');
  });

  test.fixme('Section 9.6: DataObject port colour matches spec (#E5E7EB)', async ({ page }) => {
    // Blocked by #184: port colours may not match spec hex values
    // IO Block has input of type DataObject (fallback light grey)
    const inputHandle = page.locator('.react-flow__node').first()
      .locator('.react-flow__handle.target').first();
    const bgColor = await inputHandle.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.backgroundColor;
    });

    // Convert hex #E5E7EB to rgb(229, 231, 235)
    expect(bgColor).toBe('rgb(229, 231, 235)');
  });

  test.fixme('Section 9.6: ports NOT sharing a single colour per node', async ({ page }) => {
    // Blocked by #184: ports may share the same colour per node
    // A node with both input and output of different types should have different handle colours
    const node = page.locator('.react-flow__node').first();
    const handles = node.locator('.react-flow__handle');
    const count = await handles.count();

    if (count >= 2) {
      const colors: string[] = [];
      for (let i = 0; i < count; i++) {
        const bgColor = await handles.nth(i).evaluate((el) => {
          return window.getComputedStyle(el).backgroundColor;
        });
        colors.push(bgColor);
      }

      const uniqueColors = new Set(colors);
      // If input and output have different types, colors should differ
      expect(uniqueColors.size).toBeGreaterThan(1);
    }
  });
});
