"""MetaboliteMatrix - pivot a long PeakTable into a wide compound x sample matrix (T-LCMS-013)."""

from __future__ import annotations

from typing import Any, ClassVar, cast

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import PeakTable, SampleMetadata


class MetaboliteMatrix(_LCMSBlockMixin, ProcessBlock):
    """Pivot a long-format PeakTable to a wide compound x sample matrix."""

    name: ClassVar[str] = "Metabolite Matrix"
    type_name: ClassVar[str] = "lcms.metabolite_matrix"
    category: ClassVar[str] = "analysis"
    description: ClassVar[str] = (
        "Pivot a long-format PeakTable into a wide compound x sample matrix. "
        "Missing combinations become NaN; imputation is the caller's responsibility."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="peak_table",
            accepted_types=[PeakTable],
            required=True,
            description="Long-format peak table",
        ),
        InputPort(
            name="sample_metadata",
            accepted_types=[SampleMetadata],
            required=False,
            description="Optional metadata to fix the column order",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="matrix",
            accepted_types=[DataFrame],
            description="Wide compound x sample DataFrame",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "value_column": {
                "type": "string",
                "default": "intensity",
                "title": "Value column",
                "ui_priority": 1,
            },
            "compound_column": {
                "type": "string",
                "default": "compound",
                "title": "Compound column",
                "ui_priority": 2,
            },
            "sample_column": {
                "type": "string",
                "default": "sample_id",
                "title": "Sample column",
                "ui_priority": 3,
            },
        },
    }

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        peak_table = _extract_single_item(inputs["peak_table"], PeakTable, "peak_table")
        peak_frame = _as_pandas_frame(peak_table)

        value_column = str(config.get("value_column", "intensity"))
        compound_column = str(config.get("compound_column", "compound"))
        sample_column = str(config.get("sample_column", "sample_id"))

        for column_name in (value_column, compound_column, sample_column):
            if column_name not in peak_frame.columns:
                raise ValueError(f"MetaboliteMatrix: column {column_name!r} is missing")

        matrix = peak_frame.pivot_table(
            index=compound_column,
            columns=sample_column,
            values=value_column,
            aggfunc="first",
            sort=False,
        )
        matrix.index.name = compound_column

        metadata_payload = inputs.get("sample_metadata")
        if metadata_payload is not None:
            sample_metadata = _extract_single_item(metadata_payload, SampleMetadata, "sample_metadata")
            metadata_frame = _as_pandas_frame(sample_metadata)
            sample_id_column = cast(SampleMetadata.Meta, sample_metadata.meta).sample_id_column
            if sample_id_column not in metadata_frame.columns:
                raise ValueError(f"MetaboliteMatrix: sample id column {sample_id_column!r} is missing")
            sample_order = [str(sample_id) for sample_id in metadata_frame[sample_id_column].tolist()]
            remainder = [column for column in matrix.columns if column not in sample_order]
            matrix = matrix.reindex(columns=sample_order + remainder)

        result = DataFrame(
            columns=list(matrix.columns),
            row_count=len(matrix),
            schema={column: str(dtype) for column, dtype in matrix.dtypes.items()},
        )
        result._data = matrix.copy()  # type: ignore[attr-defined]
        return {"matrix": Collection(items=[result], item_type=DataFrame)}


def _pandas() -> Any:
    import pandas as pd

    return pd


def _extract_single_item(payload: Collection, expected_type: type[Any], name: str) -> Any:
    if len(payload) != 1:
        raise ValueError(f"MetaboliteMatrix: input {name!r} must contain exactly one item")
    item = payload[0]
    if not isinstance(item, expected_type):
        raise TypeError(f"MetaboliteMatrix: input {name!r} must be {expected_type.__name__}")
    return item


def _as_pandas_frame(item: Any) -> Any:
    pd = _pandas()
    raw = getattr(item, "_data", None)
    if isinstance(raw, pd.DataFrame):
        return raw.copy()
    if raw is not None:
        return pd.DataFrame(raw).copy()
    materialized = item.to_memory()
    if isinstance(materialized, pd.DataFrame):
        return materialized.copy()
    return pd.DataFrame(materialized).copy()
