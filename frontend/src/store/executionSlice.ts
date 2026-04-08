import type { StateCreator } from "zustand";

import type { AppStore, ExecutionSlice } from "./types";

export const createExecutionSlice: StateCreator<AppStore, [], [], ExecutionSlice> = (set) => ({
  blockStates: {},
  blockOutputs: {},
  blockErrors: {},
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

      // Extract and store error message when a block_error event arrives.
      const isBlockError = event.type === "block_error" && event.block_id != null;
      const errorText =
        isBlockError && typeof event.data.error === "string" ? event.data.error : undefined;
      const nextErrors =
        isBlockError && errorText != null
          ? { ...state.blockErrors, [event.block_id as string]: errorText }
          : state.blockErrors;

      // Append a structured log entry for block_error so the Logs panel
      // shows the full error text alongside the standard log stream.
      const nextLogs =
        isBlockError && errorText != null
          ? [
              ...state.logEntries,
              {
                timestamp: event.timestamp,
                level: "error",
                message: errorText,
                workflow_id: event.workflow_id ?? null,
                block_id: event.block_id ?? null,
              },
            ].slice(-400)
          : state.logEntries;

      return {
        blockStates: nextStates,
        blockOutputs: outputs,
        blockErrors: nextErrors,
        logEntries: nextLogs,
        executionMessages: [...state.executionMessages, `${event.type}:${event.block_id ?? "workflow"}`].slice(-100),
      };
    }),
  appendLog: (entry) =>
    set((state) => ({
      logEntries: [...state.logEntries, entry].slice(-400),
    })),
  resetExecution: () => set({ blockStates: {}, blockOutputs: {}, blockErrors: {}, executionMessages: [], logEntries: [] }),
});
