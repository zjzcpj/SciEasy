/**
 * Shared Playwright test helpers for SciEasy E2E tests.
 *
 * These helpers use data-testid selectors where available.
 * Where data-testid attributes are missing from components,
 * fallback selectors are used with TODO comments.
 */
import { Page, Locator, expect } from '@playwright/test';

/**
 * Mock the block list API to provide deterministic test data.
 * Call before navigating to avoid race conditions.
 */
export async function mockBlocksApi(page: Page) {
  await page.route('**/api/blocks', async (route) => {
    await route.fulfill({
      json: [
        {
          name: 'io_block',
          category: 'IO',
          display_name: 'IO Block',
          description: 'Load and save data',
          inputs: [{ name: 'input', type: 'DataObject' }],
          outputs: [{ name: 'output', type: 'Array' }],
          params: {
            path: { type: 'string', default: '', ui_priority: 1 },
            format: { type: 'string', default: 'auto', ui_priority: 2 },
          },
        },
        {
          name: 'process_block',
          category: 'Process',
          display_name: 'Process Block',
          description: 'Process data',
          inputs: [{ name: 'data', type: 'Array' }],
          outputs: [{ name: 'result', type: 'DataFrame' }],
          params: {
            method: { type: 'string', default: 'default', ui_priority: 1 },
            threshold: { type: 'number', default: 0.5, ui_priority: 2 },
            normalize: { type: 'boolean', default: true, ui_priority: 3 },
          },
        },
        {
          name: 'code_block',
          category: 'Code',
          display_name: 'Code Block',
          description: 'Run custom code',
          inputs: [{ name: 'input', type: 'DataObject' }],
          outputs: [{ name: 'output', type: 'DataObject' }],
          params: {
            language: { type: 'string', default: 'python', ui_priority: 1 },
          },
        },
      ],
    });
  });
}

/**
 * Mock the projects API for deterministic test data.
 */
export async function mockProjectsApi(page: Page) {
  await page.route('**/api/projects', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: [] });
    } else if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      await route.fulfill({
        json: {
          id: 'test-project-1',
          name: body?.name || 'E2E Test',
          description: body?.description || '',
          path: '/tmp/test-project',
          created_at: new Date().toISOString(),
        },
      });
    } else {
      await route.continue();
    }
  });
}

/**
 * Mock the workflow API.
 */
export async function mockWorkflowApi(page: Page) {
  await page.route('**/api/projects/*/workflows', async (route) => {
    await route.fulfill({
      json: {
        id: 'test-workflow-1',
        name: 'Main Workflow',
        nodes: [],
        edges: [],
      },
    });
  });

  await page.route('**/api/workflows/*', async (route) => {
    if (route.request().method() === 'PUT') {
      await route.fulfill({ json: { success: true } });
    } else {
      await route.fulfill({
        json: {
          id: 'test-workflow-1',
          nodes: [],
          edges: [],
        },
      });
    }
  });
}

/**
 * Set up all standard API mocks for a test.
 */
export async function setupMocks(page: Page) {
  await mockBlocksApi(page);
  await mockProjectsApi(page);
  await mockWorkflowApi(page);
}

/**
 * Create a new project via the UI.
 * Clicks New, fills the name, clicks Create, waits for the editor canvas.
 */
export async function createProject(page: Page, name = 'E2E Test') {
  // TODO: add data-testid="new-project-button" to WelcomeScreen/Toolbar
  await page.click('text=New');
  await page.fill('input[placeholder*="name" i]', name);
  // TODO: add data-testid="create-project-button" to ProjectDialog
  await page.click('text=Create');
  // Wait for the workflow canvas to appear
  await expect(page.locator('.react-flow')).toBeVisible({ timeout: 10000 });
}

/**
 * Drag a block from the palette to the canvas at the given position.
 */
export async function dragBlockToCanvas(
  page: Page,
  blockName: string,
  target: { x: number; y: number } = { x: 300, y: 200 },
) {
  // TODO: add data-testid="palette-block-{name}" to BlockPalette items
  const block = page.locator(`[data-testid="palette-block-${blockName}"]`).or(
    page.getByText(blockName, { exact: false }).first()
  );
  const canvas = page.locator('.react-flow');
  const canvasBox = await canvas.boundingBox();
  if (!canvasBox) throw new Error('Canvas not found');

  await block.dragTo(canvas, {
    targetPosition: { x: target.x, y: target.y },
  });
}

/**
 * Connect the output port of one node to the input port of another.
 */
export async function connectPorts(
  page: Page,
  sourceNodeIndex: number,
  targetNodeIndex: number,
) {
  const sourceHandle = page.locator('.react-flow__handle.source').nth(sourceNodeIndex);
  const targetHandle = page.locator('.react-flow__handle.target').nth(targetNodeIndex);
  await sourceHandle.dragTo(targetHandle);
}

/**
 * Get the nth block node on the canvas.
 */
export function getBlockNode(page: Page, index: number): Locator {
  // TODO: add data-testid="block-node" to BlockNode component
  return page.locator('.react-flow__node').nth(index);
}

/**
 * Get the bottom panel locator.
 */
export function getBottomPanel(page: Page): Locator {
  // TODO: add data-testid="bottom-panel" to BottomPanel component
  return page.locator('[data-testid="bottom-panel"]').or(
    page.locator('[class*="bottom-panel"]')
  ).first();
}

/**
 * Get the palette panel locator.
 */
export function getPalettePanel(page: Page): Locator {
  // TODO: add data-testid="block-palette" to BlockPalette component
  return page.locator('[data-testid="block-palette"]').or(
    page.locator('[class*="palette"]')
  ).first();
}

/**
 * Get the preview panel locator.
 */
export function getPreviewPanel(page: Page): Locator {
  // TODO: add data-testid="preview-panel" to DataPreview component
  return page.locator('[data-testid="preview-panel"]').or(
    page.locator('[class*="preview"]')
  ).first();
}

/**
 * Navigate to the app and wait for it to be ready.
 */
export async function gotoApp(page: Page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
}

/**
 * Navigate to the app with mocks set up and a project created.
 * Returns after the editor canvas is visible.
 */
export async function setupEditorWithProject(page: Page, projectName = 'E2E Test') {
  await setupMocks(page);
  await gotoApp(page);
  await createProject(page, projectName);
}
