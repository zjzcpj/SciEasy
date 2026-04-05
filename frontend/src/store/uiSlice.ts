import type { StateCreator } from "zustand";

import type { AppStore, UISlice } from "./types";

export const createUISlice: StateCreator<AppStore, [], [], UISlice> = (set) => ({
  selectedNodeId: null,
  activeBottomTab: "config",
  paletteCollapsed: false,
  previewCollapsed: false,
  bottomPanelCollapsed: false,
  panelSizes: {
    palette: 320,
    preview: 360,
    bottom: 280,
  },
  lastError: null,
  setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),
  setActiveBottomTab: (tab) => set({ activeBottomTab: tab }),
  togglePalette: () => set((state) => ({ paletteCollapsed: !state.paletteCollapsed })),
  togglePreview: () => set((state) => ({ previewCollapsed: !state.previewCollapsed })),
  toggleBottomPanel: () => set((state) => ({ bottomPanelCollapsed: !state.bottomPanelCollapsed })),
  setPanelSize: (panel, size) =>
    set((state) => ({
      panelSizes: {
        ...state.panelSizes,
        [panel]: size,
      },
    })),
  setLastError: (message) => set({ lastError: message }),
});
