"""MatrixPreprocess - consolidated impute / log / scale (T-LCMS-014)."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin


class MatrixPreprocess(_LCMSBlockMixin, ProcessBlock):
    """Consolidated impute / log / scale pipeline for metabolite matrices."""

    name: ClassVar[str] = "Matrix Preprocess"
    type_name: ClassVar[str] = "matrix_preprocess"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = "Consolidated impute -> log -> scale preprocessing pipeline for metabolite matrices."

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="matrix",
            accepted_types=[DataFrame],
            required=True,
            description="Wide compound x sample matrix",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="processed",
            accepted_types=[DataFrame],
            description="Preprocessed matrix (same shape as input)",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "log_transform": {
                "type": "boolean",
                "default": True,
                "title": "Log2 transform",
                "ui_priority": 1,
            },
            "impute_method": {
                "type": "string",
                "enum": ["knn", "mean", "zero", "none"],
                "default": "knn",
                "title": "Imputation method",
                "ui_priority": 2,
            },
            "scale": {
                "type": "string",
                "enum": ["auto", "pareto", "none"],
                "default": "auto",
                "title": "Scaling method",
                "ui_priority": 3,
            },
        },
    }

    def process_item(self, item: DataFrame, config: BlockConfig, state: Any = None) -> DataFrame:
        frame = _as_pandas_frame(item).astype(float)

        frame = _impute(frame, str(config.get("impute_method", "knn")))

        if bool(config.get("log_transform", True)):
            frame = _log_transform(frame)

        frame = _scale(frame, str(config.get("scale", "auto")))

        result = DataFrame(
            columns=list(frame.columns),
            row_count=len(frame),
            schema={column: str(dtype) for column, dtype in frame.dtypes.items()},
        )
        result._data = frame.copy()  # type: ignore[attr-defined]
        return result


def _pandas() -> Any:
    import pandas as pd

    return pd


def _numpy() -> Any:
    import numpy as np

    return np


def _as_pandas_frame(item: DataFrame) -> Any:
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


def _impute(frame: Any, method: str) -> Any:
    pd = _pandas()
    if method == "none":
        return frame.copy()
    if method == "zero":
        return frame.fillna(0.0)
    if method == "mean":
        means = frame.mean(axis=1)
        return frame.T.fillna(means).T
    if method == "knn":
        from sklearn.impute import KNNImputer

        imputer = KNNImputer(n_neighbors=5)
        imputed = imputer.fit_transform(frame.T)
        return pd.DataFrame(imputed, index=frame.T.index, columns=frame.T.columns).T
    raise ValueError(f"MatrixPreprocess: unsupported impute_method {method!r}")


def _log_transform(frame: Any) -> Any:
    np = _numpy()
    values = frame.to_numpy(dtype=float)
    positive = values[np.isfinite(values) & (values > 0)]
    pseudocount = float(positive.min() / 2.0) if positive.size else 0.5
    return np.log2(frame + pseudocount)


def _scale(frame: Any, scale: str) -> Any:
    np = _numpy()
    if scale == "none":
        return frame.copy()
    centred = frame.sub(frame.mean(axis=1), axis=0)
    if scale == "auto":
        denom = frame.std(axis=1, ddof=0).replace(0.0, np.nan)
        return centred.div(denom, axis=0).fillna(0.0)
    if scale == "pareto":
        denom = frame.std(axis=1, ddof=0).pow(0.5).replace(0.0, np.nan)
        return centred.div(denom, axis=0).fillna(0.0)
    raise ValueError(f"MatrixPreprocess: unsupported scale {scale!r}")
