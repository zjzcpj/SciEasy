import type { ProjectResponse } from "../types/api";

interface ToolbarProps {
  currentProject: ProjectResponse | null;
  workflowId: string | null;
  selectedNodeId: string | null;
  wsConnected: boolean;
  sseConnected: boolean;
  onNewProject: () => void;
  onOpenProject: () => void;
  onSave: () => void;
  onRun: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onReloadBlocks: () => void;
  onStartFromSelected: () => void;
  onTogglePalette: () => void;
  onTogglePreview: () => void;
}

function StatusPill({ connected, label }: { connected: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
        connected ? "bg-pine/15 text-pine" : "bg-stone-200 text-stone-500"
      }`}
    >
      <span className={`h-2 w-2 rounded-full ${connected ? "bg-pine" : "bg-stone-400"}`} />
      {label}
    </span>
  );
}

export function Toolbar(props: ToolbarProps) {
  const {
    currentProject,
    workflowId,
    selectedNodeId,
    wsConnected,
    sseConnected,
    onNewProject,
    onOpenProject,
    onSave,
    onRun,
    onPause,
    onResume,
    onStop,
    onReloadBlocks,
    onStartFromSelected,
    onTogglePalette,
    onTogglePreview,
  } = props;

  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-stone-200 bg-white/85 px-5 py-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="rounded-[1.4rem] bg-ink px-4 py-3 text-stone-50">
          <p className="font-display text-xl">SciEasy</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-stone-500">Current Project</p>
          <p className="font-display text-xl text-ink">{currentProject?.name ?? "No project open"}</p>
          <p className="text-xs text-stone-500">{workflowId ? `Workflow: ${workflowId}` : "Open or create a project"}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button className="toolbar-button toolbar-button-dark" onClick={onNewProject} type="button">
          New
        </button>
        <button className="toolbar-button" onClick={onOpenProject} type="button">
          Open
        </button>
        <button className="toolbar-button" disabled={!currentProject} onClick={onSave} type="button">
          Save
        </button>
        <button className="toolbar-button" disabled={!currentProject} onClick={onRun} type="button">
          Run
        </button>
        <button className="toolbar-button" disabled={!workflowId} onClick={onPause} type="button">
          Pause
        </button>
        <button className="toolbar-button" disabled={!workflowId} onClick={onResume} type="button">
          Resume
        </button>
        <button className="toolbar-button" disabled={!workflowId} onClick={onStop} type="button">
          Stop
        </button>
        <button className="toolbar-button" disabled={!selectedNodeId || !workflowId} onClick={onStartFromSelected} type="button">
          Start From Here
        </button>
        <button className="toolbar-button" onClick={onReloadBlocks} type="button">
          Reload Blocks
        </button>
        <button className="toolbar-button" onClick={onTogglePalette} type="button">
          Toggle Palette
        </button>
        <button className="toolbar-button" onClick={onTogglePreview} type="button">
          Toggle Preview
        </button>
      </div>

      <div className="flex items-center gap-2">
        <StatusPill connected={wsConnected} label="WebSocket" />
        <StatusPill connected={sseConnected} label="Logs" />
      </div>
    </header>
  );
}
