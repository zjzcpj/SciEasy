"""Tests for the EventBus."""

from __future__ import annotations

from scieasy.engine.events import EngineEvent, EventBus


class TestEventBus:
    """EventBus — in-process pub/sub."""

    def test_subscribe_and_emit(self) -> None:
        bus = EventBus()
        received: list[EngineEvent] = []
        bus.subscribe("test", received.append)
        bus.emit(EngineEvent(event_type="test", data={"x": 1}))
        assert len(received) == 1
        assert received[0].data == {"x": 1}

    def test_unsubscribe(self) -> None:
        bus = EventBus()
        received: list[EngineEvent] = []
        bus.subscribe("test", received.append)
        bus.unsubscribe("test", received.append)
        bus.emit(EngineEvent(event_type="test"))
        assert len(received) == 0

    def test_wildcard_subscriber(self) -> None:
        bus = EventBus()
        received: list[EngineEvent] = []
        bus.subscribe("*", received.append)
        bus.emit(EngineEvent(event_type="foo"))
        bus.emit(EngineEvent(event_type="bar"))
        assert len(received) == 2

    def test_multiple_subscribers(self) -> None:
        bus = EventBus()
        a: list[EngineEvent] = []
        b: list[EngineEvent] = []
        bus.subscribe("test", a.append)
        bus.subscribe("test", b.append)
        bus.emit(EngineEvent(event_type="test"))
        assert len(a) == 1
        assert len(b) == 1

    def test_event_type_isolation(self) -> None:
        bus = EventBus()
        received: list[EngineEvent] = []
        bus.subscribe("foo", received.append)
        bus.emit(EngineEvent(event_type="bar"))
        assert len(received) == 0

    def test_history(self) -> None:
        bus = EventBus()
        bus.emit(EngineEvent(event_type="a"))
        bus.emit(EngineEvent(event_type="b"))
        assert len(bus.history) == 2
        assert bus.history[0].event_type == "a"

    def test_clear_history(self) -> None:
        bus = EventBus()
        bus.emit(EngineEvent(event_type="a"))
        bus.clear_history()
        assert len(bus.history) == 0

    def test_unsubscribe_nonexistent_is_noop(self) -> None:
        bus = EventBus()
        bus.unsubscribe("test", lambda e: None)  # Should not raise

    def test_block_id_in_event(self) -> None:
        bus = EventBus()
        received: list[EngineEvent] = []
        bus.subscribe("state", received.append)
        bus.emit(EngineEvent(event_type="state", block_id="node_1"))
        assert received[0].block_id == "node_1"
