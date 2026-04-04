"""Format adapter: CSV files to/from DataFrame."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.csv as pcsv

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.dataframe import DataFrame


class CSVAdapter:
    """Format adapter for CSV files.

    Reads CSV into an Arrow Table wrapped in a DataFrame.
    Writes a DataFrame (with _arrow_table or storage ref) to CSV.
    """

    def read(self, path: str | Path, **kwargs: Any) -> DataFrame:
        """Read a CSV file and return a DataFrame."""
        path = Path(path)
        table = pcsv.read_csv(str(path), **kwargs)
        df = DataFrame(
            columns=table.column_names,
            row_count=table.num_rows,
        )
        df._arrow_table = table  # type: ignore[attr-defined]
        return df

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        """Write data to a CSV file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, DataFrame) and hasattr(data, "_arrow_table"):
            table = data._arrow_table  # type: ignore[attr-defined]
        elif isinstance(data, pa.Table):
            table = data
        elif isinstance(data, dict):
            table = pa.table(data)
        else:
            raise TypeError(f"Cannot write {type(data).__name__} as CSV")

        pcsv.write_csv(table, str(path))
        return path

    def supported_extensions(self) -> list[str]:
        """Return the list of file extensions this adapter handles."""
        return [".csv"]

    def create_reference(self, path: str | Path) -> StorageReference:
        """Build a StorageReference for a CSV file without reading data."""
        return StorageReference(backend="arrow", path=str(Path(path)), format="csv")
