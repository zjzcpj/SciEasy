"""MergeBlock — merge, join, concatenate multi-input data."""

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

    ADR-031 D2: no _arrow_table backdoor.
    """
    from scieasy.core.storage.arrow_backend import ArrowBackend
    from scieasy.core.storage.ref import StorageReference

    tmp_path = str(Path(tempfile.gettempdir()) / f"{uuid.uuid4()}.parquet")
    ref = StorageReference(backend="arrow", path=tmp_path)
    ref = ArrowBackend().write(table, ref)
    return DataFrame(columns=table.column_names, row_count=table.num_rows, storage_ref=ref)


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

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Merge two DataFrames via Arrow tables.

        Accepts both raw DataFrame and Collection[DataFrame] inputs for
        backward compatibility during the ADR-020 transition.
        """
        from scieasy.core.types.collection import Collection

        left_obj = inputs["left"]
        right_obj = inputs["right"]

        # ADR-020: Unpack Collection inputs if present.
        if isinstance(left_obj, Collection):
            left_obj = self.unpack_single(left_obj)
        if isinstance(right_obj, Collection):
            right_obj = self.unpack_single(right_obj)

        left_data = to_arrow(left_obj)
        right_data = to_arrow(right_obj)

        if not isinstance(left_data, pa.Table):
            raise TypeError(f"Expected Arrow Table, got {type(left_data).__name__}")
        if not isinstance(right_data, pa.Table):
            raise TypeError(f"Expected Arrow Table, got {type(right_data).__name__}")

        how = config.get("how", "concat")

        if how == "concat":
            merged = pa.concat_tables([left_data, right_data], promote_options="default")
        else:
            raise NotImplementedError(f"Join strategy '{how}' is not yet implemented; use 'concat'.")

        return {"merged": Collection([_persist_arrow(merged)], item_type=DataFrame)}
