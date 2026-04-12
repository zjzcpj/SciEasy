"""Built-in process blocks shipped with the framework."""

from scieasy.blocks.process.builtins.data_router import DataRouter
from scieasy.blocks.process.builtins.filter_collection import FilterCollection
from scieasy.blocks.process.builtins.merge import MergeBlock
from scieasy.blocks.process.builtins.merge_collection import MergeCollection
from scieasy.blocks.process.builtins.pair_editor import PairEditor
from scieasy.blocks.process.builtins.slice_collection import SliceCollection
from scieasy.blocks.process.builtins.split import SplitBlock
from scieasy.blocks.process.builtins.split_collection import SplitCollection

__all__ = [
    "DataRouter",
    "FilterCollection",
    "MergeBlock",
    "MergeCollection",
    "PairEditor",
    "SliceCollection",
    "SplitBlock",
    "SplitCollection",
]
