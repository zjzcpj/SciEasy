"""LineageStore — SQLite-backed read/write for lineage records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from scieasy.core.lineage.environment import EnvironmentSnapshot
from scieasy.core.lineage.record import LineageRecord

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id TEXT NOT NULL,
    block_version TEXT NOT NULL,
    block_config TEXT NOT NULL,
    input_hashes TEXT NOT NULL,
    output_hashes TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    environment TEXT,
    termination TEXT NOT NULL DEFAULT 'completed',
    partial_output_refs TEXT,
    termination_detail TEXT
);
"""
# ADR-018: Added termination, partial_output_refs, termination_detail.
# ADR-020: Removed batch_info column.

_CREATE_INDEX_BLOCK = """
CREATE INDEX IF NOT EXISTS idx_lineage_block_id ON lineage (block_id);
"""

_CREATE_INDEX_OUTPUT = """
CREATE INDEX IF NOT EXISTS idx_lineage_output_hashes ON lineage (output_hashes);
"""


class LineageStore:
    """Persistent SQLite-backed store for :class:`LineageRecord` instances."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            default_dir = Path(".scieasy")
            default_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(default_dir / "lineage.db")
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_TABLE)
        self._conn.execute(_CREATE_INDEX_BLOCK)
        self._conn.execute(_CREATE_INDEX_OUTPUT)
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def write(self, record: LineageRecord) -> None:
        """Persist a single :class:`LineageRecord`."""
        env_json: str | None = None
        if record.environment is not None:
            env_json = json.dumps(
                {
                    "python_version": record.environment.python_version,
                    "platform": record.environment.platform,
                    "key_packages": record.environment.key_packages,
                    "full_freeze": record.environment.full_freeze,
                    "conda_env": record.environment.conda_env,
                }
            )
        # ADR-018: persist termination, partial_output_refs, termination_detail.
        # ADR-020: batch_info removed.
        self._conn.execute(
            "INSERT INTO lineage (block_id, block_version, block_config, "
            "input_hashes, output_hashes, timestamp, duration_ms, environment, "
            "termination, partial_output_refs, termination_detail) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.block_id,
                record.block_version,
                json.dumps(record.block_config),
                json.dumps(record.input_hashes),
                json.dumps(record.output_hashes),
                record.timestamp,
                record.duration_ms,
                env_json,
                record.termination,
                json.dumps(record.partial_output_refs),
                record.termination_detail,
            ),
        )
        self._conn.commit()

    @staticmethod
    def _normalize_hashes(raw: Any) -> dict[str, list[str]]:
        """Normalize hash data from JSON, handling backward compatibility.

        Old format (pre-#55): ``["hash1", "hash2"]`` -- wrapped as ``{"default": [...]}``.
        New format (#55+): ``{"port_name": ["hash1", "hash2"]}``.
        """
        if isinstance(raw, list):
            return {"default": raw}
        return raw  # already a dict

    def _row_to_record(self, row: tuple[Any, ...]) -> LineageRecord:
        """Convert a database row to a :class:`LineageRecord`.

        ADR-018: Added termination, partial_output_refs, termination_detail.
        ADR-020: Removed batch_info.
        Issue #55: input_hashes/output_hashes are now per-port dicts.
        """
        env: EnvironmentSnapshot | None = None
        if row[7] is not None:
            env_data = json.loads(row[7])
            env = EnvironmentSnapshot(**env_data)
        return LineageRecord(
            block_id=row[0],
            block_version=row[1],
            block_config=json.loads(row[2]),
            input_hashes=self._normalize_hashes(json.loads(row[3])),
            output_hashes=self._normalize_hashes(json.loads(row[4])),
            timestamp=row[5],
            duration_ms=row[6],
            environment=env,
            termination=row[8] if row[8] is not None else "completed",
            partial_output_refs=json.loads(row[9]) if row[9] is not None else [],
            termination_detail=row[10] if row[10] is not None else "",
        )

    def query(
        self,
        block_id: str | None = None,
        **filters: Any,
    ) -> list[LineageRecord]:
        """Query records, optionally filtered by *block_id*."""
        if block_id is not None:
            cursor = self._conn.execute(
                "SELECT block_id, block_version, block_config, input_hashes, "
                "output_hashes, timestamp, duration_ms, environment, "
                "termination, partial_output_refs, termination_detail "
                "FROM lineage WHERE block_id = ? ORDER BY id",
                (block_id,),
            )
        else:
            cursor = self._conn.execute(
                "SELECT block_id, block_version, block_config, input_hashes, "
                "output_hashes, timestamp, duration_ms, environment, "
                "termination, partial_output_refs, termination_detail "
                "FROM lineage ORDER BY id",
            )
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def ancestors(self, output_hash: str) -> list[LineageRecord]:
        """Return all records in the ancestor chain of *output_hash*.

        Traces backwards: finds the record that produced *output_hash*,
        then recursively finds records that produced each of its inputs.
        """
        visited: set[str] = set()
        visited_records: set[tuple[str, str]] = set()
        result: list[LineageRecord] = []
        queue = [output_hash]

        while queue:
            current_hash = queue.pop(0)
            if current_hash in visited:
                continue
            visited.add(current_hash)

            cursor = self._conn.execute(
                "SELECT block_id, block_version, block_config, input_hashes, "
                "output_hashes, timestamp, duration_ms, environment, "
                "termination, partial_output_refs, termination_detail "
                "FROM lineage WHERE output_hashes LIKE ? ORDER BY id",
                (f'%"{current_hash}"%',),
            )
            for row in cursor.fetchall():
                record = self._row_to_record(row)
                record_key = (record.block_id, record.timestamp)
                if record_key not in visited_records:
                    visited_records.add(record_key)
                    result.append(record)
                    for port_hashes in record.input_hashes.values():
                        for inp in port_hashes:
                            if inp not in visited:
                                queue.append(inp)

        return result
