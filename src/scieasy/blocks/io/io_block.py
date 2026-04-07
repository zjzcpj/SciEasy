"""IOBlock — abstract base for plugin-owned data ingress and egress.

Per ADR-028 §D1, ``IOBlock`` is an abstract base class. Subclasses
override :meth:`load` (for ``direction="input"``) or :meth:`save` (for
``direction="output"``); the default :meth:`run` dispatches based on
the ``direction`` ClassVar.

The legacy ``adapter_registry`` / ``adapters/`` dispatch layer was
removed in T-TRK-004. Concrete core loaders (``LoadData``, ``SaveData``)
arrive in T-TRK-007 and T-TRK-008. Plugin-owned IO blocks (e.g.
``LoadImage`` in ``scieasy-blocks-imaging``) subclass ``IOBlock``
directly and register via the ``scieasy.blocks`` entry-point group.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy.core.types.text import Text


class IOBlock(Block):
    """Abstract base for blocks that load or save data.

    Subclasses must override :meth:`load` (for ``direction='input'``)
    or :meth:`save` (for ``direction='output'``). The default
    :meth:`run` dispatches based on the ``direction`` ClassVar.
    """

    # ``name`` and ``description`` are preserved from the pre-T-TRK-004
    # concrete IOBlock so that the existing ``BlockRegistry`` builtin
    # registration (``registry._scan_builtins``) keeps surfacing the
    # ``"IO Block"`` / ``"io_block"`` identity that integration tests,
    # workflow YAMLs, and the API connection-validator depend on. The
    # spec body at standards doc lines 914-976 omits these but does not
    # forbid them; ADR-028 §D1 only mandates ``load`` / ``save``
    # abstractness and the ``run()`` dispatch contract.
    name: ClassVar[str] = "IO Block"
    description: ClassVar[str] = "Abstract base for blocks that load or save data."

    direction: ClassVar[str] = "input"
    category: ClassVar[str] = "io"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[DataObject], required=False),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="data", accepted_types=[DataObject]),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {"path": {"type": "string", "ui_priority": 1}},
        "required": ["path"],
    }

    @abstractmethod
    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Load and return a single :class:`DataObject` or :class:`Collection`."""
        ...

    @abstractmethod
    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Persist *obj* to the configured path."""
        ...

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Dispatch to :meth:`load` or :meth:`save` based on ``direction``.

        For ``direction='input'`` the result of :meth:`load` is wrapped
        in a single-item :class:`Collection` if it is not already a
        Collection, and returned under the ``"data"`` output port.

        For ``direction='output'`` the ``"data"`` input is required and
        is forwarded to :meth:`save`; the configured ``path`` is
        returned under the ``"path"`` key for downstream consumers.
        """
        if self.direction == "input":
            result = self.load(config)
            if not isinstance(result, Collection):
                result = Collection(items=[result], item_type=type(result))
            return {"data": result}
        else:
            data = inputs.get("data")
            if data is None:
                raise ValueError("IOBlock(output) requires 'data' input")
            self.save(data, config)
            # T-TRK-008: wrap the path receipt in a single-item Collection
            # of Text so the return type matches the public
            # ``dict[str, Collection]`` signature without a type-ignore
            # suppression. The pre-T-TRK-004 IOBlock returned a bare
            # string here; the spec body for the post-T-TRK-004 ABC made
            # the same shape literal which forced a targeted
            # ``# type: ignore[dict-item]``. Wrapping in a typed
            # ``Text`` Collection preserves the "configured path" receipt
            # semantics for downstream consumers (they call
            # ``coll[0].content`` instead of ``result["path"]``) and
            # restores strict typing across the IO surface. See
            # ``project_phase11_ttrk007_008_bookkeeping.md`` Item 1.
            path_receipt = Text(content=str(config.get("path")), format="plain")
            return {"path": Collection(items=[path_receipt], item_type=Text)}
