"""Calculate13CEnrichment - average tracer enrichment per compound x sample (T-LCMS-008)."""

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


class Calculate13CEnrichment(_LCMSBlockMixin, ProcessBlock):
    """Average tracer enrichment per compound per sample."""

    name: ClassVar[str] = "Calculate 13C Enrichment"
    type_name: ClassVar[str] = "lcms.calculate_13c_enrichment"
    category: ClassVar[str] = "isotope_tracing"
    description: ClassVar[str] = (
        "Average 13C (or other tracer) enrichment per compound per sample, "
        "computed as the weighted sum of M+n fractional abundances divided "
        "by the compound's maximum tracer atom count."
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
            name="enrichment",
            accepted_types=[DataFrame],
            description="Per-compound per-sample average enrichment (long format)",
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
        """Compute the long-format enrichment DataFrame."""
        frame = _as_pandas_frame(item)
        compound_column = _resolve_compound_column(frame, str(config.get("compound_column", "Compound")))
        meta = cast(MIDTable.Meta, item.meta)
        tracer_atoms = list(meta.tracer_atoms)
        sample_columns = list(meta.sample_columns)

        for tracer_atom in tracer_atoms:
            if tracer_atom not in frame.columns:
                raise ValueError(f"Calculate13CEnrichment: tracer atom column {tracer_atom!r} is missing")
        for sample_column in sample_columns:
            if sample_column not in frame.columns:
                raise ValueError(f"Calculate13CEnrichment: sample column {sample_column!r} is missing")

        enrichment_columns = (
            ["enrichment"] if len(tracer_atoms) == 1 else [f"enrichment_{atom}" for atom in tracer_atoms]
        )
        if frame.empty:
            return _to_core_dataframe(_pandas().DataFrame(columns=["compound", "sample", *enrichment_columns]))

        rows: list[dict[str, object]] = []
        for compound, compound_frame in frame.groupby(compound_column, sort=False):
            for sample_column in sample_columns:
                row: dict[str, object] = {"compound": compound, "sample": sample_column}
                for tracer_atom in tracer_atoms:
                    weighted_sum = (
                        compound_frame[tracer_atom].astype(float) * compound_frame[sample_column].astype(float)
                    ).sum()
                    max_count = float(compound_frame[tracer_atom].astype(float).max())
                    value = 0.0 if max_count == 0.0 else float(weighted_sum / max_count)
                    key = "enrichment" if len(tracer_atoms) == 1 else f"enrichment_{tracer_atom}"
                    row[key] = value
                rows.append(row)

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
    raise ValueError(f"Calculate13CEnrichment: no compound column found (preferred {preferred!r})")


def _to_core_dataframe(frame: pd.DataFrame) -> DataFrame:
    result = DataFrame(columns=list(frame.columns), row_count=len(frame))
    result._data = frame.reset_index(drop=True)  # type: ignore[attr-defined]
    return result
