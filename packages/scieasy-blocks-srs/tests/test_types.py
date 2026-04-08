"""T-SRS-001 test stubs — SRSImage type and Meta model.

All tests skipped pending implementation. The ``imaging_types`` fixture
from ``conftest.py`` (per standards doc §Q5) is used for cross-plugin
``Image`` access.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="T-SRS-001 impl pending — skeleton stub")


def test_srsimage_subclass_of_image(imaging_types: object) -> None:
    """SRSImage must inherit from imaging plugin's Image."""


def test_srsimage_required_axes() -> None:
    """SRSImage.required_axes == frozenset({'y','x','lambda'})."""


def test_srsimage_inherits_allowed_axes_from_image(imaging_types: object) -> None:
    """allowed_axes is inherited (not overridden)."""


def test_srsimage_canonical_order() -> None:
    """canonical_order == ('t','z','c','lambda','y','x')."""


def test_srsimage_construct_minimal() -> None:
    """3D (lambda, y, x) construction succeeds."""


def test_srsimage_construct_5d() -> None:
    """5D (t, c, lambda, y, x) construction succeeds."""


def test_srsimage_missing_lambda_raises() -> None:
    """Constructing without a lambda axis raises via Array._validate_axes."""


def test_srsimage_meta_default_none() -> None:
    """All nine SRS-specific meta fields default to None."""


def test_srsimage_meta_with_wavenumbers() -> None:
    """Meta round-trips wavenumbers_cm1 through model_dump_json."""


def test_srsimage_meta_with_digitizer_fields() -> None:
    """Meta round-trips all four digitizer_* fields."""


def test_srsimage_meta_laser_power_float() -> None:
    """laser_power stored as float (mW); future PhysicalQuantity upgrade."""


def test_srsimage_meta_with_integration_time() -> None:
    """integration_time stored as PhysicalQuantity with time units."""


def test_srsimage_meta_pump_stokes_wavelengths() -> None:
    """pump_wavelength_nm and stokes_wavelength_nm round-trip."""


def test_srsimage_with_meta_immutable_update() -> None:
    """Meta is frozen — updates produce new instances (ADR-027 D5)."""


def test_srsimage_in_type_registry_after_scan() -> None:
    """TypeRegistry.scan() resolves the full type chain to SRSImage."""
