import { type Node, Handle, Position, type NodeProps } from "@xyflow/react";

import { resolveTypeColor, resolveRingColor, isAnyType, primaryTypeName } from "../../config/typeColorMap";
import type { BlockNodeData } from "../../types/ui";
import { computeEffectivePorts } from "../../utils/computeEffectivePorts";

// ---------------------------------------------------------------------------
// Category icon map
// ---------------------------------------------------------------------------
const categoryIcons: Record<string, string> = {
  io: "\uD83D\uDCC1",
  process: "\u2699\uFE0F",
  code: "\uD83D\uDCBB",
  app: "\uD83D\uDDA5\uFE0F",
  ai: "\u2728",
  subworkflow: "\uD83D\uDCE6",
  custom: "\uD83E\uDDE9",
};

// ---------------------------------------------------------------------------
// State badge configuration
// ---------------------------------------------------------------------------
interface BadgeStyle {
  icon: string;
  label: string;
  bg: string;
  text: string;
  spin?: boolean;
  italic?: boolean;
  clickable?: boolean;
}

const badgeStyles: Record<string, BadgeStyle> = {
  idle: { icon: "\u25CB", label: "Idle", bg: "rgba(156,163,175,0.15)", text: "#9CA3AF" },
  ready: { icon: "\u25C9", label: "Ready", bg: "rgba(59,130,246,0.15)", text: "#3B82F6" },
  running: { icon: "\u27F3", label: "Running", bg: "rgba(59,130,246,0.15)", text: "#3B82F6", spin: true },
  paused: { icon: "\u23F8", label: "Paused", bg: "rgba(245,158,11,0.15)", text: "#F59E0B" },
  done: { icon: "\u2705", label: "Done", bg: "rgba(34,197,94,0.15)", text: "#22C55E" },
  error: { icon: "\u274C", label: "Error", bg: "rgba(239,68,68,0.15)", text: "#EF4444", clickable: true },
  cancelled: { icon: "\u2298", label: "Cancelled", bg: "rgba(249,115,22,0.15)", text: "#F97316" },
  skipped: { icon: "\u2298", label: "Skipped", bg: "rgba(156,163,175,0.15)", text: "#9CA3AF", italic: true },
};

// ---------------------------------------------------------------------------
// StatusBadge sub-component
// ---------------------------------------------------------------------------
function StatusBadge({
  status,
  onErrorClick,
}: {
  status?: string;
  onErrorClick?: () => void;
}) {
  const style = badgeStyles[status ?? "idle"] ?? badgeStyles.idle;

  const inner = (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium leading-none"
      style={{
        backgroundColor: style.bg,
        color: style.text,
        fontStyle: style.italic ? "italic" : undefined,
        cursor: style.clickable ? "pointer" : undefined,
      }}
    >
      <span className={style.spin ? "inline-block animate-spin" : undefined}>
        {style.icon}
      </span>
      {style.label}
    </span>
  );

  if (style.clickable && onErrorClick) {
    return (
      <button type="button" onClick={onErrorClick} className="focus:outline-none">
        {inner}
      </button>
    );
  }

  return inner;
}

// ---------------------------------------------------------------------------
// Inline config helpers
// ---------------------------------------------------------------------------
interface ConfigProperty {
  key: string;
  schema: Record<string, unknown>;
}

function getTopConfigProperties(
  configSchema?: { properties?: Record<string, Record<string, unknown>> },
): ConfigProperty[] {
  if (!configSchema?.properties) return [];

  return Object.entries(configSchema.properties)
    .map(([key, schema]) => ({ key, schema }))
    .sort((a, b) => {
      const pa = (a.schema.ui_priority as number) ?? 999;
      const pb = (b.schema.ui_priority as number) ?? 999;
      return pa - pb;
    })
    .slice(0, 3);
}

function InlineConfigField({
  prop,
  value,
  onChange,
}: {
  prop: ConfigProperty;
  value: unknown;
  onChange: (key: string, val: unknown) => void;
}) {
  const { key, schema } = prop;
  const label = (schema.title as string) ?? key;

  // Enum dropdown
  if (Array.isArray(schema.enum)) {
    return (
      <label className="flex items-center justify-between gap-2 text-xs">
        <span className="shrink-0 text-stone-500">{label}</span>
        <select
          className="nodrag nowheel min-w-0 flex-1 rounded border border-stone-200 bg-white px-2 py-1 text-xs text-ink focus:border-sea focus:outline-none"
          value={String(value ?? schema.default ?? "")}
          onChange={(e) => onChange(key, e.target.value)}
        >
          {(schema.enum as unknown[]).map((opt) => (
            <option key={String(opt)} value={String(opt)}>
              {String(opt)}
            </option>
          ))}
        </select>
      </label>
    );
  }

  // Boolean checkbox
  if (schema.type === "boolean") {
    const checked = (value ?? schema.default ?? false) as boolean;
    return (
      <label className="flex items-center justify-between gap-2 text-xs">
        <span className="text-stone-500">{label}</span>
        <input
          type="checkbox"
          className="nodrag nowheel h-4 w-4 accent-sea"
          checked={checked}
          onChange={(e) => onChange(key, e.target.checked)}
        />
      </label>
    );
  }

  // Number input
  if (schema.type === "number" || schema.type === "integer") {
    return (
      <label className="flex items-center justify-between gap-2 text-xs">
        <span className="shrink-0 text-stone-500">{label}</span>
        <input
          type="number"
          className="nodrag nowheel min-w-0 flex-1 rounded border border-stone-200 bg-white px-2 py-1 text-xs text-ink focus:border-sea focus:outline-none"
          value={value != null ? String(value) : String(schema.default ?? "")}
          onChange={(e) => {
            const num = Number(e.target.value);
            onChange(key, Number.isNaN(num) ? e.target.value : num);
          }}
        />
      </label>
    );
  }

  // Default: text input (Browse buttons removed — tkinter native dialogs
  // crash on macOS; users type/paste paths directly, see #467).
  return (
    <label className="flex items-center justify-between gap-2 text-xs">
      <span className="shrink-0 text-stone-500">{label}</span>
      <div className="flex min-w-0 flex-1">
        <input
          type="text"
          className="nodrag nowheel min-w-0 flex-1 rounded border border-stone-200 bg-white px-2 py-1 text-xs text-ink focus:border-sea focus:outline-none"
          placeholder={key === "path" ? "Type or paste path" : undefined}
          value={String(value ?? schema.default ?? "")}
          onChange={(e) => onChange(key, e.target.value)}
        />
      </div>
    </label>
  );
}

// ---------------------------------------------------------------------------
// Error message inline display
// ---------------------------------------------------------------------------
const MAX_INLINE_ERROR_LEN = 80;

function ErrorMessage({ message }: { message: string }) {
  const truncated =
    message.length > MAX_INLINE_ERROR_LEN
      ? `${message.slice(0, MAX_INLINE_ERROR_LEN)}…`
      : message;
  return (
    <span
      className="ml-2 min-w-0 flex-1 truncate text-[10px] leading-tight text-red-500"
      title={message}
    >
      {truncated}
    </span>
  );
}

// ---------------------------------------------------------------------------
// BlockNode component
// ---------------------------------------------------------------------------
export function BlockNode({ data, selected }: NodeProps<Node<BlockNodeData>>) {
  // ADR-028 Addendum 1 §B fix #2 / §C11: hide the ``direction`` config
  // field for any IO block (not just the legacy abstract-base type_name).
  // ``direction`` is a ClassVar on the IOBlock subclass — it is not a
  // user-editable runtime config field — so it must not be rendered in
  // any IO block's inline config strip.
  const configProps = getTopConfigProperties(data.schema?.config_schema).filter(
    (prop) => !(data.category === "io" && prop.key === "direction"),
  );
  const typeHierarchy = data.schema?.type_hierarchy;
  const categoryIcon = categoryIcons[data.category] ?? categoryIcons.custom;
  // ADR-028 Addendum 1 §B fix #3 / §C8: read ``direction`` from the schema
  // (class-level ClassVar, populated by the backend at scan time) instead
  // of from ``data.config?.direction``. After ADR-028 there is no runtime
  // ``direction`` config value — reading the old path always returned
  // undefined, breaking the Save Block directory picker.
  // ADR-028 Addendum 1 §D4 / spec §d step 4: compute effective ports from
  // the dynamic-port descriptor + driving config value. Static blocks pay
  // zero cost (the helper returns ``basePorts`` by reference). Dynamic
  // blocks (e.g. ``LoadData``) get per-instance ``accepted_types`` so the
  // port colour resolved by ``resolveTypeColor()`` updates live as the
  // user changes the dropdown.
  const dynamicPorts = data.schema?.dynamic_ports ?? null;
  const sourceConfigKey = dynamicPorts?.source_config_key;
  const drivingConfigValue =
    sourceConfigKey != null
      ? (data.config?.[sourceConfigKey] as string | undefined)
      : undefined;
  const effectiveInputPorts = computeEffectivePorts(
    dynamicPorts,
    drivingConfigValue,
    data.inputPorts,
    "input",
  );
  const effectiveOutputPorts = computeEffectivePorts(
    dynamicPorts,
    drivingConfigValue,
    data.outputPorts,
    "output",
  );

  const handleConfigChange = (key: string, value: unknown) => {
    data.onUpdateConfig?.({ [key]: value });
  };

  return (
    <div
      className={`w-[280px] rounded-xl border bg-white shadow-sm ${
        selected ? "border-ember shadow-panel" : "border-stone-200"
      }`}
    >
      {/* ----------------------------------------------------------------- */}
      {/* Header                                                            */}
      {/* ----------------------------------------------------------------- */}
      <div className="flex items-center justify-between gap-2 border-b border-stone-100 px-3 py-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="text-base leading-none">{categoryIcon}</span>
          <span className="truncate font-display text-sm font-semibold text-ink">
            {data.label}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            className="nodrag rounded p-1 text-stone-400 transition-colors hover:bg-stone-100 hover:text-ink"
            title="Run block"
            onClick={() => data.onRun?.()}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4 2.5v11l9-5.5z" />
            </svg>
          </button>
          <button
            type="button"
            className="nodrag rounded p-1 text-stone-400 transition-colors hover:bg-stone-100 hover:text-ink"
            title="Restart block"
            onClick={() => data.onRestart?.()}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M13 8a5 5 0 1 1-1.5-3.5M13 3v2.5h-2.5" />
            </svg>
          </button>
          <button
            type="button"
            className="nodrag rounded p-1 text-stone-400 transition-colors hover:bg-red-50 hover:text-red-500"
            title="Remove block"
            onClick={() => data.onDelete?.()}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Inline config                                                     */}
      {/* ----------------------------------------------------------------- */}
      <div className="nodrag nowheel space-y-2 border-b border-stone-100 px-3 py-2">
        {configProps.length > 0 ? (
          configProps.map((prop) => (
            <InlineConfigField
              key={prop.key}
              prop={prop}
              value={data.config?.[prop.key]}
              onChange={handleConfigChange}
            />
          ))
        ) : (
          <p className="text-center text-[11px] italic text-stone-400">
            No parameters
          </p>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Port handles (positioned absolutely by React Flow)                */}
      {/* ----------------------------------------------------------------- */}
      {/* Use effective ports so dynamic blocks (LoadData, SaveData) get   */}
      {/* per-instance accepted_types resolved from data.schema?.dynamic_ports */}
      {/* + the current driving config value (ADR-028 Addendum 1 §D4).      */}
      {effectiveInputPorts.map((port, index) => {
        const fillColor = resolveTypeColor(port.accepted_types, typeHierarchy);
        const ringColor = resolveRingColor(port.accepted_types, typeHierarchy);
        const anyType = isAnyType(port.accepted_types);
        const typeName = primaryTypeName(port.accepted_types);
        const borderColor = ringColor ?? (anyType ? "#d1d5db" : fillColor);
        const shadows: string[] = [];
        if (port.is_collection) {
          shadows.push(`0 0 0 2px white`, `0 0 0 4px ${fillColor}`);
        }
        return (
          <Handle
            key={port.name}
            id={port.name}
            type="target"
            position={Position.Left}
            className="!h-3.5 !w-3.5 !border-2"
            title={`${typeName}${port.description ? " \u2014 " + port.description : ""}`}
            style={{
              backgroundColor: anyType ? "#ffffff" : fillColor,
              borderColor,
              borderStyle: anyType ? "dashed" : "solid",
              left: -7,
              top: 80 + index * 20,
              boxShadow: shadows.length > 0 ? shadows.join(", ") : undefined,
            }}
          />
        );
      })}
      {effectiveOutputPorts.map((port, index) => {
        const fillColor = resolveTypeColor(port.accepted_types, typeHierarchy);
        const ringColor = resolveRingColor(port.accepted_types, typeHierarchy);
        const anyType = isAnyType(port.accepted_types);
        const typeName = primaryTypeName(port.accepted_types);
        const borderColor = ringColor ?? (anyType ? "#d1d5db" : fillColor);
        const shadows: string[] = [];
        if (port.is_collection) {
          shadows.push(`0 0 0 2px white`, `0 0 0 4px ${fillColor}`);
        }
        return (
          <Handle
            key={port.name}
            id={port.name}
            type="source"
            position={Position.Right}
            className="!h-3.5 !w-3.5 !border-2"
            title={`${typeName}${port.description ? " \u2014 " + port.description : ""}`}
            style={{
              backgroundColor: anyType ? "#ffffff" : fillColor,
              borderColor,
              borderStyle: anyType ? "dashed" : "solid",
              right: -7,
              top: 80 + index * 20,
              boxShadow: shadows.length > 0 ? shadows.join(", ") : undefined,
            }}
          />
        );
      })}

      {/* ----------------------------------------------------------------- */}
      {/* Footer                                                            */}
      {/* ----------------------------------------------------------------- */}
      <div className="flex min-w-0 items-center border-t border-stone-100 px-3 py-2">
        <StatusBadge status={data.status} onErrorClick={data.onErrorClick} />
        {data.status === "error" && data.errorMessage ? (
          <ErrorMessage message={data.errorMessage} />
        ) : null}
      </div>
    </div>
  );
}
