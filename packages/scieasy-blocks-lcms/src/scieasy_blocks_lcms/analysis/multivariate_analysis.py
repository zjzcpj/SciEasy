"""MultivariateAnalysis — PCA / PLSDA / OPLSDA (T-LCMS-016).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-016.

Three methods consolidated into one block via a ``method`` config
param. PLSDA / OPLSDA require :class:`SampleMetadata` with a
``group_column``. OPLSDA may be deferred to a follow-up ticket per
spec — in which case it raises :class:`NotImplementedError` with a
pointer.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import SampleMetadata


class MultivariateAnalysis(_LCMSBlockMixin, ProcessBlock):
    """Consolidated PCA / PLSDA / OPLSDA with scores, loadings, and scatter plot.

    See spec §9 T-LCMS-016 for the 12 acceptance criteria.
    """

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
            description="Wide compound × sample matrix",
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

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Fit the chosen multivariate model and emit scores / loadings / plot.

        Implementation must:

        * dispatch on ``method``: PCA → ``sklearn.decomposition.PCA``,
          PLSDA → ``sklearn.cross_decomposition.PLSRegression``,
          OPLSDA → Trygg-Wold algorithm or
          :class:`NotImplementedError` with follow-up pointer
        * raise :class:`ValueError` for PLSDA / OPLSDA without
          ``sample_metadata`` + ``group_column``
        * raise :class:`ValueError` on unknown ``method``
        * save the scatter plot via ``matplotlib.pyplot.savefig``
        """
        raise NotImplementedError(
            "T-LCMS-016 MultivariateAnalysis.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-016."
        )
