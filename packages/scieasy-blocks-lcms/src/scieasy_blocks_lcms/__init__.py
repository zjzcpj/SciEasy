"""SciEasy LC-MS plugin — Phase 11.

User-facing entry surface for ``scieasy-blocks-lcms``. Re-exports the
four LC-MS types plus public block classes across the sub-packages
(``io``, ``external``, ``isotope_tracing``).
"""

from __future__ import annotations

from scieasy.blocks.base.package_info import PackageInfo
from scieasy_blocks_lcms.external import AccuCorR, ElMAVENBlock
from scieasy_blocks_lcms.io import (
    LoadMIDTable,
    LoadMSRawFiles,
    LoadPeakTable,
    LoadSampleMetadata,
    SaveTable,
)
from scieasy_blocks_lcms.isotope_tracing import (
    FluxEstimate,
    PoolSizeNormalize,
)
from scieasy_blocks_lcms.types import (
    MIDTable,
    MSRawFile,
    PeakTable,
    SampleMetadata,
    get_types,
)

__version__ = "0.1.0.dev0"

_LCMS_BLOCKS: tuple[type, ...] = (
    # IO
    LoadMSRawFiles,
    LoadPeakTable,
    LoadMIDTable,
    LoadSampleMetadata,
    SaveTable,
    # External
    ElMAVENBlock,
    AccuCorR,
    # Isotope tracing
    FluxEstimate,
    PoolSizeNormalize,
)


def get_package_info() -> PackageInfo:
    """Return package metadata for the ``scieasy.blocks`` registry."""
    return PackageInfo(
        name="scieasy-blocks-lcms",
        description="LC-MS / stable-isotope tracing blocks for SciEasy workflows.",
        author="SciEasy Contributors",
        version=__version__,
    )


def get_blocks() -> list[type]:
    """Return the LC-MS plugin's exported concrete block classes."""
    return list(_LCMS_BLOCKS)


def get_block_package() -> tuple[PackageInfo, list[type]]:
    """Return package metadata and block classes for ``scieasy.blocks``."""
    return get_package_info(), get_blocks()


__all__ = [
    "AccuCorR",
    "ElMAVENBlock",
    "FluxEstimate",
    "LoadMIDTable",
    "LoadMSRawFiles",
    "LoadPeakTable",
    "LoadSampleMetadata",
    "MIDTable",
    "MSRawFile",
    "PeakTable",
    "PoolSizeNormalize",
    "SampleMetadata",
    "SaveTable",
    "get_block_package",
    "get_blocks",
    "get_package_info",
    "get_types",
]
