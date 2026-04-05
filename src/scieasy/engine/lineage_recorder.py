"""LineageRecorder -- subscribes to block terminal events and persists LineageRecord.

Architecture doc: 'Every block execution produces a lineage record.'
EventBus subscription matrix: LineageRecorder subscribes to
BLOCK_DONE, BLOCK_ERROR, BLOCK_CANCELLED, BLOCK_SKIPPED.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from scieasy.core.lineage.record import LineageRecord
from scieasy.engine.events import (
    BLOCK_CANCELLED,
    BLOCK_DONE,
    BLOCK_ERROR,
    BLOCK_SKIPPED,
    EngineEvent,
)

if TYPE_CHECKING:
    from scieasy.core.lineage.store import LineageStore
    from scieasy.engine.events import EventBus

logger = logging.getLogger(__name__)


class LineageRecorder:
    """Listens for terminal block events and persists LineageRecords.

    Parameters
    ----------
    event_bus:
        The workflow EventBus to subscribe on.
    lineage_store:
        The LineageStore to persist records into. If None, recording is
        disabled (useful for tests that don't need lineage).
    """

    def __init__(self, event_bus: EventBus, lineage_store: LineageStore | None = None) -> None:
        self._event_bus = event_bus
        self._store = lineage_store
        self._start_times: dict[str, datetime] = {}

        event_bus.subscribe(BLOCK_DONE, self._on_terminal)
        event_bus.subscribe(BLOCK_ERROR, self._on_terminal)
        event_bus.subscribe(BLOCK_CANCELLED, self._on_terminal)
        event_bus.subscribe(BLOCK_SKIPPED, self._on_terminal)

    def record_start(self, block_id: str) -> None:
        """Record when a block starts executing (called by scheduler._dispatch)."""
        self._start_times[block_id] = datetime.now()

    async def _on_terminal(self, event: EngineEvent) -> None:
        """Handle any terminal block event."""
        if self._store is None or event.block_id is None:
            return

        block_id = event.block_id
        data: dict[str, Any] = event.data or {}

        termination_map = {
            BLOCK_DONE: "completed",
            BLOCK_ERROR: "error",
            BLOCK_CANCELLED: "cancelled",
            BLOCK_SKIPPED: "skipped",
        }
        termination = termination_map.get(event.event_type, "completed")

        start = self._start_times.pop(block_id, None)
        duration_ms = int((datetime.now() - start).total_seconds() * 1000) if start else 0

        record = LineageRecord(
            block_id=block_id,
            block_config=data.get("config", {}),
            block_version=data.get("block_version", "unknown"),
            input_hashes=data.get("input_hashes", {}),
            output_hashes=data.get("output_hashes", {}),
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            environment=data.get("environment"),
            termination=termination,
            partial_output_refs=data.get("partial_output_refs", []),
            termination_detail=data.get("error", ""),
        )

        try:
            self._store.write(record)
        except Exception:
            logger.warning("Failed to write lineage record for block %s", block_id, exc_info=True)
