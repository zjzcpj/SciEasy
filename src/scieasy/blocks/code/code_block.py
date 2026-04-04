"""CodeBlock -- inline and script mode execution with language dispatch.

ADR-017: All execution in isolated subprocesses. No in-process exec/importlib.
ADR-020-Add4: Auto-unpack Collection inputs, auto-repack outputs.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.code.lazy_list import LazyList
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection


class CodeBlock(Block):
    """Block for executing user-provided scripts in Python, R, or Julia.

    *language* selects the runner; *mode* is ``"inline"`` or ``"script"``.

    Delivery modes (per-port or block-level):
        MEMORY  -- ``to_memory()`` is called, block receives raw data.
        PROXY   -- block receives :class:`ViewProxy` instances directly.
        CHUNKED -- ``iter_chunks()`` is called, results are concatenated.

    Auto-unpack/repack layer (ADR-020-Add4):
        Before user code runs, ``_unpack_inputs()`` converts Collection
        inputs so that user scripts never see Collection objects directly:
        - Collection length=1 -> single native object via ``.view().to_memory()``
        - Collection length>1 -> :class:`LazyList` (memory-safe lazy wrapper)
        After user code runs, ``_repack_outputs()`` wraps native outputs
        back into Collection for downstream transport.

    TODO(ADR-017): All execution delegated to subprocess-based runner
        via spawn_block_process(). No in-process exec() or importlib.
    TODO(ADR-017): _prepare_inputs() moves to subprocess worker
        (engine/runners/worker.py). Input preparation happens in child process.
    """

    language: ClassVar[str] = "python"
    mode: ClassVar[str] = "inline"

    name: ClassVar[str] = "Code Block"
    description: ClassVar[str] = "Execute user-provided scripts"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[DataObject], required=False, description="Primary input data"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[DataObject], description="Script output"),
    ]

    # -- auto-unpack / repack (ADR-020-Add4) -----------------------------------

    def _unpack_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Convert Collection inputs into user-friendly representations.

        For each value that is a :class:`Collection`:
        - length == 1: replaced with the single item materialised via
          ``collection[0].view().to_memory()`` (e.g. a numpy array).
        - length > 1: replaced with a :class:`LazyList` that loads items
          on demand, keeping peak memory at O(1) per iteration step.

        Non-Collection values pass through unchanged.
        """
        unpacked: dict[str, Any] = {}
        for key, value in inputs.items():
            if isinstance(value, Collection):
                if len(value) == 1:
                    unpacked[key] = value[0].view().to_memory()
                else:
                    unpacked[key] = LazyList(value)
            else:
                unpacked[key] = value
        return unpacked

    def _repack_outputs(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Wrap native outputs back into Collection for block-to-block transport.

        ADR-020-Add4 auto-repack rules:
        - Already a Collection: pass through unchanged
        - list of DataObjects: wrap in Collection
        - Single DataObject: wrap in a length-1 Collection
        - Non-DataObject values pass through unchanged
        """
        repacked: dict[str, Any] = {}
        for key, value in outputs.items():
            if isinstance(value, Collection):
                repacked[key] = value
            elif isinstance(value, list) and value and all(isinstance(v, DataObject) for v in value):
                repacked[key] = Collection(value)
            elif isinstance(value, DataObject):
                repacked[key] = Collection([value])
            else:
                repacked[key] = value
        return repacked

    # -- execution (ADR-017: subprocess delegation) ----------------------------

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the code block via subprocess-based language runner.

        TODO(ADR-017): Delegate to subprocess via spawn_block_process() (Phase 5.2).
            The subprocess worker will call ``_unpack_inputs()`` before
            passing data to the user script, and ``_repack_outputs()``
            after the user script returns.
        """
        raise NotImplementedError(
            "CodeBlock.run() requires subprocess delegation (ADR-017, Phase 5.2). "
            "Direct in-process execution is not supported. "
            "Use spawn_block_process() with _unpack_inputs() / _repack_outputs()."
        )
