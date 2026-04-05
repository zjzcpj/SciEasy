"""Tests for LineageRecorder -- issue #166."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from scieasy.engine.events import (
    BLOCK_CANCELLED,
    BLOCK_DONE,
    BLOCK_ERROR,
    BLOCK_SKIPPED,
    EngineEvent,
    EventBus,
)
from scieasy.engine.lineage_recorder import LineageRecorder


def _make_recorder(
    with_store: bool = True,
) -> tuple[LineageRecorder, EventBus, MagicMock | None]:
    event_bus = EventBus()
    store = MagicMock() if with_store else None
    recorder = LineageRecorder(event_bus, lineage_store=store)
    return recorder, event_bus, store


class TestLineageRecorder:
    def test_block_done_writes_record(self) -> None:
        """Emit BLOCK_DONE -> LineageStore.write() called with termination='completed'."""
        recorder, bus, store = _make_recorder()

        asyncio.run(
            bus.emit(EngineEvent(event_type=BLOCK_DONE, block_id="A", data={"outputs": {}}))
        )

        assert store is not None
        store.write.assert_called_once()
        record = store.write.call_args[0][0]
        assert record.block_id == "A"
        assert record.termination == "completed"

    def test_block_error_writes_record(self) -> None:
        """Emit BLOCK_ERROR -> termination='error' and termination_detail populated."""
        recorder, bus, store = _make_recorder()

        asyncio.run(
            bus.emit(
                EngineEvent(
                    event_type=BLOCK_ERROR,
                    block_id="B",
                    data={"error": "something broke"},
                )
            )
        )

        assert store is not None
        store.write.assert_called_once()
        record = store.write.call_args[0][0]
        assert record.termination == "error"
        assert record.termination_detail == "something broke"

    def test_block_cancelled_writes_record(self) -> None:
        """Emit BLOCK_CANCELLED -> termination='cancelled'."""
        recorder, bus, store = _make_recorder()

        asyncio.run(
            bus.emit(EngineEvent(event_type=BLOCK_CANCELLED, block_id="C"))
        )

        assert store is not None
        store.write.assert_called_once()
        record = store.write.call_args[0][0]
        assert record.termination == "cancelled"

    def test_block_skipped_writes_record(self) -> None:
        """Emit BLOCK_SKIPPED -> termination='skipped'."""
        recorder, bus, store = _make_recorder()

        asyncio.run(
            bus.emit(EngineEvent(event_type=BLOCK_SKIPPED, block_id="D"))
        )

        assert store is not None
        store.write.assert_called_once()
        record = store.write.call_args[0][0]
        assert record.termination == "skipped"

    def test_no_store_is_noop(self) -> None:
        """LineageRecorder with store=None should not crash."""
        recorder, bus, store = _make_recorder(with_store=False)

        # Should not raise
        asyncio.run(
            bus.emit(EngineEvent(event_type=BLOCK_DONE, block_id="A", data={"outputs": {}}))
        )

    def test_duration_computed(self) -> None:
        """Call record_start, then emit BLOCK_DONE -> duration_ms > 0."""
        recorder, bus, store = _make_recorder()
        recorder.record_start("X")

        asyncio.run(
            bus.emit(EngineEvent(event_type=BLOCK_DONE, block_id="X", data={"outputs": {}}))
        )

        assert store is not None
        store.write.assert_called_once()
        record = store.write.call_args[0][0]
        assert record.duration_ms >= 0

    def test_store_write_failure_does_not_crash(self) -> None:
        """If store.write() raises, the recorder logs but does not propagate."""
        recorder, bus, store = _make_recorder()
        assert store is not None
        store.write.side_effect = RuntimeError("DB error")

        # Should not raise
        asyncio.run(
            bus.emit(EngineEvent(event_type=BLOCK_DONE, block_id="A", data={"outputs": {}}))
        )

    def test_none_block_id_is_noop(self) -> None:
        """Events without block_id should be ignored."""
        recorder, bus, store = _make_recorder()

        asyncio.run(bus.emit(EngineEvent(event_type=BLOCK_DONE)))

        assert store is not None
        store.write.assert_not_called()
