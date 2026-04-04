"""DataObject type hierarchy — re-exports all base and domain types."""

from __future__ import annotations

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.array import Array, FluorImage, Image, MSImage, SRSImage
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject, TypeSignature
from scieasy.core.types.collection import Collection
from scieasy.core.types.composite import AnnData, CompositeData, SpatialData
from scieasy.core.types.dataframe import DataFrame, MetabPeakTable, PeakTable
from scieasy.core.types.registry import TypeRegistry, TypeSpec
from scieasy.core.types.series import MassSpectrum, RamanSpectrum, Series, Spectrum
from scieasy.core.types.text import Text

__all__ = [
    "AnnData",
    "Array",
    "Artifact",
    "Collection",
    "CompositeData",
    "DataFrame",
    "DataObject",
    "FluorImage",
    "Image",
    "MSImage",
    "MassSpectrum",
    "MetabPeakTable",
    "PeakTable",
    "RamanSpectrum",
    "SRSImage",
    "Series",
    "SpatialData",
    "Spectrum",
    "StorageReference",
    "Text",
    "TypeRegistry",
    "TypeSignature",
    "TypeSpec",
]
