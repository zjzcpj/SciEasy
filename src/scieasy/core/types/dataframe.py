"""DataFrame type — columnar tabular data (peak tables, metadata)."""

from __future__ import annotations

from typing import Any

from scieasy.core.types.base import DataObject


class DataFrame(DataObject):
    """Columnar tabular data, backed by Arrow/Parquet for large datasets.

    Attributes:
        columns: Column names, if known.
        row_count: Number of rows, if known.
        schema: Column-level type schema, if known.
    """

    def __init__(
        self,
        *,
        columns: list[str] | None = None,
        row_count: int | None = None,
        schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.columns = columns
        self.row_count = row_count
        self.schema = schema


class PeakTable(DataFrame):
    """Tabular peak-detection output (m/z, intensity, retention time, etc.)."""


class MetabPeakTable(PeakTable):
    """Metabolomics peak table with additional annotation columns."""
