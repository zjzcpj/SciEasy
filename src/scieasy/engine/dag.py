"""DAG construction from workflow definition (topological sort, dependency resolution)."""

from __future__ import annotations

from typing import Any


# TODO(ADR-018): DAG must support querying downstream dependents for skip propagation.
# DAGScheduler._propagate_skip() walks downstream from a failed/cancelled block
# and marks blocks SKIPPED if all required inputs are unsatisfiable.
def build_dag(workflow: Any) -> dict[str, Any]:
    """Construct an internal DAG representation from a WorkflowDefinition.

    Parameters
    ----------
    workflow:
        A ``WorkflowDefinition`` instance describing nodes and edges.

    Returns
    -------
    dict[str, Any]
        An adjacency-list representation of the workflow graph keyed by node ID.
    """
    raise NotImplementedError


def topological_sort(graph: dict[str, Any]) -> list[str]:
    """Return node IDs in topological order.

    Parameters
    ----------
    graph:
        Adjacency-list graph produced by :func:`build_dag`.

    Returns
    -------
    list[str]
        Node IDs ordered so that every dependency appears before its dependents.

    Raises
    ------
    NotImplementedError
        Skeleton-only; not yet implemented.
    """
    raise NotImplementedError
