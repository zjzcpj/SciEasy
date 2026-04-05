import type { StateCreator } from "zustand";

import type { AppStore, UISlice } from "./types";

export const createUISlice: StateCreator<AppStore, [], [], UISlice> = (set) => ({
  selectedNodeId: null,
  activeBottomTab: "config",
  paletteCollapsed: false,
  previewCollapsed: false,
  bottomPanelCollapsed: false,
  minimapVisible: true,
  panelSizes: {
    palette: 15,
    preview: 22,
    bottom: 30,
  },
  lastError: null,
  setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),
  setActiveBottomTab: (tab) => set({ activeBottomTab: tab }),
  togglePalette: () => set((state) => ({ paletteCollapsed: !state.paletteCollapsed })),
  togglePreview: () => set((state) => ({ previewCollapsed: !state.previewCollapsed })),
  toggleBottomPanel: () => set((state) => ({ bottomPanelCollapsed: !state.bottomPanelCollapsed })),
  toggleMinimap: () => set((state) => ({ minimapVisible: !state.minimapVisible })),
  setPanelSize: (panel, size) =>
    set((state) => ({
      panelSizes: {
        ...state.panelSizes,
        [panel]: size,
      },
    })),
  setLastError: (message) => set({ lastError: message }),
});
