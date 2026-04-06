import {
  Play,
  Pause,
  Square,
  RotateCcw,
  Trash2,
  RefreshCw,
  FolderOpen,
  Save,
  Import,
  Download,
  ChevronDown,
  Plus,
  X,
  StickyNote,
  BoxSelect,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import type { ProjectResponse } from "../types/api";

interface ToolbarProps {
  currentProject: ProjectResponse | null;
  workflowId: string | null;
  selectedNodeId: string | null;
  wsConnected: boolean;
  sseConnected: boolean;
  recentProjects: ProjectResponse[];
  onNewProject: () => void;
  onOpenProject: () => void;
  onCloseProject: () => void;
  onSave: () => void;
  onImport: () => void;
  onExport: () => void;
  onRun: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onReset: () => void;
  onDelete: () => void;
  onReloadBlocks: () => void;
  onStartFromSelected: () => void;
  onAddAnnotation: () => void;
  onAddGroup: () => void;
}

function StatusPill({
  connected,
  label,
}: {
  connected: boolean;
  label: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
        connected
          ? "bg-pine/15 text-pine"
          : "bg-stone-200 text-stone-500"
      }`}
    >
      <span
        className={`h-2 w-2 rounded-full ${
          connected ? "bg-pine" : "bg-stone-400"
        }`}
      />
      {label}
    </span>
  );
}

function ToolbarButton({
  icon: Icon,
  label,
  shortcut,
  disabled,
  variant = "toolbar",
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  shortcut?: string;
  disabled?: boolean;
  variant?: "toolbar" | "toolbar-dark";
  onClick: () => void;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant={variant}
          size="toolbar"
          disabled={disabled}
          onClick={onClick}
          type="button"
        >
          <Icon className="size-3.5" />
          {label}
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>
          {label}
          {shortcut ? (
            <span className="ml-2 text-xs opacity-70">{shortcut}</span>
          ) : null}
        </p>
      </TooltipContent>
    </Tooltip>
  );
}

export function Toolbar(props: ToolbarProps) {
  const {
    currentProject,
    workflowId,
    selectedNodeId,
    wsConnected,
    sseConnected,
    recentProjects,
    onNewProject,
    onOpenProject,
    onCloseProject,
    onSave,
    onImport,
    onExport,
    onRun,
    onPause,
    onResume,
    onStop,
    onReset,
    onDelete,
    onReloadBlocks,
    onStartFromSelected,
    onAddAnnotation,
    onAddGroup,
  } = props;

  return (
    <TooltipProvider delayDuration={300}>
      <header className="flex items-center gap-3 border-b border-stone-200 bg-white/85 px-5 py-3 backdrop-blur">
        {/* Logo + Project Header */}
        <div className="flex items-center gap-3">
          <div className="rounded-[1.4rem] bg-ink px-4 py-2.5 text-stone-50">
            <p className="font-display text-lg leading-tight">SciEasy</p>
          </div>
          <div className="min-w-0">
            <p className="font-display text-base leading-tight text-ink">
              {currentProject?.name ?? "No project open"}
            </p>
            <p className="truncate text-xs text-stone-500">
              {workflowId
                ? `Workflow: ${workflowId}`
                : "Open or create a project"}
            </p>
          </div>
        </div>

        <Separator orientation="vertical" className="mx-1 h-8" />

        {/* Group 1: Projects Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="toolbar" size="toolbar" type="button">
              <FolderOpen className="size-3.5" />
              Projects
              <ChevronDown className="size-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuItem onClick={onNewProject}>
              <Plus className="size-4" />
              New Project...
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onOpenProject}>
              <FolderOpen className="size-4" />
              Open Project...
            </DropdownMenuItem>
            <DropdownMenuItem
              disabled={!currentProject}
              onClick={onSave}
            >
              <Save className="size-4" />
              Save Project
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuLabel>Recent Projects</DropdownMenuLabel>
            {recentProjects.length > 0 ? (
              recentProjects.slice(0, 5).map((project) => (
                <DropdownMenuItem
                  key={project.id}
                  onClick={onOpenProject}
                >
                  <span className="truncate">{project.name}</span>
                </DropdownMenuItem>
              ))
            ) : (
              <DropdownMenuItem disabled>
                <span className="text-stone-400">No recent projects</span>
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              disabled={!currentProject}
              onClick={onCloseProject}
            >
              <X className="size-4" />
              Close Project
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Separator orientation="vertical" className="mx-1 h-8" />

        {/* Group 2: File Operations */}
        <div className="flex items-center gap-1">
          <ToolbarButton
            icon={Import}
            label="Import"
            shortcut="Ctrl+O"
            onClick={onImport}
          />
          <ToolbarButton
            icon={Save}
            label="Save"
            shortcut="Ctrl+S"
            disabled={!currentProject}
            onClick={onSave}
          />
          <ToolbarButton
            icon={Download}
            label="Export"
            shortcut="Ctrl+Shift+S"
            disabled={!currentProject}
            onClick={onExport}
          />
        </div>

        <Separator orientation="vertical" className="mx-1 h-8" />

        {/* Group 3: Execution Controls */}
        <div className="flex items-center gap-1">
          <ToolbarButton
            icon={Play}
            label="Run"
            shortcut="Ctrl+Enter"
            variant="toolbar-dark"
            disabled={!currentProject}
            onClick={onRun}
          />
          <ToolbarButton
            icon={Pause}
            label="Pause"
            disabled={!workflowId}
            onClick={onPause}
          />
          <ToolbarButton
            icon={Square}
            label="Stop"
            shortcut="Ctrl+."
            disabled={!workflowId}
            onClick={onStop}
          />
          <ToolbarButton
            icon={RotateCcw}
            label="Reset"
            disabled={!workflowId}
            onClick={onReset}
          />
        </div>

        <Separator orientation="vertical" className="mx-1 h-8" />

        {/* Group 4: Edit Operations */}
        <div className="flex items-center gap-1">
          <ToolbarButton
            icon={Trash2}
            label="Delete"
            disabled={!selectedNodeId}
            onClick={onDelete}
          />
          <ToolbarButton
            icon={RefreshCw}
            label="Reload"
            onClick={onReloadBlocks}
          />
          <ToolbarButton
            icon={StickyNote}
            label="Note"
            disabled={!currentProject}
            onClick={onAddAnnotation}
          />
          <ToolbarButton
            icon={BoxSelect}
            label="Group"
            disabled={!currentProject}
            onClick={onAddGroup}
          />
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Connection Status */}
        <div className="flex items-center gap-2">
          <StatusPill connected={wsConnected} label="WS" />
          <StatusPill connected={sseConnected} label="Logs" />
        </div>
      </header>
    </TooltipProvider>
  );
}
