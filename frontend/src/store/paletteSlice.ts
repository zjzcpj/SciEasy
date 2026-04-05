import type { StateCreator } from "zustand";

import type { AppStore, PaletteSlice } from "./types";

export const createPaletteSlice: StateCreator<AppStore, [], [], PaletteSlice> = (set) => ({
  blocks: [],
  blockSchemas: {},
  paletteSearch: "",
  setBlocks: (blocks) => set({ blocks }),
  setBlockSchema: (schema) =>
    set((state) => ({
      blockSchemas: {
        ...state.blockSchemas,
        [schema.type_name]: schema,
      },
    })),
  setPaletteSearch: (paletteSearch) => set({ paletteSearch }),
});
