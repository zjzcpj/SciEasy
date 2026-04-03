"""Content hashing for lineage (xxhash on data chunks)."""

from __future__ import annotations

from typing import Any


def content_hash(data: Any) -> str:
    """Compute a content hash for lineage tracking using xxhash."""
    raise NotImplementedError
