"""Format adapter: Apache Parquet files to/from DataFrame."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from scieasy.core.types.dataframe import DataFrame


class ParquetAdapter:
    """Format adapter for Apache Parquet files.

    Reads Parquet into an Arrow Table wrapped in a :class:`DataFrame`.
    Writes a :class:`DataFrame` (with ``_arrow_table``) to Parquet.
    """

    def read(self, path: str | Path, **kwargs: Any) -> DataFrame:
        """Read a Parquet file and return a :class:`DataFrame`."""
        path = Path(path)
        table = pq.read_table(str(path), **kwargs)
        df = DataFrame(
            columns=table.column_names,
            row_count=table.num_rows,
        )
        df._arrow_table = table  # type: ignore[attr-defined]
        return df

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        """Write data to a Parquet file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, DataFrame) and hasattr(data, "_arrow_table"):
            table = data._arrow_table  # type: ignore[attr-defined]
        elif isinstance(data, pa.Table):
            table = data
        elif isinstance(data, dict):
            table = pa.table(data)
        else:
            raise TypeError(f"Cannot write {type(data).__name__} as Parquet")

        pq.write_table(table, str(path))
        return path

    def supported_extensions(self) -> list[str]:
        """Return the list of file extensions this adapter handles."""
        return [".parquet", ".pq"]


# TODO(ADR-020-Add2): Implement create_reference(path) -> StorageReference.
# Build a StorageReference pointing to the file without reading its contents.
