"""IOBlock — data ingress and egress with pluggable format adapters."""

from __future__ import annotations

from scieasy.blocks.io.io_block import IOBlock
from scieasy.blocks.io.savers.save_data import SaveData

__all__ = ["IOBlock", "SaveData"]
