// Spec: ARCHITECTURE.md Section 9.2
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, getPalettePanel, getPreviewPanel, getBottomPanel } from '../fixtures/test-helpers';
import { SPEC_PANEL_DEFAULTS } from '../fixtures/spec-constants';

test.describe('Section 9.2: Layout', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
  });

  test.fixme('Section 9.2: three panels visible simultaneously (palette, canvas, preview)', async ({ page }) => {
    // Blocked by #184: requires project creation flow and full layout to be functional
    const palette = getPalettePanel(page);
    const canvas = page.locator('.react-flow');
    const preview = getPreviewPanel(page);

    await expect(palette).toBeVisible();
    await expect(canvas).toBeVisible();
    await expect(preview).toBeVisible();
  });

  test.fixme('Section 9.2: bottom panel visible alongside palette (not hidden behind it)', async ({ page }) => {
    // Blocked by #184: bottom panel may overlap or be hidden behind palette
    const palette = getPalettePanel(page);
    const bottom = getBottomPanel(page);

    await expect(palette).toBeVisible();
    await expect(bottom).toBeVisible();

    const paletteBox = await palette.boundingBox();
    const bottomBox = await bottom.boundingBox();
    expect(paletteBox).toBeTruthy();
    expect(bottomBox).toBeTruthy();

    // Bottom panel should NOT overlap with palette — it should be in the center column
    if (paletteBox && bottomBox) {
      expect(bottomBox.x).toBeGreaterThanOrEqual(paletteBox.x + paletteBox.width - 5);
    }
  });

  test.fixme('Section 9.2: palette default width ~220px (within 20% tolerance)', async ({ page }) => {
    // Blocked by #184: palette width may not match spec default
    const palette = getPalettePanel(page);
    const box = await palette.boundingBox();
    expect(box).toBeTruthy();
    if (box) {
      const expected = SPEC_PANEL_DEFAULTS.palette.default;
      const tolerance = expected * 0.2;
      expect(box.width).toBeGreaterThan(expected - tolerance);
      expect(box.width).toBeLessThan(expected + tolerance);
    }
  });

  test.fixme('Section 9.2: preview default width ~320px (within 20% tolerance)', async ({ page }) => {
    // Blocked by #184: preview width may not match spec default
    const preview = getPreviewPanel(page);
    const box = await preview.boundingBox();
    expect(box).toBeTruthy();
    if (box) {
      const expected = SPEC_PANEL_DEFAULTS.preview.default;
      const tolerance = expected * 0.2;
      expect(box.width).toBeGreaterThan(expected - tolerance);
      expect(box.width).toBeLessThan(expected + tolerance);
    }
  });

  test.fixme('Section 9.2: panels have drag handles for resizing', async ({ page }) => {
    // Blocked by #184: drag handles may not be present or identifiable
    // Look for resize handles between panels
    const handles = page.locator('[data-panel-group-direction] [data-resize-handle]').or(
      page.locator('[class*="resize-handle"]')
    );
    const count = await handles.count();
    // Should have at least 2 horizontal handles (palette|canvas, canvas|preview)
    // and 1 vertical handle (canvas|bottom)
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test.fixme('Section 9.2: Ctrl+B toggles palette collapse', async ({ page }) => {
    // Blocked by #184: keyboard shortcut may not be wired
    const palette = getPalettePanel(page);
    await expect(palette).toBeVisible();
    const initialBox = await palette.boundingBox();

    await page.keyboard.press('Control+b');
    await page.waitForTimeout(300);

    const collapsedBox = await palette.boundingBox();
    if (initialBox && collapsedBox) {
      // Collapsed palette should be significantly narrower (icon-only ~48px)
      expect(collapsedBox.width).toBeLessThan(initialBox.width * 0.5);
    }

    // Toggle back
    await page.keyboard.press('Control+b');
    await page.waitForTimeout(300);

    const restoredBox = await palette.boundingBox();
    if (initialBox && restoredBox) {
      expect(restoredBox.width).toBeCloseTo(initialBox.width, -1);
    }
  });

  test.fixme('Section 9.2: Ctrl+D toggles preview collapse', async ({ page }) => {
    // Blocked by #184: keyboard shortcut may not be wired
    const preview = getPreviewPanel(page);
    await expect(preview).toBeVisible();

    await page.keyboard.press('Control+d');
    await page.waitForTimeout(300);

    // Preview should be hidden (0px width) when collapsed
    const collapsedBox = await preview.boundingBox();
    if (collapsedBox) {
      expect(collapsedBox.width).toBeLessThanOrEqual(5);
    }
  });

  test.fixme('Section 9.2: Ctrl+J toggles bottom panel collapse', async ({ page }) => {
    // Blocked by #184: keyboard shortcut may not be wired
    const bottom = getBottomPanel(page);
    await expect(bottom).toBeVisible();
    const initialBox = await bottom.boundingBox();

    await page.keyboard.press('Control+j');
    await page.waitForTimeout(300);

    const collapsedBox = await bottom.boundingBox();
    if (initialBox && collapsedBox) {
      // Collapsed bottom panel should show only tab bar (~32px height)
      expect(collapsedBox.height).toBeLessThan(initialBox.height * 0.5);
    }
  });
});
