import { useMemo, useState } from "react";

import type { BlockSchemaResponse, ChatMessage, LogEntry, WorkflowNode } from "../types/api";
import type { BottomTab } from "../types/ui";

interface BottomPanelProps {
  activeTab: BottomTab;
  selectedNode: WorkflowNode | null;
  selectedSchema?: BlockSchemaResponse;
  chatMessages: ChatMessage[];
  logEntries: LogEntry[];
  onTabChange: (tab: BottomTab) => void;
  onUpdateConfig: (patch: Record<string, unknown>) => void;
  onSendChat: (message: string) => void;
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
  const ordered = Object.entries(properties).sort(([, left], [, right]) => {
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

function AIChat({ messages, onSendChat }: { messages: ChatMessage[]; onSendChat: (message: string) => void }) {
  const [draft, setDraft] = useState("");

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 rounded-[1.5rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        The Phase 8 AI tab is a shell only. Real generation, workflow synthesis, and optimization arrive in Phase 9.
      </div>
      <div className="flex-1 space-y-3 overflow-auto">
        {messages.map((message) => (
          <div
            className={`rounded-[1.4rem] px-4 py-3 text-sm ${message.role === "user" ? "bg-ink text-white" : "bg-white text-stone-700"}`}
            key={message.id}
          >
            <p className="text-[11px] uppercase tracking-[0.25em] opacity-70">{message.role}</p>
            <p className="mt-2 whitespace-pre-wrap">{message.content}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-3">
        <input
          className="flex-1 rounded-full border border-stone-300 bg-white px-4 py-3"
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask for workflow ideas, then get the Phase 9 placeholder."
          value={draft}
        />
        <button
          className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-white"
          onClick={() => {
            if (!draft.trim()) {
              return;
            }
            onSendChat(draft);
            setDraft("");
          }}
          type="button"
        >
          Send
        </button>
      </div>
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
  onTabChange,
  onUpdateConfig,
  onSendChat,
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

      <div className="min-h-0 flex-1 overflow-hidden px-4 py-4">
        <div className="h-full rounded-[1.8rem] border border-stone-200 bg-white/80 p-4">
          {activeTab === "ai" ? (
            <AIChat messages={chatMessages} onSendChat={onSendChat} />
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
