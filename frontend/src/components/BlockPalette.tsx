import { useRef, useState, useCallback } from "react";

import type { BlockSummary } from "../types/api";

interface BlockPaletteProps {
  blocks: BlockSummary[];
  search: string;
  collapsed: boolean;
  onSearch: (value: string) => void;
  onReload: () => void;
  onAddBlock: (block: BlockSummary) => void;
}

const categoryOrder = ["io", "process", "code", "app", "ai", "subworkflow", "custom"];

/** Display label for a package_name. Empty string becomes "Core". */
function packageLabel(packageName: string): string {
  return packageName || "Core";
}

/**
 * Expand io_block into separate Load Block / Save Block palette entries.
 * Both map to the same backend block type with different default direction.
 */
function expandIOBlocks(blocks: BlockSummary[]): BlockSummary[] {
  const result: BlockSummary[] = [];
  for (const block of blocks) {
    if (block.type_name === "io_block") {
      result.push({
        ...block,
        name: "Load Block",
        description: "Load data from a file (input)",
        type_name: "io_block",
      });
      result.push({
        ...block,
        name: "Save Block",
        description: "Save data to a file (output)",
        type_name: "io_block",
      });
    } else {
      result.push(block);
    }
  }
  return result;
}

interface CategoryGroup {
  category: string;
  blocks: BlockSummary[];
}

interface PackageGroup {
  packageName: string;
  label: string;
  categories: CategoryGroup[];
}

/**
 * Group filtered blocks into a two-level hierarchy: package -> category -> blocks.
 * Packages are sorted with "Core" (empty package_name) first, then alphabetically.
 * Categories within each package follow the standard categoryOrder.
 */
function groupByPackageAndCategory(blocks: BlockSummary[]): PackageGroup[] {
  // Group by package_name first
  const byPackage: Record<string, BlockSummary[]> = {};
  for (const block of blocks) {
    const pkg = block.package_name ?? "";
    if (!byPackage[pkg]) byPackage[pkg] = [];
    byPackage[pkg].push(block);
  }

  // Sort package names: "" (Core) first, then alphabetical
  const packageNames = Object.keys(byPackage).sort((a, b) => {
    if (a === "") return -1;
    if (b === "") return 1;
    return a.localeCompare(b);
  });

  return packageNames.map((packageName) => {
    const pkgBlocks = byPackage[packageName];
    const categories = categoryOrder
      .map((category) => ({
        category,
        blocks: pkgBlocks.filter((block) => block.category === category),
      }))
      .filter((entry) => entry.blocks.length > 0);

    // Also include blocks with categories not in categoryOrder
    const knownCategories = new Set(categoryOrder);
    const unknownCategories = new Set(
      pkgBlocks.map((b) => b.category).filter((c) => !knownCategories.has(c)),
    );
    for (const cat of unknownCategories) {
      categories.push({
        category: cat,
        blocks: pkgBlocks.filter((b) => b.category === cat),
      });
    }

    return {
      packageName,
      label: packageLabel(packageName),
      categories,
    };
  });
}

export function BlockPalette({
  blocks,
  search,
  collapsed,
  onSearch,
  onReload,
  onAddBlock,
}: BlockPaletteProps) {
  const dragImageRef = useRef<HTMLDivElement | null>(null);
  const [collapsedPackages, setCollapsedPackages] = useState<Record<string, boolean>>({});
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});

  const expanded = expandIOBlocks(blocks);

  const filtered = expanded.filter((block) => {
    const value = `${block.name} ${block.description} ${block.category}`.toLowerCase();
    return value.includes(search.toLowerCase());
  });

  const packageGroups = groupByPackageAndCategory(filtered);

  // When there is only one package, skip the outer package grouping layer
  const singlePackage = packageGroups.length <= 1;

  const togglePackage = useCallback((packageName: string) => {
    setCollapsedPackages((prev) => ({
      ...prev,
      [packageName]: !prev[packageName],
    }));
  }, []);

  const toggleCategory = useCallback((key: string) => {
    setCollapsedCategories((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  }, []);

  const handleDragStart = (event: React.DragEvent, block: BlockSummary) => {
    const payload = { ...block };
    if (block.type_name === "io_block") {
      (payload as Record<string, unknown>)._default_direction =
        block.name === "Load Block" ? "input" : "output";
    }
    event.dataTransfer.setData("application/scieasy-block", JSON.stringify(payload));
    event.dataTransfer.effectAllowed = "copy";

    if (dragImageRef.current) {
      dragImageRef.current.textContent = block.name;
      dragImageRef.current.style.display = "block";
      event.dataTransfer.setDragImage(dragImageRef.current, 40, 16);
      requestAnimationFrame(() => {
        if (dragImageRef.current) dragImageRef.current.style.display = "none";
      });
    }
  };

  const renderBlockCard = (block: BlockSummary, index: number) => (
    <div
      className="rounded-[1.4rem] border border-stone-200 bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-ember"
      draggable
      key={`${block.type_name}-${block.name}-${index}`}
      onDragStart={(event) => handleDragStart(event, block)}
    >
      <button
        className="w-full text-left"
        onClick={() => onAddBlock(block)}
        type="button"
      >
        <p className="font-medium text-ink">{collapsed ? block.name.slice(0, 2) : block.name}</p>
        {collapsed ? null : (
          <>
            <p className="mt-1 text-xs text-stone-500">{block.description}</p>
            <p className="mt-2 text-[11px] uppercase tracking-[0.25em] text-stone-400">
              {block.input_ports.length} in / {block.output_ports.length} out
            </p>
          </>
        )}
      </button>
    </div>
  );

  const renderCategorySection = (
    group: CategoryGroup,
    packageName: string,
  ) => {
    const catKey = `${packageName}:${group.category}`;
    const isCatCollapsed = collapsedCategories[catKey] ?? false;

    return (
      <section key={catKey}>
        {collapsed ? null : (
          <button
            className="mb-2 flex w-full items-center gap-1 text-left"
            onClick={() => toggleCategory(catKey)}
            type="button"
          >
            <span className="text-[10px] text-stone-400">{isCatCollapsed ? "\u25B6" : "\u25BC"}</span>
            <span className="text-[11px] uppercase tracking-[0.3em] text-stone-500">
              {group.category}
            </span>
            <span className="text-[10px] text-stone-400">({group.blocks.length})</span>
          </button>
        )}
        {isCatCollapsed ? null : (
          <div className="space-y-2">
            {group.blocks.map((block, index) => renderBlockCard(block, index))}
          </div>
        )}
      </section>
    );
  };

  return (
    <aside
      className="flex h-full flex-col overflow-hidden border-r border-stone-200 bg-[linear-gradient(180deg,_rgba(255,255,255,0.95),_rgba(245,241,232,0.98))] p-4"
    >
      {/* Drag ghost element (offscreen) */}
      <div
        ref={dragImageRef}
        className="pointer-events-none fixed -left-[9999px] -top-[9999px] rounded-xl border border-ember bg-white px-4 py-2 text-sm font-medium text-ink shadow-lg"
        style={{ display: "none" }}
      />

      <div className="flex items-center justify-between gap-2">
        {collapsed ? null : <p className="font-display text-xl text-ink">Palette</p>}
        <button className="toolbar-button" onClick={onReload} type="button">
          {collapsed ? "\u21BB" : "Reload"}
        </button>
      </div>

      {collapsed ? null : (
        <input
          className="mt-4 w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-ember"
          onChange={(event) => onSearch(event.target.value)}
          placeholder="Search blocks"
          value={search}
        />
      )}

      <div className="mt-4 min-h-0 flex-1 space-y-4 overflow-y-auto pb-6 scrollbar-thin">
        {packageGroups.map((pkg) => {
          const isPkgCollapsed = collapsedPackages[pkg.packageName] ?? false;

          if (singlePackage) {
            // Skip the package-level wrapper when there is only one package
            return pkg.categories.map((group) =>
              renderCategorySection(group, pkg.packageName),
            );
          }

          return (
            <div key={pkg.packageName || "__core__"} className="space-y-2">
              {collapsed ? null : (
                <button
                  className="flex w-full items-center gap-1.5 rounded-lg px-1 py-1 text-left transition hover:bg-stone-100"
                  onClick={() => togglePackage(pkg.packageName)}
                  type="button"
                >
                  <span className="text-[11px] text-stone-400">
                    {isPkgCollapsed ? "\u25B6" : "\u25BC"}
                  </span>
                  <span className="font-display text-sm font-semibold text-ink">
                    {pkg.label}
                  </span>
                  <span className="text-[10px] text-stone-400">
                    ({pkg.categories.reduce((sum, c) => sum + c.blocks.length, 0)})
                  </span>
                </button>
              )}
              {isPkgCollapsed ? null : (
                <div className="space-y-3 pl-2">
                  {pkg.categories.map((group) =>
                    renderCategorySection(group, pkg.packageName),
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
