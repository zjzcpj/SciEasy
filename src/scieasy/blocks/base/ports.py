"""Port, InputPort, OutputPort — typed connection endpoints on blocks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(kw_only=True)
class Port:
    """Base class for block connection endpoints."""

    name: str
    accepted_types: list[type]
    description: str = ""
    required: bool = True


@dataclass(kw_only=True)
class InputPort(Port):
    """An input connection endpoint on a block."""

    default: Any | None = None
    constraint: Callable[[Any], bool] | None = None
    constraint_description: str = ""


@dataclass(kw_only=True)
class OutputPort(Port):
    """An output connection endpoint on a block."""
