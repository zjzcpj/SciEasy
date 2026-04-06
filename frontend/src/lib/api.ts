import type {
  BlockListResponse,
  BlockSchemaResponse,
  CancelPropagationResponse,
  ConnectionValidationResponse,
  DataMetadataResponse,
  DataPreviewResponse,
  DataUploadResponse,
  ExecuteFromResponse,
  PackageListResponse,
  ProjectResponse,
  WorkflowExecutionResponse,
  WorkflowResponse,
} from "../types/api";

const JSON_HEADERS = {
  "Content-Type": "application/json",
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({ detail: response.statusText }))) as {
      detail?: string;
    };
    throw new Error(payload.detail ?? `Request failed with ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  listProjects: () => apiFetch<ProjectResponse[]>("/api/projects/"),
  createProject: (body: { name: string; description: string; path: string }) =>
    apiFetch<ProjectResponse>("/api/projects/", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(body),
    }),
  openProject: (projectIdOrPath: string) =>
    apiFetch<ProjectResponse>(`/api/projects/${encodeURIComponent(projectIdOrPath)}`),
  updateProject: (projectId: string, body: { name?: string; description?: string }) =>
    apiFetch<ProjectResponse>(`/api/projects/${encodeURIComponent(projectId)}`, {
      method: "PUT",
      headers: JSON_HEADERS,
      body: JSON.stringify(body),
    }),
  deleteProject: (projectId: string) =>
    apiFetch<void>(`/api/projects/${encodeURIComponent(projectId)}`, {
      method: "DELETE",
    }),
  browseDirectory: () => apiFetch<{ path: string | null }>("/api/projects/browse-directory", { method: "POST" }),
  listBlocks: () => apiFetch<BlockListResponse>("/api/blocks/"),
  listPackages: () => apiFetch<PackageListResponse>("/api/blocks/packages"),
  getBlockSchema: (blockType: string) =>
    apiFetch<BlockSchemaResponse>(`/api/blocks/${encodeURIComponent(blockType)}/schema`),
  validateConnection: (body: {
    source_block: string;
    source_port: string;
    target_block: string;
    target_port: string;
  }) =>
    apiFetch<ConnectionValidationResponse>("/api/blocks/validate-connection", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(body),
    }),
  createWorkflow: (body: WorkflowResponse) =>
    apiFetch<WorkflowResponse>("/api/workflows/", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(body),
    }),
  getWorkflow: (workflowId: string) => apiFetch<WorkflowResponse>(`/api/workflows/${encodeURIComponent(workflowId)}`),
  updateWorkflow: (workflowId: string, body: WorkflowResponse) =>
    apiFetch<WorkflowResponse>(`/api/workflows/${encodeURIComponent(workflowId)}`, {
      method: "PUT",
      headers: JSON_HEADERS,
      body: JSON.stringify(body),
    }),
  deleteWorkflow: (workflowId: string) =>
    apiFetch<void>(`/api/workflows/${encodeURIComponent(workflowId)}`, {
      method: "DELETE",
    }),
  executeWorkflow: (workflowId: string) =>
    apiFetch<WorkflowExecutionResponse>(`/api/workflows/${encodeURIComponent(workflowId)}/execute`, {
      method: "POST",
    }),
  pauseWorkflow: (workflowId: string) =>
    apiFetch<WorkflowExecutionResponse>(`/api/workflows/${encodeURIComponent(workflowId)}/pause`, {
      method: "POST",
    }),
  resumeWorkflow: (workflowId: string) =>
    apiFetch<WorkflowExecutionResponse>(`/api/workflows/${encodeURIComponent(workflowId)}/resume`, {
      method: "POST",
    }),
  cancelWorkflow: (workflowId: string) =>
    apiFetch<CancelPropagationResponse>(`/api/workflows/${encodeURIComponent(workflowId)}/cancel`, {
      method: "POST",
    }),
  cancelBlock: (workflowId: string, blockId: string) =>
    apiFetch<CancelPropagationResponse>(
      `/api/workflows/${encodeURIComponent(workflowId)}/blocks/${encodeURIComponent(blockId)}/cancel`,
      { method: "POST" },
    ),
  executeFrom: (workflowId: string, blockId: string) =>
    apiFetch<ExecuteFromResponse>(`/api/workflows/${encodeURIComponent(workflowId)}/execute-from`, {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify({ block_id: blockId }),
    }),
  uploadData: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch<DataUploadResponse>("/api/data/upload", {
      method: "POST",
      body: formData,
    });
  },
  getDataMetadata: (dataRef: string) => apiFetch<DataMetadataResponse>(`/api/data/${encodeURIComponent(dataRef)}`),
  getDataPreview: (dataRef: string) =>
    apiFetch<DataPreviewResponse>(`/api/data/${encodeURIComponent(dataRef)}/preview`),
};
