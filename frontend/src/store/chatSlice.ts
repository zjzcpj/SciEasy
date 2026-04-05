import type { StateCreator } from "zustand";

import type { AppStore, ChatSlice } from "./types";

export const createChatSlice: StateCreator<AppStore, [], [], ChatSlice> = (set) => ({
  chatMessages: [],
  pushChatMessage: (message) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, message].slice(-60),
    })),
  clearChatMessages: () => set({ chatMessages: [] }),
});
