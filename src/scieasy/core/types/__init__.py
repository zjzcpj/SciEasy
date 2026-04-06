"""DataObject type hierarchy — re-exports all base types.

Per ADR-027 D2, ``scieasy.core.types`` contains ONLY the base types.
Domain subtypes (``Image``, ``FluorImage``, ``MSImage``, ``SRSImage``,
``Spectrum``, ``RamanSpectrum``, ``MassSpectrum``, ``PeakTable``,
``MetabPeakTable``, ``AnnData``, ``SpatialData``) live in plugin
packages (``scieasy-blocks-imaging``, ``scieasy-blocks-spectral``,
``scieasy-blocks-msi``, ``scieasy-blocks-singlecell``,
``scieasy-blocks-spatial-omics``).

T-006 deleted the Array-family subclasses; T-007 deletes the remaining
Series/DataFrame/Composite domain subclasses.
"""

from __future__ import annotations

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.array import Array
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject, TypeSignature
from scieasy.core.types.collection import Collection
from scieasy.core.types.composite import CompositeData
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.registry import TypeRegistry, TypeSpec
from scieasy.core.types.series import Series
from scieasy.core.types.text import Text

__all__ = [
    "Array",
    "Artifact",
    "Collection",
    "CompositeData",
    "DataFrame",
    "DataObject",
    "Series",
    "StorageReference",
    "Text",
    "TypeRegistry",
    "TypeSignature",
    "TypeSpec",
]
