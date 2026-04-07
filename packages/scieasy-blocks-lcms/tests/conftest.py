"""LC-MS plugin test configuration with marker registration per §Q5/§Q7.

Markers: ``requires_r``, ``requires_elmaven``, ``requires_graphpad``.
Full marker behaviour and skip semantics land with the per-ticket
implementation PRs (T-LCMS-007, T-LCMS-019). This placeholder only
registers the marker names so pytest does not warn about unknown marks
when the plugin tests begin to use them.
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register LC-MS plugin marker names."""
    config.addinivalue_line(
        "markers",
        "requires_r: skip unless an R runtime is available (T-LCMS-007/017).",
    )
    config.addinivalue_line(
        "markers",
        "requires_elmaven: skip unless ElMAVEN is installed (T-LCMS-007).",
    )
    config.addinivalue_line(
        "markers",
        "requires_graphpad: skip unless GraphPad Prism is installed (T-LCMS-019).",
    )
