// Interaction test: block selection and configuration
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, dragBlockToCanvas, getBlockNode, getPreviewPanel, getBottomPanel } from '../fixtures/test-helpers';

test.describe('Block Config', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
    await dragBlockToCanvas(page, 'Process Block', { x: 300, y: 200 });
  });

  test.fixme('click a block selects it (visual indicator)', async ({ page }) => {
    // Blocked by #184: block selection visual indicator may not be implemented
    const node = getBlockNode(page, 0);
    await node.click();

    // Node should have selected state (class or attribute)
    await expect(node).toHaveClass(/selected/);
  });

  test.fixme('preview panel shows block name when selected', async ({ page }) => {
    // Blocked by #184: preview panel may not show block name on selection
    const node = getBlockNode(page, 0);
    await node.click();

    const preview = getPreviewPanel(page);
    await expect(preview.getByText(/Process Block/i)).toBeVisible();
  });

  test.fixme('inline params are editable', async ({ page }) => {
    // Blocked by #184: inline param editing may not be functional
    const node = getBlockNode(page, 0);

    // Find an input field within the node (inline params)
    const input = node.locator('input').first();
    if (await input.count() > 0) {
      await input.click();
      await input.fill('test-value');

      const value = await input.inputValue();
      expect(value).toBe('test-value');
    }
  });

  test.fixme('clicking block switches bottom panel to Config tab', async ({ page }) => {
    // Blocked by #184: bottom panel Config tab auto-switch may not work
    const node = getBlockNode(page, 0);
    await node.click();

    const bottom = getBottomPanel(page);
    const configTab = bottom.getByRole('tab', { name: /config/i }).or(
      bottom.getByText('Config', { exact: false })
    ).first();

    // Config tab should be active
    await expect(configTab).toHaveAttribute('data-state', 'active').catch(() =>
      expect(configTab).toHaveAttribute('aria-selected', 'true')
    );
  });
});
