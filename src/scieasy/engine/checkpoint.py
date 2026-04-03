"""WorkflowCheckpoint -- serialise and deserialise workflow state."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
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


def save_checkpoint(checkpoint: WorkflowCheckpoint, path: str | Path) -> None:
    """Persist *checkpoint* to the file at *path*.

    Serialises the checkpoint as JSON.  The ``timestamp`` field is
    converted to an ISO-8601 string for portability.
    """
    data = asdict(checkpoint)
    data["timestamp"] = checkpoint.timestamp.isoformat()
    Path(path).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


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
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    raw["timestamp"] = datetime.fromisoformat(raw["timestamp"])
    return WorkflowCheckpoint(**raw)
