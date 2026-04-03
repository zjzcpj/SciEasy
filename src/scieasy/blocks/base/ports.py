"""Port, InputPort, OutputPort — typed connection endpoints on blocks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from scieasy.core.types.base import DataObject, TypeSignature


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


def port_accepts_type(port: Port, data_type: type) -> bool:
    """Check whether *port* accepts *data_type* (isinstance-based, inheritance-aware).

    Returns ``True`` if *data_type* is a subclass of any type listed in
    ``port.accepted_types``.  An empty ``accepted_types`` list means the port
    accepts anything.
    """
    if not port.accepted_types:
        return True
    return any(issubclass(data_type, t) for t in port.accepted_types)


def port_accepts_signature(port: Port, signature: TypeSignature) -> bool:
    """Check whether *port* accepts a :class:`TypeSignature`.

    Builds the signature for each accepted type and checks if the incoming
    signature matches (i.e. is a subtype of) at least one of them.
    """
    if not port.accepted_types:
        return True
    for accepted in port.accepted_types:
        accepted_sig = TypeSignature.from_type(accepted)
        if signature.matches(accepted_sig):
            return True
    return False


def validate_port_constraint(port: InputPort, value: Any) -> tuple[bool, str]:
    """Validate *value* against the input port's constraint function.

    Returns ``(True, "")`` if valid or no constraint is set.
    Returns ``(False, description)`` on constraint failure.
    """
    if port.constraint is None:
        return True, ""
    try:
        result = port.constraint(value)
    except Exception as exc:
        return False, f"Constraint raised {type(exc).__name__}: {exc}"
    if not result:
        return False, port.constraint_description or "Constraint not satisfied"
    return True, ""


def validate_connection(
    source_port: OutputPort,
    target_port: InputPort,
) -> tuple[bool, str]:
    """Check whether an edge from *source_port* to *target_port* is type-compatible.

    Returns ``(True, "")`` if at least one type produced by the source is
    accepted by the target.  Returns ``(False, reason)`` otherwise.
    """
    if not source_port.accepted_types:
        # Source can produce anything — always compatible.
        return True, ""
    if not target_port.accepted_types:
        # Target accepts anything — always compatible.
        return True, ""

    for src_type in source_port.accepted_types:
        if any(issubclass(src_type, tgt_type) for tgt_type in target_port.accepted_types):
            return True, ""

    src_names = [t.__name__ for t in source_port.accepted_types]
    tgt_names = [t.__name__ for t in target_port.accepted_types]
    return False, (
        f"Source port '{source_port.name}' produces {src_names} but "
        f"target port '{target_port.name}' accepts {tgt_names}"
    )
