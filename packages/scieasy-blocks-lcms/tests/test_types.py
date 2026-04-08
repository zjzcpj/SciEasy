"""Test stub for T-LCMS-002 — types module (skeleton @ c08a885).

Real assertions are added by the T-LCMS-002 implementation agent.
This stub only verifies that the four type classes import without
error and registers the test names listed in the spec so the impl
agent has a clear target list.
"""

import pytest

# Import smoke-check (must succeed at collection time).
from scieasy_blocks_lcms.types import MIDTable, MSRawFile, PeakTable, SampleMetadata


@pytest.mark.parametrize(
    "test_name",
    [
        "test_msrawfile_subclass_of_artifact",
        "test_msrawfile_meta_frozen",
        "test_msrawfile_meta_required_format",
        "test_peaktable_subclass_of_dataframe",
        "test_midtable_subclass_of_dataframe",
        "test_midtable_meta_tracer_atoms_required",
        "test_samplemetadata_subclass_of_dataframe",
        "test_get_types_returns_all_four_classes",
    ],
)
def test_t_lcms_002_pending(test_name: str) -> None:
    """Spec-listed cases skipped pending T-LCMS-002 impl."""
    assert MSRawFile and PeakTable and MIDTable and SampleMetadata
    pytest.skip(f"T-LCMS-002 {test_name} — impl pending (skeleton @ c08a885)")
