import type { StateCreator } from "zustand";

import type { AppStore, ExecutionSlice } from "./types";

export const createExecutionSlice: StateCreator<AppStore, [], [], ExecutionSlice> = (set) => ({
  blockStates: {},
  blockOutputs: {},
  executionMessages: [],
  logEntries: [],
  consumeEvent: (event) =>
    set((state) => {
      const nextStates = event.block_id
        ? {
            ...state.blockStates,
            [event.block_id]: event.type.replace("block_", ""),
          }
        : state.blockStates;
      const outputs =
        event.block_id && event.data.outputs && typeof event.data.outputs === "object"
          ? {
              ...state.blockOutputs,
              [event.block_id]: event.data.outputs as Record<string, unknown>,
            }
          : state.blockOutputs;
      return {
        blockStates: nextStates,
        blockOutputs: outputs,
        executionMessages: [...state.executionMessages, `${event.type}:${event.block_id ?? "workflow"}`].slice(-100),
      };
    }),
  appendLog: (entry) =>
    set((state) => ({
      logEntries: [...state.logEntries, entry].slice(-400),
    })),
  resetExecution: () => set({ blockStates: {}, blockOutputs: {}, executionMessages: [], logEntries: [] }),
});
