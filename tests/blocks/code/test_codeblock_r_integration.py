"""Integration tests for ``CodeBlock(language='r')``.

Phase 11 T-TRK-013 — audit the R runner end-to-end.

These tests are guarded by ``@pytest.mark.requires_r`` and auto-skip when
``Rscript`` is not available on PATH. They exercise the real subprocess
path of :class:`scieasy.blocks.code.runners.r_runner.RRunner` via the
public :class:`scieasy.blocks.code.code_block.CodeBlock` interface.

Scope (per spec §T-TRK-013):
    1. DataFrame-like payload roundtrip: Python dict-of-columns -> R data.frame ->
       row-filtered data.frame -> parsed back on the Python side.
    2. Error propagation: an R ``stop()`` call must surface as a Python
       exception whose message contains the original R error text.

If the runner is structurally broken on a machine that does have R, these
tests will fail loudly; the failure is the audit signal and a follow-up
issue should be filed (outside this PR's scope).
"""

from __future__ import annotations

import shutil

import pytest

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.code.code_block import CodeBlock

pytestmark = pytest.mark.requires_r


_RSCRIPT_AVAILABLE = shutil.which("Rscript") is not None


def _require_rscript() -> None:
    if not _RSCRIPT_AVAILABLE:
        pytest.skip("Rscript not available on PATH; skipping R integration test")


def test_codeblock_r_dataframe_roundtrip() -> None:
    """DataFrame-like payload -> R filter -> Python, values preserved.

    The input is a dict of columns (JSON-serialisable, which is what the
    RRunner's JSON bridge expects). The R script rebuilds a data.frame,
    filters rows where ``value > 5``, and exposes the result as
    ``filtered``. We assert the returned object contains the expected
    filtered rows and nothing else.
    """
    _require_rscript()

    block = CodeBlock()
    config = BlockConfig(
        params={
            "language": "r",
            "mode": "inline",
            "script": ("df <- as.data.frame(data)\nfiltered <- df[df$value > 5, ]\nrm(df)\n"),
        }
    )
    inputs = {
        "data": {
            "id": ["a", "b", "c", "d"],
            "value": [1, 6, 3, 9],
        }
    }

    result = block.run(inputs, config)

    assert "filtered" in result, f"R runner did not return 'filtered'; got keys={list(result)}"
    filtered = result["filtered"]

    # jsonlite serialises a data.frame as either a list-of-records or a
    # dict-of-columns depending on version / auto_unbox. Normalise to a
    # dict-of-columns view before asserting.
    if isinstance(filtered, list):
        ids = [row["id"] for row in filtered]
        values = [row["value"] for row in filtered]
    elif isinstance(filtered, dict):
        ids = list(filtered["id"]) if not isinstance(filtered["id"], str) else [filtered["id"]]
        values = list(filtered["value"]) if not isinstance(filtered["value"], (int, float)) else [filtered["value"]]
    else:  # pragma: no cover - diagnostic branch for audit failure
        pytest.fail(f"Unexpected R filtered payload shape: {type(filtered).__name__} -> {filtered!r}")

    assert ids == ["b", "d"], f"Expected filtered ids ['b','d'], got {ids}"
    assert [float(v) for v in values] == [6.0, 9.0], f"Expected filtered values [6, 9], got {values}"


def test_codeblock_r_error_propagates() -> None:
    """An R ``stop()`` must surface as a Python exception with the message preserved."""
    _require_rscript()

    block = CodeBlock()
    config = BlockConfig(
        params={
            "language": "r",
            "mode": "inline",
            "script": 'stop("scieasy-r-audit: boom from R")\n',
        }
    )

    with pytest.raises(RuntimeError) as excinfo:
        block.run({}, config)

    message = str(excinfo.value)
    assert "scieasy-r-audit: boom from R" in message, f"R error message not preserved through runner; got: {message!r}"
