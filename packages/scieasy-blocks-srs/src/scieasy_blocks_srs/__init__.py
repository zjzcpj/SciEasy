"""SciEasy SRS plugin exports."""

from __future__ import annotations

from scieasy.blocks.base.package_info import PackageInfo
from scieasy_blocks_srs.component_analysis import (
    SRSICA,
    SRSPCA,
    SRSVCA,
    SRSKMeansCluster,
    SRSUnmix,
)
from scieasy_blocks_srs.preprocess import SRSBaseline, SRSCalibrate, SRSSpectralDenoise
from scieasy_blocks_srs.spectral_extraction.extract_spectrum import ExtractSpectrum
from scieasy_blocks_srs.types import SRSImage, get_types

__version__ = "0.1.0.dev0"

_SRS_BLOCKS: tuple[type, ...] = (
    # Preprocess
    SRSSpectralDenoise,
    SRSBaseline,
    SRSCalibrate,
    # Component analysis
    SRSPCA,
    SRSICA,
    SRSVCA,
    SRSUnmix,
    SRSKMeansCluster,
    # Spectral extraction
    ExtractSpectrum,
)


def get_package_info() -> PackageInfo:
    """Return package metadata for the ``scieasy.blocks`` registry."""
    return PackageInfo(
        name="scieasy-blocks-srs",
        description="SRS (Stimulated Raman Scattering) blocks for SciEasy workflows.",
        author="SciEasy Contributors",
        version=__version__,
    )


def get_blocks() -> list[type]:
    """Return the SRS plugin's exported concrete block classes."""
    return list(_SRS_BLOCKS)


def get_block_package() -> tuple[PackageInfo, list[type]]:
    """Return package metadata and block classes for ``scieasy.blocks``."""
    return get_package_info(), get_blocks()


__all__ = [
    "SRSICA",
    "SRSPCA",
    "SRSVCA",
    "ExtractSpectrum",
    "SRSBaseline",
    "SRSCalibrate",
    "SRSImage",
    "SRSKMeansCluster",
    "SRSSpectralDenoise",
    "SRSUnmix",
    "get_block_package",
    "get_blocks",
    "get_package_info",
    "get_types",
]
