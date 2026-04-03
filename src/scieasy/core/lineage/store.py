"""LineageStore — SQLite-backed read/write for lineage records."""

from __future__ import annotations

from typing import Any

from scieasy.core.lineage.record import LineageRecord


class LineageStore:
    """Persistent store for :class:`LineageRecord` instances.

    Phase 1 stub — all methods raise :class:`NotImplementedError`.
    """

    def write(self, record: LineageRecord) -> None:
        """Persist a single :class:`LineageRecord`."""
        raise NotImplementedError

    def query(
        self,
        block_id: str | None = None,
        **filters: Any,
    ) -> list[LineageRecord]:
        """Query records, optionally filtered by *block_id* and extra criteria."""
        raise NotImplementedError

    def ancestors(self, output_hash: str) -> list[LineageRecord]:
        """Return all records in the ancestor chain of *output_hash*."""
        raise NotImplementedError
