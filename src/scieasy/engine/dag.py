"""DAG construction from workflow definition (topological sort, dependency resolution)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scieasy.workflow.definition import WorkflowDefinition


@dataclass
class DAGNode:
    """Internal representation of a single node in the execution DAG."""

    node_id: str
    block_type: str
    config: dict[str, Any] = field(default_factory=dict)
    execution_mode: str | None = None
    batch_mode: str | None = None
    dependencies: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)
    input_edges: dict[str, tuple[str, str]] = field(default_factory=dict)
    output_edges: dict[str, list[tuple[str, str]]] = field(default_factory=dict)


def build_dag(workflow: WorkflowDefinition) -> dict[str, DAGNode]:
    """Construct an internal DAG representation from a WorkflowDefinition.

    Parameters
    ----------
    workflow:
        A ``WorkflowDefinition`` instance describing nodes and edges.

    Returns
    -------
    dict[str, DAGNode]
        Mapping of node ID to :class:`DAGNode`.
    """
    nodes: dict[str, DAGNode] = {}
    for node_def in workflow.nodes:
        nodes[node_def.id] = DAGNode(
            node_id=node_def.id,
            block_type=node_def.block_type,
            config=dict(node_def.config),
            execution_mode=node_def.execution_mode,
            batch_mode=node_def.batch_mode,
        )

    for edge in workflow.edges:
        src_node_id, src_port = _parse_port_ref(edge.source)
        tgt_node_id, tgt_port = _parse_port_ref(edge.target)

        if src_node_id not in nodes:
            raise ValueError(f"Edge references unknown source node '{src_node_id}'")
        if tgt_node_id not in nodes:
            raise ValueError(f"Edge references unknown target node '{tgt_node_id}'")

        # Record dependency: target depends on source.
        nodes[tgt_node_id].dependencies.add(src_node_id)
        nodes[src_node_id].dependents.add(tgt_node_id)

        # Record port-level edges.
        nodes[tgt_node_id].input_edges[tgt_port] = (src_node_id, src_port)
        nodes[src_node_id].output_edges.setdefault(src_port, []).append(
            (tgt_node_id, tgt_port)
        )

    return nodes


def topological_sort(graph: dict[str, DAGNode]) -> list[str]:
    """Return node IDs in topological order using Kahn's algorithm.

    Parameters
    ----------
    graph:
        DAG produced by :func:`build_dag`.

    Returns
    -------
    list[str]
        Node IDs ordered so that every dependency appears before its dependents.

    Raises
    ------
    ValueError
        If the graph contains a cycle.
    """
    in_degree: dict[str, int] = {nid: len(node.dependencies) for nid, node in graph.items()}
    queue: list[str] = [nid for nid, deg in in_degree.items() if deg == 0]
    order: list[str] = []

    while queue:
        # Sort for deterministic ordering among nodes at the same level.
        queue.sort()
        nid = queue.pop(0)
        order.append(nid)
        for dep_id in sorted(graph[nid].dependents):
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                queue.append(dep_id)

    if len(order) != len(graph):
        remaining = set(graph.keys()) - set(order)
        raise ValueError(f"Cycle detected in workflow graph involving nodes: {remaining}")

    return order


def _parse_port_ref(ref: str) -> tuple[str, str]:
    """Parse a port reference of the form ``'node_id:port_name'``."""
    parts = ref.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid port reference '{ref}': expected 'node_id:port_name'")
    return parts[0], parts[1]
