import { useRef } from "react";

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
        // We tag a virtual key so palette can distinguish them.
        // The actual type_name stays io_block for the backend.
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

export function BlockPalette({
  blocks,
  search,
  collapsed,
  onSearch,
  onReload,
  onAddBlock,
}: BlockPaletteProps) {
  const dragImageRef = useRef<HTMLDivElement | null>(null);

  const expanded = expandIOBlocks(blocks);

  const filtered = expanded.filter((block) => {
    const value = `${block.name} ${block.description} ${block.category}`.toLowerCase();
    return value.includes(search.toLowerCase());
  });

  const grouped = categoryOrder
    .map((category) => ({
      category,
      blocks: filtered.filter((block) => block.category === category),
    }))
    .filter((entry) => entry.blocks.length);

  const handleDragStart = (event: React.DragEvent, block: BlockSummary) => {
    // Set the block data for drop handling
    const payload = { ...block };
    // Inject default direction for split IO blocks
    if (block.type_name === "io_block") {
      (payload as Record<string, unknown>)._default_direction =
        block.name === "Load Block" ? "input" : "output";
    }
    event.dataTransfer.setData("application/scieasy-block", JSON.stringify(payload));
    event.dataTransfer.effectAllowed = "copy";

    // Create a drag ghost image
    if (dragImageRef.current) {
      dragImageRef.current.textContent = block.name;
      dragImageRef.current.style.display = "block";
      event.dataTransfer.setDragImage(dragImageRef.current, 40, 16);
      requestAnimationFrame(() => {
        if (dragImageRef.current) dragImageRef.current.style.display = "none";
      });
    }
  };

  return (
    <aside
      className="h-full overflow-hidden border-r border-stone-200 bg-[linear-gradient(180deg,_rgba(255,255,255,0.95),_rgba(245,241,232,0.98))] p-4"
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

      <div className="mt-4 flex-1 space-y-4 overflow-auto pb-6">
        {grouped.map((group) => (
          <section key={group.category}>
            {collapsed ? null : (
              <p className="mb-2 text-[11px] uppercase tracking-[0.3em] text-stone-500">{group.category}</p>
            )}
            <div className="space-y-2">
              {group.blocks.map((block, index) => (
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
              ))}
            </div>
          </section>
        ))}
      </div>
    </aside>
  );
}
