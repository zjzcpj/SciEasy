"""BatchExecutor -- parallel, serial, and adaptive dispatch for data collections."""

from __future__ import annotations

from typing import Any


class BatchExecutor:
    """Execute a block over a collection of data items.

    Supports serial, parallel, and adaptive strategies with configurable
    error handling.
    """

    def __init__(self, error_strategy: str = "skip") -> None:
        """Initialise the batch executor.

        Parameters
        ----------
        error_strategy:
            How to handle per-item errors.  Supported values will include
            ``"skip"``, ``"fail_fast"``, and ``"collect"``.
        """
        raise NotImplementedError

    async def execute_serial(
        self,
        block: Any,
        items: list[Any],
        config: Any,
    ) -> Any:
        """Process *items* one at a time through *block*.

        Parameters
        ----------
        block:
            The block instance to execute.
        items:
            Ordered collection of input data items.
        config:
            Execution configuration forwarded to the block.

        Returns
        -------
        Any
            Aggregated results for every item.
        """
        raise NotImplementedError

    async def execute_parallel(
        self,
        block: Any,
        items: list[Any],
        config: Any,
        max_workers: int = 4,
    ) -> Any:
        """Process *items* concurrently through *block*.

        Parameters
        ----------
        block:
            The block instance to execute.
        items:
            Ordered collection of input data items.
        config:
            Execution configuration forwarded to the block.
        max_workers:
            Maximum number of concurrent tasks.

        Returns
        -------
        Any
            Aggregated results for every item.
        """
        raise NotImplementedError

    async def execute_adaptive(
        self,
        block: Any,
        items: list[Any],
        config: Any,
    ) -> Any:
        """Automatically choose serial or parallel execution based on heuristics.

        Parameters
        ----------
        block:
            The block instance to execute.
        items:
            Ordered collection of input data items.
        config:
            Execution configuration forwarded to the block.

        Returns
        -------
        Any
            Aggregated results for every item.
        """
        raise NotImplementedError
