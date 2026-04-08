"""MatrixPreprocess — consolidated impute / log / scale (T-LCMS-014).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-014.

Pipeline order (locked by spec):

1. **Impute** — fill NaNs (knn / mean / zero / none).
2. **Log transform** — ``log2(x + pseudocount)`` where pseudocount =
   half the min positive value. Skipped if ``log_transform=False``.
3. **Scale** — z-score (auto), pareto, or none.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin


class MatrixPreprocess(_LCMSBlockMixin, ProcessBlock):
    """Consolidated impute / log / scale pipeline for metabolite matrices.

    See spec §9 T-LCMS-014 for the 13 acceptance criteria.
    """

    name: ClassVar[str] = "Matrix Preprocess"
    type_name: ClassVar[str] = "matrix_preprocess"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Consolidated impute → log → scale preprocessing pipeline for "
        "metabolite matrices."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="matrix",
            accepted_types=[DataFrame],
            required=True,
            description="Wide compound × sample matrix",
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

    def process_item(
        self,
        item: DataFrame,
        config: BlockConfig,
        state: Any = None,
    ) -> DataFrame:
        """Apply impute → log → scale.

        Implementation must:

        * raise :class:`ValueError` on unknown ``impute_method`` /
          ``scale`` values
        * preserve the input shape
        * use ``sklearn.impute.KNNImputer(n_neighbors=5)`` for knn
        * use ``log2(x + min_positive / 2)`` for log
        """
        raise NotImplementedError(
            "T-LCMS-014 MatrixPreprocess.process_item — impl pending "
            "(skeleton @ c08a885). See docs/specs/phase11-lcms-block-spec.md "
            "§9 T-LCMS-014."
        )
