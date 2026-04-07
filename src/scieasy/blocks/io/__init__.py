"""IO blocks — abstract base + core dynamic-port concrete loaders/savers.

The :class:`IOBlock` ABC (post-T-TRK-004) is the base every IO block
must inherit from; the concrete core loader :class:`LoadData` is added
in T-TRK-007 per ADR-028 Addendum 1 §C5 / §C9. The concrete core saver
``SaveData`` arrives in T-TRK-008.
"""

from __future__ import annotations

from scieasy.blocks.io.io_block import IOBlock
from scieasy.blocks.io.loaders.load_data import LoadData

__all__ = ["IOBlock", "LoadData"]
