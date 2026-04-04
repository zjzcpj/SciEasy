"""WorkflowCheckpoint -- serialise and deserialise workflow state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class WorkflowCheckpoint:
    """Snapshot of a workflow execution that can be persisted and restored.

    Captures block states, intermediate data references, and configuration
    so that execution can be resumed from this point.
    """

    workflow_id: str
    timestamp: datetime
    block_states: dict[str, str]
    intermediate_refs: dict[str, Any] = field(default_factory=dict)
    pending_block: str | None = None
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    skip_reasons: dict[str, str] = field(default_factory=dict)  # ADR-018: block_id → skip reason


# TODO(ADR-018): Checkpoint must record all 8 block states including CANCELLED and SKIPPED.
# TODO(ADR-018): CheckpointManager class needed — subscribes to terminal events
# via EventBus, saves checkpoint after each block state change.


def save_checkpoint(checkpoint: WorkflowCheckpoint, path: str | Path) -> None:
    """Persist *checkpoint* to the file at *path*.

    Parameters
    ----------
    checkpoint:
        The checkpoint data to write.
    path:
        Destination file path (will be created or overwritten).
    """
    raise NotImplementedError


def load_checkpoint(path: str | Path) -> WorkflowCheckpoint:
    """Restore a :class:`WorkflowCheckpoint` from a previously saved file.

    Parameters
    ----------
    path:
        File path written by :func:`save_checkpoint`.

    Returns
    -------
    WorkflowCheckpoint
        The deserialised checkpoint.
    """
    raise NotImplementedError
