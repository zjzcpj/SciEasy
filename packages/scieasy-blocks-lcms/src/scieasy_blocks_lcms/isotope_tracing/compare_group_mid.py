"""CompareGroupMID - per-isotopologue group statistics (T-LCMS-010)."""

from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable, SampleMetadata

if TYPE_CHECKING:
    import pandas as pd

TDataObject = TypeVar("TDataObject", bound=DataObject)


class CompareGroupMID(_LCMSBlockMixin, ProcessBlock):
    """Per-isotopologue statistical comparison of MID values between groups."""

    name: ClassVar[str] = "Compare Group MID"
    type_name: ClassVar[str] = "lcms.compare_group_mid"
    category: ClassVar[str] = "isotope_tracing"
    description: ClassVar[str] = (
        "Per-isotopologue statistical comparison of MID values between "
        "two sample groups. Supports t-test / Wilcoxon / Mann-Whitney "
        "with Bonferroni / FDR correction."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="mid_table",
            accepted_types=[MIDTable],
            required=True,
            description="Mass Isotopomer Distribution table",
        ),
        InputPort(
            name="sample_metadata",
            accepted_types=[SampleMetadata],
            required=True,
            description="Per-sample metadata with the group column",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="comparison",
            accepted_types=[DataFrame],
            description="Long-format per-isotopologue group comparison",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "test": {
                "type": "string",
                "enum": ["t-test", "wilcoxon", "mann-whitney"],
                "default": "t-test",
                "title": "Statistical test",
                "ui_priority": 1,
            },
            "correction": {
                "type": "string",
                "enum": ["bonferroni", "fdr", "none"],
                "default": "fdr",
                "title": "Multiple-testing correction",
                "ui_priority": 2,
            },
            "per_isotopologue": {
                "type": "boolean",
                "default": True,
                "title": "Per-isotopologue (vs summed M+n>0)",
                "ui_priority": 3,
            },
            "group_column": {
                "type": "string",
                "title": "Group column in sample metadata",
                "ui_priority": 4,
            },
            "alpha": {
                "type": "number",
                "default": 0.05,
                "title": "Significance threshold",
                "ui_priority": 5,
            },
        },
        "required": ["group_column"],
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Run the per-isotopologue group comparison."""
        mid_table = _extract_single_item(inputs["mid_table"], MIDTable, "mid_table")
        sample_metadata = _extract_single_item(inputs["sample_metadata"], SampleMetadata, "sample_metadata")
        mid_frame = _as_pandas_frame(mid_table)
        metadata_frame = _as_pandas_frame(sample_metadata)

        group_column = str(config.get("group_column", ""))
        if not group_column:
            raise ValueError("CompareGroupMID: group_column is required")
        if group_column not in metadata_frame.columns:
            raise ValueError(f"CompareGroupMID: group column {group_column!r} is missing")

        metadata_meta = cast(SampleMetadata.Meta, sample_metadata.meta)
        sample_id_column = metadata_meta.sample_id_column
        if sample_id_column not in metadata_frame.columns:
            raise ValueError(f"CompareGroupMID: sample id column {sample_id_column!r} is missing")

        groups = metadata_frame[group_column].dropna().drop_duplicates().tolist()
        if len(groups) < 2:
            raise ValueError("CompareGroupMID: at least two groups are required")
        if len(groups) > 2:
            raise NotImplementedError("CompareGroupMID: >2 groups should use UnivariateStats (T-LCMS-015)")
        group1, group2 = groups[0], groups[1]

        compound_column = _resolve_compound_column(mid_frame)
        mid_meta = cast(MIDTable.Meta, mid_table.meta)
        tracer_atoms = list(mid_meta.tracer_atoms)
        per_isotopologue = bool(config.get("per_isotopologue", True))
        alpha = float(config.get("alpha", 0.05))
        test_name = str(config.get("test", "t-test"))
        correction = str(config.get("correction", "fdr"))

        sample_to_group = metadata_frame.set_index(sample_id_column)[group_column].to_dict()
        sample_columns = [
            sample for sample in mid_meta.sample_columns if sample in mid_frame.columns and sample in sample_to_group
        ]

        rows: list[dict[str, object]] = []
        for compound, compound_frame in mid_frame.groupby(compound_column, sort=False):
            if per_isotopologue:
                work_items = [
                    (
                        f"M+{int(row[tracer_atoms].astype(float).sum())}",
                        {sample: float(row[sample]) for sample in sample_columns},
                    )
                    for _, row in compound_frame.iterrows()
                ]
            else:
                labeled = compound_frame.loc[compound_frame[tracer_atoms].astype(float).sum(axis=1) > 0]
                work_items = [("summed_labeled", labeled[sample_columns].astype(float).sum(axis=0).to_dict())]

            for isotopologue, values_by_sample in work_items:
                group1_values = [
                    value for sample, value in values_by_sample.items() if sample_to_group[sample] == group1
                ]
                group2_values = [
                    value for sample, value in values_by_sample.items() if sample_to_group[sample] == group2
                ]
                pvalue = _run_test(group1_values, group2_values, test_name)
                row: dict[str, object] = {
                    "compound": compound,
                    "group1": group1,
                    "group2": group2,
                    "group1_mean": float(sum(group1_values) / len(group1_values)),
                    "group2_mean": float(sum(group2_values) / len(group2_values)),
                    "pvalue": pvalue,
                }
                if per_isotopologue:
                    row["isotopologue"] = isotopologue
                rows.append(row)

        adjusted = _adjust_pvalues([cast(float, row["pvalue"]) for row in rows], correction) if rows else []
        for row, adjusted_pvalue in zip(rows, adjusted, strict=True):
            row["pvalue_adj"] = adjusted_pvalue
            row["significant"] = bool(adjusted_pvalue < alpha)

        result_object = _to_core_dataframe(_pandas().DataFrame(rows))
        return {"comparison": Collection(items=[result_object], item_type=DataFrame)}


def _pandas() -> ModuleType:
    import pandas as pd

    return cast(ModuleType, pd)


def _extract_single_item(payload: Collection | DataObject, expected_type: type[TDataObject], name: str) -> TDataObject:
    if isinstance(payload, Collection):
        if len(payload) != 1:
            raise ValueError(f"CompareGroupMID: input {name!r} must contain exactly one item")
        item = payload[0]
    else:
        item = payload
    if not isinstance(item, expected_type):
        raise TypeError(f"CompareGroupMID: input {name!r} must be {expected_type.__name__}")
    return cast(TDataObject, item)


def _as_pandas_frame(item: DataObject) -> pd.DataFrame:
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


def _resolve_compound_column(frame: pd.DataFrame) -> str:
    if "Compound" in frame.columns:
        return "Compound"
    if "compound" in frame.columns:
        return "compound"
    raise ValueError("CompareGroupMID: no compound column found")


def _run_test(group1_values: list[float], group2_values: list[float], test_name: str) -> float:
    from scipy import stats

    if test_name == "t-test":
        return float(stats.ttest_ind(group1_values, group2_values, equal_var=False, nan_policy="omit").pvalue)
    if test_name == "mann-whitney":
        return float(stats.mannwhitneyu(group1_values, group2_values, alternative="two-sided").pvalue)
    if test_name == "wilcoxon":
        if len(group1_values) != len(group2_values):
            raise ValueError("CompareGroupMID: wilcoxon requires equal group sizes")
        try:
            return float(stats.wilcoxon(group1_values, group2_values).pvalue)
        except ValueError:
            return 1.0
    raise ValueError(f"CompareGroupMID: unsupported test {test_name!r}")


def _adjust_pvalues(pvalues: list[float], method: str) -> list[float]:
    if method == "none":
        return pvalues
    if method == "bonferroni":
        count = len(pvalues)
        return [min(1.0, pvalue * count) for pvalue in pvalues]
    if method == "fdr":
        from statsmodels.stats.multitest import multipletests

        return [float(value) for value in multipletests(pvalues, method="fdr_bh")[1]]
    raise ValueError(f"CompareGroupMID: unsupported correction {method!r}")


def _to_core_dataframe(frame: pd.DataFrame) -> DataFrame:
    result = DataFrame(columns=list(frame.columns), row_count=len(frame))
    result._data = frame.reset_index(drop=True)  # type: ignore[attr-defined]
    return result
