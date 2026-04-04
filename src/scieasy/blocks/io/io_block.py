"""IOBlock — loads and saves data in any supported format."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState
from scieasy.core.types.base import DataObject


class IOBlock(Block):
    """Block for data ingress and egress with pluggable format adapters.

    Subclasses should set *direction* to ``"input"`` or ``"output"`` and
    *format* to the target file format identifier.

    For ``direction="input"``, the block reads a file at config ``path``
    using the registered adapter and outputs a :class:`DataObject`.

    For ``direction="output"``, the block takes a :class:`DataObject` input
    and writes it to the config ``path``.
    """

    direction: ClassVar[str] = "input"
    format: ClassVar[str] = ""

    name: ClassVar[str] = "IO Block"
    description: ClassVar[str] = "Load or save data using a format adapter"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[DataObject], required=False, description="Data to save (output mode)"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="data", accepted_types=[DataObject], description="Loaded data (input mode)"),
    ]

    # TODO(ADR-020): direction="input" must produce Collection output, not single DataObject.
    # TODO(ADR-020-Add2): Lazy Collection construction — when path.is_dir(), iterate
    #   files and create StorageReference per file WITHOUT calling adapter.read().
    #   100 files = ~100KB refs, not 100GB data in memory.
    #   For single files, same lazy pattern — create StorageReference without reading.
    #   Adapter is invoked lazily by ViewProxy when downstream blocks access data.
    # TODO(ADR-020): direction="output" must accept Collection input and write each item.
    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the IO operation (read or write)."""
        from scieasy.blocks.io.adapter_registry import AdapterRegistry

        self.transition(BlockState.RUNNING)
        try:
            path_str = config.get("path") or config.params.get("path")
            if not path_str:
                raise ValueError("IOBlock requires 'path' in config.params")

            path = Path(path_str)
            registry = AdapterRegistry()
            registry.register_defaults()

            ext = path.suffix.lower()
            adapter_cls = registry.get_for_extension(ext)
            adapter = adapter_cls()

            if self.direction == "input":
                result = adapter.read(path)
                self.transition(BlockState.DONE)
                return {"data": result}
            else:
                data = inputs.get("data")
                if data is None:
                    raise ValueError("IOBlock in output mode requires 'data' input")
                adapter.write(data, path)
                self.transition(BlockState.DONE)
                return {"path": str(path)}
        except Exception:
            self.transition(BlockState.ERROR)
            raise
