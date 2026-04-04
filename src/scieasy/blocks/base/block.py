"""Block ABC — validate(), run(), postprocess() contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

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

            # Type check: unwrap ViewProxy to check dtype_info if available.
            actual_type = type(value)
            from scieasy.core.proxy import ViewProxy

            if isinstance(value, ViewProxy):
                # For proxies, we can't do isinstance; check signature instead.
                from scieasy.blocks.base.ports import port_accepts_signature

                if not port_accepts_signature(port, value.dtype_info):
                    accepted = [t.__name__ for t in port.accepted_types]
                    raise ValueError(
                        f"Port '{port.name}': type signature {value.dtype_info.type_chain} "
                        f"not compatible with accepted types {accepted}"
                    )
            else:
                if port.accepted_types and not port_accepts_type(port, actual_type):
                    accepted = [t.__name__ for t in port.accepted_types]
                    raise ValueError(f"Port '{port.name}': got {actual_type.__name__}, expected one of {accepted}")

            # Constraint check.
            ok, desc = validate_port_constraint(port, value)
            if not ok:
                raise ValueError(f"Port '{port.name}' constraint failed: {desc}")

        return True

    @abstractmethod
    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the block's main logic and return output mapping."""
        ...

    def postprocess(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Optional post-processing of *outputs* before downstream delivery.

        Default implementation passes outputs through unchanged.
        """
        return outputs

    # -- ADR-020: Collection utilities (Tier 1/2/3 block authoring) ----------

    # TODO(ADR-020-Add5): Implement process_item() — Tier 1 entry point.
    # 80% of blocks override this. Framework handles iteration, flush, packing.
    # Signature: def process_item(self, item: DataObject, config: BlockConfig) -> DataObject
    # Default run() iterates primary input Collection, calls process_item() per
    # item, auto-flushes each result, packs into output Collection.
    # Peak memory = O(1 item).

    # TODO(ADR-020): Implement pack() static method.
    # Signature: pack(items: list[DataObject], item_type: type | None = None) -> Collection
    # Auto-flushes each item if no StorageReference.

    # TODO(ADR-020): Implement unpack() static method.
    # Signature: unpack(collection: Collection) -> list[DataObject]
    # Returns DataObject instances, NOT ViewProxy (ADR-020-Add1).
    # Block authors explicitly call .view() when ready.

    # TODO(ADR-020): Implement unpack_single() static method.
    # Signature: unpack_single(collection: Collection) -> DataObject
    # Collection must have length=1, raises ValueError otherwise.

    # TODO(ADR-020): Implement map_items() static method.
    # Signature: map_items(func: Callable, collection: Collection) -> Collection
    # Sequential per-item processing. Auto-flushes each result.

    # TODO(ADR-020): Implement parallel_map() static method.
    # Signature: parallel_map(func: Callable, collection: Collection, max_workers: int = 4) -> Collection
    # Parallel per-item processing. Auto-flushes each result.
    # Memory is block author's responsibility — choose max_workers based on item size.

    # TODO(ADR-020-Add5): Implement _auto_flush() private method.
    # Signature: _auto_flush(data: DataObject) -> DataObject
    # If data has no StorageReference, write to output directory via appropriate
    # backend, replace with lightweight ref (~KB). Called by map_items,
    # parallel_map, pack, and process_item default run().
    # Subprocess worker also performs final force-write scan after block.run().
