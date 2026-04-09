import type { ProjectResponse } from "../types/api";

interface ProjectDialogProps {
  open: boolean;
  mode: "new" | "open";
  name: string;
  description: string;
  path: string;
  recentProjects: ProjectResponse[];
  onClose: () => void;
  onChange: (patch: Partial<{ name: string; description: string; path: string }>) => void;
  onSubmit: () => void;
  onOpenRecent: (projectIdOrPath: string) => void;
}

export function ProjectDialog({
  open,
  mode,
  name,
  description,
  path,
  recentProjects,
  onClose,
  onChange,
  onSubmit,
  onOpenRecent,
}: ProjectDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/55 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-[2rem] border border-stone-200 bg-stone-50 p-6 shadow-panel">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-stone-500">Projects</p>
            <h2 className="mt-2 font-display text-3xl text-ink">
              {mode === "new" ? "Create a new workspace" : "Open an existing workspace"}
            </h2>
          </div>
          <button className="rounded-full border border-stone-300 px-3 py-1 text-sm" onClick={onClose} type="button">
            Close
          </button>
        </div>

        <div className={`grid gap-4 ${mode === "new" ? "md:grid-cols-2" : ""}`}>
          <label className="grid gap-2 text-sm text-stone-700">
            <span className="font-medium">{mode === "new" ? "Project name" : "Project ID or path"}</span>
            {mode === "open" ? (
              <input
                className="min-w-0 flex-1 rounded-2xl border border-stone-300 bg-white px-4 py-3 outline-none transition focus:border-ember"
                onChange={(event) => onChange({ path: event.target.value })}
                placeholder="C:\\research\\atlas-project"
                value={path}
              />
            ) : (
              <input
                className="rounded-2xl border border-stone-300 bg-white px-4 py-3 outline-none transition focus:border-ember"
                onChange={(event) => onChange({ name: event.target.value })}
                placeholder="Multimodal Atlas"
                value={name}
              />
            )}
          </label>
          {mode === "new" ? (
            <label className="grid gap-2 text-sm text-stone-700">
              <span className="font-medium">Parent directory</span>
              <input
                className="min-w-0 flex-1 rounded-2xl border border-stone-300 bg-white px-4 py-3 outline-none transition focus:border-ember"
                onChange={(event) => onChange({ path: event.target.value })}
                placeholder="C:\\projects"
                value={path}
              />
            </label>
          ) : null}
          {mode === "new" ? (
            <label className="grid gap-2 text-sm text-stone-700 md:col-span-2">
              <span className="font-medium">Description</span>
              <textarea
                className="min-h-28 rounded-2xl border border-stone-300 bg-white px-4 py-3 outline-none transition focus:border-ember"
                onChange={(event) => onChange({ description: event.target.value })}
                placeholder="Integrated IF, Raman, and LC-MS pilot."
                value={description}
              />
            </label>
          ) : null}
        </div>

        <div className="mt-6 rounded-[1.5rem] border border-stone-200 bg-white/80 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">Recent projects</p>
          <div className="mt-3 flex flex-col gap-2">
            {recentProjects.length ? (
              recentProjects.slice(0, 5).map((project) => (
                <button
                  className="flex items-center justify-between rounded-2xl border border-stone-200 px-4 py-3 text-left transition hover:border-pine hover:bg-pine/5"
                  key={project.id}
                  onClick={() => onOpenRecent(project.id)}
                  type="button"
                >
                  <span>
                    <span className="block font-medium text-ink">{project.name}</span>
                    <span className="block text-xs text-stone-500">{project.path}</span>
                  </span>
                  <span className="rounded-full bg-sand px-3 py-1 text-xs text-stone-700">
                    {project.workflow_count} workflow{project.workflow_count === 1 ? "" : "s"}
                  </span>
                </button>
              ))
            ) : (
              <p className="text-sm text-stone-500">No project history yet. Create one to get started.</p>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button className="rounded-full border border-stone-300 px-4 py-2 text-sm" onClick={onClose} type="button">
            Cancel
          </button>
          <button
            className="rounded-full bg-ink px-5 py-2 text-sm font-medium text-stone-50 transition hover:bg-pine"
            onClick={onSubmit}
            type="button"
          >
            {mode === "new" ? "Create project" : "Open project"}
          </button>
        </div>
      </div>
    </div>
  );
}
