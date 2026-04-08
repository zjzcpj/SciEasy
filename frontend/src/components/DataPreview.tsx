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

const COLORMAPS: { label: string; filter: string }[] = [
  { label: "Color", filter: "none" },
  { label: "Grayscale", filter: "grayscale(1)" },
  { label: "Invert", filter: "invert(1) grayscale(1)" },
  { label: "Hot", filter: "grayscale(1) sepia(1) saturate(8) hue-rotate(0deg)" },
  { label: "Cool", filter: "grayscale(1) sepia(1) saturate(8) hue-rotate(180deg)" },
];

interface ImageViewerProps {
  src: string;
  shape?: number[];
}

function ImageViewer({ src, shape }: ImageViewerProps) {
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [colormapIndex, setColormapIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef<{ mx: number; my: number; px: number; py: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const colormap = COLORMAPS[colormapIndex];
  const cssFilter = [
    colormap.filter !== "none" ? colormap.filter : "",
    `brightness(${brightness}%)`,
    `contrast(${contrast}%)`,
  ]
    .filter(Boolean)
    .join(" ");

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
    if (scale <= 1) return;
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
    setBrightness(100);
    setContrast(100);
    setColormapIndex(0);
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-stone-200 bg-white px-3 py-2 text-xs">
        {/* Zoom buttons */}
        <div className="flex items-center gap-1">
          <button
            aria-label="Zoom in"
            className="rounded-lg border border-stone-200 px-2 py-1 text-stone-600 hover:border-ember"
            onClick={() => zoom(1.25)}
            type="button"
          >
            +
          </button>
          <span className="min-w-[3rem] text-center text-stone-500">{Math.round(scale * 100)}%</span>
          <button
            aria-label="Zoom out"
            className="rounded-lg border border-stone-200 px-2 py-1 text-stone-600 hover:border-ember"
            onClick={() => zoom(0.8)}
            type="button"
          >
            −
          </button>
          <button
            className="rounded-lg border border-stone-200 px-2 py-1 text-stone-500 hover:border-ember"
            onClick={reset}
            type="button"
          >
            Reset
          </button>
        </div>

        {/* Brightness */}
        <label className="flex items-center gap-1 text-stone-500">
          <span>Bright</span>
          <input
            aria-label="Brightness"
            className="w-20 accent-ember"
            max={300}
            min={0}
            onChange={(e) => setBrightness(Number(e.target.value))}
            type="range"
            value={brightness}
          />
        </label>

        {/* Contrast */}
        <label className="flex items-center gap-1 text-stone-500">
          <span>Contrast</span>
          <input
            aria-label="Contrast"
            className="w-20 accent-ember"
            max={400}
            min={0}
            onChange={(e) => setContrast(Number(e.target.value))}
            type="range"
            value={contrast}
          />
        </label>

        {/* Colormap */}
        <label className="flex items-center gap-1 text-stone-500">
          <span>LUT</span>
          <select
            aria-label="Colormap"
            className="rounded-lg border border-stone-200 bg-white px-1 py-0.5 text-stone-600"
            onChange={(e) => setColormapIndex(Number(e.target.value))}
            value={colormapIndex}
          >
            {COLORMAPS.map((cm, i) => (
              <option key={cm.label} value={i}>
                {cm.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Image viewport */}
      <div
        className="relative overflow-hidden rounded-[1.4rem] border border-stone-200 bg-stone-100"
        ref={containerRef}
        style={{ height: "280px", cursor: scale > 1 ? (isDragging ? "grabbing" : "grab") : "default" }}
        onMouseDown={onMouseDown}
        onMouseLeave={onMouseUp}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
      >
        <img
          alt="Preview"
          draggable={false}
          src={src}
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: `translate(calc(-50% + ${pan.x}px), calc(-50% + ${pan.y}px)) scale(${scale})`,
            transformOrigin: "center",
            maxWidth: "none",
            filter: cssFilter,
            userSelect: "none",
          }}
        />
      </div>

      {shape ? (
        <p className="text-xs text-stone-500">Shape: {shape.join(" × ")}</p>
      ) : null}
    </div>
  );
}

interface TableViewerProps {
  columns: string[];
  rows: Array<Record<string, unknown>>;
}

function TableViewer({ columns, rows }: TableViewerProps) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs text-stone-500">
        {rows.length} row{rows.length !== 1 ? "s" : ""} × {columns.length} column{columns.length !== 1 ? "s" : ""}
      </p>
      <div
        className="overflow-auto rounded-[1.4rem] border border-stone-200 bg-white"
        style={{ maxHeight: "320px" }}
      >
        <table className="min-w-full text-left text-sm">
          <thead
            className="bg-canvas text-stone-600"
            style={{ position: "sticky", top: 0, zIndex: 1 }}
          >
            <tr>
              {columns.map((column) => (
                <th
                  className="whitespace-nowrap border-b border-stone-200 px-3 py-2 font-medium"
                  key={column}
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr className="border-t border-stone-100 hover:bg-stone-50" key={index}>
                {columns.map((column) => (
                  <td className="whitespace-nowrap px-3 py-1.5 text-xs" key={column}>
                    {String(row[column] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
