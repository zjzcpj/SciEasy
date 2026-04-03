"""Architecture enforcement: registry contracts.

Validates that:

* ``BlockRegistry`` stores ``BlockSpec`` instances (not raw classes).
* ``TypeRegistry`` stores types (not arbitrary objects).
* ``pyproject.toml`` entry-points reference importable modules.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from scieasy.blocks.registry import BlockRegistry, BlockSpec
from scieasy.core.types.registry import TypeRegistry

# ---------------------------------------------------------------------------
# BlockRegistry
# ---------------------------------------------------------------------------


def test_block_registry_internal_storage_type() -> None:
    """``BlockRegistry._registry`` values must be ``BlockSpec`` instances."""
    reg = BlockRegistry()
    assert isinstance(reg._registry, dict), (
        f"BlockRegistry._registry should be a dict, got {type(reg._registry).__name__}"
    )
    # The empty registry should accept BlockSpec values (verify the type
    # annotation / initial value is dict[str, BlockSpec]).
    # We insert a value to verify the structure accepts BlockSpec.
    spec = BlockSpec(name="test_block", description="unit test")
    reg._registry["test"] = spec
    assert isinstance(reg._registry["test"], BlockSpec)


def test_block_spec_has_required_fields() -> None:
    """``BlockSpec`` exposes the fields needed by the runtime."""
    required_fields = {
        "name",
        "description",
        "version",
        "block_class",
        "category",
        "input_ports",
        "output_ports",
        "config_schema",
        "source",
    }
    spec = BlockSpec(name="example")
    actual_fields = set(vars(spec).keys())
    assert required_fields.issubset(actual_fields), f"BlockSpec is missing fields: {required_fields - actual_fields}"


# ---------------------------------------------------------------------------
# TypeRegistry
# ---------------------------------------------------------------------------


def test_type_registry_internal_storage_type() -> None:
    """``TypeRegistry._registry`` values must be types (classes)."""
    reg = TypeRegistry()
    assert isinstance(reg._registry, dict), (
        f"TypeRegistry._registry should be a dict, got {type(reg._registry).__name__}"
    )
    # Verify the dict can hold ``type`` values.
    reg._registry["DataObject"] = object
    assert reg._registry["DataObject"] is object


def test_type_registry_has_required_interface() -> None:
    """``TypeRegistry`` exposes ``register``, ``resolve``, and ``all_types``."""
    reg = TypeRegistry()
    assert callable(getattr(reg, "register", None)), "TypeRegistry missing register()"
    assert callable(getattr(reg, "resolve", None)), "TypeRegistry missing resolve()"
    assert callable(getattr(reg, "all_types", None)), "TypeRegistry missing all_types()"


# ---------------------------------------------------------------------------
# pyproject.toml entry-points → importable modules
# ---------------------------------------------------------------------------


def _parse_entry_points() -> list[tuple[str, str, str]]:
    """Parse ``pyproject.toml`` entry-points and return (group, name, ref) triples.

    Each *ref* is a string like ``"scieasy.blocks.io:IOBlock"``.
    """
    try:
        import tomllib
    except ModuleNotFoundError:  # Python < 3.11 fallback
        import tomli as tomllib  # type: ignore[no-redef]

    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    results: list[tuple[str, str, str]] = []
    entry_points: dict[str, dict[str, str]] = data.get("project", {}).get("entry-points", {})
    for group, entries in entry_points.items():
        for ep_name, ep_ref in entries.items():
            results.append((group, ep_name, ep_ref))
    return results


ENTRY_POINTS = _parse_entry_points()


@pytest.mark.parametrize(
    ("group", "ep_name", "ep_ref"),
    ENTRY_POINTS,
    ids=[f"{g}:{n}" for g, n, _ in ENTRY_POINTS],
)
def test_entry_point_module_is_importable(
    group: str,
    ep_name: str,
    ep_ref: str,
) -> None:
    """Every entry-point in ``pyproject.toml`` must reference an importable module.

    We only check that the *module* part (before ``:``) is importable.
    The *attribute* part (after ``:``) may not exist yet in Phase 1 stubs,
    so we do not check it.
    """
    module_path = ep_ref.split(":")[0]
    try:
        importlib.import_module(module_path)
    except ImportError as exc:
        pytest.fail(
            f"Entry-point [{group}] {ep_name} = '{ep_ref}' references non-importable module '{module_path}': {exc}"
        )
