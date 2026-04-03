"""CodeBlock — inline and script mode execution with language dispatch."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState, InputDelivery
from scieasy.core.types.base import DataObject


class CodeBlock(Block):
    """Block for executing user-provided scripts in Python, R, or Julia.

    *language* selects the runner; *mode* is ``"inline"`` or ``"script"``.

    Delivery modes (per-port or block-level):
        MEMORY  — ``to_memory()`` is called, block receives raw data.
        PROXY   — block receives :class:`ViewProxy` instances directly.
        CHUNKED — ``iter_chunks()`` is called, results are concatenated.
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
        """Execute the code block via the appropriate language runner."""
        from scieasy.blocks.code.runner_registry import RunnerRegistry

        self.transition(BlockState.RUNNING)
        try:
            delivery = InputDelivery(config.get("delivery", InputDelivery.MEMORY.value))
            prepared_inputs = self._prepare_inputs(inputs, delivery, config)

            runner_registry = RunnerRegistry()
            runner_registry.register_defaults()
            runner_cls = runner_registry.get(self.language)
            runner = runner_cls()

            if self.mode == "inline":
                script = config.get("script", "")
                if not script:
                    raise ValueError("Inline CodeBlock requires 'script' in config.params")
                namespace = dict(prepared_inputs)
                namespace["config"] = config
                result = runner.execute_inline(script, namespace)
            elif self.mode == "script":
                script_path = config.get("script_path", "")
                if not script_path:
                    raise ValueError("Script CodeBlock requires 'script_path' in config.params")
                entry = config.get("entry_function", "run")
                result = runner.execute_script(
                    script_path,
                    entry,
                    prepared_inputs,
                    config.params,
                )
            else:
                raise ValueError(f"Unknown CodeBlock mode: {self.mode}")

            self.transition(BlockState.DONE)
            return result
        except Exception:
            self.transition(BlockState.ERROR)
            raise

    def _prepare_inputs(
        self,
        inputs: dict[str, Any],
        delivery: InputDelivery,
        config: BlockConfig,
    ) -> dict[str, Any]:
        """Prepare inputs according to the delivery mode."""
        from scieasy.core.proxy import ViewProxy

        prepared: dict[str, Any] = {}

        for key, value in inputs.items():
            if delivery == InputDelivery.MEMORY:
                if isinstance(value, ViewProxy):
                    prepared[key] = value.to_memory()
                else:
                    prepared[key] = value

            elif delivery == InputDelivery.PROXY:
                # Pass ViewProxy directly to the user script.
                prepared[key] = value

            elif delivery == InputDelivery.CHUNKED:
                if isinstance(value, ViewProxy):
                    chunk_size = int(config.get("chunk_size", 1000))
                    chunks = list(value.iter_chunks(chunk_size))
                    prepared[key] = chunks
                else:
                    prepared[key] = [value]

            else:
                prepared[key] = value

        return prepared
