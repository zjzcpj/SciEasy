"""UnivariateStats - per-metabolite t-test / ANOVA / Wilcoxon (T-LCMS-015)."""

from __future__ import annotations

from typing import Any, ClassVar, cast

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import SampleMetadata


class UnivariateStats(_LCMSBlockMixin, ProcessBlock):
    """Per-metabolite univariate statistics with multiple-testing correction."""

    name: ClassVar[str] = "Univariate Stats"
    type_name: ClassVar[str] = "univariate_stats"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Per-metabolite t-test / ANOVA / Wilcoxon with optional fold change "
        "and Bonferroni / FDR multiple-testing correction."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="matrix",
            accepted_types=[DataFrame],
            required=True,
            description="Wide compound x sample matrix",
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
            name="stats",
            accepted_types=[DataFrame],
            description="Long-format DataFrame: compound, fold_change, pvalue, pvalue_adj, significant",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "test": {
                "type": "string",
                "enum": ["t-test", "anova", "wilcoxon"],
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
            "group_column": {
                "type": "string",
                "title": "Group column in sample metadata",
                "ui_priority": 3,
            },
            "alpha": {
                "type": "number",
                "default": 0.05,
                "title": "Significance threshold",
                "ui_priority": 4,
            },
        },
        "required": ["group_column"],
    }

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        matrix_item = _extract_single_item(inputs["matrix"], DataFrame, "matrix")
        sample_metadata_item = _extract_single_item(inputs["sample_metadata"], SampleMetadata, "sample_metadata")

        matrix_frame = _as_pandas_frame(matrix_item).astype(float)
        metadata_frame = _as_pandas_frame(sample_metadata_item)
        metadata_meta = cast(SampleMetadata.Meta, sample_metadata_item.meta)

        group_column = str(config.get("group_column", ""))
        if not group_column:
            raise ValueError("UnivariateStats: group_column is required")
        if group_column not in metadata_frame.columns:
            raise ValueError(f"UnivariateStats: group column {group_column!r} is missing")
        if metadata_meta.sample_id_column not in metadata_frame.columns:
            raise ValueError(f"UnivariateStats: sample id column {metadata_meta.sample_id_column!r} is missing")

        sample_order = [
            str(sample_id)
            for sample_id in metadata_frame[metadata_meta.sample_id_column].tolist()
            if sample_id in matrix_frame.columns
        ]
        if len(sample_order) < 2:
            raise ValueError("UnivariateStats: at least two shared samples are required")

        groups = (
            metadata_frame.loc[metadata_frame[metadata_meta.sample_id_column].isin(sample_order), group_column]
            .dropna()
            .drop_duplicates()
            .tolist()
        )
        test_name = str(config.get("test", "t-test"))
        if test_name in {"t-test", "wilcoxon"} and len(groups) != 2:
            raise ValueError(f"UnivariateStats: {test_name} requires exactly two groups")
        if test_name == "anova" and len(groups) < 3:
            raise ValueError("UnivariateStats: anova requires at least three groups")
        if test_name not in {"t-test", "anova", "wilcoxon"}:
            raise ValueError(f"UnivariateStats: unsupported test {test_name!r}")

        group_lookup = metadata_frame.set_index(metadata_meta.sample_id_column)[group_column].to_dict()
        alpha = float(config.get("alpha", 0.05))
        correction = str(config.get("correction", "fdr"))

        rows: list[dict[str, Any]] = []
        for compound, row in matrix_frame.loc[:, sample_order].iterrows():
            group_values: dict[Any, list[float]] = {group: [] for group in groups}
            for sample_id, value in row.items():
                group = group_lookup[sample_id]
                if group in group_values:
                    group_values[group].append(float(value))

            if test_name == "anova":
                pvalue = _run_anova([values for values in group_values.values()])
                fold_change = float("nan")
            else:
                group1, group2 = groups[0], groups[1]
                pvalue = _run_two_group_test(group_values[group1], group_values[group2], test_name)
                fold_change = _fold_change(group_values[group1], group_values[group2])

            pvalue = _clean_pvalue(pvalue)
            rows.append(
                {
                    "compound": compound,
                    "fold_change": fold_change,
                    "pvalue": pvalue,
                }
            )

        adjusted = _adjust_pvalues([float(row["pvalue"]) for row in rows], correction) if rows else []
        for row, pvalue_adj in zip(rows, adjusted, strict=True):
            row["pvalue_adj"] = pvalue_adj
            row["significant"] = bool(pvalue_adj < alpha)

        out_frame = _pandas().DataFrame(
            rows,
            columns=["compound", "fold_change", "pvalue", "pvalue_adj", "significant"],
        )
        result = DataFrame(
            columns=list(out_frame.columns),
            row_count=len(out_frame),
            schema={column: str(dtype) for column, dtype in out_frame.dtypes.items()},
        )
        result._data = out_frame.reset_index(drop=True)  # type: ignore[attr-defined]
        return {"stats": Collection(items=[result], item_type=DataFrame)}


def _pandas() -> Any:
    import pandas as pd

    return pd


def _extract_single_item(payload: Collection, expected_type: type[Any], name: str) -> Any:
    if len(payload) != 1:
        raise ValueError(f"UnivariateStats: input {name!r} must contain exactly one item")
    item = payload[0]
    if not isinstance(item, expected_type):
        raise TypeError(f"UnivariateStats: input {name!r} must be {expected_type.__name__}")
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


def _run_two_group_test(group1_values: list[float], group2_values: list[float], test_name: str) -> float:
    from scipy import stats

    if test_name == "t-test":
        return float(stats.ttest_ind(group1_values, group2_values, equal_var=False, nan_policy="omit").pvalue)
    if test_name == "wilcoxon":
        return float(stats.mannwhitneyu(group1_values, group2_values, alternative="two-sided").pvalue)
    raise ValueError(f"UnivariateStats: unsupported test {test_name!r}")


def _run_anova(group_values: list[list[float]]) -> float:
    from scipy import stats

    return float(stats.f_oneway(*group_values).pvalue)


def _fold_change(group1_values: list[float], group2_values: list[float]) -> float:
    import math

    group1_mean = sum(group1_values) / len(group1_values)
    group2_mean = sum(group2_values) / len(group2_values)
    if group1_mean <= 0 or group2_mean <= 0:
        return float("nan")
    return float(math.log2(group1_mean / group2_mean))


def _adjust_pvalues(pvalues: list[float], method: str) -> list[float]:
    if method == "none":
        return pvalues
    if method == "bonferroni":
        count = len(pvalues)
        return [min(1.0, pvalue * count) for pvalue in pvalues]
    if method == "fdr":
        from statsmodels.stats.multitest import multipletests

        return [float(value) for value in multipletests(pvalues, method="fdr_bh")[1]]
    raise ValueError(f"UnivariateStats: unsupported correction {method!r}")


def _clean_pvalue(pvalue: float) -> float:
    import math

    if math.isnan(pvalue):
        return 1.0
    return pvalue
