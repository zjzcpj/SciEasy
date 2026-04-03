"""BatchExecutor -- parallel, serial, and adaptive dispatch for data collections."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.result import BatchResult
from scieasy.blocks.base.state import BatchErrorStrategy, BatchMode, BlockState, ExecutionMode


class BatchExecutor:
    """Execute a block over a collection of data items.

    Supports serial, parallel, and adaptive strategies with configurable
    error handling.
    """

    def __init__(self, error_strategy: BatchErrorStrategy = BatchErrorStrategy.SKIP) -> None:
        self._error_strategy = error_strategy

    async def execute_serial(
        self,
        block_factory: type[Block],
        items: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> BatchResult:
        """Process *items* one at a time through fresh block instances.

        Each item is a dict mapping port names to values.  A fresh block
        instance is created per item to avoid state leakage.
        """
        result = BatchResult()

        for idx, item in enumerate(items):
            try:
                block = block_factory(config=config)
                block.transition(BlockState.READY)
                block.validate(item)
                block.transition(BlockState.RUNNING)
                outputs = block.run(item, block.config)
                outputs = block.postprocess(outputs)
                block.transition(BlockState.DONE)
                result.succeeded.append((idx, outputs))
            except Exception as exc:
                if self._error_strategy == BatchErrorStrategy.STOP:
                    result.failed.append((idx, exc))
                    break
                elif self._error_strategy == BatchErrorStrategy.SKIP:
                    result.failed.append((idx, exc))
                    continue
                elif self._error_strategy == BatchErrorStrategy.RETRY:
                    # Single retry attempt.
                    try:
                        block2 = block_factory(config=config)
                        block2.transition(BlockState.READY)
                        block2.validate(item)
                        block2.transition(BlockState.RUNNING)
                        outputs = block2.run(item, block2.config)
                        outputs = block2.postprocess(outputs)
                        block2.transition(BlockState.DONE)
                        result.succeeded.append((idx, outputs))
                    except Exception as exc2:
                        result.failed.append((idx, exc2))
                elif self._error_strategy == BatchErrorStrategy.PAUSE:
                    result.failed.append((idx, exc))
                    # Mark remaining as skipped.
                    for remaining_idx in range(idx + 1, len(items)):
                        result.skipped.append(remaining_idx)
                    break

        return result

    async def execute_parallel(
        self,
        block_factory: type[Block],
        items: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
        max_workers: int = 4,
    ) -> BatchResult:
        """Process *items* concurrently through fresh block instances.

        Uses a thread pool to run block.run() calls concurrently, since
        most scientific blocks are CPU-bound.
        """
        result = BatchResult()
        loop = asyncio.get_event_loop()

        def _run_item(idx: int, item: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            block = block_factory(config=config)
            block.transition(BlockState.READY)
            block.validate(item)
            block.transition(BlockState.RUNNING)
            outputs = block.run(item, block.config)
            outputs = block.postprocess(outputs)
            block.transition(BlockState.DONE)
            return idx, outputs

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for idx, item in enumerate(items):
                future = loop.run_in_executor(executor, _run_item, idx, item)
                futures.append((idx, future))

            for idx, future in futures:
                try:
                    _, outputs = await future
                    result.succeeded.append((idx, outputs))
                except Exception as exc:
                    if self._error_strategy == BatchErrorStrategy.STOP:
                        result.failed.append((idx, exc))
                        # Mark remaining as skipped.
                        for remaining_idx, remaining_future in futures:
                            if remaining_idx > idx:
                                result.skipped.append(remaining_idx)
                                remaining_future.cancel()
                        break
                    else:
                        result.failed.append((idx, exc))

        return result

    async def execute_adaptive(
        self,
        block_factory: type[Block],
        items: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
        max_workers: int = 4,
    ) -> BatchResult:
        """Automatically choose serial or parallel execution.

        Scans the block class for execution_mode and batch_mode hints.
        If the block or its downstream context requires SERIAL or
        INTERACTIVE mode, falls back to serial execution.
        """
        exec_mode = getattr(block_factory, "execution_mode", ExecutionMode.AUTO)
        batch_mode = getattr(block_factory, "batch_mode", BatchMode.PARALLEL)

        if exec_mode == ExecutionMode.INTERACTIVE or batch_mode == BatchMode.SERIAL:
            return await self.execute_serial(block_factory, items, config)
        elif batch_mode == BatchMode.PARALLEL:
            return await self.execute_parallel(block_factory, items, config, max_workers)
        else:
            # ADAPTIVE: use parallel for many items, serial for few.
            if len(items) <= 2:
                return await self.execute_serial(block_factory, items, config)
            return await self.execute_parallel(block_factory, items, config, max_workers)
