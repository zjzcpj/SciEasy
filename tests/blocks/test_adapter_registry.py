"""Tests for AdapterRegistry priority enforcement (issue #213, ADR-025 Phase 2.4)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from scieasy.blocks.io.adapter_registry import BUILTIN_EXTENSIONS, AdapterRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeBuiltinAdapter:
    """Adapter that claims a built-in extension (.csv)."""

    def supported_extensions(self) -> list[str]:
        return [".csv"]


class _FakeNovelAdapter:
    """Adapter that claims a novel, non-built-in extension (.srs)."""

    def supported_extensions(self) -> list[str]:
        return [".srs"]


class _FakeMixedAdapter:
    """Adapter that claims both a built-in and a novel extension."""

    def supported_extensions(self) -> list[str]:
        return [".tiff", ".srs"]


# ---------------------------------------------------------------------------
# Tests -- BUILTIN_EXTENSIONS constant
# ---------------------------------------------------------------------------


class TestBuiltinExtensions:
    """Verify the BUILTIN_EXTENSIONS constant."""

    def test_contains_expected_extensions(self) -> None:
        expected = {".csv", ".parquet", ".tiff", ".tif", ".zarr", ".json", ".npy", ".npz"}
        assert expected == BUILTIN_EXTENSIONS

    def test_is_frozenset(self) -> None:
        assert isinstance(BUILTIN_EXTENSIONS, frozenset)


# ---------------------------------------------------------------------------
# Tests -- _register_external
# ---------------------------------------------------------------------------


class TestRegisterExternal:
    """Test the _register_external method that enforces priority."""

    def test_builtin_extension_cannot_be_overridden(self) -> None:
        """External adapter claiming a built-in extension is skipped."""
        registry = AdapterRegistry()
        registry.register_defaults()

        original_csv = registry.get_for_extension(".csv")
        registry._register_external(_FakeBuiltinAdapter, "evil-plugin")

        # The adapter for .csv must still be the original built-in one.
        assert registry.get_for_extension(".csv") is original_csv

    def test_novel_extension_can_be_registered(self) -> None:
        """External adapter registering a new extension succeeds."""
        registry = AdapterRegistry()
        registry.register_defaults()
        registry._register_external(_FakeNovelAdapter, "srs-plugin")

        assert registry.get_for_extension(".srs") is _FakeNovelAdapter

    def test_mixed_adapter_partial_registration(self) -> None:
        """Adapter with both built-in and novel extensions: only novel one registered."""
        registry = AdapterRegistry()
        registry.register_defaults()
        registry._register_external(_FakeMixedAdapter, "mixed-plugin")

        # .srs should be registered.
        assert registry.get_for_extension(".srs") is _FakeMixedAdapter
        # .tiff should still point to the original built-in adapter.
        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter

        assert registry.get_for_extension(".tiff") is TIFFAdapter

    def test_warning_logged_on_override_attempt(self, caplog: pytest.LogCaptureFixture) -> None:
        """A warning is emitted when an external adapter tries to override built-in."""
        registry = AdapterRegistry()
        registry.register_defaults()

        with caplog.at_level(logging.WARNING, logger="scieasy.blocks.io.adapter_registry"):
            registry._register_external(_FakeBuiltinAdapter, "evil-plugin")

        assert any("evil-plugin" in msg and ".csv" in msg for msg in caplog.messages)

    def test_info_logged_on_successful_registration(self, caplog: pytest.LogCaptureFixture) -> None:
        """An info message is emitted when an external adapter is successfully registered."""
        registry = AdapterRegistry()
        registry.register_defaults()

        with caplog.at_level(logging.INFO, logger="scieasy.blocks.io.adapter_registry"):
            registry._register_external(_FakeNovelAdapter, "srs-plugin")

        assert any("srs-plugin" in msg and ".srs" in msg for msg in caplog.messages)

    def test_builtin_extension_blocked_even_without_defaults(self) -> None:
        """Built-in extensions are blocked by BUILTIN_EXTENSIONS set, not by
        whether register_defaults() was called first."""
        registry = AdapterRegistry()
        # Do NOT call register_defaults() -- the set still protects the extension.
        registry._register_external(_FakeBuiltinAdapter, "attacker")

        # .csv should not be registered at all.
        with pytest.raises(KeyError):
            registry.get_for_extension(".csv")


# ---------------------------------------------------------------------------
# Tests -- scan_entry_points integration
# ---------------------------------------------------------------------------


class TestScanEntryPoints:
    """Test scan_entry_points() with mocked entry-points."""

    def test_external_adapter_via_entry_point(self) -> None:
        """Entry-point adapter for a novel extension is registered."""
        ep = MagicMock()
        ep.name = "srs-plugin"
        ep.load.return_value = _FakeNovelAdapter

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [ep]
            registry = AdapterRegistry()
            registry.register_defaults()
            registry.scan_entry_points()

        assert registry.get_for_extension(".srs") is _FakeNovelAdapter

    def test_builtin_override_blocked_via_entry_point(self, caplog: pytest.LogCaptureFixture) -> None:
        """Entry-point adapter trying to override built-in extension is blocked."""
        ep = MagicMock()
        ep.name = "csv-override"
        ep.load.return_value = _FakeBuiltinAdapter

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [ep]
            registry = AdapterRegistry()
            registry.register_defaults()

            with caplog.at_level(logging.WARNING, logger="scieasy.blocks.io.adapter_registry"):
                registry.scan_entry_points()

        from scieasy.blocks.io.adapters.csv_adapter import CSVAdapter

        assert registry.get_for_extension(".csv") is CSVAdapter
        assert any("csv-override" in msg and ".csv" in msg for msg in caplog.messages)

    def test_entry_point_load_failure_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        """Entry-point that fails to load logs a warning and does not crash."""
        ep = MagicMock()
        ep.name = "broken-plugin"
        ep.load.side_effect = ImportError("no such module")

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [ep]
            registry = AdapterRegistry()

            with caplog.at_level(logging.WARNING, logger="scieasy.blocks.io.adapter_registry"):
                registry.scan_entry_points()

        assert any("broken-plugin" in msg for msg in caplog.messages)
