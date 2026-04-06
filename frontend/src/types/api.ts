export interface Position {
  x: number;
  y: number;
}

export interface WorkflowNode {
  id: string;
  block_type: string;
  config: Record<string, unknown>;
  execution_mode?: string | null;
  layout?: Position | null;
}

export interface WorkflowEdge {
  source: string;
  target: string;
}

export interface WorkflowResponse {
  id: string;
  version: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  metadata: Record<string, unknown>;
}

export interface WorkflowExecutionResponse {
  workflow_id: string;
  status: string;
  message: string;
}

export interface ExecuteFromResponse extends WorkflowExecutionResponse {
  reused_blocks: string[];
  reset_blocks: string[];
}

export interface ProjectResponse {
  id: string;
  name: string;
  description: string;
  path: string;
  last_opened?: string | null;
  workflow_count: number;
  workflows: string[];
  current_workflow_id?: string | null;
}

export interface BlockPortResponse {
  name: string;
  direction: string;
  accepted_types: string[];
  required: boolean;
  description: string;
  constraint_description: string;
  is_collection: boolean;
}

export interface BlockSummary {
  name: string;
  type_name: string;
  category: string;
  description: string;
  version: string;
  package_name: string;
  input_ports: BlockPortResponse[];
  output_ports: BlockPortResponse[];
}

export interface TypeHierarchyEntry {
  name: string;
  base_type: string;
  description: string;
  ui_ring_color?: string | null;
}

export interface BlockSchemaResponse extends BlockSummary {
  config_schema: {
    type?: string;
    properties?: Record<string, Record<string, unknown>>;
    required?: string[];
  };
  type_hierarchy: TypeHierarchyEntry[];
}

export interface BlockListResponse {
  blocks: BlockSummary[];
}

export interface PackageInfoResponse {
  name: string;
  description: string;
  author: string;
  version: string;
}

export interface PackageListResponse {
  packages: PackageInfoResponse[];
}

export interface ConnectionValidationResponse {
  compatible: boolean;
  reason: string;
}

export interface DataUploadResponse {
  ref: string;
  type_name: string;
  metadata: Record<string, unknown>;
}

export interface DataMetadataResponse {
  ref: string;
  type_name: string;
  metadata: Record<string, unknown>;
}

export interface DataPreviewResponse {
  ref: string;
  type_name: string;
  preview: Record<string, unknown>;
}

export interface CancelPropagationResponse {
  cancelled_blocks: string[];
  skipped_blocks: string[];
  skip_reasons: Record<string, string>;
}

export interface WorkflowEventMessage {
  type: string;
  block_id?: string | null;
  workflow_id?: string | null;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  workflow_id?: string | null;
  block_id?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}
