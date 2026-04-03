"""BlockResult and BatchResult — execution outcome containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BlockResult:
    """Outcome of a single block execution."""

    outputs: dict[str, Any]
    duration_ms: int = 0
    error: Exception | None = None


@dataclass
class BatchResult:
    """Aggregate outcome of a batch execution across multiple items."""

    succeeded: list[tuple[int, Any]] = field(default_factory=list)
    failed: list[tuple[int, Exception]] = field(default_factory=list)
    skipped: list[int] = field(default_factory=list)
