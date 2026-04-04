"""BlockState, ExecutionMode, BatchMode, InputDelivery, BatchErrorStrategy enums."""

from __future__ import annotations

from enum import Enum


class BlockState(Enum):
    """Lifecycle state of a block instance."""

    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"  # ADR-018: user explicitly terminated this block
    SKIPPED = "skipped"  # ADR-018: block cannot execute — required upstream inputs missing


class ExecutionMode(Enum):
    """How the block is executed by the runtime."""

    AUTO = "auto"
    INTERACTIVE = "interactive"
    EXTERNAL = "external"


# ADR-020: BatchMode enum REMOVED — engine no longer iterates collections.
# Collection iteration is block-internal (see process_item(), map_items(), parallel_map()).

class InputDelivery(Enum):
    """How input data is delivered to the block."""

    MEMORY = "memory"
    PROXY = "proxy"
    CHUNKED = "chunked"

# ADR-020: BatchErrorStrategy enum REMOVED — block authors handle item-level
# errors internally. Engine only sees DONE, ERROR, CANCELLED, SKIPPED.
