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


class IOBlock(Block):
    """Abstract base for blocks that load or save data.

    Subclasses must override :meth:`load` (for ``direction='input'``)
    or :meth:`save` (for ``direction='output'``). The default
    :meth:`run` dispatches based on the ``direction`` ClassVar.
    """

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
            return {"path": str(config.get("path"))}
