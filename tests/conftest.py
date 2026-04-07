"""Shared test fixtures for the SciEasy test suite."""

import pytest

# ---------------------------------------------------------------------------
# Phase 11 / T-TRK-003 — test-only NoopBlock registration
# ---------------------------------------------------------------------------
#
# ``TransformBlock`` was relocated to ``tests/fixtures/noop_block.py`` as
# ``NoopBlock`` (see docs/specs/phase11-implementation-standards.md T-TRK-003).
# Production code no longer registers it as a builtin. However, ~12 existing
# test files (api/blocks, integration/cancel scenario, integration/multimodal,
# blocks/subworkflow, etc.) reference the legacy ``block_type="process_block"``
# string via the BlockRegistry, which used to resolve to ``TransformBlock``.
#
# Rather than rewrite those 12 files (out of scope for T-TRK-003 per the
# standards doc estimated diff and master plan §6.7 "no silent scope
# expansion"), this module-level hook patches ``BlockRegistry._scan_builtins``
# at test-collection time so that every fresh registry built during the
# test session also registers ``NoopBlock`` and aliases the legacy
# ``"process_block"`` type_name to it.
#
# This is a TEST-ONLY shim. Production registries created outside the
# pytest session do not see ``NoopBlock`` and do not expose
# ``"process_block"``. Per master plan §1 user override on decision 1
# (doc-external changes permitted when scoped to the feature being tested).
from scieasy.blocks import registry as _registry_module

_original_scan_builtins = _registry_module.BlockRegistry._scan_builtins


def _patched_scan_builtins(self: "_registry_module.BlockRegistry") -> None:
    _original_scan_builtins(self)
    from tests.fixtures.noop_block import NoopBlock

    spec = _registry_module._spec_from_class(NoopBlock, source="builtin")
    self._register_spec(spec)
    # Legacy alias: tests still reference block_type="process_block".
    self._aliases["process_block"] = spec.name


_registry_module.BlockRegistry._scan_builtins = _patched_scan_builtins  # type: ignore[method-assign]


@pytest.fixture()
def tmp_project_dir(tmp_path: pytest.TempPathFactory) -> "Path":  # noqa: F821
    """Create a temporary project directory structure for testing."""
    from pathlib import Path

    project_dir: Path = tmp_path / "test_project"  # type: ignore[operator]
    project_dir.mkdir()
    return project_dir
