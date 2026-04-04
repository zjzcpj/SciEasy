"""CodeBlock — inline and script mode execution with language dispatch.

ADR-017: All execution in isolated subprocesses. No in-process exec/importlib.
ADR-020-Add4: Auto-unpack Collection inputs, auto-repack outputs.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.core.types.base import DataObject


class CodeBlock(Block):
    """Block for executing user-provided scripts in Python, R, or Julia.

    *language* selects the runner; *mode* is ``"inline"`` or ``"script"``.

    Delivery modes (per-port or block-level):
        MEMORY  — ``to_memory()`` is called, block receives raw data.
        PROXY   — block receives :class:`ViewProxy` instances directly.
        CHUNKED — ``iter_chunks()`` is called, results are concatenated.

    TODO(ADR-017): All execution delegated to subprocess-based runner
        via spawn_block_process(). No in-process exec() or importlib.

    TODO(ADR-020-Add4): Auto-unpack Collection inputs:
        - Collection length=1 → single native object (numpy array, pandas DataFrame)
        - Collection length>1 → LazyList (from blocks/code/lazy_list.py)
        - User scripts never see Collection object directly.
        Auto-repack outputs as Collection.

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

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the code block via subprocess-based language runner.

        TODO(ADR-017): Delegate to subprocess via spawn_block_process().
        TODO(ADR-020-Add4): Auto-unpack Collection inputs before passing
            to user script, auto-repack outputs as Collection.
        """
        raise NotImplementedError
