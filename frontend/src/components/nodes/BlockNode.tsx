import { type Node, Handle, Position, type NodeProps } from "@xyflow/react";

import { resolveTypeColor } from "../../config/typeColorMap";
import type { BlockNodeData } from "../../types/ui";

function configEntries(config: Record<string, unknown> | undefined): Array<[string, unknown]> {
  return Object.entries(config ?? {}).slice(0, 3);
}

function StatusBadge({ status }: { status?: string }) {
  const palette: Record<string, string> = {
    idle: "bg-stone-200 text-stone-600",
    ready: "bg-sea/15 text-sea",
    running: "bg-ember/15 text-ember",
    done: "bg-pine/15 text-pine",
    error: "bg-red-100 text-red-700",
    cancelled: "bg-red-200 text-red-800",
    skipped: "bg-stone-300 text-stone-700",
  };

  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${palette[status ?? "idle"]}`}>{status ?? "idle"}</span>;
}

export function BlockNode({ data, selected }: NodeProps<Node<BlockNodeData>>) {
  const inputColor = resolveTypeColor(data.inputPorts[0]?.accepted_types ?? []);
  const outputColor = resolveTypeColor(data.outputPorts[0]?.accepted_types ?? []);

  return (
    <div className={`min-w-[240px] rounded-[1.6rem] border bg-white px-4 py-3 shadow-sm ${selected ? "border-ember shadow-panel" : "border-stone-200"}`}>
      {data.inputPorts.map((port, index) => (
        <Handle
          className="!h-4 !w-4 !border-2 !bg-white"
          id={port.name}
          key={port.name}
          position={Position.Left}
          style={{ borderColor: inputColor, left: -8, top: 48 + index * 24 }}
          type="target"
        />
      ))}
      {data.outputPorts.map((port, index) => (
        <Handle
          className="!h-4 !w-4 !border-2 !bg-white"
          id={port.name}
          key={port.name}
          position={Position.Right}
          style={{ borderColor: outputColor, right: -8, top: 48 + index * 24 }}
          type="source"
        />
      ))}

      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-stone-400">{data.category}</p>
          <h3 className="mt-1 font-display text-lg text-ink">{data.label}</h3>
          <p className="text-xs text-stone-500">{data.blockType}</p>
        </div>
        <StatusBadge status={data.status} />
      </div>

      <div className="mt-4 grid gap-2">
        {configEntries(data.config).length ? (
          configEntries(data.config).map(([key, value]) => (
            <div className="flex items-center justify-between rounded-2xl bg-canvas px-3 py-2 text-xs" key={key}>
              <span className="uppercase tracking-[0.2em] text-stone-500">{key}</span>
              <span className="font-medium text-ink">{String(value)}</span>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-stone-200 px-3 py-2 text-xs text-stone-500">
            Inline params appear here.
          </div>
        )}
      </div>
    </div>
  );
}
