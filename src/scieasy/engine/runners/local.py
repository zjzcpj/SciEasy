"""LocalRunner -- in-process or subprocess execution."""

from __future__ import annotations

from typing import Any


class LocalRunner:
    """Execute blocks in the local process or as a local subprocess.

    Implements the :class:`~scieasy.engine.runners.base.BlockRunner`
    protocol for same-machine execution.
    """

    async def run(
        self,
        block: Any,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute *block* locally with the given *inputs* and *config*.

        Parameters
        ----------
        block:
            The block instance to run.
        inputs:
            Mapping of port names to input data references.
        config:
            Execution-time configuration for this invocation.

        Returns
        -------
        dict[str, Any]
            Mapping of output port names to result data references.
        """
        raise NotImplementedError

    async def check_status(self, run_id: str) -> Any:
        """Query the current status of a previously started run.

        Parameters
        ----------
        run_id:
            Opaque identifier returned when the run was initiated.

        Returns
        -------
        Any
            Runner-specific status descriptor.
        """
        raise NotImplementedError

    async def cancel(self, run_id: str) -> None:
        """Request cancellation of a running execution.

        Parameters
        ----------
        run_id:
            Opaque identifier of the run to cancel.
        """
        raise NotImplementedError
