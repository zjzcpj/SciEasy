"""Example multi-block package for SciEasy.

This package demonstrates the Tier 2 distribution pattern:
- PackageInfo metadata
- get_blocks() / get_types() / get_block_package() callables
- scieasy.blocks and scieasy.types entry-points in pyproject.toml
"""

from __future__ import annotations

from my_blocks.blocks.gaussian_blur import GaussianBlur
from my_blocks.blocks.threshold import SimpleThreshold
from my_blocks.types.custom_image import AnalysisImage
from scieasy.blocks.base.package_info import PackageInfo

__version__ = "0.1.0"

_TYPES: tuple[type, ...] = (AnalysisImage,)
_BLOCKS: tuple[type, ...] = (GaussianBlur, SimpleThreshold)


def get_package_info() -> PackageInfo:
    """Return package metadata for the scieasy.blocks registry."""
    return PackageInfo(
        name="scieasy-blocks-example",
        description="Example blocks for the Block Developer SDK guide.",
        author="SciEasy Contributors",
        version=__version__,
    )


def get_types() -> list[type]:
    """Return exported type classes for the scieasy.types entry-point."""
    return list(_TYPES)


def get_blocks() -> list[type]:
    """Return exported block classes."""
    return list(_BLOCKS)


def get_block_package() -> tuple[PackageInfo, list[type]]:
    """Return package metadata and blocks for the scieasy.blocks entry-point."""
    return get_package_info(), get_blocks()
