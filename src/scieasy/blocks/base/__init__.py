"""Block ABC and core machinery — ports, config, state, results."""

from __future__ import annotations

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import (
    InputPort,
    OutputPort,
    Port,
    port_accepts_signature,
    port_accepts_type,
    validate_connection,
    validate_port_constraint,
)
from scieasy.blocks.base.result import BatchResult, BlockResult
from scieasy.blocks.base.state import (
    BatchErrorStrategy,
    BatchMode,
    BlockState,
    ExecutionMode,
    InputDelivery,
)

__all__ = [
    "BatchErrorStrategy",
    "BatchMode",
    "BatchResult",
    "Block",
    "BlockConfig",
    "BlockResult",
    "BlockState",
    "ExecutionMode",
    "InputDelivery",
    "InputPort",
    "OutputPort",
    "Port",
    "port_accepts_signature",
    "port_accepts_type",
    "validate_connection",
    "validate_port_constraint",
]
