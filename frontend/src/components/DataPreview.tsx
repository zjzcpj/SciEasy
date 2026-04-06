import Plot from "react-plotly.js";
import { useEffect, useMemo, useState } from "react";

import type { DataPreviewResponse } from "../types/api";

interface DataPreviewProps {
  selectedNodeId: string | null;
  selectedNodeLabel: string;
  blockOutputs: Record<string, Record<string, unknown>>;
  previewCache: Record<string, DataPreviewResponse>;
  previewLoading: Record<string, boolean>;
  onLoadPreview: (dataRef: string) => Promise<void>;
  onStartFromHere: () => void;
  onCancelSelected: () => void;
}

function extractDataRefs(payload: unknown): string[] {
  if (!payload || typeof payload !== "object") {
    return [];
  }
  const record = payload as Record<string, unknown>;
  if (typeof record.data_ref === "string") {
    return [record.data_ref];
  }
  if (record.kind === "collection" && Array.isArray(record.items)) {
    return record.items.flatMap((item) => extractDataRefs(item));
  }
  return Object.values(record).flatMap((value) => extractDataRefs(value));
}

function PreviewRenderer({ preview }: { preview: Record<string, unknown> }) {
  switch (preview.kind) {
    case "table":
      return (
        <div className="overflow-auto rounded-[1.4rem] border border-stone-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-canvas text-stone-600">
              <tr>
                {(preview.columns as string[] | undefined)?.map((column) => (
                  <th className="px-3 py-2 font-medium" key={column}>
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(preview.rows as Array<Record<string, unknown>> | undefined)?.map((row, index) => (
                <tr className="border-t border-stone-100" key={index}>
                  {(preview.columns as string[] | undefined)?.map((column) => (
                    <td className="px-3 py-2" key={column}>
                      {String(row[column] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    case "image":
      return (
        <div className="grid gap-3">
          <img alt="Preview" className="max-h-72 rounded-[1.4rem] border border-stone-200 object-contain" src={String(preview.src)} />
          <p className="text-xs text-stone-500">Shape: {(preview.shape as number[] | undefined)?.join(" × ")}</p>
        </div>
      );
    case "chart":
      return (
        <Plot
          className="w-full"
          data={[
            {
              x: (preview.points as Array<{ x: number; y: number }> | undefined)?.map((point) => point.x) ?? [],
              y: (preview.points as Array<{ x: number; y: number }> | undefined)?.map((point) => point.y) ?? [],
              type: "scatter",
              mode: "lines+markers",
              marker: { color: "#f06a44" },
            },
          ]}
          layout={{
            autosize: true,
            margin: { l: 30, r: 10, b: 30, t: 10 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { family: "IBM Plex Sans, sans-serif", size: 12 },
          }}
          style={{ width: "100%", height: "260px" }}
          useResizeHandler
        />
      );
    case "text":
      return <pre className="max-h-80 overflow-auto rounded-[1.4rem] border border-stone-200 bg-white p-4 text-sm">{String(preview.content ?? "")}</pre>;
    case "composite":
      return (
        <div className="space-y-2">
          {Object.entries((preview.slots as Record<string, unknown> | undefined) ?? {}).map(([slot, value]) => (
            <div className="rounded-2xl border border-stone-200 bg-white px-4 py-3" key={slot}>
              <p className="text-xs uppercase tracking-[0.25em] text-stone-500">{slot}</p>
              <p className="mt-1 text-sm text-ink">{String(value)}</p>
            </div>
          ))}
        </div>
      );
    default:
      return (
        <div className="rounded-[1.4rem] border border-stone-200 bg-white p-4 text-sm text-stone-600">
          <p>Artifact preview</p>
          <p className="mt-2 text-xs">{String(preview.path ?? "")}</p>
          <p className="text-xs">{String(preview.mime_type ?? "")}</p>
        </div>
      );
  }
}

export function DataPreview({
  selectedNodeId,
  selectedNodeLabel,
  blockOutputs,
  previewCache,
  previewLoading,
  onLoadPreview,
  onStartFromHere,
  onCancelSelected,
}: DataPreviewProps) {
  const [activeRef, setActiveRef] = useState<string | null>(null);
  const outputRefs = useMemo(() => {
    if (!selectedNodeId) {
      return [];
    }
    return extractDataRefs(blockOutputs[selectedNodeId] ?? {});
  }, [blockOutputs, selectedNodeId]);

  useEffect(() => {
    setActiveRef(outputRefs[0] ?? null);
  }, [outputRefs]);

  useEffect(() => {
    if (activeRef && !previewCache[activeRef] && !previewLoading[activeRef]) {
      void onLoadPreview(activeRef);
    }
  }, [activeRef, onLoadPreview, previewCache, previewLoading]);

  const preview = activeRef ? previewCache[activeRef] : null;

  return (
    <aside className="flex h-full flex-col overflow-hidden border-l border-stone-200 bg-[linear-gradient(180deg,_rgba(255,255,255,0.94),_rgba(245,241,232,0.98))] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-stone-500">Preview</p>
          <h2 className="mt-2 font-display text-2xl text-ink">{selectedNodeId ? selectedNodeLabel : "Select a node"}</h2>
        </div>
        {selectedNodeId ? (
          <div className="flex gap-2">
            <button className="toolbar-button" onClick={onStartFromHere} type="button">
              Start Here
            </button>
            <button className="toolbar-button" onClick={onCancelSelected} type="button">
              Cancel
            </button>
          </div>
        ) : null}
      </div>

      {!selectedNodeId ? (
        <div className="mt-6 rounded-[1.8rem] border border-dashed border-stone-300 px-4 py-6 text-sm text-stone-500">
          Pick a block to inspect its latest outputs and cached previews.
        </div>
      ) : outputRefs.length === 0 ? (
        <div className="mt-6 rounded-[1.8rem] border border-dashed border-stone-300 px-4 py-6 text-sm text-stone-500">
          This block has no previewable outputs yet.
        </div>
      ) : (
        <>
          <div className="mt-5 flex flex-wrap gap-2">
            {outputRefs.map((dataRef) => (
              <button
                className={`rounded-full px-3 py-1 text-xs ${activeRef === dataRef ? "bg-ink text-white" : "bg-white text-stone-600"}`}
                key={dataRef}
                onClick={() => setActiveRef(dataRef)}
                type="button"
              >
                {dataRef.slice(0, 10)}
              </button>
            ))}
          </div>
          <div className="mt-4 min-h-0 flex-1 overflow-y-auto scrollbar-thin">
            {activeRef && previewLoading[activeRef] ? (
              <div className="rounded-[1.6rem] border border-stone-200 bg-white p-4 text-sm text-stone-500">Loading preview…</div>
            ) : preview ? (
              <PreviewRenderer preview={preview.preview} />
            ) : (
              <div className="rounded-[1.6rem] border border-stone-200 bg-white p-4 text-sm text-stone-500">
                Preview not loaded yet.
              </div>
            )}
          </div>
        </>
      )}
    </aside>
  );
}
