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

    Note (ADR-017): All execution is delegated to subprocess-based runner
        via spawn_block_process(). No in-process exec() or importlib.
    Note (ADR-017): _prepare_inputs() moves to subprocess worker
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
        """Execute user code via the appropriate language runner.

        ADR-017: This method runs INSIDE an isolated subprocess (spawned
        by engine's spawn_block_process). It is safe to use exec/importlib.

        Steps:
            1. Resolve language runner from RunnerRegistry.
            2. Unpack Collection inputs for user scripts (ADR-020-Add4).
            3. Apply delivery mode (MEMORY/PROXY/CHUNKED) to ViewProxy inputs.
            4. Dispatch to runner (inline or script mode).
            5. Repack outputs into Collections (ADR-020-Add4).
        """
        from scieasy.blocks.base.state import BlockState
        from scieasy.blocks.code.runner_registry import RunnerRegistry

        self.transition(BlockState.RUNNING)
        try:
            language = config.get("language") or self.language
            mode = config.get("mode") or self.mode
            delivery = config.get("delivery", "memory")

            # Step 1: Get runner
            registry = RunnerRegistry()
            registry.register_defaults()
            runner = registry.get(language)()

            # Step 2: Unpack Collection inputs
            unpacked = self._unpack_inputs(inputs)

            # Step 3: Apply delivery mode to ViewProxy inputs
            prepared = self._apply_delivery(unpacked, delivery, config)

            # Step 4: Dispatch to runner
            if mode == "inline":
                script = config.get("script", "")
                if not script:
                    raise ValueError("Inline mode requires 'script' in config")
                raw_outputs = runner.execute_inline(script, prepared)
            elif mode == "script":
                script_path = config.get("script_path", "")
                if not script_path:
                    raise ValueError("Script mode requires 'script_path' in config")
                entry = config.get("entry_function", "run")
                raw_outputs = runner.execute_script(script_path, entry, prepared, dict(config.params))
            else:
                raise ValueError(f"Unknown CodeBlock mode: '{mode}'")

            # Step 5: Repack outputs
            result = self._repack_outputs(raw_outputs)

            self.transition(BlockState.DONE)
            return result
        except Exception:
            self.transition(BlockState.ERROR)
            raise

    @staticmethod
    def _apply_delivery(inputs: dict[str, Any], delivery: str, config: BlockConfig) -> dict[str, Any]:
        """Apply delivery mode to ViewProxy inputs.

        MEMORY:  call to_memory() -- block receives raw data.
        PROXY:   pass through -- block receives ViewProxy directly.
        CHUNKED: call iter_chunks() -- block receives list of chunks.
        """
        from scieasy.core.proxy import ViewProxy

        prepared: dict[str, Any] = {}
        for key, value in inputs.items():
            if not isinstance(value, ViewProxy):
                prepared[key] = value
                continue

            if delivery == "proxy":
                prepared[key] = value
            elif delivery == "chunked":
                chunk_size = int(config.get("chunk_size", 1024))
                prepared[key] = list(value.iter_chunks(chunk_size))
            else:  # "memory" (default)
                prepared[key] = value.to_memory()
        return prepared
