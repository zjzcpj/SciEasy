"""Block ABC — validate(), run(), postprocess() contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BatchErrorStrategy, BatchMode, BlockState, ExecutionMode


class Block(ABC):
    """Abstract base class for all processing blocks.

    Subclasses must override :meth:`run`.  The optional :meth:`validate` and
    :meth:`postprocess` hooks default to raising ``NotImplementedError`` so
    that Phase-1 skeletons are never silently treated as implemented.
    """

    # -- class-level metadata --------------------------------------------------

    name: ClassVar[str] = "Unnamed Block"
    description: ClassVar[str] = ""
    version: ClassVar[str] = "0.1.0"

    input_ports: ClassVar[list[InputPort]] = []
    output_ports: ClassVar[list[OutputPort]] = []

    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.AUTO
    batch_mode: ClassVar[BatchMode] = BatchMode.PARALLEL
    on_batch_error: ClassVar[BatchErrorStrategy] = BatchErrorStrategy.SKIP

    key_dependencies: ClassVar[list[str]] = []

    # -- instance lifecycle ----------------------------------------------------

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: BlockConfig = BlockConfig(**(config or {}))
        self.state: BlockState = BlockState.IDLE

    # -- hooks -----------------------------------------------------------------

    def validate(self, inputs: dict[str, Any]) -> bool:
        """Validate *inputs* against the block's port contract.

        Returns ``True`` when all inputs satisfy their constraints.
        """
        raise NotImplementedError

    @abstractmethod
    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the block's main logic and return output mapping."""
        ...

    def postprocess(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Optional post-processing of *outputs* before downstream delivery."""
        raise NotImplementedError
