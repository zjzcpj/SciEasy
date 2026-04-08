"""CompareGroupMID — per-isotopologue group statistics (T-LCMS-010).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-010.

Compares MID values between two sample groups using a per-isotopologue
t-test, Wilcoxon, or Mann-Whitney test, with optional Bonferroni / FDR
multiple-testing correction. >2 groups raise
:class:`NotImplementedError` pointing at :class:`UnivariateStats`
(T-LCMS-015) which supports ANOVA.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable, SampleMetadata


class CompareGroupMID(_LCMSBlockMixin, ProcessBlock):
    """Per-isotopologue statistical comparison of MID values between groups.

    See spec §9 T-LCMS-010 for the 12 acceptance criteria.
    """

    name: ClassVar[str] = "Compare Group MID"
    type_name: ClassVar[str] = "compare_group_mid"
    category: ClassVar[str] = "process"
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
        """Run the per-isotopologue group comparison.

        Implementation must:

        * raise :class:`ValueError` on missing ``group_column``
        * raise :class:`ValueError` on a single group
        * raise :class:`NotImplementedError` on >2 groups (with a
          pointer to :class:`UnivariateStats` for ANOVA)
        * dispatch to ``scipy.stats.ttest_ind`` /
          ``scipy.stats.wilcoxon`` / ``scipy.stats.mannwhitneyu``
        * apply Bonferroni or FDR correction
          (``statsmodels.stats.multitest.multipletests``)
        * emit a long-format DataFrame with the columns documented in
          spec §9 T-LCMS-010
        """
        raise NotImplementedError(
            "T-LCMS-010 CompareGroupMID.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-010."
        )
