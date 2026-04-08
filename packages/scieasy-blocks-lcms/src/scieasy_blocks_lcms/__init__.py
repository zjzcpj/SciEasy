"""SciEasy LC-MS plugin — Phase 11 skeleton (skeleton @ c08a885).

User-facing entry surface for ``scieasy-blocks-lcms``. Re-exports the
four LC-MS types defined in T-LCMS-002 plus the public block classes
across the four sub-packages (``io``, ``external``,
``isotope_tracing``, ``analysis``). Per master plan §2.4 the LC-MS
plugin's USP is stable-isotope tracing — the ``isotope_tracing``
sub-package is the flagship surface.

Block classes are imported lazily-by-name only to surface them in
``__all__``; entry-point registration into the BlockRegistry is the
responsibility of the T-LCMS-021 impl agent (it edits
``pyproject.toml`` ``[project.entry-points."scieasy.blocks"]``).
"""

from scieasy_blocks_lcms.types import (
    MIDTable,
    MSRawFile,
    PeakTable,
    SampleMetadata,
    get_types,
)

__all__ = [
    "MIDTable",
    "MSRawFile",
    "PeakTable",
    "SampleMetadata",
    "get_types",
]
