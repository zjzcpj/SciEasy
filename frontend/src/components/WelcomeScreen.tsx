import type { ProjectResponse } from "../types/api";

interface WelcomeScreenProps {
  recentProjects: ProjectResponse[];
  onNewProject: () => void;
  onOpenProject: () => void;
  onOpenRecent: (projectId: string) => void;
}

export function WelcomeScreen({
  recentProjects,
  onNewProject,
  onOpenProject,
  onOpenRecent,
}: WelcomeScreenProps) {
  return (
    <div className="flex h-full items-center justify-center overflow-auto p-6">
      <div className="w-full max-w-4xl rounded-[2.5rem] border border-stone-200 bg-[radial-gradient(circle_at_top_left,_rgba(240,106,68,0.2),_transparent_35%),linear-gradient(135deg,_rgba(255,255,255,0.95),_rgba(245,241,232,0.98))] p-8 shadow-panel">
        <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-stone-500">SciEasy Studio</p>
            <h1 className="mt-4 max-w-xl font-display text-5xl leading-tight text-ink">
              Every tool. Every format. One workflow.
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-8 text-stone-600">
              Build typed scientific workflows that connect Python, R, CLI tools, and GUI applications
              in a single backend-owned runtime.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-stone-50 transition hover:bg-pine"
                onClick={onNewProject}
                type="button"
              >
                New Project
              </button>
              <button
                className="rounded-full border border-stone-300 bg-white px-6 py-3 text-sm font-medium text-ink transition hover:border-ember hover:text-ember"
                onClick={onOpenProject}
                type="button"
              >
                Open Project
              </button>
            </div>
          </div>

          <div className="rounded-[2rem] border border-stone-200 bg-white/80 p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">Recent Workspaces</p>
            <div className="mt-4 flex flex-col gap-3">
              {recentProjects.length ? (
                recentProjects.slice(0, 5).map((project) => (
                  <button
                    className="rounded-[1.5rem] border border-stone-200 px-4 py-4 text-left transition hover:border-pine hover:bg-pine/5"
                    key={project.id}
                    onClick={() => onOpenRecent(project.id)}
                    type="button"
                  >
                    <span className="block font-medium text-ink">{project.name}</span>
                    <span className="mt-1 block text-xs text-stone-500">{project.path}</span>
                  </button>
                ))
              ) : (
                <p className="text-sm text-stone-500">No recent projects yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
