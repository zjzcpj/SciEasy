"""WorkflowCheckpoint -- serialise and deserialise workflow state.

ADR-018: Checkpoint must record all 8 block states including CANCELLED
and SKIPPED.  The ``skip_reasons`` field captures why a block was
cancelled or skipped so that resumed workflows can honour those
decisions.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def save_checkpoint(checkpoint: WorkflowCheckpoint, path: str | Path) -> None:
    """Persist *checkpoint* to the file at *path*.

    The checkpoint is serialised as JSON.  The ``timestamp`` field is
    written in ISO-8601 format.  Any non-JSON-native values inside
    ``intermediate_refs`` or ``config_snapshot`` are coerced to strings
    via the ``default=str`` fallback.

    Parameters
    ----------
    checkpoint:
        The checkpoint data to write.
    path:
        Destination file path (will be created or overwritten).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(checkpoint)
    data["timestamp"] = checkpoint.timestamp.isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


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
    path = Path(path)
    with open(path) as f:
        data = json.load(f)
    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
    return WorkflowCheckpoint(**data)


# ---------------------------------------------------------------------------
# CheckpointManager
# ---------------------------------------------------------------------------


class CheckpointManager:
    """Manages checkpoint files for workflow executions.

    Checkpoints are stored as JSON files in a configurable directory,
    named ``checkpoint_<workflow_id>.json``.  When an :class:`EventBus`
    is provided the manager automatically subscribes to terminal block
    events (``BLOCK_DONE``, ``BLOCK_ERROR``, ``BLOCK_CANCELLED``,
    ``BLOCK_SKIPPED``) so that a future scheduler integration can
    trigger auto-saves on state changes.
    """

    def __init__(self, checkpoint_dir: str | Path, event_bus: Any = None) -> None:
        self._checkpoint_dir = Path(checkpoint_dir)
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._latest: WorkflowCheckpoint | None = None
        if event_bus is not None:
            from scieasy.engine.events import (
                BLOCK_CANCELLED,
                BLOCK_DONE,
                BLOCK_ERROR,
                BLOCK_SKIPPED,
            )

            event_bus.subscribe(BLOCK_DONE, self._on_state_change)
            event_bus.subscribe(BLOCK_ERROR, self._on_state_change)
            event_bus.subscribe(BLOCK_CANCELLED, self._on_state_change)
            event_bus.subscribe(BLOCK_SKIPPED, self._on_state_change)

    # -- public API ---------------------------------------------------------

    def save(self, checkpoint: WorkflowCheckpoint) -> Path:
        """Write *checkpoint* to disk and update :pyattr:`latest`.

        Returns the path of the saved file.
        """
        path = self._checkpoint_dir / f"checkpoint_{checkpoint.workflow_id}.json"
        save_checkpoint(checkpoint, path)
        self._latest = checkpoint
        return path

    def load(self, workflow_id: str) -> WorkflowCheckpoint | None:
        """Load the checkpoint for *workflow_id*, or ``None`` if absent."""
        path = self._checkpoint_dir / f"checkpoint_{workflow_id}.json"
        if path.exists():
            return load_checkpoint(path)
        return None

    # -- EventBus callback --------------------------------------------------

    def _on_state_change(self, event: Any) -> None:
        """Hook invoked on terminal block events.

        Currently a no-op stub — future integration with the DAGScheduler
        will use this to trigger automatic checkpoint saves after each
        block state transition.
        """
        # TODO(ADR-018): Auto-save checkpoint when scheduler provides
        # workflow state snapshot on terminal block events.

    # -- properties ---------------------------------------------------------

    @property
    def latest(self) -> WorkflowCheckpoint | None:
        """The most recently saved checkpoint (in-memory cache)."""
        return self._latest
