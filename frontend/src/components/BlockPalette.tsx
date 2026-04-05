import { clsx } from "clsx";

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

export function BlockPalette({
  blocks,
  search,
  collapsed,
  onSearch,
  onReload,
  onAddBlock,
}: BlockPaletteProps) {
  const filtered = blocks.filter((block) => {
    const value = `${block.name} ${block.description} ${block.category}`.toLowerCase();
    return value.includes(search.toLowerCase());
  });

  const grouped = categoryOrder
    .map((category) => ({
      category,
      blocks: filtered.filter((block) => block.category === category),
    }))
    .filter((entry) => entry.blocks.length);

  return (
    <aside
      className={clsx(
        "border-r border-stone-200 bg-[linear-gradient(180deg,_rgba(255,255,255,0.95),_rgba(245,241,232,0.98))] p-4",
        collapsed ? "w-20" : "w-full",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        {collapsed ? null : <p className="font-display text-xl text-ink">Palette</p>}
        <button className="toolbar-button" onClick={onReload} type="button">
          {collapsed ? "↻" : "Reload"}
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

      <div className="mt-4 space-y-4 overflow-auto pb-6">
        {grouped.map((group) => (
          <section key={group.category}>
            {collapsed ? null : (
              <p className="mb-2 text-[11px] uppercase tracking-[0.3em] text-stone-500">{group.category}</p>
            )}
            <div className="space-y-2">
              {group.blocks.map((block) => (
                <div
                  className="rounded-[1.4rem] border border-stone-200 bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-ember"
                  draggable
                  key={block.type_name}
                  onDragStart={(event) => {
                    event.dataTransfer.setData("application/scieasy-block", JSON.stringify(block));
                    event.dataTransfer.effectAllowed = "copy";
                  }}
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
