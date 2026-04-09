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


# ---------------------------------------------------------------------------
# intermediate_refs serialisation (Collection-aware)
# ---------------------------------------------------------------------------


def serialize_intermediate_refs(block_outputs: dict[str, Any]) -> dict[str, Any]:
    """Serialize block outputs for checkpoint storage.

    Preserves Collection structure as ``{"_collection": True, "items": [...],
    "item_type": "ClassName"}`` instead of flattening via ``str()``.
    StorageReference-backed objects are serialized as ref dicts.
    """
    result: dict[str, Any] = {}
    for block_id, outputs in block_outputs.items():
        if isinstance(outputs, dict):
            serialized: dict[str, Any] = {}
            for port_name, value in outputs.items():
                serialized[port_name] = _serialize_value(value)
            result[block_id] = serialized
        else:
            result[block_id] = _serialize_value(outputs)
    return result


def _serialize_value(value: Any) -> Any:
    """Serialize a single output value for checkpoint storage."""
    from scieasy.core.types.base import DataObject
    from scieasy.core.types.collection import Collection

    if isinstance(value, Collection):
        items = []
        for item in value:
            if hasattr(item, "storage_ref") and item.storage_ref is not None:
                ref = item.storage_ref
                items.append(
                    {
                        "backend": ref.backend,
                        "path": ref.path,
                        "format": ref.format,
                        "metadata": ref.metadata,
                    }
                )
            else:
                items.append({"_value": str(item), "_type": type(item).__name__})
        return {
            "_collection": True,
            "items": items,
            "item_type": value.item_type.__name__,
        }

    if isinstance(value, DataObject) and hasattr(value, "storage_ref") and value.storage_ref is not None:
        ref = value.storage_ref
        return {
            "backend": ref.backend,
            "path": ref.path,
            "format": ref.format,
            "metadata": ref.metadata,
        }

    if isinstance(value, (str, int, float, bool, type(None), list, dict)):
        return value

    return str(value)


def deserialize_intermediate_refs(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize checkpoint intermediate_refs back to live objects.

    .. deprecated::
        This function is **not called** in the production execute-from path
        and must not be introduced there.  The execute-from path in
        :meth:`~scieasy.engine.scheduler.DAGScheduler.execute_from` assigns
        ``checkpoint.intermediate_refs[node_id]`` directly to
        ``_block_outputs[node_id]`` as a wire-format dict.  The downstream
        worker subprocess then calls ``_reconstruct_one()`` (ADR-027 Addendum
        1 §1) which reads ``metadata.type_chain`` from the wire-format dict
        and reconstructs the typed object inside the sandboxed subprocess.

        Calling this function would produce :class:`~scieasy.core.proxy.ViewProxy`
        objects that are **not JSON-serialisable** and would break
        ``spawn_block_process()`` when the scheduler tries to ship inputs to
        the worker via stdin/stdout.

        The function is preserved (not deleted) for:
        - historical reference and future testing utilities
        - potential use in offline / introspection tooling that does not
          route through the subprocess execution path

        Do **not** call this from within the scheduler, runner, or any path
        that feeds inputs to a worker subprocess.

    Reconstructs :class:`ViewProxy` instances from serialized
    StorageReference dicts, and preserves Collection structure with
    ViewProxy items so that resumed workflows can feed data to blocks.
    """
    result: dict[str, Any] = {}
    for block_id, outputs in data.items():
        if isinstance(outputs, dict):
            result[block_id] = {port_name: _deserialize_value(value) for port_name, value in outputs.items()}
        else:
            result[block_id] = _deserialize_value(outputs)
    return result


def _deserialize_value(value: Any) -> Any:
    """Deserialize a single value from checkpoint storage.

    .. deprecated::
        Only called by :func:`deserialize_intermediate_refs`, which is itself
        deprecated.  See the deprecation notice on that function for the full
        rationale.  Do not call this directly from scheduler or runner code.
    """
    if not isinstance(value, dict):
        return value

    # --- Collection structure ---
    if value.get("_collection") is True:
        if "items" not in value or "item_type" not in value:
            logger.warning(
                "Malformed _collection dict (missing 'items' or 'item_type'), returning raw data: %s",
                list(value.keys()),
            )
            return value

        from scieasy.core.proxy import ViewProxy
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.base import TypeSignature

        item_type_name: str = value["item_type"]
        proxies: list[ViewProxy] = []
        for item_data in value["items"]:
            if not isinstance(item_data, dict):
                continue
            if "_value" in item_data:
                logger.warning(
                    "Cannot fully reconstruct non-persisted item (type=%s, value=%s) — skipping",
                    item_data.get("_type", "unknown"),
                    item_data["_value"],
                )
                continue
            if "backend" in item_data and "path" in item_data:
                ref = StorageReference(
                    backend=item_data["backend"],
                    path=item_data["path"],
                    format=item_data.get("format"),
                    metadata=item_data.get("metadata"),
                )
                # #404: read type_chain from item metadata when available so
                # ViewProxy carries the correct plugin type identity rather
                # than falling back to just [item_type_name].
                item_meta = item_data.get("metadata") or {}
                item_chain = item_meta.get("type_chain") if isinstance(item_meta, dict) else None
                if not (isinstance(item_chain, list) and item_chain):
                    item_chain = [item_type_name]
                sig = TypeSignature(type_chain=item_chain)
                proxies.append(ViewProxy(storage_ref=ref, dtype_info=sig))

        return {"_collection": True, "items": proxies, "item_type": item_type_name}

    # --- Single StorageReference dict ---
    if "backend" in value and "path" in value:
        from scieasy.core.proxy import ViewProxy
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.base import TypeSignature

        ref = StorageReference(
            backend=value["backend"],
            path=value["path"],
            format=value.get("format"),
            metadata=value.get("metadata"),
        )
        # #404: read type_chain from ref metadata when available so ViewProxy
        # carries the correct plugin type identity rather than hardcoding
        # ["DataObject"].
        ref_meta = value.get("metadata") or {}
        ref_chain = ref_meta.get("type_chain") if isinstance(ref_meta, dict) else None
        if not (isinstance(ref_chain, list) and ref_chain):
            ref_chain = ["DataObject"]
        sig = TypeSignature(type_chain=ref_chain)
        return ViewProxy(storage_ref=ref, dtype_info=sig)

    return value


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

        ADR-018: Auto-save checkpoint when latest state is available.
        If a checkpoint has been saved previously (via save()), updates it
        with the new block state from the event.
        """
        if self._latest is not None:
            block_id = getattr(event, "block_id", None)
            event_type = getattr(event, "event_type", "")
            if block_id and event_type:
                self._latest.block_states[block_id] = event_type.replace("block_", "")
                self.save(self._latest)

    # -- properties ---------------------------------------------------------

    @property
    def latest(self) -> WorkflowCheckpoint | None:
        """The most recently saved checkpoint (in-memory cache)."""
        return self._latest
