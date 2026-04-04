"""ProvenanceGraph — ancestry, descendant, diff, and audit queries."""

from __future__ import annotations

from typing import Any

from scieasy.core.lineage.record import LineageRecord


class ProvenanceGraph:
    """In-memory provenance graph built from :class:`LineageRecord` instances.

    The graph maps output hashes to the records that produced them and
    input hashes to the records that consumed them.
    """

    def __init__(self) -> None:
        self._records: list[LineageRecord] = []
        # output_hash -> record that produced it
        self._output_to_record: dict[str, LineageRecord] = {}
        # input_hash -> records that consumed it
        self._input_to_records: dict[str, list[LineageRecord]] = {}

    def build(self, records: list[LineageRecord]) -> None:
        """Construct the graph from a list of lineage records."""
        self._records = list(records)
        self._output_to_record = {}
        self._input_to_records = {}

        for record in self._records:
            for out_hash in record.output_hashes:
                self._output_to_record[out_hash] = record
            for in_hash in record.input_hashes:
                self._input_to_records.setdefault(in_hash, []).append(record)

    def ancestors(self, output_hash: str) -> list[LineageRecord]:
        """Return all ancestor records of *output_hash*."""
        visited: set[str] = set()
        visited_records: set[int] = set()
        result: list[LineageRecord] = []
        queue = [output_hash]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            record = self._output_to_record.get(current)
            if record is not None and id(record) not in visited_records:
                visited_records.add(id(record))
                result.append(record)
                for inp in record.input_hashes:
                    if inp not in visited:
                        queue.append(inp)

        return result

    def descendants(self, input_hash: str) -> list[LineageRecord]:
        """Return all descendant records of *input_hash*."""
        visited: set[str] = set()
        visited_records: set[int] = set()
        result: list[LineageRecord] = []
        queue = [input_hash]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            consumers = self._input_to_records.get(current, [])
            for record in consumers:
                if id(record) not in visited_records:
                    visited_records.add(id(record))
                    result.append(record)
                for out_hash in record.output_hashes:
                    if out_hash not in visited:
                        queue.append(out_hash)

        return result

    def diff(self, hash_a: str, hash_b: str) -> dict[str, Any]:
        """Compute the provenance diff between two data hashes.

        Returns blocks that are in the ancestry of hash_b but not hash_a.
        """
        ancestors_a = {r.block_id for r in self.ancestors(hash_a)}
        ancestors_b_records = self.ancestors(hash_b)
        only_in_b = [r for r in ancestors_b_records if r.block_id not in ancestors_a]
        return {
            "only_in_b": only_in_b,
            "shared_blocks": ancestors_a & {r.block_id for r in ancestors_b_records},
        }

    def audit_trail(self, output_hash: str) -> list[LineageRecord]:
        """Return the full ordered audit trail leading to *output_hash*.

        Records are returned in topological order (earliest ancestor first).
        """
        ancestors = self.ancestors(output_hash)
        # Sort by timestamp for a topological-like ordering
        return sorted(ancestors, key=lambda r: r.timestamp)
