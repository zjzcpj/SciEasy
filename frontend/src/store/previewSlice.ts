import type { StateCreator } from "zustand";

import type { AppStore, PreviewSlice } from "./types";

export const createPreviewSlice: StateCreator<AppStore, [], [], PreviewSlice> = (set) => ({
  previewCache: {},
  previewLoading: {},
  cachePreview: (payload) =>
    set((state) => ({
      previewCache: {
        ...state.previewCache,
        [payload.ref]: payload,
      },
      previewLoading: {
        ...state.previewLoading,
        [payload.ref]: false,
      },
    })),
  setPreviewLoading: (ref, loading) =>
    set((state) => ({
      previewLoading: {
        ...state.previewLoading,
        [ref]: loading,
      },
    })),
});
