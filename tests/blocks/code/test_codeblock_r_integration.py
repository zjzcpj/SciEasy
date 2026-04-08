"""Integration audit for ``CodeBlock(language="r")`` — T-TRK-013 v2.

These tests exercise the real :class:`RRunner` subprocess path end-to-end.
They follow the canonical spec pattern from
``docs/specs/phase11-implementation-standards.md`` §9.1 T-TRK-013 §h:

    block = CodeBlock(language="r", script=...)
    result = block.run(inputs={"data": df}, config=...)

where ``df`` is a real :class:`pandas.DataFrame`. This contract is
LOAD-BEARING and must NOT be relaxed to a dict-of-columns or any other
workaround payload — see issue #341 (v2 rationale) and master plan §5
red flag #4 (scope argument shrinkage).

NOTE: ``test_codeblock_r_dataframe_roundtrip`` may currently FAIL on
machines that have ``Rscript`` installed because of the RRunner JSON
bridge limitation tracked in issue #342: ``RRunner.execute_inline``
serialises its namespace via ``json.dumps(namespace, default=str)``,
which stringifies any pandas.DataFrame to its ``str(df)`` repr instead
of a jsonlite-parseable structure. The failure IS the audit signal —
T-TRK-013 was spawned to discover and document this exact class of
runner bugs. Do NOT work around the failure in this test. The runner
fix lives in a separate PR that closes #342.

Both tests are gated by ``@pytest.mark.requires_r`` plus a
``shutil.which("Rscript")`` skip guard so CI (which has no R toolchain)
stays green.
"""

from __future__ import annotations

import shutil

import pytest

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.code.code_block import CodeBlock

pd = pytest.importorskip("pandas")

pytestmark = pytest.mark.requires_r


_RSCRIPT_AVAILABLE = shutil.which("Rscript") is not None
_SKIP_REASON = "Rscript not on PATH; R runner integration audit skipped"


_FILTER_SCRIPT = """
# Filter rows where value > 5 and return as a data.frame.
data <- as.data.frame(data)
filtered <- data[data$value > 5, ]
"""


_ERROR_SCRIPT = """
stop("scieasy-r-audit: boom from R")
"""


@pytest.mark.skipif(not _RSCRIPT_AVAILABLE, reason=_SKIP_REASON)
def test_codeblock_r_dataframe_roundtrip() -> None:
    """A pandas.DataFrame round-trips through a real R filter script.

    Spec §9.1 T-TRK-013 §h canonical contract:
        block = CodeBlock(language="r", script=...)
        result = block.run(inputs={"data": df}, config=...)
    where ``df`` is :class:`pandas.DataFrame` (NOT a dict-of-columns).

    Asserts the returned ``filtered`` object describes the two rows whose
    ``value`` column exceeds 5 (``id in {"b", "d"}``, ``value in {6, 9}``).

    If the runner cannot serialise pandas.DataFrame (issue #342), this
    test fails with a clear diagnostic — that failure is the audit signal.
    Do NOT relax the contract to make it pass.
    """
    df = pd.DataFrame({"id": ["a", "b", "c", "d"], "value": [1, 6, 3, 9]})
    assert isinstance(df, pd.DataFrame)  # contract assertion: input MUST be pd.DataFrame

    block = CodeBlock()
    config = BlockConfig(params={"language": "r", "mode": "inline", "script": _FILTER_SCRIPT})

    result = block.run({"data": df}, config)

    assert "filtered" in result, f"R runner did not return 'filtered'; got keys={list(result)!r}"
    filtered = result["filtered"]

    # jsonlite may surface the data.frame as a list-of-records or a
    # dict-of-columns, depending on auto_unbox behaviour. Accept either
    # shape on the OUTPUT side, but the INPUT side stays strict pd.DataFrame.
    if isinstance(filtered, dict):
        ids_raw = filtered["id"]
        values_raw = filtered["value"]
        ids = list(ids_raw) if not isinstance(ids_raw, str) else [ids_raw]
        values = list(values_raw) if not isinstance(values_raw, (int, float)) else [values_raw]
    elif isinstance(filtered, list):
        ids = [row["id"] for row in filtered]
        values = [row["value"] for row in filtered]
    else:
        raise AssertionError(
            f"Unexpected filtered shape from RRunner: type={type(filtered).__name__!r} value={filtered!r}"
        )

    assert ids == ["b", "d"], f"expected ids ['b','d'], got {ids!r}"
    assert [int(v) for v in values] == [6, 9], f"expected values [6,9], got {values!r}"


@pytest.mark.skipif(not _RSCRIPT_AVAILABLE, reason=_SKIP_REASON)
def test_codeblock_r_error_propagates() -> None:
    """An R ``stop()`` surfaces as a Python exception with the original message."""
    block = CodeBlock()
    config = BlockConfig(params={"language": "r", "mode": "inline", "script": _ERROR_SCRIPT})

    with pytest.raises(RuntimeError) as excinfo:
        block.run({}, config)

    assert "scieasy-r-audit: boom from R" in str(excinfo.value), (
        f"R error message not preserved in Python exception; got: {excinfo.value!s}"
    )
