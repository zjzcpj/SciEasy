"""UnivariateStats — per-metabolite t-test / ANOVA / Wilcoxon (T-LCMS-015).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-015.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import SampleMetadata


class UnivariateStats(_LCMSBlockMixin, ProcessBlock):
    """Per-metabolite univariate statistics with multiple-testing correction.

    See spec §9 T-LCMS-015 for the 12 acceptance criteria.
    """

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
            description="Wide compound × sample matrix",
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

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Run the per-metabolite univariate test.

        Implementation must:

        * raise :class:`ValueError` for ``t-test`` with !=2 groups
        * raise :class:`ValueError` for ``anova`` with <2 groups
        * raise :class:`ValueError` for ``wilcoxon`` with !=2 groups
        * compute ``fold_change = log2(g1_mean / g2_mean)`` for 2-group
          tests; ``NaN`` for ANOVA
        * apply Bonferroni / FDR correction
        """
        raise NotImplementedError(
            "T-LCMS-015 UnivariateStats.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-015."
        )
