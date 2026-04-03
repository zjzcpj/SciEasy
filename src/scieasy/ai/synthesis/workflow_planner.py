"""Given data description and analysis goal, propose a complete workflow DAG."""

from __future__ import annotations

from typing import Any


def plan_workflow(data_description: str, goal: str) -> dict[str, Any]:
    """Propose a complete workflow DAG for the given data and goal.

    Parameters
    ----------
    data_description:
        Free-text description of the input dataset(s), including format,
        modality, and approximate size.
    goal:
        Free-text description of the desired analysis outcome.

    Returns
    -------
    dict[str, Any]
        A serialisable workflow graph containing at least ``"nodes"``
        and ``"edges"`` keys that conform to the workflow schema.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
