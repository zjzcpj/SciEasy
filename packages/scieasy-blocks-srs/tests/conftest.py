"""SRS plugin test configuration with cross-plugin ``imaging_types`` fixture per §Q5."""

import pytest


@pytest.fixture(scope="session")
def imaging_types():
    """Session-scoped fixture that imports the imaging plugin or skips.

    Per ``docs/specs/phase11-implementation-standards.md`` §Q5, this is the
    only sanctioned way to import imaging-plugin types from SRS tests.
    Callers access ``imaging_types.Image``, ``imaging_types.Mask``, etc.
    """
    imaging = pytest.importorskip("scieasy_blocks_imaging")
    return imaging
