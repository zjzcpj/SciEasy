"""LineageRecord dataclass — immutable log of a single block execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scieasy.core.lineage.environment import EnvironmentSnapshot


@dataclass
class LineageRecord:
    """Immutable record of a single block execution for provenance tracking.

    Attributes:
        input_hashes: Per-port content hashes of input data objects.
            Keys are port names; values are lists of content hashes
            (one per item for Collections, one-element list for scalars).
        block_id: Unique identifier of the block that executed.
        block_config: Frozen snapshot of the block's configuration/parameters.
        block_version: Semantic version of the block implementation.
        output_hashes: Per-port content hashes of output data objects.
            Keys are port names; values are lists of content hashes.
        timestamp: ISO-8601 timestamp of execution start.
        duration_ms: Wall-clock duration in milliseconds.
        environment: Optional snapshot of the runtime environment.
        batch_info: Optional batch/parallel execution metadata.
    """

    input_hashes: dict[str, list[str]]
    block_id: str
    block_config: dict[str, Any]
    block_version: str
    output_hashes: dict[str, list[str]]
    timestamp: str
    duration_ms: int
    environment: EnvironmentSnapshot | None = None
    # ADR-020: batch_info REMOVED — no engine-level batch.
    # ADR-018: New fields for all terminal states (not just success):
    termination: str = "completed"  # "completed" | "cancelled" | "error" | "skipped"
    partial_output_refs: list[str] = field(default_factory=list)  # outputs produced before termination
    termination_detail: str = ""  # human-readable reason for non-completed termination
