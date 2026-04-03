"""ProvenanceGraph — ancestry, descendant, diff, and audit queries."""

from __future__ import annotations

from typing import Any

from scieasy.core.lineage.record import LineageRecord


class ProvenanceGraph:
    """In-memory provenance graph built from :class:`LineageRecord` instances.

    Phase 1 stub — all methods raise :class:`NotImplementedError`.
    """

    def build(self, records: list[LineageRecord]) -> None:
        """Construct the graph from a list of lineage records."""
        raise NotImplementedError

    def ancestors(self, output_hash: str) -> list[LineageRecord]:
        """Return all ancestor records of *output_hash*."""
        raise NotImplementedError

    def descendants(self, input_hash: str) -> list[LineageRecord]:
        """Return all descendant records of *input_hash*."""
        raise NotImplementedError

    def diff(self, hash_a: str, hash_b: str) -> dict[str, Any]:
        """Compute the provenance diff between two data hashes."""
        raise NotImplementedError

    def audit_trail(self, output_hash: str) -> list[LineageRecord]:
        """Return the full ordered audit trail leading to *output_hash*."""
        raise NotImplementedError
