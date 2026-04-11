"""SplitBlock — filter, subset, train-test split."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pyarrow as pa

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.blocks.process.utils import to_arrow
from scieasy.core.types.dataframe import DataFrame

if TYPE_CHECKING:
    from scieasy.core.types.collection import Collection


def _persist_arrow(table: pa.Table) -> DataFrame:
    """Persist *table* to a temp parquet file and return a storage-backed DataFrame.

    ADR-031 D2: no _arrow_table backdoor; derived DataFrames are always
    backed by a StorageReference.
    """
    from scieasy.core.storage.arrow_backend import ArrowBackend
    from scieasy.core.storage.ref import StorageReference

    tmp_path = str(Path(tempfile.gettempdir()) / f"{uuid.uuid4()}.parquet")
    ref = StorageReference(backend="arrow", path=tmp_path)
    ref = ArrowBackend().write(table, ref)
    return DataFrame(columns=table.column_names, row_count=table.num_rows, storage_ref=ref)


class SplitBlock(ProcessBlock):
    """Filter, subset, or split input data.

    Config params:
        mode: "filter" (column-based filter), "head" (first N rows),
              or "ratio" (train-test split).  Default: "head".
        n: Number of rows for "head" mode.  Default: 100.
        ratio: Fraction for the first split in "ratio" mode.  Default: 0.8.
        column: Column name for "filter" mode.
        value: Value to match for "filter" mode.
    """

    name: ClassVar[str] = "Split"
    algorithm: ClassVar[str] = "split"
    description: ClassVar[str] = "Filter, subset, or split tabular data"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[DataFrame], description="Input table"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="out", accepted_types=[DataFrame], description="Primary output"),
        OutputPort(name="remainder", accepted_types=[DataFrame], required=False, description="Complement (ratio mode)"),
    ]

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Split the input DataFrame.

        Accepts both raw DataFrame and Collection[DataFrame] inputs for
        backward compatibility during the ADR-020 transition.
        """
        from scieasy.core.types.collection import Collection

        data_obj = inputs["data"]

        # ADR-020: Unpack Collection input if present.
        if isinstance(data_obj, Collection):
            data_obj = self.unpack_single(data_obj)
        data = to_arrow(data_obj)

        if not isinstance(data, pa.Table):
            raise TypeError(f"Expected Arrow Table, got {type(data).__name__}")

        mode = config.get("mode", "head")

        if mode == "head":
            n = int(config.get("n", 100))
            out_table = data.slice(0, n)
            return {"out": Collection([_persist_arrow(out_table)], item_type=DataFrame)}

        elif mode == "ratio":
            ratio = float(config.get("ratio", 0.8))
            split_idx = int(data.num_rows * ratio)
            first = data.slice(0, split_idx)
            second = data.slice(split_idx)
            return {
                "out": Collection([_persist_arrow(first)], item_type=DataFrame),
                "remainder": Collection([_persist_arrow(second)], item_type=DataFrame),
            }

        elif mode == "filter":
            column = config.get("column")
            value = config.get("value")
            if column is None or value is None:
                raise ValueError("Filter mode requires 'column' and 'value' in config")
            import pyarrow.compute as pc

            mask = pc.equal(data.column(column), pa.scalar(value))
            filtered = data.filter(mask)
            return {"out": Collection([_persist_arrow(filtered)], item_type=DataFrame)}

        else:
            raise ValueError(f"Unknown split mode: {mode}")
