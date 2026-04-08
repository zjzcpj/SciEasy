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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scieasy.blocks.base.package_info import PackageInfo

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
    package_name: str = ""
    # ADR-028 Addendum 1 D3: IO direction for IO blocks ("input" | "output").
    # Empty string means "not an IO block / no direction".
    direction: str = ""
    # ADR-028 Addendum 1 D3: enum-driven dynamic-port descriptor copied from
    # the class-level ``Block.dynamic_ports`` ClassVar. Validated at scan
    # time by :meth:`BlockRegistry._validate_dynamic_ports`.
    dynamic_ports: dict[str, Any] | None = None


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
        self._packages: dict[str, PackageInfo] = {}

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

    @staticmethod
    def _validate_dynamic_ports(cls: type) -> None:
        """Validate the shape of ``cls.dynamic_ports`` per ADR-028 Addendum 1.

        Called at scan time so malformed declarations fail loudly at import.
        Accepts ``None`` (the default) and any dict that matches::

            {
                "source_config_key": str,
                # Exactly one of the following two keys must be present.
                # ``output_port_mapping`` is used by input-direction blocks
                # (LoadData) and ``input_port_mapping`` by output-direction
                # blocks (SaveData). The shape of the value is identical.
                "output_port_mapping": {
                    "<port_name>": {
                        "<enum_value>": ["<TypeName>", ...],
                        ...
                    },
                    ...
                },
                # OR
                "input_port_mapping": {
                    "<port_name>": {
                        "<enum_value>": ["<TypeName>", ...],
                        ...
                    },
                    ...
                },
            }

        Raises ``ValueError`` with the offending class name and field path
        when the shape is wrong.

        T-TRK-008 (SaveData) note: the ``input_port_mapping`` variant was
        added in this ticket per ADR-028 Addendum 1 §C5/§C9. T-TRK-006
        (PR #321) only declared the ``output_port_mapping`` variant
        because LoadData (T-TRK-007) was the first consumer; SaveData is
        the symmetric output-direction consumer and uses the
        ``input_port_mapping`` key. The frontend
        ``computeEffectivePorts`` helper in T-TRK-009 must handle both
        keys.
        """
        descriptor = getattr(cls, "dynamic_ports", None)
        if descriptor is None:
            return

        cls_name = cls.__name__
        if not isinstance(descriptor, dict):
            raise ValueError(f"{cls_name}.dynamic_ports must be a dict or None, got {type(descriptor).__name__}")

        if "source_config_key" not in descriptor:
            raise ValueError(f"{cls_name}.dynamic_ports is missing required key 'source_config_key'")
        source_key = descriptor["source_config_key"]
        if not isinstance(source_key, str) or not source_key:
            raise ValueError(
                f"{cls_name}.dynamic_ports['source_config_key'] must be a non-empty string, "
                f"got {type(source_key).__name__}"
            )

        # Exactly one of ``output_port_mapping`` or ``input_port_mapping``
        # must be present. Per ADR-028 Addendum 1 §C5: input-direction
        # blocks (LoadData) drive output ports from a config enum, and
        # output-direction blocks (SaveData) drive input ports from a
        # config enum. Both use the same nested-dict shape.
        has_output = "output_port_mapping" in descriptor
        has_input = "input_port_mapping" in descriptor
        if not has_output and not has_input:
            raise ValueError(
                f"{cls_name}.dynamic_ports is missing required key 'output_port_mapping' or 'input_port_mapping'"
            )
        if has_output and has_input:
            raise ValueError(
                f"{cls_name}.dynamic_ports must declare exactly one of "
                "'output_port_mapping' or 'input_port_mapping', not both"
            )
        mapping_key = "output_port_mapping" if has_output else "input_port_mapping"
        mapping = descriptor[mapping_key]
        if not isinstance(mapping, dict):
            raise ValueError(f"{cls_name}.dynamic_ports[{mapping_key!r}] must be a dict, got {type(mapping).__name__}")

        for port_name, enum_map in mapping.items():
            if not isinstance(port_name, str) or not port_name:
                raise ValueError(
                    f"{cls_name}.dynamic_ports[{mapping_key!r}] keys must be non-empty strings, got {port_name!r}"
                )
            if not isinstance(enum_map, dict):
                raise ValueError(
                    f"{cls_name}.dynamic_ports[{mapping_key!r}][{port_name!r}] must be a dict, "
                    f"got {type(enum_map).__name__}"
                )
            for enum_value, type_names in enum_map.items():
                if not isinstance(enum_value, str) or not enum_value:
                    raise ValueError(
                        f"{cls_name}.dynamic_ports[{mapping_key!r}][{port_name!r}] keys must be "
                        f"non-empty strings, got {enum_value!r}"
                    )
                if not isinstance(type_names, list):
                    raise ValueError(
                        f"{cls_name}.dynamic_ports[{mapping_key!r}][{port_name!r}][{enum_value!r}] "
                        f"must be a list, got {type(type_names).__name__}"
                    )
                for type_name in type_names:
                    if not isinstance(type_name, str) or not type_name:
                        raise ValueError(
                            f"{cls_name}.dynamic_ports[{mapping_key!r}][{port_name!r}][{enum_value!r}] "
                            f"entries must be non-empty strings, got {type_name!r}"
                        )

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
        from scieasy.blocks.subworkflow.subworkflow_block import SubWorkflowBlock

        # Phase 11 / T-TRK-003: ``TransformBlock`` was relocated to
        # ``tests/fixtures/noop_block.py`` as ``NoopBlock``. It is no
        # longer registered as a core builtin. Tests that need a generic
        # pass-through Process block under the legacy ``"process_block"``
        # registry alias rely on the test-only registration hook in
        # ``tests/conftest.py``.

        for cls in (
            IOBlock,
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
            if inspect.isabstract(cls):
                continue
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
        """Tier 2: scan ``scieasy.blocks`` entry-points using callable protocol.

        Each entry-point resolves to a callable.  When invoked, it returns
        either:

        * ``(PackageInfo, list[type[Block]])`` -- package metadata + block list
        * ``list[type[Block]]`` -- plain list (backward compatible, uses
          entry-point name as the package display name)

        See ADR-025 for the full specification.
        """
        from scieasy.blocks.base.block import Block
        from scieasy.blocks.base.package_info import PackageInfo

        try:
            eps = importlib.metadata.entry_points()
        except Exception:
            logger.warning("Failed to load entry_points for block discovery", exc_info=True)
            return

        block_eps: Any = eps.select(group="scieasy.blocks") if hasattr(eps, "select") else eps.get("scieasy.blocks", [])

        for ep in block_eps:
            try:
                loaded = ep.load()
            except Exception:
                logger.warning(
                    "Failed to load entry_point '%s'",
                    ep.name,
                    exc_info=True,
                )
                continue

            try:
                # Invoke the callable to get blocks (and optionally PackageInfo).
                result = loaded
                if callable(loaded) and not (isinstance(loaded, type) and issubclass(loaded, Block)):
                    result = loaded()

                info: PackageInfo | None = None
                block_classes: list[type] = []

                if isinstance(result, tuple) and len(result) == 2:
                    first, second = result
                    if isinstance(first, PackageInfo) and isinstance(second, list):
                        info = first
                        block_classes = second
                    else:
                        logger.warning(
                            "Entry-point '%s' returned unexpected tuple format",
                            ep.name,
                        )
                        continue
                elif isinstance(result, list):
                    block_classes = result
                else:
                    # Legacy path: entry-point points directly to a class.
                    if isinstance(result, type) and issubclass(result, Block):
                        block_classes = [result]
                    else:
                        logger.warning(
                            "Entry-point '%s' returned unsupported type: %s",
                            ep.name,
                            type(result).__name__,
                        )
                        continue

                pkg_name = info.name if info is not None else ep.name
                if info is not None:
                    self._packages[info.name] = info

                for cls in block_classes:
                    if isinstance(cls, type) and issubclass(cls, Block) and not inspect.isabstract(cls):
                        block_spec = _spec_from_class(cls, source="entry_point")
                        block_spec.module_path = cls.__module__
                        block_spec.class_name = cls.__name__
                        block_spec.package_name = pkg_name
                        self._register_spec(block_spec)
                    elif isinstance(cls, type) and issubclass(cls, Block) and inspect.isabstract(cls):
                        logger.warning(
                            "Entry-point '%s' contained abstract Block class: %s",
                            ep.name,
                            cls.__name__,
                        )
                    else:
                        logger.warning(
                            "Entry-point '%s' contained non-Block item: %s",
                            ep.name,
                            cls,
                        )
            except Exception:
                logger.warning(
                    "Failed to process entry_point '%s'",
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

    def packages(self) -> dict[str, PackageInfo]:
        """Return registered package metadata keyed by package name.

        Only packages that provided a :class:`PackageInfo` via the
        ``(PackageInfo, list)`` return convention are included.
        """
        return dict(self._packages)

    def specs_by_package(self) -> dict[str, list[BlockSpec]]:
        """Return block specs grouped by ``package_name``.

        Blocks without a ``package_name`` (builtins, Tier 1) are grouped
        under the empty string key ``""``.
        """
        grouped: dict[str, list[BlockSpec]] = {}
        for spec in self._registry.values():
            grouped.setdefault(spec.package_name, []).append(spec)
        return grouped

    def all_specs(self) -> dict[str, BlockSpec]:
        """Return a copy of the full registry mapping."""
        return dict(self._registry)


def _spec_from_class(cls: type, source: str = "") -> BlockSpec:
    """Build a :class:`BlockSpec` from a Block subclass's class-level metadata.

    ADR-028 Addendum 1 D3: validates ``dynamic_ports`` shape at scan time and
    captures both ``direction`` (for IO blocks) and ``dynamic_ports`` (for
    enum-driven dynamic-port blocks) onto the spec.
    """
    # Fail loudly at scan time on malformed dynamic-port descriptors.
    BlockRegistry._validate_dynamic_ports(cls)

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
        direction=getattr(cls, "direction", "") or "",
        dynamic_ports=getattr(cls, "dynamic_ports", None),
    )


def _infer_category(cls: type) -> str:
    """Infer the block category from the class hierarchy."""
    # TODO(agent-b, stage-10.1): check ``cls.category`` ClassVar override first.
    # If ``getattr(cls, "category", "")`` is a non-empty string, return it
    # verbatim before falling through to the hierarchy checks below.
    # See docs/design/stage-10-1-palette.md §3.2.1 for the full resolution order.
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
