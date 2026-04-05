// Spec: ARCHITECTURE.md Section 9.5
import { test, expect } from '@playwright/test';
import { setupMocks, gotoApp, createProject, dragBlockToCanvas, getBlockNode } from '../fixtures/test-helpers';
import { SPEC_BLOCK_NODE } from '../fixtures/spec-constants';

test.describe('Section 9.5: Block Node Design', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
    await gotoApp(page);
    await createProject(page);
    await dragBlockToCanvas(page, 'Process Block');
  });

  test.fixme('Section 9.5: block node width is 280px', async ({ page }) => {
    // Blocked by #184: block node width may not match spec
    const node = getBlockNode(page, 0);
    const box = await node.boundingBox();
    expect(box).toBeTruthy();
    if (box) {
      expect(box.width).toBeCloseTo(SPEC_BLOCK_NODE.width, -1);
    }
  });

  test.fixme('Section 9.5: block has 3-part structure (header, inline config, footer)', async ({ page }) => {
    // Blocked by #184: block structure may not have distinct header/config/footer
    const node = getBlockNode(page, 0);

    // Look for header section
    const header = node.locator('[data-testid="block-header"]').or(
      node.locator('[class*="header"]')
    ).first();
    await expect(header).toBeVisible();

    // Look for inline config section (form controls)
    const config = node.locator('[data-testid="block-inline-config"]').or(
      node.locator('input, select, [class*="param"]')
    ).first();
    await expect(config).toBeVisible();

    // Look for footer section with state badge
    const footer = node.locator('[data-testid="block-footer"]').or(
      node.locator('[class*="footer"]')
    ).first();
    await expect(footer).toBeVisible();
  });

  test.fixme('Section 9.5: header contains block name, run button, restart button', async ({ page }) => {
    // Blocked by #184: header elements may not all be present
    const node = getBlockNode(page, 0);

    // Block name
    await expect(node.getByText('Process Block')).toBeVisible();

    // Per-node run button [▶]
    const runButton = node.locator('[data-testid="block-run-button"]').or(
      node.getByRole('button', { name: /run|▶/i })
    ).first();
    await expect(runButton).toBeVisible();

    // Per-node restart/start-from-here button [↻]
    const restartButton = node.locator('[data-testid="block-restart-button"]').or(
      node.getByRole('button', { name: /restart|start from here|↻/i })
    ).first();
    await expect(restartButton).toBeVisible();
  });

  test.fixme('Section 9.5: inline config renders form controls (not placeholder text)', async ({ page }) => {
    // Blocked by #184: inline config may render placeholder text instead of form controls
    const node = getBlockNode(page, 0);

    // Should have actual form controls, not just text
    const formControls = node.locator('input, select, [role="combobox"], [role="checkbox"]');
    const count = await formControls.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test.fixme('Section 9.5: state badge is in footer (not header)', async ({ page }) => {
    // Blocked by #184: state badge location may not be in footer
    const node = getBlockNode(page, 0);

    // State badge should contain state text like "Idle", "Ready", etc.
    const stateBadge = node.locator('[data-testid="block-state-badge"]').or(
      node.getByText(/idle|ready|running|done|error/i)
    ).first();
    await expect(stateBadge).toBeVisible();

    // Verify it's in the lower portion of the node
    const nodeBox = await node.boundingBox();
    const badgeBox = await stateBadge.boundingBox();
    if (nodeBox && badgeBox) {
      const nodeMidY = nodeBox.y + nodeBox.height / 2;
      expect(badgeBox.y).toBeGreaterThan(nodeMidY);
    }
  });

  test.fixme('Section 9.5: per-node run button exists', async ({ page }) => {
    // Blocked by #184: per-node run button may not exist
    const node = getBlockNode(page, 0);
    const runButton = node.locator('[data-testid="block-run-button"]').or(
      node.getByRole('button', { name: /run|▶/i })
    ).first();
    await expect(runButton).toBeVisible();
  });

  test.fixme('Section 9.5: per-node start-from-here button exists', async ({ page }) => {
    // Blocked by #184: start-from-here button may not exist
    const node = getBlockNode(page, 0);
    const restartButton = node.locator('[data-testid="block-restart-button"]').or(
      node.getByRole('button', { name: /restart|start from here|↻/i })
    ).first();
    await expect(restartButton).toBeVisible();
  });
});
