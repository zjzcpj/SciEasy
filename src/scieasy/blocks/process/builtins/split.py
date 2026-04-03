"""SplitBlock — filter, subset, train-test split."""

from __future__ import annotations

from typing import Any, ClassVar

import pyarrow as pa

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame


def _to_arrow(obj: Any) -> pa.Table:
    """Extract an Arrow Table from a DataFrame, ViewProxy, or raw Table."""
    from scieasy.core.proxy import ViewProxy

    if isinstance(obj, ViewProxy):
        obj = obj.to_memory()
    if isinstance(obj, pa.Table):
        return obj
    if isinstance(obj, DataFrame) and hasattr(obj, "_arrow_table"):
        return obj._arrow_table  # type: ignore[attr-defined]
    if isinstance(obj, DataFrame) and obj.storage_ref is not None:
        return obj.to_memory()
    raise TypeError(f"Cannot extract Arrow Table from {type(obj).__name__}")


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

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Split the input DataFrame."""
        self.transition(BlockState.RUNNING)
        try:
            data_obj = inputs["data"]
            data = _to_arrow(data_obj)

            if not isinstance(data, pa.Table):
                raise TypeError(f"Expected Arrow Table, got {type(data).__name__}")

            mode = config.get("mode", "head")

            if mode == "head":
                n = int(config.get("n", 100))
                out_table = data.slice(0, n)
                result = DataFrame(columns=out_table.column_names, row_count=out_table.num_rows)
                result._arrow_table = out_table  # type: ignore[attr-defined]
                self.transition(BlockState.DONE)
                return {"out": result}

            elif mode == "ratio":
                ratio = float(config.get("ratio", 0.8))
                split_idx = int(data.num_rows * ratio)
                first = data.slice(0, split_idx)
                second = data.slice(split_idx)
                r1 = DataFrame(columns=first.column_names, row_count=first.num_rows)
                r1._arrow_table = first  # type: ignore[attr-defined]
                r2 = DataFrame(columns=second.column_names, row_count=second.num_rows)
                r2._arrow_table = second  # type: ignore[attr-defined]
                self.transition(BlockState.DONE)
                return {"out": r1, "remainder": r2}

            elif mode == "filter":
                column = config.get("column")
                value = config.get("value")
                if column is None or value is None:
                    raise ValueError("Filter mode requires 'column' and 'value' in config")
                import pyarrow.compute as pc

                mask = pc.equal(data.column(column), pa.scalar(value))
                filtered = data.filter(mask)
                result = DataFrame(columns=filtered.column_names, row_count=filtered.num_rows)
                result._arrow_table = filtered  # type: ignore[attr-defined]
                self.transition(BlockState.DONE)
                return {"out": result}

            else:
                raise ValueError(f"Unknown split mode: {mode}")
        except Exception:
            self.transition(BlockState.ERROR)
            raise
