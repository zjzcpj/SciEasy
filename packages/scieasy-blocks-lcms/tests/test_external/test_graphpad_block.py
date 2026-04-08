"""Test stub for T-LCMS-019 — GraphPadBlock (skeleton @ c08a885)."""

import pytest

from scieasy_blocks_lcms.external.graphpad_block import GraphPadBlock


def test_t_lcms_019_graphpad_pending() -> None:
    assert GraphPadBlock is not None
    pytest.skip("T-LCMS-019 GraphPadBlock — impl pending (skeleton @ c08a885)")


@pytest.mark.requires_graphpad
def test_t_lcms_019_graphpad_end_to_end_pending() -> None:
    pytest.skip(
        "T-LCMS-019 GraphPadBlock end-to-end — impl pending (skeleton @ c08a885)"
    )
