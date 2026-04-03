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


class ExecutionMode(Enum):
    """How the block is executed by the runtime."""

    AUTO = "auto"
    INTERACTIVE = "interactive"
    EXTERNAL = "external"


class BatchMode(Enum):
    """Strategy for processing multiple inputs."""

    PARALLEL = "parallel"
    SERIAL = "serial"
    ADAPTIVE = "adaptive"


class InputDelivery(Enum):
    """How input data is delivered to the block."""

    MEMORY = "memory"
    PROXY = "proxy"
    CHUNKED = "chunked"


class BatchErrorStrategy(Enum):
    """What to do when a batch item fails."""

    STOP = "stop"
    SKIP = "skip"
    RETRY = "retry"
    PAUSE = "pause"
