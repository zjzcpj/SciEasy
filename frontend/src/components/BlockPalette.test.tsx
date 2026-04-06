import { describe, it } from "vitest";

/*
 * Stage 10.1 Part 2 — skipped test stubs authored by Agent A.
 *
 * Agent B will remove the .skip markers and implement these in Part 2,
 * after rewriting BlockPalette.tsx as a 3-level collapsible tree.
 * See docs/design/stage-10-1-palette.md §4.2 for the test plan.
 *
 * Intentionally minimal imports — adding @testing-library/react harnessing
 * is deferred to Part 2 so Part 1 stays type-only.
 */

describe("BlockPalette — Stage 10.1 Part 2", () => {
  it.skip("renders a 3-level tree (package -> category -> block)", () => {
    // Given a mix of builtin, package, and custom blocks,
    // assert that the DOM contains:
    //   - a package header for "SciEasy Core" (builtins)
    //   - a package header for "Custom" (custom/drop-in)
    //   - category headers nested under each package header
    //   - block cards nested under each category header
  });

  it.skip('"Custom" package always sorts to the bottom', () => {
    // Given blocks with source "builtin", "package", and "custom",
    // assert that the "Custom" package header appears AFTER all other
    // package headers in DOM order.
  });

  it.skip("packages and categories are collapsible", () => {
    // Clicking a package header toggles visibility of its category
    // children. Clicking a category header toggles visibility of its
    // block children. Default expansion state is TBD in Part 2.
  });

  it.skip("search expands matching branches automatically", () => {
    // When the search input matches a block by name/description, its
    // parent package and parent category expand automatically so the
    // matching block is visible in the rendered tree.
  });

  it.skip("empty categories are hidden when filtered", () => {
    // If a category has no matching blocks after filter, its header
    // and empty body are NOT rendered.
  });

  it.skip("IO block expansion still produces Load Block and Save Block", () => {
    // The 3-level rewrite must preserve the existing expandIOBlocks
    // behavior — an io_block is split into two palette entries.
  });
});
