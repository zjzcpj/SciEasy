import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useMemo, useState } from "react";

import { resolveTypeColor } from "../config/typeColorMap";
import type { BlockSchemaResponse, BlockSummary, WorkflowEdge, WorkflowNode } from "../types/api";
import type { BlockNodeData } from "../types/ui";
import { AnnotationNode } from "./nodes/AnnotationNode";
import { BlockNode } from "./nodes/BlockNode";
import { GroupNode } from "./nodes/GroupNode";
import { TypedEdge } from "./TypedEdge";

const nodeTypes = {
  block: BlockNode,
  _annotation: AnnotationNode,
  _group: GroupNode,
};
const edgeTypes = { typed: TypedEdge };

function parsePortRef(ref: string): { nodeId: string; portName: string } {
  const [nodeId, portName] = ref.split(":");
  return { nodeId, portName };
}

interface WorkflowCanvasProps {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  blocks: BlockSummary[];
  schemas: Record<string, BlockSchemaResponse>;
  blockStates: Record<string, string>;
  blockErrors: Record<string, string>;
  selectedNodeId: string | null;
  minimapVisible: boolean;
  onSelectNode: (nodeId: string | null) => void;
  onAddNode: (block: BlockSummary, position: { x: number; y: number }, defaultParams?: Record<string, unknown>) => void;
  onUpdateNodePosition: (nodeId: string, position: { x: number; y: number }) => void;
  onUpdateNodeConfig: (nodeId: string, config: Record<string, unknown>) => void;
  onConnect: (connection: WorkflowEdge) => Promise<void>;
  onDeleteNode: (nodeId: string) => void;
  onDeleteEdge: (edge: WorkflowEdge) => void;
  onRunBlock: (blockId: string) => void;
  onRestartBlock: (blockId: string) => void;
  onErrorClick: (blockId: string) => void;
}

export function WorkflowCanvas(props: WorkflowCanvasProps) {
  const reactFlow = useReactFlow();
  const {
    blocks,
    schemas,
    blockStates,
    blockErrors,
    edges,
    minimapVisible,
    nodes,
    onAddNode,
    onConnect,
    onDeleteEdge,
    onDeleteNode,
    onErrorClick,
    onRestartBlock,
    onRunBlock,
    onSelectNode,
    onUpdateNodeConfig,
    onUpdateNodePosition,
    selectedNodeId,
  } = props;

  // Track positions locally during drag so nodes follow the cursor smoothly.
  // ReactFlow is in controlled mode (nodes prop), so without this the node
  // would only jump to its final position on drag-stop.
  const [dragPositions, setDragPositions] = useState<Record<string, { x: number; y: number }>>({});

  const makeOnRun = useCallback((nodeId: string) => () => onRunBlock(nodeId), [onRunBlock]);
  const makeOnRestart = useCallback((nodeId: string) => () => onRestartBlock(nodeId), [onRestartBlock]);
  const makeOnDelete = useCallback((nodeId: string) => () => onDeleteNode(nodeId), [onDeleteNode]);
  const makeOnErrorClick = useCallback((nodeId: string) => () => onErrorClick(nodeId), [onErrorClick]);
  const makeOnUpdateConfig = useCallback(
    (nodeId: string) => (patch: Record<string, unknown>) => onUpdateNodeConfig(nodeId, patch),
    [onUpdateNodeConfig],
  );

  /** Derive canvas display label for a node. For io_block nodes the label
   *  reflects the configured direction (Load Block / Save Block). */
  const resolveLabel = useCallback(
    (node: WorkflowNode, summary?: BlockSummary, schema?: BlockSchemaResponse) => {
      if (node.block_type === "io_block") {
        const params = (node.config.params as Record<string, unknown> | undefined) ?? {};
        const direction = params.direction as string | undefined;
        if (direction === "output") return "Save Block";
        return "Load Block";
      }
      return summary?.name ?? schema?.name ?? node.block_type;
    },
    [],
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const flowNodes = useMemo<Array<Node<any>>>(() => {
    return nodes.map((node, index) => {
      const storePos = node.layout ?? { x: 120 + index * 80, y: 120 + index * 40 };
      const position = dragPositions[node.id] ?? storePos;
      const params = ((node.config.params as Record<string, unknown> | undefined) ?? {}) as Record<string, unknown>;

      // Annotation node
      if (node.block_type === "_annotation") {
        return {
          id: node.id,
          type: "_annotation",
          position,
          data: {
            text: (params.text as string) ?? "Note",
            onUpdateText: (text: string) => onUpdateNodeConfig(node.id, { text }),
          },
          selected: selectedNodeId === node.id,
        };
      }

      // Group frame node
      if (node.block_type === "_group") {
        return {
          id: node.id,
          type: "_group",
          position,
          style: {
            width: (node.config.style as Record<string, unknown> | undefined)?.width as number ?? 400,
            height: (node.config.style as Record<string, unknown> | undefined)?.height as number ?? 250,
          },
          data: {
            title: (params.title as string) ?? "Group",
            note: (params.note as string) ?? "",
            color: (params.color as string) ?? "gray",
            onUpdateTitle: (title: string) => onUpdateNodeConfig(node.id, { title }),
            onUpdateNote: (note: string) => onUpdateNodeConfig(node.id, { note }),
          },
          selected: selectedNodeId === node.id,
        };
      }

      // Regular block node
      const summary = blocks.find((block) => block.type_name === node.block_type);
      const schema = schemas[node.block_type];
      return {
        id: node.id,
        type: "block",
        position,
        data: {
          label: resolveLabel(node, summary, schema),
          blockType: node.block_type,
          category: summary?.category ?? schema?.category ?? "custom",
          summary,
          schema,
          config: params,
          inputPorts: schema?.input_ports ?? summary?.input_ports ?? [],
          outputPorts: schema?.output_ports ?? summary?.output_ports ?? [],
          status: blockStates[node.id] ?? "idle",
          errorMessage: blockErrors[node.id],
          selected: selectedNodeId === node.id,
          onRun: makeOnRun(node.id),
          onRestart: makeOnRestart(node.id),
          onDelete: makeOnDelete(node.id),
          onUpdateConfig: makeOnUpdateConfig(node.id),
          onErrorClick: makeOnErrorClick(node.id),
        },
        selected: selectedNodeId === node.id,
      };
    });
  }, [blocks, blockStates, blockErrors, dragPositions, makeOnDelete, makeOnErrorClick, makeOnRestart, makeOnRun, makeOnUpdateConfig, nodes, onUpdateNodeConfig, resolveLabel, schemas, selectedNodeId]);

  const flowEdges = useMemo<Array<Edge>>(() => {
    return edges.map((edge) => {
      const source = parsePortRef(edge.source);
      const target = parsePortRef(edge.target);
      const sourceNode = nodes.find((node) => node.id === source.nodeId);
      const sourceSchema = sourceNode ? schemas[sourceNode.block_type] : undefined;
      const sourcePort = sourceSchema?.output_ports.find((port) => port.name === source.portName);
      return {
        id: `${edge.source}->${edge.target}`,
        source: source.nodeId,
        sourceHandle: source.portName,
        target: target.nodeId,
        targetHandle: target.portName,
        type: "typed",
        data: {
          color: resolveTypeColor(sourcePort?.accepted_types ?? [], sourceSchema?.type_hierarchy),
          dashed: sourcePort?.is_collection ?? false,
        },
      };
    });
  }, [edges, nodes, schemas]);

  return (
    <div
      className="h-full"
      onDragOver={(event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
      }}
      onDrop={(event) => {
        event.preventDefault();
        const payload = event.dataTransfer.getData("application/scieasy-block");
        if (!payload) {
          return;
        }
        const parsed = JSON.parse(payload) as BlockSummary & { _default_direction?: string };
        const position = reactFlow.screenToFlowPosition({ x: event.clientX, y: event.clientY });
        onAddNode(parsed, position, parsed._default_direction ? { direction: parsed._default_direction } : undefined);
      }}
    >
      <ReactFlow
        edges={flowEdges}
        edgeTypes={edgeTypes}
        fitView
        nodeTypes={nodeTypes}
        nodes={flowNodes}
        onNodesChange={(changes: NodeChange<Node<BlockNodeData>>[]) => {
          // Apply position changes locally during drag so nodes follow the
          // cursor in real time. Other change types (select, remove, etc.)
          // are handled by dedicated callbacks below.
          const positionUpdates: Record<string, { x: number; y: number }> = {};
          for (const change of changes) {
            if (change.type === "position" && change.position) {
              positionUpdates[change.id] = change.position;
            }
          }
          if (Object.keys(positionUpdates).length > 0) {
            setDragPositions((prev) => ({ ...prev, ...positionUpdates }));
          }
        }}
        onConnect={async (connection: Connection) => {
          if (!connection.source || !connection.target || !connection.sourceHandle || !connection.targetHandle) {
            return;
          }
          await onConnect({
            source: `${connection.source}:${connection.sourceHandle}`,
            target: `${connection.target}:${connection.targetHandle}`,
          });
        }}
        onEdgeClick={(_, edge) => {
          const match = edges.find((candidate) => `${candidate.source}->${candidate.target}` === edge.id);
          if (match) {
            onDeleteEdge(match);
          }
        }}
        onEdgesDelete={(deleted) => {
          deleted.forEach((edge) => {
            const match = edges.find((candidate) => `${candidate.source}->${candidate.target}` === edge.id);
            if (match) {
              onDeleteEdge(match);
            }
          });
        }}
        onNodeClick={(_, node) => onSelectNode(node.id)}
        onNodeDragStop={(_, node) => {
          // Persist the final position to the store and clear the local
          // drag override so subsequent renders use the store value.
          onUpdateNodePosition(node.id, node.position);
          setDragPositions((prev) => {
            const next = { ...prev };
            delete next[node.id];
            return next;
          });
        }}
        onNodesDelete={(deleted) => deleted.forEach((node) => onDeleteNode(node.id))}
        onPaneClick={() => onSelectNode(null)}
        deleteKeyCode={["Backspace", "Delete"]}
        proOptions={{ hideAttribution: true }}
      >
        {minimapVisible && (
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => {
              const data = node.data as BlockNodeData | undefined;
              return resolveTypeColor(data?.outputPorts?.[0]?.accepted_types ?? []);
            }}
          />
        )}
        <Controls />
        <Background color="#d8d2c4" gap={20} size={1.2} />
      </ReactFlow>
    </div>
  );
}
