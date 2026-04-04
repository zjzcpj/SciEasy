"""Path conventions for intermediate output storage.

ADR-020 Addendum 5: _auto_flush writes per-run, per-block intermediate
outputs to ``data/runs/{run_id}/{block_id}/``.  This module defines the
path construction utility used by the subprocess worker and _auto_flush.
"""

from __future__ import annotations

from pathlib import Path


def run_output_dir(workspace: str | Path, run_id: str, block_id: str) -> Path:
    """Construct the output directory path for a block within a run.

    Returns ``{workspace}/data/runs/{run_id}/{block_id}/``.

    Parameters
    ----------
    workspace:
        Root of the project workspace directory.
    run_id:
        Unique identifier for the current execution run
        (e.g. ``"run_20260404_143000"``).
    block_id:
        Unique identifier for the block within the workflow
        (e.g. ``"cellpose_001"``).
    """
    return Path(workspace) / "data" / "runs" / run_id / block_id
