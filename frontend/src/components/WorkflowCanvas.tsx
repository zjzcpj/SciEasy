import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Connection,
  type Edge,
  type Node,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useMemo } from "react";

import { resolveTypeColor } from "../config/typeColorMap";
import type { BlockSchemaResponse, BlockSummary, WorkflowEdge, WorkflowNode } from "../types/api";
import type { BlockNodeData } from "../types/ui";
import { BlockNode } from "./nodes/BlockNode";
import { TypedEdge } from "./TypedEdge";

const nodeTypes = { block: BlockNode };
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

  const makeOnRun = useCallback((nodeId: string) => () => onRunBlock(nodeId), [onRunBlock]);
  const makeOnRestart = useCallback((nodeId: string) => () => onRestartBlock(nodeId), [onRestartBlock]);
  const makeOnDelete = useCallback((nodeId: string) => () => onDeleteNode(nodeId), [onDeleteNode]);
  const makeOnErrorClick = useCallback((nodeId: string) => () => onErrorClick(nodeId), [onErrorClick]);
  const makeOnUpdateConfig = useCallback(
    (nodeId: string) => (patch: Record<string, unknown>) => onUpdateNodeConfig(nodeId, patch),
    [onUpdateNodeConfig],
  );

  const flowNodes = useMemo<Array<Node<BlockNodeData>>>(() => {
    return nodes.map((node, index) => {
      const summary = blocks.find((block) => block.type_name === node.block_type);
      const schema = schemas[node.block_type];
      const params = ((node.config.params as Record<string, unknown> | undefined) ?? {}) as Record<string, unknown>;
      return {
        id: node.id,
        type: "block",
        dragHandle: ".drag-handle",
        position: node.layout ?? { x: 120 + index * 80, y: 120 + index * 40 },
        data: {
          label: summary?.name ?? schema?.name ?? node.block_type,
          blockType: node.block_type,
          category: summary?.category ?? schema?.category ?? "custom",
          summary,
          schema,
          config: params,
          inputPorts: schema?.input_ports ?? summary?.input_ports ?? [],
          outputPorts: schema?.output_ports ?? summary?.output_ports ?? [],
          status: blockStates[node.id] ?? "idle",
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
  }, [blocks, blockStates, makeOnDelete, makeOnErrorClick, makeOnRestart, makeOnRun, makeOnUpdateConfig, nodes, schemas, selectedNodeId]);

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
        onNodeDragStop={(_, node) => onUpdateNodePosition(node.id, node.position)}
        onNodesDelete={(deleted) => deleted.forEach((node) => onDeleteNode(node.id))}
        onPaneClick={() => onSelectNode(null)}
        deleteKeyCode={["Backspace", "Delete"]}
        proOptions={{ hideAttribution: true }}
      >
        {minimapVisible && (
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => resolveTypeColor((node.data as BlockNodeData).outputPorts[0]?.accepted_types ?? [])}
          />
        )}
        <Controls />
        <Background color="#d8d2c4" gap={20} size={1.2} />
      </ReactFlow>
    </div>
  );
}
