"""MetadataStore -- project-level SQLite persistent mirror of DataObject metadata.

Implements ADR-032: a per-project SQLite database that stores the exact
wire-format JSON produced by :func:`_serialise_one` for every DataObject
that passes through the engine.  The database preserves framework
identity, typed plugin metadata, and user annotations across project
reopens, checkpoint restores, and cross-workflow data reuse.

The store is **not** a replacement for storage backends (Zarr, Arrow,
filesystem) -- those still store the data payloads.  This database
stores only the DataObject identity and metadata envelope.

Per ADR-032 Addendum 1, writes happen in the **engine process** (not
worker subprocesses) after the engine receives wire-format output dicts.
The singleton accessor (:func:`get_metadata_store`) follows the same
pattern as :mod:`scieasy.core.storage.flush_context`.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scieasy.core.types.base import DataObject

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema version -- bump when the table DDL changes.
# ---------------------------------------------------------------------------
_SCHEMA_VERSION = 1

_CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS data_objects (
    object_id       TEXT PRIMARY KEY,
    derived_from    TEXT,
    type_name       TEXT NOT NULL,
    backend         TEXT,
    storage_path    TEXT,
    created_at      TEXT NOT NULL,
    wire_payload    TEXT NOT NULL,
    workflow_id     TEXT,
    block_id        TEXT,
    port_name       TEXT
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_derived_from ON data_objects(derived_from);",
    "CREATE INDEX IF NOT EXISTS idx_type_name ON data_objects(type_name);",
    "CREATE INDEX IF NOT EXISTS idx_storage_path ON data_objects(storage_path);",
    "CREATE INDEX IF NOT EXISTS idx_workflow_block ON data_objects(workflow_id, block_id);",
]


# ---------------------------------------------------------------------------
# MetadataStore
# ---------------------------------------------------------------------------


class MetadataStore:
    """Project-level SQLite metadata store for DataObject identity and metadata.

    Each project directory contains one ``metadata.db`` file.  The database
    mirrors the wire-format JSON produced by ``_serialise_one()``, with
    extracted index columns for efficient queries.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  Created if it does not exist.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._init_schema()

    # -- Schema management --------------------------------------------------

    def _init_schema(self) -> None:
        """Create tables/indexes if absent and track schema version."""
        current_version = self._conn.execute("PRAGMA user_version;").fetchone()[0]
        if current_version < _SCHEMA_VERSION:
            self._conn.execute(_CREATE_TABLE)
            for idx_sql in _CREATE_INDEXES:
                self._conn.execute(idx_sql)
            self._conn.execute(f"PRAGMA user_version = {_SCHEMA_VERSION};")
            self._conn.commit()

    # -- Write methods ------------------------------------------------------

    def put(
        self,
        obj: DataObject,
        workflow_id: str | None = None,
        block_id: str | None = None,
        port_name: str | None = None,
    ) -> None:
        """Persist DataObject metadata.  Upsert by ``object_id``.

        Serialises *obj* via ``_serialise_one()`` then delegates to
        :meth:`put_wire`.
        """
        from scieasy.core.types.serialization import _serialise_one

        wire_dict = _serialise_one(obj)
        self.put_wire(wire_dict, workflow_id=workflow_id, block_id=block_id, port_name=port_name)

    def put_wire(
        self,
        wire_dict: dict[str, Any],
        workflow_id: str | None = None,
        block_id: str | None = None,
        port_name: str | None = None,
    ) -> None:
        """Persist a raw wire-format dict.  Upsert by ``object_id``.

        Extracts index columns from the wire-format structure and performs
        an ``INSERT OR REPLACE``.  If the dict has no ``object_id`` in its
        ``metadata.framework`` sub-dict the call is silently ignored (cannot
        store without identity).

        Parameters
        ----------
        wire_dict:
            The exact dict produced by ``_serialise_one()``.
        workflow_id:
            Optional workflow identifier for bookkeeping.
        block_id:
            Optional block identifier for bookkeeping.
        port_name:
            Optional output port name for bookkeeping.
        """
        md = wire_dict.get("metadata") or {}
        if not isinstance(md, dict):
            return
        framework = md.get("framework") or {}
        if not isinstance(framework, dict):
            return
        object_id = framework.get("object_id")
        if not object_id:
            return

        type_chain = md.get("type_chain")
        type_name = str(type_chain[-1]) if isinstance(type_chain, list) and type_chain else "DataObject"

        self._conn.execute(
            "INSERT OR REPLACE INTO data_objects "
            "(object_id, derived_from, type_name, backend, storage_path, "
            "created_at, wire_payload, workflow_id, block_id, port_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                object_id,
                framework.get("derived_from"),
                type_name,
                wire_dict.get("backend"),
                wire_dict.get("path"),
                framework.get("created_at", ""),
                json.dumps(wire_dict),
                workflow_id,
                block_id,
                port_name,
            ),
        )
        self._conn.commit()

    def put_wire_if_missing(
        self,
        wire_dict: dict[str, Any],
        workflow_id: str | None = None,
        block_id: str | None = None,
        port_name: str | None = None,
    ) -> None:
        """Insert wire-format dict only when the object_id is not already stored.

        Used by checkpoint restore sync to avoid overwriting entries that
        were written during a prior execution.
        """
        md = wire_dict.get("metadata") or {}
        if not isinstance(md, dict):
            return
        framework = md.get("framework") or {}
        if not isinstance(framework, dict):
            return
        object_id = framework.get("object_id")
        if not object_id:
            return

        existing = self._conn.execute(
            "SELECT 1 FROM data_objects WHERE object_id = ?",
            (object_id,),
        ).fetchone()
        if existing is not None:
            return

        self.put_wire(wire_dict, workflow_id=workflow_id, block_id=block_id, port_name=port_name)

    # -- Read methods -------------------------------------------------------

    def get(self, object_id: str) -> DataObject | None:
        """Reconstruct a full DataObject from stored metadata.

        Uses the same ``_reconstruct_one()`` path as the worker subprocess.
        Returns ``None`` when *object_id* is not found.
        """
        wire = self.get_wire(object_id)
        if wire is None:
            return None
        from scieasy.core.types.serialization import _reconstruct_one

        return _reconstruct_one(wire)

    def get_wire(self, object_id: str) -> dict[str, Any] | None:
        """Return the raw wire-format dict for *object_id*, or ``None``."""
        row = self._conn.execute(
            "SELECT wire_payload FROM data_objects WHERE object_id = ?",
            (object_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def get_by_storage_path(self, path: str) -> DataObject | None:
        """Look up metadata for a data file on disk.

        Returns the first matching DataObject, or ``None``.
        """
        row = self._conn.execute(
            "SELECT wire_payload FROM data_objects WHERE storage_path = ? LIMIT 1",
            (path,),
        ).fetchone()
        if row is None:
            return None
        from scieasy.core.types.serialization import _reconstruct_one

        return _reconstruct_one(json.loads(row[0]))

    # -- Lineage queries ----------------------------------------------------

    def ancestors(self, object_id: str) -> list[dict[str, Any]]:
        """Return the full provenance chain (derived_from traversal).

        Returns a list of dicts with ``object_id``, ``derived_from``,
        ``type_name``, ``block_id`` for each ancestor, starting from the
        given object and walking up through ``derived_from`` links.
        The first element is the queried object itself.
        """
        rows = self._conn.execute(
            """
            WITH RECURSIVE anc AS (
                SELECT object_id, derived_from, type_name, block_id
                FROM data_objects WHERE object_id = ?
                UNION ALL
                SELECT d.object_id, d.derived_from, d.type_name, d.block_id
                FROM data_objects d
                JOIN anc a ON d.object_id = a.derived_from
            )
            SELECT object_id, derived_from, type_name, block_id FROM anc;
            """,
            (object_id,),
        ).fetchall()
        return [{"object_id": r[0], "derived_from": r[1], "type_name": r[2], "block_id": r[3]} for r in rows]

    def descendants(self, object_id: str) -> list[dict[str, Any]]:
        """Return all objects derived from this one.

        Returns a list of dicts with ``object_id``, ``derived_from``,
        ``type_name``, ``block_id`` for each descendant.
        The first element is the queried object itself.
        """
        rows = self._conn.execute(
            """
            WITH RECURSIVE desc AS (
                SELECT object_id, derived_from, type_name, block_id
                FROM data_objects WHERE object_id = ?
                UNION ALL
                SELECT d.object_id, d.derived_from, d.type_name, d.block_id
                FROM data_objects d
                JOIN desc a ON d.derived_from = a.object_id
            )
            SELECT object_id, derived_from, type_name, block_id FROM desc;
            """,
            (object_id,),
        ).fetchall()
        return [{"object_id": r[0], "derived_from": r[1], "type_name": r[2], "block_id": r[3]} for r in rows]

    # -- Listing queries ----------------------------------------------------

    def list_by_type(self, type_name: str) -> list[dict[str, Any]]:
        """List all objects of a given type (e.g. all Images)."""
        rows = self._conn.execute(
            "SELECT object_id, type_name, storage_path, workflow_id, block_id FROM data_objects WHERE type_name = ?",
            (type_name,),
        ).fetchall()
        return [
            {
                "object_id": r[0],
                "type_name": r[1],
                "storage_path": r[2],
                "workflow_id": r[3],
                "block_id": r[4],
            }
            for r in rows
        ]

    def list_by_workflow(self, workflow_id: str) -> list[dict[str, Any]]:
        """List all objects produced by a workflow run."""
        rows = self._conn.execute(
            "SELECT object_id, type_name, storage_path, block_id, port_name FROM data_objects WHERE workflow_id = ?",
            (workflow_id,),
        ).fetchall()
        return [
            {
                "object_id": r[0],
                "type_name": r[1],
                "storage_path": r[2],
                "block_id": r[3],
                "port_name": r[4],
            }
            for r in rows
        ]

    # -- Maintenance --------------------------------------------------------

    def delete(self, object_id: str) -> None:
        """Remove metadata entry (e.g. when data file is deleted)."""
        self._conn.execute("DELETE FROM data_objects WHERE object_id = ?", (object_id,))
        self._conn.commit()

    def vacuum(self, existing_paths: set[str]) -> int:
        """Remove entries whose ``storage_path`` no longer exists.

        Parameters
        ----------
        existing_paths:
            Set of storage paths that are known to exist on disk.

        Returns
        -------
        int
            Number of rows removed.
        """
        rows = self._conn.execute(
            "SELECT object_id, storage_path FROM data_objects WHERE storage_path IS NOT NULL"
        ).fetchall()
        orphan_ids = [r[0] for r in rows if r[1] not in existing_paths]
        if orphan_ids:
            placeholders = ",".join("?" for _ in orphan_ids)
            self._conn.execute(
                f"DELETE FROM data_objects WHERE object_id IN ({placeholders})",
                orphan_ids,
            )
            self._conn.commit()
        return len(orphan_ids)

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    # -- Dunder -------------------------------------------------------------

    def __repr__(self) -> str:
        return f"MetadataStore(db_path={self._db_path!r})"


# ---------------------------------------------------------------------------
# Module-level singleton (same pattern as flush_context.py)
# ---------------------------------------------------------------------------

_store: MetadataStore | None = None


def get_metadata_store() -> MetadataStore | None:
    """Return the active MetadataStore, or ``None`` when no project context."""
    return _store


def set_metadata_store(store: MetadataStore | None) -> None:
    """Set (or clear) the active MetadataStore singleton."""
    global _store
    _store = store
