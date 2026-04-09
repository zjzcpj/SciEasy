import Plot from "react-plotly.js";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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

// ─── LUT Colormaps (canvas-based, matching OptEasy) ─────────────────────────

function buildLUT(fn: (t: number) => [number, number, number]): [number, number, number][] {
  return Array.from({ length: 256 }, (_, i) => {
    const [r, g, b] = fn(i);
    return [
      Math.max(0, Math.min(255, Math.round(r))),
      Math.max(0, Math.min(255, Math.round(g))),
      Math.max(0, Math.min(255, Math.round(b))),
    ] as [number, number, number];
  });
}

const LUTS: Record<string, [number, number, number][]> = {
  gray: Array.from({ length: 256 }, (_, i) => [i, i, i] as [number, number, number]),
  fire: buildLUT((t) => [Math.min(255, t * 3), Math.max(0, (t - 85) * 3), Math.max(0, (t - 170) * 3)]),
  ice: buildLUT((t) => [Math.max(0, (t - 170) * 3), Math.max(0, (t - 85) * 3), Math.min(255, t * 3)]),
  green: buildLUT((t) => [0, t, 0]),
  red: buildLUT((t) => [t, 0, 0]),
  blue: buildLUT((t) => [0, 0, t]),
  cyan: buildLUT((t) => [0, t, t]),
  magenta: buildLUT((t) => [t, 0, t]),
  viridis: buildLUT((t) => {
    const r = Math.round(68 + (253 - 68) * Math.sin((t / 256) * Math.PI * 0.8));
    const g = Math.round(1 + (231 - 1) * (t / 255));
    const b = Math.round(84 + (37 - 84) * (t / 255));
    return [Math.min(255, r), Math.min(255, g), Math.max(0, b)];
  }),
};

function lutGradient(lut: [number, number, number][]): string {
  const stops = [0, 64, 128, 192, 255].map((i) => {
    const [r, g, b] = lut[i];
    return `rgb(${r},${g},${b})`;
  });
  return stops.join(", ");
}

function applyLUTToImage(
  dataUrl: string,
  lut: [number, number, number][],
  minVal: number,
  maxVal: number,
): Promise<string> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d")!;
      ctx.drawImage(img, 0, 0);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const pixels = imageData.data;
      const range = maxVal - minVal || 1;

      for (let i = 0; i < pixels.length; i += 4) {
        const gray = pixels[i] * 0.299 + pixels[i + 1] * 0.587 + pixels[i + 2] * 0.114;
        const normalized = Math.max(0, Math.min(255, ((gray - minVal) / range) * 255));
        const idx = Math.round(normalized);
        const [r, g, b] = lut[idx] ?? [idx, idx, idx];
        pixels[i] = r;
        pixels[i + 1] = g;
        pixels[i + 2] = b;
      }

      ctx.putImageData(imageData, 0, 0);
      resolve(canvas.toDataURL("image/png"));
    };
    img.src = dataUrl;
  });
}

interface ImageViewerProps {
  src: string;
  shape?: number[];
}

function ImageViewer({ src, shape }: ImageViewerProps) {
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [lutName, setLutName] = useState("gray");
  const [minDisplay, setMinDisplay] = useState(0);
  const [maxDisplay, setMaxDisplay] = useState(255);
  const [isDragging, setIsDragging] = useState(false);
  const [processedUrl, setProcessedUrl] = useState<string | null>(null);
  const dragStart = useRef<{ mx: number; my: number; px: number; py: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Apply LUT when settings change
  useEffect(() => {
    if (!src) {
      setProcessedUrl(null);
      return;
    }
    if (lutName === "gray" && minDisplay === 0 && maxDisplay === 255) {
      setProcessedUrl(src);
      return;
    }
    void applyLUTToImage(src, LUTS[lutName] ?? LUTS.gray, minDisplay, maxDisplay).then(setProcessedUrl);
  }, [src, lutName, minDisplay, maxDisplay]);

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    setScale((prev) => Math.max(0.1, Math.min(20, prev * (e.deltaY < 0 ? 1.15 : 0.87))));
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, [handleWheel]);

  const onMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    dragStart.current = { mx: e.clientX, my: e.clientY, px: pan.x, py: pan.y };
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !dragStart.current) return;
    setPan({
      x: dragStart.current.px + (e.clientX - dragStart.current.mx),
      y: dragStart.current.py + (e.clientY - dragStart.current.my),
    });
  };

  const onMouseUp = () => {
    setIsDragging(false);
    dragStart.current = null;
  };

  const zoom = (delta: number) => {
    setScale((prev) => Math.max(0.1, Math.min(20, prev * delta)));
  };

  const reset = () => {
    setScale(1);
    setPan({ x: 0, y: 0 });
    setLutName("gray");
    setMinDisplay(0);
    setMaxDisplay(255);
  };

  const displaySrc = processedUrl ?? src;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0px" }}>
      {/* Dark image viewport */}
      <div
        ref={containerRef}
        style={{
          position: "relative",
          overflow: "hidden",
          borderRadius: "0.8rem 0.8rem 0 0",
          background: "#1e293b",
          height: "300px",
          cursor: isDragging ? "grabbing" : "grab",
        }}
        onMouseDown={onMouseDown}
        onMouseLeave={onMouseUp}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
      >
        {displaySrc && (
          <img
            alt="Preview"
            draggable={false}
            src={displaySrc}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              transform: `translate(-50%, -50%) translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
              imageRendering: scale > 2 ? "pixelated" : "auto",
              maxWidth: "none",
              maxHeight: "none",
              userSelect: "none",
            }}
          />
        )}

        {/* Info badge */}
        <div
          data-testid="image-info-badge"
          style={{
            position: "absolute",
            bottom: 6,
            left: 6,
            fontSize: 10,
            color: "#94a3b8",
            background: "rgba(0,0,0,0.5)",
            padding: "2px 8px",
            borderRadius: 3,
            pointerEvents: "none",
          }}
        >
          {shape ? `${shape.join(" \u00d7 ")} | ` : ""}{Math.round(scale * 100)}%
        </div>
      </div>

      {/* LUT & Display controls */}
      <div
        style={{
          padding: "8px 10px",
          borderRadius: "0 0 0.8rem 0.8rem",
          border: "1px solid #e7e5e4",
          borderTop: "none",
          background: "#fff",
          fontSize: 10,
        }}
      >
        {/* Zoom row */}
        <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 6 }}>
          <button
            aria-label="Zoom in"
            onClick={() => zoom(1.25)}
            type="button"
            style={{ fontSize: 12, padding: "1px 8px", border: "1px solid #d6d3d1", borderRadius: 4, cursor: "pointer", background: "#fff" }}
          >
            +
          </button>
          <span style={{ minWidth: "3rem", textAlign: "center", color: "#78716c" }}>{Math.round(scale * 100)}%</span>
          <button
            aria-label="Zoom out"
            onClick={() => zoom(0.8)}
            type="button"
            style={{ fontSize: 12, padding: "1px 8px", border: "1px solid #d6d3d1", borderRadius: 4, cursor: "pointer", background: "#fff" }}
          >
            {"\u2212"}
          </button>
          <button
            onClick={reset}
            type="button"
            style={{ fontSize: 10, padding: "2px 8px", border: "1px solid #d6d3d1", borderRadius: 4, cursor: "pointer", background: "#fff", color: "#78716c", marginLeft: "auto" }}
          >
            Reset
          </button>
        </div>

        {/* LUT selector (gradient swatches) */}
        <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 4 }}>
          <span style={{ width: 30, color: "#78716c" }}>LUT</span>
          <div style={{ display: "flex", gap: 2, flex: 1, flexWrap: "wrap" }}>
            {Object.keys(LUTS).map((name) => (
              <button
                key={name}
                aria-label={`LUT ${name}`}
                onClick={() => setLutName(name)}
                title={name}
                type="button"
                style={{
                  width: 20,
                  height: 14,
                  borderRadius: 2,
                  cursor: "pointer",
                  padding: 0,
                  border: name === lutName ? "2px solid #3b82f6" : "1px solid #475569",
                  background: `linear-gradient(to right, ${lutGradient(LUTS[name])})`,
                }}
              />
            ))}
          </div>
        </div>

        {/* Min/Max display range */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
          <span style={{ width: 30, color: "#78716c" }}>Min</span>
          <input
            aria-label="Display minimum"
            type="range"
            min={0}
            max={254}
            value={minDisplay}
            onChange={(e) => setMinDisplay(Math.min(Number(e.target.value), maxDisplay - 1))}
            style={{ flex: 1 }}
          />
          <span style={{ width: 24, textAlign: "right", color: "#78716c" }}>{minDisplay}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 30, color: "#78716c" }}>Max</span>
          <input
            aria-label="Display maximum"
            type="range"
            min={1}
            max={255}
            value={maxDisplay}
            onChange={(e) => setMaxDisplay(Math.max(Number(e.target.value), minDisplay + 1))}
            style={{ flex: 1 }}
          />
          <span style={{ width: 24, textAlign: "right", color: "#78716c" }}>{maxDisplay}</span>
        </div>
      </div>
    </div>
  );
}

interface TableViewerProps {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  rowCount?: number;
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }
  return String(value);
}

function TableViewer({ columns, rows, rowCount }: TableViewerProps) {
  const totalRows = rowCount ?? rows.length;
  const isTruncated = totalRows > rows.length || rows.length >= 100;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      <div
        style={{
          overflow: "auto",
          borderRadius: "0.8rem",
          border: "1px solid #e7e5e4",
          background: "#fff",
          maxHeight: "360px",
        }}
      >
        <table
          style={{
            borderCollapse: "collapse",
            minWidth: "100%",
            textAlign: "left",
            fontSize: 11,
          }}
        >
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  style={{
                    whiteSpace: "nowrap",
                    padding: "6px 10px",
                    borderBottom: "1px solid #cbd5e1",
                    fontWeight: 600,
                    fontSize: 11,
                    color: "#475569",
                    background: "#fff",
                    position: "sticky",
                    top: 0,
                    zIndex: 1,
                  }}
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} style={{ borderBottom: "1px solid #f1f5f9" }}>
                {columns.map((column) => (
                  <td
                    key={column}
                    style={{
                      whiteSpace: "nowrap",
                      padding: "3px 10px",
                      fontSize: 10,
                      color: "#334155",
                      borderBottom: "1px solid #f1f5f9",
                    }}
                  >
                    {formatCell(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p style={{ fontSize: 10, color: "#78716c", padding: "6px 4px 0", margin: 0 }}>
        {isTruncated
          ? `Showing ${rows.length} of ${totalRows > rows.length ? totalRows : `${rows.length}+`} rows`
          : `${rows.length} row${rows.length !== 1 ? "s" : ""}`}{" "}
        {"\u00d7"} {columns.length} column{columns.length !== 1 ? "s" : ""}
      </p>
    </div>
  );
}

function PreviewRenderer({ preview }: { preview: Record<string, unknown> }) {
  switch (preview.kind) {
    case "table":
      return (
        <TableViewer
          columns={(preview.columns as string[] | undefined) ?? []}
          rows={(preview.rows as Array<Record<string, unknown>> | undefined) ?? []}
          rowCount={typeof preview.row_count === "number" ? preview.row_count : undefined}
        />
      );
    case "image":
      return (
        <ImageViewer
          shape={preview.shape as number[] | undefined}
          src={String(preview.src)}
        />
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
