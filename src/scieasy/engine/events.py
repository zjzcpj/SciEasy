"""Engine event bus -- block state changes, progress updates."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EngineEvent:
    """A single event emitted by the engine during workflow execution.

    Events carry a type tag, an optional block identifier, and an
    arbitrary data payload.
    """

    event_type: str
    block_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus:
    """Publish/subscribe dispatcher for :class:`EngineEvent` instances.

    Supports subscribing to specific event types or to all events via
    the wildcard ``"*"`` type.  Callbacks are invoked synchronously in
    registration order.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[EngineEvent], None]]] = defaultdict(list)
        self._history: list[EngineEvent] = []

    def emit(self, event: EngineEvent) -> None:
        """Broadcast *event* to all subscribers of its ``event_type``.

        Also delivers to wildcard (``"*"``) subscribers.
        """
        self._history.append(event)

        for callback in self._subscribers.get(event.event_type, []):
            callback(event)

        # Deliver to wildcard subscribers.
        if event.event_type != "*":
            for callback in self._subscribers.get("*", []):
                callback(event)

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[EngineEvent], None],
    ) -> None:
        """Register *callback* to receive events of the given type.

        Use ``"*"`` to receive all events.
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(
        self,
        event_type: str,
        callback: Callable[[EngineEvent], None],
    ) -> None:
        """Remove a previously registered *callback* for *event_type*."""
        try:
            self._subscribers[event_type].remove(callback)
        except ValueError:
            pass

    @property
    def history(self) -> list[EngineEvent]:
        """Return the full ordered list of emitted events."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear the event history."""
        self._history.clear()
