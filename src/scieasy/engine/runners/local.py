"""LocalRunner -- subprocess execution on the local machine.

ADR-017: All block execution in isolated subprocesses. No in-process execution.
Uses async subprocess to avoid os.fork() deadlock on macOS (#483).
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scieasy.engine.runners.process_handle import ProcessRegistry

logger = logging.getLogger(__name__)


def _derive_output_dir(block: Any, config: dict[str, Any]) -> str:
    """Return a persistence directory for worker auto-flush outputs."""
    explicit_output_dir = config.get("output_dir")
    if isinstance(explicit_output_dir, str) and explicit_output_dir:
        path = Path(explicit_output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    project_dir = config.get("project_dir")
    block_id = str(config.get("block_id") or getattr(block, "id", "block"))
    workflow_id = str(config.get("workflow_id") or "adhoc")
    if isinstance(project_dir, str) and project_dir:
        # Truncate block_id to avoid Windows MAX_PATH (260) overflow.
        short_block_id = block_id[:40] if len(block_id) > 40 else block_id
        path = Path(project_dir) / "data" / "zarr" / workflow_id / short_block_id
        from scieasy.blocks.base.block import _win_long_path

        result = _win_long_path(str(path))
        Path(result).mkdir(parents=True, exist_ok=True)
        return result

    return tempfile.mkdtemp(prefix="scieasy-worker-")


class LocalRunner:
    """Execute blocks as local subprocesses.

    Implements the BlockRunner protocol (engine/runners/base.py).

    Methods:
        async run(block, inputs, config) -> dict[str, Any]
            - Calls spawn_block_process() to create isolated subprocess.
            - Waits for subprocess to complete.
            - Returns parsed JSON output from subprocess stdout.

        async check_status(run_id) -> str
            - Queries ProcessHandle.is_alive() for the given run_id.
            - Returns "running" if alive, "completed" otherwise.

        async cancel(run_id) -> None
            - Calls ProcessHandle.terminate() for the given run_id.
    """

    def __init__(self, event_bus: Any | None = None, registry: ProcessRegistry | None = None) -> None:
        self._event_bus = event_bus
        self._registry = registry

    async def run(
        self,
        block: Any,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute *block* in an isolated subprocess.

        Uses ``asyncio.create_subprocess_exec`` to avoid ``os.fork()``
        deadlock on macOS when native extensions have been imported (#483).

        Parameters
        ----------
        block:
            The block instance to run. Its class path is resolved for
            serialization to the worker subprocess.
        inputs:
            Mapping of port names to input data references.
        config:
            Execution-time configuration for this invocation.

        Returns
        -------
        dict[str, Any]
            Parsed JSON result from the subprocess worker.
        """
        from scieasy.engine.runners.process_handle import (
            ProcessRegistry,
            build_worker_payload,
            register_async_process,
        )

        block_class_path = f"{block.__class__.__module__}.{block.__class__.__qualname__}"
        registry = self._registry if self._registry is not None else ProcessRegistry()
        block_id = getattr(block, "id", block_class_path)
        output_dir = _derive_output_dir(block, config)

        # Build the serialized payload for the worker subprocess.
        payload_bytes = build_worker_payload(
            block_class=block_class_path,
            inputs_refs=inputs,
            config=config,
            output_dir=output_dir,
        )

        # Launch via asyncio.create_subprocess_exec to avoid os.fork()
        # deadlock on macOS after importing native extensions (#483).
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "scieasy.engine.runners.worker",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )

        # Register the process in the ProcessRegistry for lifecycle tracking.
        register_async_process(
            pid=proc.pid,
            block_id=block_id,
            registry=registry,
            event_bus=self._event_bus,
        )

        stdout, stderr = await proc.communicate(input=payload_bytes)

        if proc.returncode != 0:
            error_msg = stderr.decode(errors="replace") if stderr else "unknown error"
            logger.error(
                "Block subprocess %s exited with code %d: %s",
                block_class_path,
                proc.returncode,
                error_msg,
            )
            # Try to parse stdout for structured error from worker
            if stdout:
                try:
                    payload = dict(json.loads(stdout.decode()))
                    if "error" in payload:
                        raise RuntimeError(str(payload["error"]))
                    outputs = payload.get("outputs", payload)
                    if not isinstance(outputs, dict):
                        raise RuntimeError("Worker returned a non-dict output payload.")
                    return outputs
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            raise RuntimeError(error_msg)

        if stdout:
            try:
                parsed = json.loads(stdout.decode())
                # Worker wraps outputs as {"outputs": {...}}. Unwrap the
                # envelope so callers see port names at the top level.
                if isinstance(parsed, dict) and "outputs" in parsed:
                    return dict(parsed["outputs"])
                return dict(parsed)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise RuntimeError(f"Failed to parse worker output: {exc}") from exc

        return {}

    async def check_status(self, run_id: str) -> str:
        """Query the current status of a previously started run.

        Parameters
        ----------
        run_id:
            Block ID / opaque identifier returned when the run was initiated.

        Returns
        -------
        str
            "running", "completed", or "unknown".
        """
        if self._registry is None:
            return "unknown"
        handle = self._registry.get_handle(run_id)
        if handle is None:
            return "unknown"
        alive = handle.is_alive()
        return "running" if alive else "completed"

    async def cancel(self, run_id: str) -> None:
        """Request cancellation of a running execution.

        Parameters
        ----------
        run_id:
            Block ID / opaque identifier of the run to cancel.
        """
        if self._registry is None:
            return
        handle = self._registry.get_handle(run_id)
        if handle is not None:
            handle.terminate()
