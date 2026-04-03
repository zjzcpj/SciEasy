"""Observe intermediate results, suggest or apply parameter changes."""

from __future__ import annotations

from typing import Any


def optimize_params(
    block_id: str,
    intermediate_results: dict[str, Any],
    search_space: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe intermediate outputs and suggest parameter adjustments.

    Parameters
    ----------
    block_id:
        Identifier of the block whose parameters should be tuned.
    intermediate_results:
        Key-value mapping of metric names to their current values.
    search_space:
        Optional description of the parameter search space.  When
        *None* the optimiser infers the space from the block schema.

    Returns
    -------
    dict[str, Any]
        Suggested parameter values keyed by parameter name.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
