import { useState } from "react";

import { typeColorMap, subtypeRingColorMap } from "../config/typeColorMap";

interface TypeLegendProps {
  /**
   * Set of type names that are actually present in the current workflow.
   * The legend only shows entries for types in this set.
   */
  activeTypes: Set<string>;
}

/** All possible legend entries, in display order. */
const legendEntries: { name: string; fill: string; ring?: string }[] = [
  { name: "Array", fill: typeColorMap.Array },
  { name: "Image", fill: typeColorMap.Image, ring: subtypeRingColorMap.Image },
  { name: "Mask", fill: typeColorMap.Mask, ring: subtypeRingColorMap.Mask },
  { name: "DataFrame", fill: typeColorMap.DataFrame },
  { name: "Series", fill: typeColorMap.Series },
  { name: "Text", fill: typeColorMap.Text },
  { name: "Artifact", fill: typeColorMap.Artifact },
  { name: "CompositeData", fill: typeColorMap.CompositeData },
  { name: "Label", fill: typeColorMap.Label, ring: subtypeRingColorMap.Label },
  { name: "Any", fill: "#ffffff", ring: undefined },
];

export function TypeLegend({ activeTypes }: TypeLegendProps) {
  const [collapsed, setCollapsed] = useState(true);

  const visible = legendEntries.filter(
    (entry) => activeTypes.has(entry.name) || (entry.name === "Any" && activeTypes.has("Any")),
  );

  if (visible.length === 0) return null;

  return (
    <div
      className="absolute bottom-3 right-3 z-10 rounded-lg border border-stone-200 bg-white/95 shadow-sm backdrop-blur-sm"
      style={{ minWidth: collapsed ? "auto" : 140 }}
    >
      <button
        type="button"
        className="flex w-full items-center gap-1.5 px-2.5 py-1.5 text-[10px] font-medium uppercase tracking-wider text-stone-500 hover:text-stone-700"
        onClick={() => setCollapsed((prev) => !prev)}
      >
        <span
          className="inline-block h-2.5 w-2.5 rounded-sm"
          style={{
            background: "linear-gradient(135deg, #3b82f6, #f59e0b, #22c55e, #8b5cf6)",
          }}
        />
        {collapsed ? "Legend" : "Type Legend"}
        <span className="ml-auto text-[9px]">{collapsed ? "\u25B6" : "\u25BC"}</span>
      </button>
      {!collapsed && (
        <div className="space-y-1 border-t border-stone-100 px-2.5 pb-2 pt-1.5">
          {visible.map((entry) => (
            <div key={entry.name} className="flex items-center gap-2">
              <span
                className="inline-block h-3 w-3 shrink-0 rounded-full border-2"
                style={{
                  backgroundColor: entry.fill,
                  borderColor: entry.ring ?? entry.fill,
                  borderStyle: entry.name === "Any" ? "dashed" : "solid",
                }}
              />
              <span className="text-[11px] text-stone-600">{entry.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
