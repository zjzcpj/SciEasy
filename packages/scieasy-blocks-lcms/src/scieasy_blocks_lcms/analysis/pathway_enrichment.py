"""PathwayEnrichment — KEGG REST pathway enrichment (T-LCMS-017).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-017.

Per §8 Q-6 the default implementation is **Python-native** via the
KEGG REST API — no R dependency. A future ticket may add an
``"HMDB"`` or ``"MetaboAnalystR"`` backend behind the same
``database`` enum.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin


class PathwayEnrichment(_LCMSBlockMixin, ProcessBlock):
    """Pathway enrichment via KEGG REST + Fisher's exact test.

    See spec §9 T-LCMS-017 for the 11 acceptance criteria.
    """

    name: ClassVar[str] = "Pathway Enrichment"
    type_name: ClassVar[str] = "pathway_enrichment"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Pathway enrichment analysis via KEGG REST and Fisher's exact "
        "test, with FDR correction. Python-native; no R dependency."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="compounds",
            accepted_types=[DataFrame],
            required=True,
            description="DataFrame with a compound column to test for enrichment",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="enrichment",
            accepted_types=[DataFrame],
            description="Long-format pathway enrichment results",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "database": {
                "type": "string",
                "enum": ["KEGG"],
                "default": "KEGG",
                "title": "Database backend",
                "ui_priority": 1,
            },
            "organism": {
                "type": "string",
                "default": "hsa",
                "title": "KEGG organism code (e.g. hsa, mmu, eco)",
                "ui_priority": 2,
            },
            "pvalue_cutoff": {
                "type": "number",
                "default": 0.05,
                "title": "Adjusted p-value cutoff",
                "ui_priority": 3,
            },
            "compound_column": {
                "type": "string",
                "default": "compound",
                "title": "Compound column name",
                "ui_priority": 4,
            },
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Query KEGG, run Fisher's exact tests, return enrichment table.

        Implementation must:

        * use :mod:`requests` to call KEGG REST endpoints
        * cache responses in a process-local dict keyed by
          ``(endpoint, organism)``
        * sleep 100 ms between requests (KEGG rate limit ~10 req/s)
        * compute Fisher's exact test via ``scipy.stats.fisher_exact``
        * apply FDR correction via
          ``statsmodels.stats.multitest.multipletests``
        """
        raise NotImplementedError(
            "T-LCMS-017 PathwayEnrichment.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-017."
        )
