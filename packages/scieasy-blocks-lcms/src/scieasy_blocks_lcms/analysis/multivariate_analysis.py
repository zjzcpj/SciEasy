"""MultivariateAnalysis - PCA / PLSDA / OPLSDA (T-LCMS-016)."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, ClassVar, cast

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import SampleMetadata


class MultivariateAnalysis(_LCMSBlockMixin, ProcessBlock):
    """Consolidated PCA / PLSDA / OPLSDA with scores, loadings, and scatter plot."""

    name: ClassVar[str] = "Multivariate Analysis"
    type_name: ClassVar[str] = "multivariate_analysis"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "PCA / PLSDA / OPLSDA on a metabolite matrix. Outputs scores "
        "DataFrame, loadings DataFrame, and a PNG scatter-plot Artifact."
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
            required=False,
            description="Required for PLSDA / OPLSDA (group response)",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="scores",
            accepted_types=[DataFrame],
            description="Component scores per sample",
        ),
        OutputPort(
            name="loadings",
            accepted_types=[DataFrame],
            description="Component loadings per compound",
        ),
        OutputPort(
            name="plot",
            accepted_types=[Artifact],
            description="PNG scatter plot of the first two components",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["PCA", "PLSDA", "OPLSDA"],
                "default": "PCA",
                "title": "Method",
                "ui_priority": 1,
            },
            "n_components": {
                "type": "integer",
                "default": 2,
                "title": "Number of components",
                "ui_priority": 2,
            },
            "scale": {
                "type": "boolean",
                "default": True,
                "title": "StandardScaler before fit",
                "ui_priority": 3,
            },
            "group_column": {
                "type": ["string", "null"],
                "default": None,
                "title": "Group column (required for PLSDA / OPLSDA)",
                "ui_priority": 4,
            },
        },
    }

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        matrix_item = _extract_single_item(inputs["matrix"], DataFrame, "matrix")
        matrix_frame = _as_pandas_frame(matrix_item).astype(float)

        method = str(config.get("method", "PCA"))
        n_components = max(1, int(config.get("n_components", 2)))
        scale = bool(config.get("scale", True))
        group_column = config.get("group_column")

        metadata_frame = None
        sample_order = [str(column) for column in matrix_frame.columns]
        group_values = None
        if method in {"PLSDA", "OPLSDA"}:
            metadata_payload = inputs.get("sample_metadata")
            if metadata_payload is None or group_column in {None, ""}:
                raise ValueError(
                    "MultivariateAnalysis: sample_metadata and group_column are required for PLSDA / OPLSDA"
                )
            sample_metadata_item = _extract_single_item(metadata_payload, SampleMetadata, "sample_metadata")
            metadata_frame = _as_pandas_frame(sample_metadata_item)
            metadata_meta = cast(SampleMetadata.Meta, sample_metadata_item.meta)
            if metadata_meta.sample_id_column not in metadata_frame.columns:
                raise ValueError(
                    f"MultivariateAnalysis: sample id column {metadata_meta.sample_id_column!r} is missing"
                )
            group_column_name = str(group_column)
            if group_column_name not in metadata_frame.columns:
                raise ValueError(f"MultivariateAnalysis: group column {group_column_name!r} is missing")
            sample_order = [
                str(sample_id)
                for sample_id in metadata_frame[metadata_meta.sample_id_column].tolist()
                if sample_id in matrix_frame.columns
            ]
            if len(sample_order) < 2:
                raise ValueError("MultivariateAnalysis: at least two shared samples are required")
            group_values = metadata_frame.set_index(metadata_meta.sample_id_column).loc[sample_order, group_column_name]

        compound_names = [str(compound) for compound in matrix_frame.index]
        x_frame = matrix_frame.loc[:, sample_order].T
        x_values = _scale_matrix(x_frame, scale)

        if method == "PCA":
            scores_array, loadings_array = _run_pca(x_values, n_components)
        elif method == "PLSDA":
            assert group_values is not None
            scores_array, loadings_array = _run_plsda(x_values, group_values, n_components)
        elif method == "OPLSDA":
            if metadata_frame is None or group_values is None:
                raise ValueError("MultivariateAnalysis: sample_metadata and group_column are required for OPLSDA")
            raise NotImplementedError("MultivariateAnalysis: OPLSDA is deferred to a follow-up ticket")
        else:
            raise ValueError(f"MultivariateAnalysis: unsupported method {method!r}")

        component_names = [f"component_{index + 1}" for index in range(scores_array.shape[1])]
        pd = _pandas()
        scores_frame = pd.DataFrame(scores_array, index=sample_order, columns=component_names).reset_index(
            names="sample_id"
        )
        loadings_frame = pd.DataFrame(
            loadings_array,
            index=compound_names,
            columns=component_names,
        ).reset_index(names="compound")
        plot_path = _save_plot(scores_frame, group_values, component_names)

        scores_result = DataFrame(
            columns=list(scores_frame.columns),
            row_count=len(scores_frame),
            schema={column: str(dtype) for column, dtype in scores_frame.dtypes.items()},
        )
        scores_result._data = scores_frame.copy()  # type: ignore[attr-defined]
        loadings_result = DataFrame(
            columns=list(loadings_frame.columns),
            row_count=len(loadings_frame),
            schema={column: str(dtype) for column, dtype in loadings_frame.dtypes.items()},
        )
        loadings_result._data = loadings_frame.copy()  # type: ignore[attr-defined]
        plot_result = Artifact(
            file_path=plot_path,
            mime_type="image/png",
            description="Multivariate analysis scatter plot",
        )

        return {
            "scores": Collection(items=[scores_result], item_type=DataFrame),
            "loadings": Collection(items=[loadings_result], item_type=DataFrame),
            "plot": Collection(items=[plot_result], item_type=Artifact),
        }


def _pandas() -> Any:
    import pandas as pd

    return pd


def _extract_single_item(payload: Collection, expected_type: type[Any], name: str) -> Any:
    if len(payload) != 1:
        raise ValueError(f"MultivariateAnalysis: input {name!r} must contain exactly one item")
    item = payload[0]
    if not isinstance(item, expected_type):
        raise TypeError(f"MultivariateAnalysis: input {name!r} must be {expected_type.__name__}")
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


def _scale_matrix(frame: Any, scale: bool) -> Any:
    if not scale:
        return frame.copy()
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    values = scaler.fit_transform(frame)
    pd = _pandas()
    return pd.DataFrame(values, index=frame.index, columns=frame.columns)


def _run_pca(frame: Any, n_components: int) -> tuple[Any, Any]:
    from sklearn.decomposition import PCA

    effective_n_components = min(n_components, frame.shape[0], frame.shape[1])
    model = PCA(n_components=effective_n_components)
    scores_array = model.fit_transform(frame)
    loadings_array = model.components_.T
    return scores_array, loadings_array


def _run_plsda(frame: Any, groups: Any, n_components: int) -> tuple[Any, Any]:
    from sklearn.cross_decomposition import PLSRegression

    pd = _pandas()
    response = pd.get_dummies(groups, drop_first=False)
    effective_n_components = min(n_components, frame.shape[0], frame.shape[1], response.shape[1])
    model = PLSRegression(n_components=effective_n_components, scale=False)
    model.fit(frame, response.to_numpy())
    scores_array = model.x_scores_
    loadings_array = model.x_loadings_
    return scores_array, loadings_array


def _save_plot(scores_frame: Any, group_values: Any, component_names: list[str]) -> Path:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4))
    if len(component_names) == 1:
        x_values = scores_frame[component_names[0]]
        y_values = [0.0] * len(scores_frame)
    else:
        x_values = scores_frame[component_names[0]]
        y_values = scores_frame[component_names[1]]

    if group_values is None:
        ax.scatter(x_values, y_values, color="tab:blue")
    else:
        pd = _pandas()
        groups = pd.Series(group_values).reset_index(drop=True)
        unique_groups = groups.dropna().drop_duplicates().tolist()
        palette = plt.get_cmap("tab10")
        for index, group in enumerate(unique_groups):
            mask = groups == group
            ax.scatter(x_values[mask], y_values[mask], label=str(group), color=palette(index % 10))
        if unique_groups:
            ax.legend()

    ax.set_xlabel(component_names[0])
    ax.set_ylabel(component_names[1] if len(component_names) > 1 else "component_2")
    ax.set_title("Multivariate analysis")
    with NamedTemporaryFile(delete=False, suffix=".png") as handle:
        path = Path(handle.name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
