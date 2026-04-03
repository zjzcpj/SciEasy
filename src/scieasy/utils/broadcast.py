"""broadcast_apply() -- named-axis-aware broadcast of arrays."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class BroadcastError(Exception):
    """Raised when axis alignment fails during broadcast."""


def broadcast_apply(
    source: Any,
    target: Any,
    func: Callable[..., Any],
    over_axes: list[str],
) -> list[Any]:
    """Apply a lower-dim array to a higher-dim array along named axes.

    Iterates over *over_axes* in the target, extracting slices that share
    the remaining axes with source, and calls *func* on each pair.

    Raises BroadcastError if source axes are not a subset of
    target axes minus over_axes.
    """
    raise NotImplementedError
