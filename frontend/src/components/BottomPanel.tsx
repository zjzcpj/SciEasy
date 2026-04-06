import { useMemo, useState } from "react";

import type { BlockSchemaResponse, ChatMessage, LogEntry, WorkflowNode } from "../types/api";
import type { BottomTab } from "../types/ui";
import { AIChat } from "./AIChat";

interface BottomPanelProps {
  activeTab: BottomTab;
  selectedNode: WorkflowNode | null;
  selectedSchema?: BlockSchemaResponse;
  chatMessages: ChatMessage[];
  logEntries: LogEntry[];
  aiLoading: boolean;
  aiError: string | null;
  onTabChange: (tab: BottomTab) => void;
  onUpdateConfig: (patch: Record<string, unknown>) => void;
  onSendChat: (message: string) => void;
  onApplyWorkflow?: (workflow: Record<string, unknown>) => void;
}

const TAB_LABELS: Record<BottomTab, string> = {
  ai: "\u{1F4AC} AI Chat",
  config: "\u{1F4CB} Config",
  logs: "\u{1F4DC} Logs",
  lineage: "\u{1F517} Lineage",
  jobs: "\u{1F4CA} Jobs",
  problems: "\u26A0 Problems",
};

const ALL_TABS: BottomTab[] = ["ai", "config", "logs", "lineage", "jobs", "problems"];

function ConfigPanel({
  selectedNode,
  schema,
  onUpdateConfig,
}: {
  selectedNode: WorkflowNode | null;
  schema?: BlockSchemaResponse;
  onUpdateConfig: (patch: Record<string, unknown>) => void;
}) {
  const params = ((selectedNode?.config.params as Record<string, unknown> | undefined) ?? {}) as Record<string, unknown>;
  const properties = schema?.config_schema.properties ?? {};
  const ordered = Object.entries(properties)
    .filter(([key]) => {
      // For io_block, hide "direction" — it is already determined by whether
      // the user dragged a Load Block or Save Block from the palette.
      if (selectedNode?.block_type === "io_block" && key === "direction") return false;
      return true;
    })
    .sort(([, left], [, right]) => {
      return Number(left.ui_priority ?? 99) - Number(right.ui_priority ?? 99);
    });

  if (!selectedNode || !schema) {
    return <div className="text-sm text-stone-500">Select a node to edit its JSON-schema-driven configuration.</div>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {ordered.map(([key, value]) => {
        const currentValue = params[key] ?? value.default ?? "";
        if (Array.isArray(value.enum)) {
          return (
            <label className="grid gap-2 text-sm" key={key}>
              <span className="font-medium text-ink">{String(value.title ?? key)}</span>
              <select
                className="rounded-2xl border border-stone-300 bg-white px-4 py-3"
                onChange={(event) => onUpdateConfig({ [key]: event.target.value })}
                value={String(currentValue)}
              >
                {value.enum.map((option) => (
                  <option key={String(option)} value={String(option)}>
                    {String(option)}
                  </option>
                ))}
              </select>
            </label>
          );
        }
        return (
          <label className="grid gap-2 text-sm" key={key}>
            <span className="font-medium text-ink">{String(value.title ?? key)}</span>
            <input
              className="rounded-2xl border border-stone-300 bg-white px-4 py-3"
              onChange={(event) =>
                onUpdateConfig({
                  [key]: value.type === "number" ? Number(event.target.value) : event.target.value,
                })
              }
              type={value.type === "number" ? "number" : "text"}
              value={String(currentValue)}
            />
          </label>
        );
      })}
    </div>
  );
}

function LogViewer({ entries }: { entries: LogEntry[] }) {
  const [level, setLevel] = useState("all");
  const filtered = useMemo(() => {
    return entries.filter((entry) => level === "all" || entry.level === level);
  }, [entries, level]);

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex items-center gap-3">
        <select className="rounded-full border border-stone-300 bg-white px-3 py-2 text-sm" onChange={(event) => setLevel(event.target.value)} value={level}>
          <option value="all">All levels</option>
          <option value="info">Info</option>
          <option value="error">Error</option>
        </select>
      </div>
      <div className="flex-1 overflow-auto rounded-[1.4rem] border border-stone-200 bg-stone-950 p-4">
        {filtered.length ? (
          filtered.map((entry, index) => (
            <div className="border-b border-stone-800 py-2 text-sm text-stone-100" key={`${entry.timestamp}-${index}`}>
              <p className="text-[11px] uppercase tracking-[0.3em] text-stone-500">
                {entry.level} · {entry.workflow_id ?? "workflow"} · {entry.block_id ?? "system"}
              </p>
              <p className="mt-1">{entry.message}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-stone-500">No logs yet.</p>
        )}
      </div>
    </div>
  );
}

function PlaceholderTab() {
  return (
    <div className="flex h-full items-center justify-center">
      <p className="text-sm text-stone-400">Coming in Phase 8.5</p>
    </div>
  );
}

export function BottomPanel({
  activeTab,
  selectedNode,
  selectedSchema,
  chatMessages,
  logEntries,
  aiLoading,
  aiError,
  onTabChange,
  onUpdateConfig,
  onSendChat,
  onApplyWorkflow,
}: BottomPanelProps) {
  return (
    <section className="flex h-full flex-col overflow-hidden bg-[linear-gradient(180deg,_rgba(255,255,255,0.94),_rgba(238,231,219,0.98))]">
      <div className="flex items-center gap-3 border-b border-stone-200 px-4 py-3">
        <div className="flex gap-2">
          {ALL_TABS.map((tab) => (
            <button
              className={`rounded-full px-4 py-2 text-sm font-medium ${activeTab === tab ? "bg-ink text-white" : "bg-white text-stone-600"}`}
              key={tab}
              onClick={() => onTabChange(tab)}
              type="button"
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 scrollbar-thin">
        <div className="h-full rounded-[1.8rem] border border-stone-200 bg-white/80 p-4">
          {activeTab === "ai" ? (
            <AIChat
              error={aiError}
              isLoading={aiLoading}
              messages={chatMessages}
              onApplyWorkflow={onApplyWorkflow}
              onSendChat={onSendChat}
            />
          ) : activeTab === "config" ? (
            <ConfigPanel onUpdateConfig={onUpdateConfig} schema={selectedSchema} selectedNode={selectedNode} />
          ) : activeTab === "logs" ? (
            <LogViewer entries={logEntries} />
          ) : (
            <PlaceholderTab />
          )}
        </div>
      </div>
    </section>
  );
}
