"""BlockRegistry — discovers blocks from drop-in files and entry_points.

Per ADR-009, the registry stores :class:`BlockSpec` descriptors (module path,
class name, metadata, file mtime) — never the class object itself.  This
ensures hot-reload safety: a reload updates specs without affecting running
workflow instances.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import inspect
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BlockSpec:
    """Metadata descriptor for a registered block type.

    Stores the *location* of the block class (module path + class name)
    rather than holding a reference to the class object.  See ADR-009.
    """

    name: str
    description: str = ""
    version: str = "0.1.0"
    module_path: str = ""
    class_name: str = ""
    file_path: str | None = None
    file_mtime: float | None = None
    category: str = ""
    input_ports: list[Any] = field(default_factory=list)
    output_ports: list[Any] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    type_name: str = ""


class BlockRegistry:
    """Central catalogue of available block types.

    The registry is populated via :meth:`scan` (entry-points / drop-in
    directories) and queried by the runtime when constructing workflows.

    Tier 1: Drop-in ``.py`` files from configured scan directories.
    Tier 2: ``pyproject.toml`` entry-points under ``"scieasy.blocks"``.
    """

    def __init__(self) -> None:
        self._registry: dict[str, BlockSpec] = {}
        self._aliases: dict[str, str] = {}
        self._scan_dirs: list[Path] = []

    def add_scan_dir(self, directory: str | Path) -> None:
        """Add a directory to the Tier 1 scan path."""
        self._scan_dirs.append(Path(directory))

    def scan(self) -> None:
        """Discover block classes from entry-points and drop-in directories."""
        self._scan_builtins()
        self._scan_tier1()
        self._scan_tier2()

    def _register_spec(self, spec: BlockSpec) -> None:
        """Register a spec under its display name and public type name."""
        self._registry[spec.name] = spec
        if spec.type_name:
            self._aliases[spec.type_name] = spec.name

    def _scan_builtins(self) -> None:
        """Register built-in core blocks used by the API/frontend."""
        from scieasy.blocks.ai.ai_block import AIBlock
        from scieasy.blocks.app.app_block import AppBlock
        from scieasy.blocks.code.code_block import CodeBlock
        from scieasy.blocks.io.io_block import IOBlock
        from scieasy.blocks.process.builtins.filter_collection import FilterCollection
        from scieasy.blocks.process.builtins.merge import MergeBlock
        from scieasy.blocks.process.builtins.merge_collection import MergeCollection
        from scieasy.blocks.process.builtins.slice_collection import SliceCollection
        from scieasy.blocks.process.builtins.split import SplitBlock
        from scieasy.blocks.process.builtins.split_collection import SplitCollection
        from scieasy.blocks.process.builtins.transform import TransformBlock
        from scieasy.blocks.subworkflow.subworkflow_block import SubWorkflowBlock

        for cls in (
            IOBlock,
            TransformBlock,
            MergeBlock,
            SplitBlock,
            MergeCollection,
            SplitCollection,
            FilterCollection,
            SliceCollection,
            CodeBlock,
            AppBlock,
            AIBlock,
            SubWorkflowBlock,
        ):
            self._register_spec(_spec_from_class(cls, source="builtin"))

    def _scan_tier1(self) -> None:
        """Tier 1: scan configured directories for ``.py`` files containing Block subclasses."""
        from scieasy.blocks.base.block import Block

        for scan_dir in self._scan_dirs:
            if not scan_dir.is_dir():
                continue
            for py_file in scan_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                try:
                    mtime = py_file.stat().st_mtime
                    mod_name = f"_scieasy_dropin_{py_file.stem}_{int(mtime)}"
                    spec = importlib.util.spec_from_file_location(mod_name, py_file)
                    if spec is None or spec.loader is None:
                        continue
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for attr_name in dir(module):
                        obj = getattr(module, attr_name)
                        if (
                            isinstance(obj, type)
                            and issubclass(obj, Block)
                            and obj is not Block
                            and not inspect.isabstract(obj)
                        ):
                            block_spec = _spec_from_class(obj, source="tier1")
                            block_spec.file_path = str(py_file)
                            block_spec.file_mtime = mtime
                            block_spec.module_path = mod_name
                            self._register_spec(block_spec)
                except Exception:
                    logger.warning(
                        "Failed to import block from %s",
                        py_file,
                        exc_info=True,
                    )
                    continue

    def _scan_tier2(self) -> None:
        """Tier 2: scan ``scieasy.blocks`` entry-points."""
        from scieasy.blocks.base.block import Block

        try:
            eps = importlib.metadata.entry_points()
        except Exception:
            logger.warning("Failed to load entry_points for block discovery", exc_info=True)
            return

        block_eps: Any = eps.select(group="scieasy.blocks") if hasattr(eps, "select") else eps.get("scieasy.blocks", [])

        for ep in block_eps:
            try:
                cls = ep.load()
                if isinstance(cls, type) and issubclass(cls, Block) and not inspect.isabstract(cls):
                    block_spec = _spec_from_class(cls, source="entry_point")
                    block_spec.module_path = f"{ep.value.rsplit(':', 1)[0]}"
                    block_spec.class_name = cls.__name__
                    self._register_spec(block_spec)
            except Exception:
                logger.warning(
                    "Failed to load block from entry_point '%s'",
                    ep.name,
                    exc_info=True,
                )
                continue

    def get_spec(self, identifier: str) -> BlockSpec | None:
        """Resolve a block spec by display name or public type name."""
        if identifier in self._registry:
            return self._registry[identifier]
        alias = self._aliases.get(identifier)
        if alias is None:
            return None
        return self._registry.get(alias)

    def instantiate(self, name: str, config: dict[str, Any] | None = None) -> Any:
        """Create a block instance by registered *name*.

        Performs a fresh import using the stored module path and class name,
        with mtime-based module name for hot-reload safety.
        """
        spec = self.get_spec(name)
        if spec is None:
            raise KeyError(f"Block '{name}' is not registered.")

        # For Tier 1 (file-based), re-import with mtime.
        if spec.file_path:
            path = Path(spec.file_path)
            mtime = path.stat().st_mtime
            mod_name = f"_scieasy_dropin_{path.stem}_{int(mtime)}"
            mod_spec = importlib.util.spec_from_file_location(mod_name, path)
            if mod_spec is None or mod_spec.loader is None:
                raise ImportError(f"Cannot load block from {spec.file_path}")
            module = importlib.util.module_from_spec(mod_spec)
            mod_spec.loader.exec_module(module)
        else:
            # For Tier 2, standard import.
            module = importlib.import_module(spec.module_path)

        cls = getattr(module, spec.class_name)
        return cls(config=config)

    def hot_reload(self) -> None:
        """Re-scan Tier 1 dirs and update specs that have changed.

        Compares file mtimes to detect changes.  New files are added,
        modified files are re-scanned, deleted files are removed.
        """
        # Remove stale Tier 1 entries.
        stale = [
            name
            for name, spec in self._registry.items()
            if spec.source == "tier1" and spec.file_path and not Path(spec.file_path).exists()
        ]
        for name in stale:
            del self._registry[name]

        # Re-scan Tier 1 only.
        self._scan_tier1()

    def all_specs(self) -> dict[str, BlockSpec]:
        """Return a copy of the full registry mapping."""
        return dict(self._registry)


def _spec_from_class(cls: type, source: str = "") -> BlockSpec:
    """Build a :class:`BlockSpec` from a Block subclass's class-level metadata."""
    return BlockSpec(
        name=getattr(cls, "name", cls.__name__),
        description=getattr(cls, "description", "") or (cls.__doc__ or "").split("\n")[0],
        version=getattr(cls, "version", "0.1.0"),
        module_path=cls.__module__,
        class_name=cls.__name__,
        category=_infer_category(cls),
        input_ports=list(getattr(cls, "input_ports", [])),
        output_ports=list(getattr(cls, "output_ports", [])),
        config_schema=getattr(cls, "config_schema", {"type": "object", "properties": {}}),
        source=source,
        type_name=_type_name_for_class(cls),
    )


def _infer_category(cls: type) -> str:
    """Infer the block category from the class hierarchy."""
    # Lazy imports to avoid circular dependencies.
    from scieasy.blocks.ai.ai_block import AIBlock
    from scieasy.blocks.app.app_block import AppBlock
    from scieasy.blocks.code.code_block import CodeBlock
    from scieasy.blocks.io.io_block import IOBlock
    from scieasy.blocks.process.process_block import ProcessBlock
    from scieasy.blocks.subworkflow.subworkflow_block import SubWorkflowBlock

    if issubclass(cls, IOBlock):
        return "io"
    if issubclass(cls, ProcessBlock):
        return "process"
    if issubclass(cls, CodeBlock):
        return "code"
    if issubclass(cls, AppBlock):
        return "app"
    if issubclass(cls, AIBlock):
        return "ai"
    if issubclass(cls, SubWorkflowBlock):
        return "subworkflow"
    if issubclass(cls, AIBlock):
        return "ai"
    return "unknown"


def _type_name_for_class(cls: type) -> str:
    """Return the public API identifier for a block class."""
    explicit = getattr(cls, "type_name", None)
    if isinstance(explicit, str) and explicit:
        return explicit
    return cls.__name__.replace("Block", "").lower() + "_block"
