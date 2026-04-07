"""DataObject type hierarchy — re-exports all base types.

Per ADR-027 D2, ``scieasy.core.types`` contains ONLY the base types.
Domain subtypes (``Image``, ``FluorImage``, ``MSImage``, ``SRSImage``,
``Spectrum``, ``RamanSpectrum``, etc.) live in plugin packages
(``scieasy-blocks-imaging``, ``scieasy-blocks-spectral``,
``scieasy-blocks-msi``, ...). T-006 deleted the Array-family subclasses;
T-007 will audit the remaining five base-class modules for stray
domain subtypes.
"""

from __future__ import annotations

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.array import Array
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
    "MassSpectrum",
    "MetabPeakTable",
    "PeakTable",
    "RamanSpectrum",
    "Series",
    "SpatialData",
    "Spectrum",
    "StorageReference",
    "Text",
    "TypeRegistry",
    "TypeSignature",
    "TypeSpec",
]
