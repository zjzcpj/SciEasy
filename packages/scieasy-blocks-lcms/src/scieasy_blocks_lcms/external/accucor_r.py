"""AccuCorR — CodeBlock R runner for the AccuCor natural-abundance corrector.

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-007 (part 2).

Wraps the bundled ``scripts/accucor.R`` driver via :class:`CodeBlock`'s
R runner (``language="r"``, ``mode="script"``). The R script body is
itself a placeholder under ``external/scripts/accucor.R``; the impl
agent replaces it with the user's vetted AccuCor wrapper script.

Per spec §8 Q-1 the AccuCor R package is a runtime dependency installed
by the user (no auto-install) and the script communicates with the
SciEasy R runner via the standard ``inputs`` / ``params`` /
``result`` contract documented in T-TRK-013.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.code.code_block import CodeBlock
from scieasy.core.types.collection import Collection
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable, PeakTable, SampleMetadata


class AccuCorR(_LCMSBlockMixin, CodeBlock):
    """Run AccuCor's natural-abundance correction on a peak table.

    See spec §9 T-LCMS-007 for the 9 acceptance criteria. The bundled
    R script lives at
    ``scieasy_blocks_lcms.external.scripts.accucor`` and is resolved
    at run-time via :func:`_resolve_script_path`.
    """

    name: ClassVar[str] = "AccuCor (R)"
    type_name: ClassVar[str] = "accucor_r"
    category: ClassVar[str] = "external"
    description: ClassVar[str] = (
        "Run the AccuCor R package on a PeakTable to apply natural abundance correction and emit a typed MIDTable."
    )

    language: ClassVar[str] = "r"
    mode: ClassVar[str] = "script"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="peak_table",
            accepted_types=[PeakTable],
            required=True,
            description="Peak table from ElMAVEN (or compatible source)",
        ),
        InputPort(
            name="sample_metadata",
            accepted_types=[SampleMetadata],
            required=True,
            description="Per-sample metadata (group, label, etc.)",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="mid_table",
            accepted_types=[MIDTable],
            description="Natural-abundance-corrected MID table",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "tracer_formula": {
                "type": "string",
                "default": "C13",
                "title": "Tracer formula",
                "ui_priority": 1,
            },
            "resolution": {
                "type": "integer",
                "default": 120000,
                "title": "Mass spec resolution",
                "ui_priority": 2,
            },
            "accucor_script_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "Override path to AccuCor R script (advanced)",
                "ui_priority": 3,
                "ui_widget": "file_browser",
            },
        },
    }

    def _resolve_script_path(self, config: BlockConfig) -> str:
        """Return the absolute path to the AccuCor R script.

        Honours the ``accucor_script_path`` config override; otherwise
        falls back to the bundled ``external/scripts/accucor.R``
        loaded via :mod:`importlib.resources`.

        Skeleton body raises ``NotImplementedError``; the impl agent
        wires up the actual ``importlib.resources.as_file`` lookup.
        """
        raise NotImplementedError(
            "T-LCMS-007 AccuCorR._resolve_script_path — impl pending "
            "(skeleton @ c08a885). See docs/specs/phase11-lcms-block-spec.md "
            "§9 T-LCMS-007."
        )

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Patch ``script_path`` / ``entry_function`` and delegate.

        Implementation must:

        * call :meth:`_resolve_script_path` and write the result into
          a copy of ``config`` under the ``script_path`` key
        * set ``entry_function="run_accucor"``
        * default ``language="r"`` and ``mode="script"``
        * delegate to :meth:`CodeBlock.run`
        * wrap the resulting CSV path in a :class:`MIDTable` with the
          appropriate ``Meta`` (``corrected=True``,
          ``correction_tool="AccuCor"``, ``tracer_atoms`` from config)
        """
        # Resolve bundled script path eagerly so the impl agent has a
        # known anchor for the importlib.resources call.
        _bundled_script = Path(__file__).parent / "scripts" / "accucor.R"
        del _bundled_script  # silence linter for the skeleton stub
        raise NotImplementedError(
            "T-LCMS-007 AccuCorR.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-007."
        )
