"""MergeBlock — merge, join, concatenate multi-input data."""

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


class MergeBlock(ProcessBlock):
    """Merge, join, or concatenate multiple DataFrames.

    Config params:
        how: Join strategy — "concat" (vertical), "inner", "outer", "left".
             Default: "concat".
        on: Column(s) to join on.  Required for inner/outer/left.
    """

    name: ClassVar[str] = "Merge"
    algorithm: ClassVar[str] = "merge"
    description: ClassVar[str] = "Merge or concatenate multiple DataFrames"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="left", accepted_types=[DataFrame], description="Left/first table"),
        InputPort(name="right", accepted_types=[DataFrame], description="Right/second table"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="merged", accepted_types=[DataFrame], description="Merged table"),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Merge two DataFrames via Arrow tables."""
        self.transition(BlockState.RUNNING)
        try:
            left_obj = inputs["left"]
            right_obj = inputs["right"]

            left_data = _to_arrow(left_obj)
            right_data = _to_arrow(right_obj)

            if not isinstance(left_data, pa.Table):
                raise TypeError(f"Expected Arrow Table, got {type(left_data).__name__}")
            if not isinstance(right_data, pa.Table):
                raise TypeError(f"Expected Arrow Table, got {type(right_data).__name__}")

            how = config.get("how", "concat")

            if how == "concat":
                merged = pa.concat_tables([left_data, right_data], promote_options="default")
            else:
                raise NotImplementedError(f"Join strategy '{how}' is not yet implemented; use 'concat'.")

            result = DataFrame(
                columns=merged.column_names,
                row_count=merged.num_rows,
            )
            result._arrow_table = merged  # type: ignore[attr-defined]
            self.transition(BlockState.DONE)
            return {"merged": result}
        except Exception:
            self.transition(BlockState.ERROR)
            raise
