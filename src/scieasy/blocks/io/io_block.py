"""IOBlock -- loads and saves data in any supported format."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection


class IOBlock(Block):
    """Block for data ingress and egress with pluggable format adapters.

    For direction=input, creates lazy StorageReference objects via
    adapter.create_reference() and wraps them in a Collection.

    For direction=output, takes a Collection (or single DataObject)
    and writes each item via the adapter.
    """

    direction: ClassVar[str] = "input"
    format: ClassVar[str] = ""

    name: ClassVar[str] = "IO Block"
    description: ClassVar[str] = "Load or save data using a format adapter"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="data",
            accepted_types=[DataObject],
            required=False,
            description="Data to save (output mode)",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="data",
            accepted_types=[DataObject],
            description="Loaded data (input mode)",
        ),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the IO operation (read or write)."""
        from scieasy.blocks.io.adapter_registry import AdapterRegistry

        self.transition(BlockState.RUNNING)
        try:
            path_str = config.get("path") or config.params.get("path")
            if not path_str:
                raise ValueError("IOBlock requires \x27path\x27 in config.params")

            path = Path(path_str)
            registry = AdapterRegistry()
            registry.register_defaults()

            if self.direction == "input":
                return self._run_input(path, registry)
            else:
                return self._run_output(path, registry, inputs)
        except Exception:
            self.transition(BlockState.ERROR)
            raise

    def _run_input(self, path: Path, registry: Any) -> dict[str, Any]:
        """Build a lazy Collection from *path* (file or directory)."""
        if path.is_dir():
            items: list[DataObject] = []
            for child in sorted(path.iterdir()):
                if child.is_file():
                    ext = child.suffix.lower()
                    try:
                        adapter_cls = registry.get_for_extension(ext)
                    except KeyError:
                        continue
                    adapter = adapter_cls()
                    ref = adapter.create_reference(child)
                    obj = DataObject(storage_ref=ref)
                    items.append(obj)

            if not items:
                raise ValueError(f"No recognised files found in directory: {path}")

            collection = Collection(items=items, item_type=DataObject)
        else:
            ext = path.suffix.lower()
            adapter_cls = registry.get_for_extension(ext)
            adapter = adapter_cls()
            ref = adapter.create_reference(path)
            obj = DataObject(storage_ref=ref)
            collection = Collection(items=[obj], item_type=DataObject)

        self.transition(BlockState.DONE)
        return {"data": collection}

    def _run_output(
        self, path: Path, registry: Any, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """Write each item in inputs data through the adapter."""
        data = inputs.get("data")
        if data is None:
            raise ValueError("IOBlock in output mode requires \x27data\x27 input")

        ext = path.suffix.lower()

        if isinstance(data, Collection):
            path.mkdir(parents=True, exist_ok=True)
            adapter_cls = registry.get_for_extension(ext) if ext else None

            for i, item in enumerate(data):
                item_ext = ext
                if not item_ext and item.storage_ref and item.storage_ref.format:
                    item_ext = f".{item.storage_ref.format}"
                if not item_ext:
                    item_ext = ".bin"

                if adapter_cls is None:
                    adapter_cls = registry.get_for_extension(item_ext)

                adapter = adapter_cls()
                item_path = path / f"item_{i:04d}{item_ext}"
                adapter.write(item, item_path)
        else:
            adapter_cls = registry.get_for_extension(ext)
            adapter = adapter_cls()
            adapter.write(data, path)

        self.transition(BlockState.DONE)
        return {"path": str(path)}
