"""Block ABC — validate(), run(), postprocess() contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from scieasy.core.types.collection import Collection

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort, port_accepts_type, validate_port_constraint
from scieasy.blocks.base.state import BlockState, ExecutionMode

# Valid state transitions (ADR-018: added CANCELLED, SKIPPED).
_VALID_TRANSITIONS: dict[BlockState, set[BlockState]] = {
    BlockState.IDLE: {BlockState.READY, BlockState.SKIPPED, BlockState.ERROR},
    BlockState.READY: {BlockState.RUNNING, BlockState.SKIPPED, BlockState.ERROR},
    BlockState.RUNNING: {BlockState.DONE, BlockState.PAUSED, BlockState.ERROR, BlockState.CANCELLED},
    BlockState.PAUSED: {BlockState.RUNNING, BlockState.ERROR, BlockState.CANCELLED},
    BlockState.DONE: {BlockState.IDLE},
    BlockState.ERROR: {BlockState.IDLE},
    BlockState.CANCELLED: {BlockState.IDLE},  # ADR-018: user explicitly terminated
    BlockState.SKIPPED: {BlockState.IDLE},  # ADR-018: upstream input unavailable
}


def _is_view_proxy(value: object) -> bool:
    """Check if *value* is a ViewProxy without top-level import."""
    from scieasy.core.proxy import ViewProxy

    return isinstance(value, ViewProxy)


class Block(ABC):
    """Abstract base class for all processing blocks.

    Subclasses must override :meth:`run`.  The optional :meth:`validate` and
    :meth:`postprocess` hooks have working default implementations.
    """

    # -- class-level metadata --------------------------------------------------

    name: ClassVar[str] = "Unnamed Block"
    description: ClassVar[str] = ""
    version: ClassVar[str] = "0.1.0"

    input_ports: ClassVar[list[InputPort]] = []
    output_ports: ClassVar[list[OutputPort]] = []

    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.AUTO
    # ADR-020: batch_mode and on_batch_error REMOVED — Collection iteration is block-internal.
    # ADR-019: grace period for SIGTERM before SIGKILL on cancellation.
    terminate_grace_sec: ClassVar[float] = 5.0

    key_dependencies: ClassVar[list[str]] = []

    # -- instance lifecycle ----------------------------------------------------

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: BlockConfig = BlockConfig(**(config or {}))
        self.state: BlockState = BlockState.IDLE

    def transition(self, target: BlockState) -> None:
        """Transition to *target* state, raising if the transition is invalid."""
        allowed = _VALID_TRANSITIONS.get(self.state, set())
        if target not in allowed:
            raise RuntimeError(f"Invalid state transition: {self.state.value} -> {target.value}")
        self.state = target

    # -- hooks -----------------------------------------------------------------

    def validate(self, inputs: dict[str, Any]) -> bool:
        """Validate *inputs* against the block's port contract.

        Checks:
        1. All required ports have a value in *inputs*.
        2. Each supplied value's type is accepted by the port.
        3. Each port's constraint function (if any) passes.

        Returns ``True`` when all inputs satisfy their constraints.
        Raises ``ValueError`` on the first failed check.
        """
        port_map = {p.name: p for p in self.input_ports}

        # Check required ports are present.
        for port in self.input_ports:
            if port.required and port.name not in inputs and port.default is None:
                raise ValueError(f"Required input port '{port.name}' is missing.")

        # Check types and constraints for supplied inputs.
        for key, value in inputs.items():
            if key not in port_map:
                continue
            port = port_map[key]

            # Type check: handle Collection, ViewProxy, and plain types.
            from scieasy.core.types.collection import Collection

            if isinstance(value, Collection):
                # ADR-020-Add6: Collection transparency — pass instance directly
                # so port_accepts_type() can inspect item_type.
                if port.accepted_types and not port_accepts_type(port, value):
                    accepted = [t.__name__ for t in port.accepted_types]
                    item_type_name = value.item_type.__name__ if value.item_type else "unknown"
                    raise ValueError(
                        f"Port '{port.name}': Collection item type {item_type_name} not compatible with {accepted}"
                    )
            elif _is_view_proxy(value):
                # For proxies, we can't do isinstance; check signature instead.
                from scieasy.blocks.base.ports import port_accepts_signature

                if not port_accepts_signature(port, value.dtype_info):
                    accepted = [t.__name__ for t in port.accepted_types]
                    raise ValueError(
                        f"Port '{port.name}': type signature {value.dtype_info.type_chain} "
                        f"not compatible with accepted types {accepted}"
                    )
            else:
                actual_type = type(value)
                if port.accepted_types and not port_accepts_type(port, actual_type):
                    accepted = [t.__name__ for t in port.accepted_types]
                    raise ValueError(f"Port '{port.name}': got {actual_type.__name__}, expected one of {accepted}")

            # Constraint check.
            ok, desc = validate_port_constraint(port, value)
            if not ok:
                raise ValueError(f"Port '{port.name}' constraint failed: {desc}")

        return True

    @abstractmethod
    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Execute the block's main logic and return output mapping."""
        ...

    def postprocess(self, outputs: dict[str, Collection]) -> dict[str, Collection]:
        """Optional post-processing of *outputs* before downstream delivery.

        ADR-020: Outputs are ``dict[str, Collection]`` — each value is a
        Collection wrapping the block's output DataObjects for that port.
        Default implementation passes outputs through unchanged.
        """
        return outputs

    # -- ADR-020: Collection utilities (Tier 1/2/3 block authoring) ----------

    def process_item(self, item: Any, config: BlockConfig) -> Any:
        """Tier 1 entry point: override for per-item processing.

        The default ``run()`` in :class:`ProcessBlock` iterates the primary
        input Collection and calls this method for each item, auto-flushing
        each result. 80% of blocks only need to override this method.
        """
        raise NotImplementedError("Subclass must implement process_item()")

    @staticmethod
    def pack(items: list[Any], item_type: type | None = None) -> Any:
        """Pack a list of DataObjects into a Collection, auto-flushing each.

        Any item without a ``StorageReference`` is flushed to storage as a
        safety net (Tier 3).
        """
        from scieasy.core.types.collection import Collection

        flushed = [Block._auto_flush(item) for item in items]
        return Collection(flushed, item_type=item_type)

    @staticmethod
    def unpack(collection: Any) -> list[Any]:
        """Unpack a Collection into a list of DataObject instances.

        Returns DataObject instances, NOT ViewProxy (ADR-020-Add1).
        Block authors explicitly call ``.view()`` when ready to access data.
        """
        return list(collection)

    @staticmethod
    def unpack_single(collection: Any) -> Any:
        """Unpack a length-1 Collection into a single DataObject.

        Raises ``ValueError`` if the Collection does not have exactly one item.
        """
        if len(collection) != 1:
            raise ValueError(f"Expected single-item Collection, got length {len(collection)}")
        return collection[0]

    @staticmethod
    def map_items(func: Any, collection: Any) -> Any:
        """Apply *func* to each item sequentially, auto-flushing each result.

        Returns a new Collection. Peak memory: 1 input + 1 output per iteration.
        """
        from scieasy.core.types.collection import Collection

        results = []
        for item in collection:
            result = func(item)
            result = Block._auto_flush(result)
            results.append(result)
        return Collection(results, item_type=collection.item_type)

    @staticmethod
    def parallel_map(func: Any, collection: Any, max_workers: int = 4) -> Any:
        """Apply *func* to each item in parallel, auto-flushing each result.

        Returns a new Collection.

        Warning: ``parallel_map`` loads ``max_workers`` items into memory
        concurrently. For large items (images, MSI datasets), set
        ``max_workers=1`` or use ``map_items()`` which processes one item
        at a time.
        """
        from concurrent.futures import ProcessPoolExecutor

        from scieasy.core.types.collection import Collection

        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(func, collection))
        flushed = [Block._auto_flush(r) for r in results]
        return Collection(flushed, item_type=collection.item_type)

    @staticmethod
    def _auto_flush(obj: Any) -> Any:
        """Write in-memory DataObject to storage, return with StorageReference set.

        If the object already has a ``StorageReference``, return as-is (no-op).
        If no flush context output directory is configured, return as-is.
        Called internally by ``map_items``, ``parallel_map``, ``pack``, and
        the ``process_item`` default ``run()``.
        """
        from scieasy.core.types.base import DataObject

        if not isinstance(obj, DataObject):
            return obj
        if obj.storage_ref is not None:
            return obj

        from scieasy.core.storage.flush_context import get_output_dir

        output_dir = get_output_dir()
        if output_dir is None:
            return obj

        import logging
        import uuid
        from pathlib import Path

        from scieasy.core.storage.backend_router import get_router

        router = get_router()
        ext = router.extension_for(type(obj))
        filename = f"{uuid.uuid4()}{ext}"
        target_path = str(Path(output_dir) / filename)

        try:
            obj.save(target_path)
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "auto_flush failed for %s: %s",
                type(obj).__name__,
                exc,
            )
            return obj
        return obj
