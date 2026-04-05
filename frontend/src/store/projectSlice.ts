import type { StateCreator } from "zustand";

import type { AppStore, ProjectDialogState, ProjectSlice } from "./types";

const defaultDialog: ProjectDialogState = {
  mode: "new",
  name: "",
  description: "",
  path: "",
};

export const createProjectSlice: StateCreator<AppStore, [], [], ProjectSlice> = (set) => ({
  currentProject: null,
  recentProjects: [],
  projectDialogOpen: false,
  projectDialog: defaultDialog,
  setProjects: (projects) => set({ recentProjects: projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
  openProjectDialog: (mode, partial) =>
    set({
      projectDialogOpen: true,
      projectDialog: {
        ...defaultDialog,
        ...partial,
        mode,
      },
    }),
  closeProjectDialog: () => set({ projectDialogOpen: false }),
  updateProjectDialog: (patch) =>
    set((state) => ({
      projectDialog: {
        ...state.projectDialog,
        ...patch,
      },
    })),
});
