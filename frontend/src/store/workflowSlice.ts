import type { StateCreator } from "zustand";

import type { BlockSummary, WorkflowEdge, WorkflowNode } from "../types/api";
import type { AppStore, WorkflowHistoryEntry, WorkflowSlice } from "./types";

function snapshot(state: AppStore): WorkflowHistoryEntry {
  return {
    nodes: state.workflowNodes.map((node) => ({ ...node, config: { ...node.config }, layout: node.layout ? { ...node.layout } : null })),
    edges: state.workflowEdges.map((edge) => ({ ...edge })),
    description: state.workflowDescription,
  };
}

function pushHistory(state: AppStore): Pick<AppStore, "workflowHistory" | "workflowFuture"> {
  return {
    workflowHistory: [...state.workflowHistory, snapshot(state)].slice(-40),
    workflowFuture: [],
  };
}

function mergeNodeConfig(node: WorkflowNode, config: Record<string, unknown>): WorkflowNode {
  return {
    ...node,
    config: {
      ...node.config,
      params: {
        ...(((node.config.params as Record<string, unknown> | undefined) ?? {})),
        ...config,
      },
    },
  };
}

export const createWorkflowSlice: StateCreator<AppStore, [], [], WorkflowSlice> = (set, get) => ({
  workflowId: null,
  workflowDescription: "",
  workflowVersion: "1.0.0",
  workflowMetadata: {},
  workflowNodes: [],
  workflowEdges: [],
  workflowDirty: false,
  workflowHistory: [],
  workflowFuture: [],
  setWorkflow: (workflow) =>
    set({
      workflowId: workflow?.id ?? null,
      workflowDescription: workflow?.description ?? "",
      workflowVersion: workflow?.version ?? "1.0.0",
      workflowMetadata: workflow?.metadata ?? {},
      workflowNodes: workflow?.nodes ?? [],
      workflowEdges: workflow?.edges ?? [],
      workflowDirty: false,
      workflowHistory: [],
      workflowFuture: [],
    }),
  addNode: (block, position, defaultParams) =>
    set((state) => ({
      ...pushHistory(state),
      workflowDirty: true,
      workflowId: state.workflowId ?? "main",
      workflowNodes: [
        ...state.workflowNodes,
        {
          id: `${block.type_name}-${Date.now()}`,
          block_type: block.type_name,
          config: { params: defaultParams ?? {} },
          layout: position,
        },
      ],
    })),
  updateNodeConfig: (nodeId, config) =>
    set((state) => ({
      ...pushHistory(state),
      workflowDirty: true,
      workflowNodes: state.workflowNodes.map((node) => (node.id === nodeId ? mergeNodeConfig(node, config) : node)),
    })),
  updateNodeLayout: (nodeId, position) =>
    set((state) => ({
      workflowDirty: true,
      workflowNodes: state.workflowNodes.map((node) => (node.id === nodeId ? { ...node, layout: position } : node)),
    })),
  connectNodes: (edge) =>
    set((state) => ({
      ...pushHistory(state),
      workflowDirty: true,
      workflowEdges: [...state.workflowEdges, edge],
    })),
  removeNode: (nodeId) =>
    set((state) => ({
      ...pushHistory(state),
      workflowDirty: true,
      workflowNodes: state.workflowNodes.filter((node) => node.id !== nodeId),
      workflowEdges: state.workflowEdges.filter(
        (edge) => !edge.source.startsWith(`${nodeId}:`) && !edge.target.startsWith(`${nodeId}:`),
      ),
    })),
  removeEdge: (edgeToRemove) =>
    set((state) => ({
      ...pushHistory(state),
      workflowDirty: true,
      workflowEdges: state.workflowEdges.filter(
        (edge) => edge.source !== edgeToRemove.source || edge.target !== edgeToRemove.target,
      ),
    })),
  setWorkflowDescription: (description) => set({ workflowDescription: description, workflowDirty: true }),
  markWorkflowSaved: () => set({ workflowDirty: false }),
  undoWorkflow: () => {
    const state = get();
    const last = state.workflowHistory[state.workflowHistory.length - 1];
    if (!last) {
      return;
    }
    set({
      workflowNodes: last.nodes,
      workflowEdges: last.edges,
      workflowDescription: last.description,
      workflowDirty: true,
      workflowHistory: state.workflowHistory.slice(0, -1),
      workflowFuture: [...state.workflowFuture, snapshot(state)].slice(-40),
    });
  },
  redoWorkflow: () => {
    const state = get();
    const next = state.workflowFuture[state.workflowFuture.length - 1];
    if (!next) {
      return;
    }
    set({
      workflowNodes: next.nodes,
      workflowEdges: next.edges,
      workflowDescription: next.description,
      workflowDirty: true,
      workflowHistory: [...state.workflowHistory, snapshot(state)].slice(-40),
      workflowFuture: state.workflowFuture.slice(0, -1),
    });
  },
});
