"""Engine event bus -- block state changes, progress updates."""

from __future__ import annotations

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
    """Publish/subscribe dispatcher for :class:`EngineEvent` instances."""

    def emit(self, event: EngineEvent) -> None:
        """Broadcast *event* to all subscribers of its ``event_type``."""
        raise NotImplementedError

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[EngineEvent], None],
    ) -> None:
        """Register *callback* to receive events of the given type.

        Parameters
        ----------
        event_type:
            The event type string to listen for.
        callback:
            Function invoked with each matching :class:`EngineEvent`.
        """
        raise NotImplementedError

    def unsubscribe(
        self,
        event_type: str,
        callback: Callable[[EngineEvent], None],
    ) -> None:
        """Remove a previously registered *callback* for *event_type*.

        Parameters
        ----------
        event_type:
            The event type string the callback was registered under.
        callback:
            The exact callable that was passed to :meth:`subscribe`.
        """
        raise NotImplementedError
