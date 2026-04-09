"""FractionalLabeling - ``1 - M+0`` per compound x sample (T-LCMS-009)."""

from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING, Any, ClassVar, cast

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable

if TYPE_CHECKING:
    import pandas as pd


class FractionalLabeling(_LCMSBlockMixin, ProcessBlock):
    """Compute ``1 - M+0`` per compound per sample."""

    name: ClassVar[str] = "Fractional Labeling"
    type_name: ClassVar[str] = "fractional_labeling"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Compute fractional labeling (1 - M+0) per compound per sample. "
        "Multi-tracer M+0 = intersection of all tracer-atom columns being 0."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="mid_table",
            accepted_types=[MIDTable],
            required=True,
            description="Mass Isotopomer Distribution table (long format)",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="fractional_labeling",
            accepted_types=[DataFrame],
            description="Long-format DataFrame: compound, sample, fractional_labeling",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "compound_column": {
                "type": "string",
                "default": "Compound",
                "title": "Compound column name",
                "ui_priority": 1,
            },
        },
    }

    def process_item(
        self,
        item: MIDTable,
        config: BlockConfig,
        state: Any = None,
    ) -> DataFrame:
        """Emit the long-format fractional labelling DataFrame."""
        frame = _as_pandas_frame(item)
        compound_column = _resolve_compound_column(frame, str(config.get("compound_column", "Compound")))
        meta = cast(MIDTable.Meta, item.meta)
        tracer_atoms = list(meta.tracer_atoms)
        sample_columns = list(meta.sample_columns)

        for tracer_atom in tracer_atoms:
            if tracer_atom not in frame.columns:
                raise ValueError(f"FractionalLabeling: tracer atom column {tracer_atom!r} is missing")

        rows: list[dict[str, object]] = []
        for compound, compound_frame in frame.groupby(compound_column, sort=False):
            m0_rows = compound_frame.copy()
            for tracer_atom in tracer_atoms:
                m0_rows = m0_rows.loc[m0_rows[tracer_atom] == 0]
            if m0_rows.empty:
                raise ValueError(f"FractionalLabeling: compound {compound!r} is missing an M+0 row")
            m0_row = m0_rows.iloc[0]
            for sample_column in sample_columns:
                rows.append(
                    {
                        "compound": compound,
                        "sample": sample_column,
                        "fractional_labeling": 1.0 - float(m0_row[sample_column]),
                    }
                )

        return _to_core_dataframe(_pandas().DataFrame(rows))


def _pandas() -> ModuleType:
    import pandas as pd

    return cast(ModuleType, pd)


def _as_pandas_frame(item: MIDTable) -> pd.DataFrame:
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


def _resolve_compound_column(frame: pd.DataFrame, preferred: str) -> str:
    if preferred in frame.columns:
        return preferred
    if "compound" in frame.columns:
        return "compound"
    if "Compound" in frame.columns:
        return "Compound"
    raise ValueError(f"FractionalLabeling: no compound column found (preferred {preferred!r})")


def _to_core_dataframe(frame: pd.DataFrame) -> DataFrame:
    result = DataFrame(columns=list(frame.columns), row_count=len(frame))
    result._data = frame.reset_index(drop=True)  # type: ignore[attr-defined]
    return result
