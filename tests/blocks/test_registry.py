"""Tests for BlockRegistry — Tier 1 scan, hot reload, Tier 2 entry_points."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scieasy.blocks.base.package_info import PackageInfo
from scieasy.blocks.base.state import BlockState
from scieasy.blocks.io.adapter_registry import AdapterRegistry
from scieasy.blocks.registry import BlockRegistry, BlockSpec


class TestBlockRegistryTier2:
    """Tier 2: entry_point discovery (always available from installed package)."""

    def test_scan_discovers_entry_points(self) -> None:
        reg = BlockRegistry()
        reg.scan()
        specs = reg.all_specs()
        # Should find at least the built-in blocks from pyproject.toml entry_points.
        assert len(specs) >= 3
        names = list(specs.keys())
        assert "Merge" in names
        assert "Split" in names

    def test_instantiate_by_name(self) -> None:
        reg = BlockRegistry()
        reg.scan()
        block = reg.instantiate("Merge")
        assert block.name == "Merge"
        assert block.state == BlockState.IDLE

    def test_instantiate_unknown_raises(self) -> None:
        reg = BlockRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.instantiate("NonexistentBlock")


class TestBlockRegistryTier1:
    """Tier 1: drop-in directory scan."""

    def test_scan_discovers_dropin(self, tmp_path: Path) -> None:
        """A .py file with a Block subclass in a scan dir is discovered."""
        dropin = tmp_path / "my_block.py"
        dropin.write_text(
            "from scieasy.blocks.process.process_block import ProcessBlock\n"
            "from scieasy.blocks.base.config import BlockConfig\n"
            "from typing import Any\n"
            "\n"
            "class MyCustomBlock(ProcessBlock):\n"
            "    name = 'My Custom'\n"
            "    algorithm = 'custom'\n"
            "\n"
            "    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:\n"
            "        return {'out': 'hello'}\n"
        )

        reg = BlockRegistry()
        reg.add_scan_dir(tmp_path)
        reg.scan()

        specs = reg.all_specs()
        assert "My Custom" in specs
        assert specs["My Custom"].source == "tier1"
        assert specs["My Custom"].category == "process"

    def test_hot_reload_picks_up_new_file(self, tmp_path: Path) -> None:
        """hot_reload() discovers a file added after initial scan."""
        reg = BlockRegistry()
        reg.add_scan_dir(tmp_path)
        reg.scan()

        initial_count = len(reg.all_specs())

        # Add a new block file.
        new_block = tmp_path / "new_block.py"
        new_block.write_text(
            "from scieasy.blocks.process.process_block import ProcessBlock\n"
            "from scieasy.blocks.base.config import BlockConfig\n"
            "from typing import Any\n"
            "\n"
            "class NewBlock(ProcessBlock):\n"
            "    name = 'New Block'\n"
            "    algorithm = 'new'\n"
            "\n"
            "    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:\n"
            "        return {}\n"
        )

        reg.hot_reload()
        assert len(reg.all_specs()) > initial_count
        assert "New Block" in reg.all_specs()

    def test_hot_reload_removes_deleted_file(self, tmp_path: Path) -> None:
        """hot_reload() removes specs for deleted files."""
        dropin = tmp_path / "temp_block.py"
        dropin.write_text(
            "from scieasy.blocks.process.process_block import ProcessBlock\n"
            "from scieasy.blocks.base.config import BlockConfig\n"
            "from typing import Any\n"
            "\n"
            "class TempBlock(ProcessBlock):\n"
            "    name = 'Temp Block'\n"
            "    algorithm = 'temp'\n"
            "\n"
            "    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:\n"
            "        return {}\n"
        )

        reg = BlockRegistry()
        reg.add_scan_dir(tmp_path)
        reg.scan()
        assert "Temp Block" in reg.all_specs()

        # Delete the file and hot-reload.
        dropin.unlink()
        reg.hot_reload()
        assert "Temp Block" not in reg.all_specs()


class TestBlockRegistryLogging:
    """Tests for logged warnings on import/load failures (#169)."""

    def test_tier1_import_error_logged(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """A .py file with a syntax error should log a warning, not crash."""
        bad_file = tmp_path / "bad_block.py"
        bad_file.write_text("this is not valid python!!!")

        registry = BlockRegistry()
        registry.add_scan_dir(tmp_path)

        with caplog.at_level(logging.WARNING):
            registry.scan()

        assert "Failed to import block from" in caplog.text
        assert "bad_block" in caplog.text

    def test_tier1_import_error_does_not_prevent_other_blocks(self, tmp_path: Path) -> None:
        """A bad file should not prevent other valid blocks from loading."""
        bad = tmp_path / "bad.py"
        bad.write_text("raise ImportError('missing dep')")

        good = tmp_path / "good_block.py"
        good.write_text(
            "from scieasy.blocks.process.process_block import ProcessBlock\n"
            "from scieasy.blocks.base.config import BlockConfig\n"
            "from typing import Any\n"
            "\n"
            "class GoodBlock(ProcessBlock):\n"
            "    name = 'good_block'\n"
            "    algorithm = 'good'\n"
            "\n"
            "    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:\n"
            "        return {}\n"
        )

        registry = BlockRegistry()
        registry.add_scan_dir(tmp_path)
        registry.scan()

        assert "good_block" in registry.all_specs()


class TestInferCategory:
    """Tests for _infer_category helper."""

    def test_infer_category_ai_block(self) -> None:
        from scieasy.blocks.ai.ai_block import AIBlock
        from scieasy.blocks.registry import _infer_category

        assert _infer_category(AIBlock) == "ai"

        class MyAIBlock(AIBlock):
            pass

        assert _infer_category(MyAIBlock) == "ai"


class TestAdapterRegistry:
    """AdapterRegistry — extension-to-adapter mapping."""

    def test_register_defaults(self) -> None:
        reg = AdapterRegistry()
        reg.register_defaults()
        adapters = reg.all_adapters()
        assert ".csv" in adapters
        assert ".parquet" in adapters
        assert ".tif" in adapters

    def test_get_for_extension(self) -> None:
        from scieasy.blocks.io.adapters.csv_adapter import CSVAdapter

        reg = AdapterRegistry()
        reg.register_defaults()
        cls = reg.get_for_extension(".csv")
        assert cls is CSVAdapter

    def test_normalisation(self) -> None:
        from scieasy.blocks.io.adapters.csv_adapter import CSVAdapter

        reg = AdapterRegistry()
        reg.register_defaults()
        assert reg.get_for_extension("CSV") is CSVAdapter
        assert reg.get_for_extension(".CSV") is CSVAdapter
        assert reg.get_for_extension("csv") is CSVAdapter

    def test_unknown_extension_raises(self) -> None:
        reg = AdapterRegistry()
        reg.register_defaults()
        with pytest.raises(KeyError, match="xyz"):
            reg.get_for_extension(".xyz")


class TestPackageInfo:
    """Tests for the PackageInfo dataclass (ADR-025 Phase 2.1)."""

    def test_creation_with_defaults(self) -> None:
        info = PackageInfo(name="Test Package")
        assert info.name == "Test Package"
        assert info.description == ""
        assert info.author == ""
        assert info.version == "0.1.0"

    def test_creation_with_all_fields(self) -> None:
        info = PackageInfo(
            name="SRS Imaging",
            description="Stimulated Raman Scattering toolkit",
            author="Dr. Wang Lab",
            version="1.2.3",
        )
        assert info.name == "SRS Imaging"
        assert info.description == "Stimulated Raman Scattering toolkit"
        assert info.author == "Dr. Wang Lab"
        assert info.version == "1.2.3"

    def test_frozen(self) -> None:
        info = PackageInfo(name="Frozen")
        with pytest.raises(AttributeError):
            info.name = "Changed"  # type: ignore[misc]

    def test_importable_from_base(self) -> None:
        from scieasy.blocks.base import PackageInfo as PackageInfoFromBase

        assert PackageInfoFromBase is PackageInfo


class TestBlockSpecPackageName:
    """Tests for the package_name field on BlockSpec (ADR-025 Phase 2.2)."""

    def test_default_package_name_is_empty(self) -> None:
        spec = BlockSpec(name="TestBlock")
        assert spec.package_name == ""

    def test_package_name_can_be_set(self) -> None:
        spec = BlockSpec(name="TestBlock", package_name="my-package")
        assert spec.package_name == "my-package"


class TestBlockRegistryPackages:
    """Tests for packages() and specs_by_package() (ADR-025 Phase 2.2)."""

    def test_packages_returns_dict(self) -> None:
        reg = BlockRegistry()
        result = reg.packages()
        assert isinstance(result, dict)
        # Empty before scan adds any external packages.
        assert len(result) == 0

    def test_packages_returns_copy(self) -> None:
        reg = BlockRegistry()
        p1 = reg.packages()
        p2 = reg.packages()
        assert p1 is not p2

    def test_specs_by_package_groups_correctly(self) -> None:
        reg = BlockRegistry()
        # Manually register some specs with different package_names.
        spec_a = BlockSpec(name="A", package_name="pkg1")
        spec_b = BlockSpec(name="B", package_name="pkg1")
        spec_c = BlockSpec(name="C", package_name="pkg2")
        spec_d = BlockSpec(name="D", package_name="")

        reg._register_spec(spec_a)
        reg._register_spec(spec_b)
        reg._register_spec(spec_c)
        reg._register_spec(spec_d)

        grouped = reg.specs_by_package()
        assert "pkg1" in grouped
        assert "pkg2" in grouped
        assert "" in grouped
        assert len(grouped["pkg1"]) == 2
        assert len(grouped["pkg2"]) == 1
        assert len(grouped[""]) == 1
        assert {s.name for s in grouped["pkg1"]} == {"A", "B"}

    def test_specs_by_package_builtins_have_empty_package(self) -> None:
        reg = BlockRegistry()
        reg.scan()
        grouped = reg.specs_by_package()
        # Built-in blocks should be under empty string or entry-point name.
        assert "" in grouped or any(grouped.values())


class TestScanTier2CallableProtocol:
    """Tests for _scan_tier2 callable protocol (ADR-025 Phase 2.2)."""

    def _make_mock_block_class(self, name: str = "MockBlock") -> type:
        """Create a minimal mock Block subclass for testing."""
        from scieasy.blocks.base.block import Block

        cls = type(
            name,
            (Block,),
            {
                "name": name,
                "description": f"Mock {name}",
                "version": "0.1.0",
                "input_ports": [],
                "output_ports": [],
                "config_schema": {"type": "object", "properties": {}},
                "run": lambda self, inputs, config: {},
            },
        )
        return cls

    def _make_mock_entry_point(self, name: str, load_return: object) -> MagicMock:
        """Create a mock entry-point that returns load_return on .load()."""
        ep = MagicMock()
        ep.name = name
        ep.value = f"mock_module:{name}"
        ep.load.return_value = load_return
        return ep

    def test_tuple_return_with_package_info(self) -> None:
        """Entry-point returning (PackageInfo, list) populates package_name."""
        info = PackageInfo(name="SRS Imaging", author="Dr. Wang")
        block_cls = self._make_mock_block_class("SRSBlock")

        def get_blocks():
            return info, [block_cls]

        ep = self._make_mock_entry_point("srs", get_blocks)

        mock_eps = MagicMock()
        mock_eps.select.return_value = [ep]

        reg = BlockRegistry()
        with patch("importlib.metadata.entry_points", return_value=mock_eps):
            reg._scan_tier2()

        # Verify block is registered with correct package_name.
        spec = reg.get_spec("SRSBlock")
        assert spec is not None
        assert spec.package_name == "SRS Imaging"
        assert spec.source == "entry_point"

        # Verify PackageInfo is stored.
        pkgs = reg.packages()
        assert "SRS Imaging" in pkgs
        assert pkgs["SRS Imaging"].author == "Dr. Wang"

    def test_plain_list_return_uses_ep_name(self) -> None:
        """Entry-point returning plain list uses ep.name as package_name."""
        block_cls = self._make_mock_block_class("GenomicsBlock")

        def get_blocks():
            return [block_cls]

        ep = self._make_mock_entry_point("genomics", get_blocks)

        mock_eps = MagicMock()
        mock_eps.select.return_value = [ep]

        reg = BlockRegistry()
        with patch("importlib.metadata.entry_points", return_value=mock_eps):
            reg._scan_tier2()

        spec = reg.get_spec("GenomicsBlock")
        assert spec is not None
        assert spec.package_name == "genomics"

        # No PackageInfo stored for plain list returns.
        assert len(reg.packages()) == 0

    def test_entry_point_load_failure_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Entry-point that fails to load logs warning and continues."""
        ep = MagicMock()
        ep.name = "bad_package"
        ep.load.side_effect = ImportError("module not found")

        mock_eps = MagicMock()
        mock_eps.select.return_value = [ep]

        reg = BlockRegistry()
        with (
            patch("importlib.metadata.entry_points", return_value=mock_eps),
            caplog.at_level(logging.WARNING),
        ):
            reg._scan_tier2()

        assert "Failed to load entry_point 'bad_package'" in caplog.text

    def test_entry_point_callable_failure_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Entry-point callable that raises logs warning and continues."""

        def bad_get_blocks():
            raise RuntimeError("something broke")

        ep = self._make_mock_entry_point("broken", bad_get_blocks)

        mock_eps = MagicMock()
        mock_eps.select.return_value = [ep]

        reg = BlockRegistry()
        with (
            patch("importlib.metadata.entry_points", return_value=mock_eps),
            caplog.at_level(logging.WARNING),
        ):
            reg._scan_tier2()

        assert "Failed to process entry_point 'broken'" in caplog.text

    def test_multiple_blocks_in_one_entry_point(self) -> None:
        """An entry-point can return multiple block classes."""
        info = PackageInfo(name="Multi-Block Package")
        cls_a = self._make_mock_block_class("AlphaBlock")
        cls_b = self._make_mock_block_class("BetaBlock")

        def get_blocks():
            return info, [cls_a, cls_b]

        ep = self._make_mock_entry_point("multi", get_blocks)

        mock_eps = MagicMock()
        mock_eps.select.return_value = [ep]

        reg = BlockRegistry()
        with patch("importlib.metadata.entry_points", return_value=mock_eps):
            reg._scan_tier2()

        assert reg.get_spec("AlphaBlock") is not None
        assert reg.get_spec("BetaBlock") is not None
        assert reg.get_spec("AlphaBlock").package_name == "Multi-Block Package"
        assert reg.get_spec("BetaBlock").package_name == "Multi-Block Package"

    def test_no_entry_points_does_not_crash(self) -> None:
        """_scan_tier2 works when no entry-points exist."""
        mock_eps = MagicMock()
        mock_eps.select.return_value = []

        reg = BlockRegistry()
        with patch("importlib.metadata.entry_points", return_value=mock_eps):
            reg._scan_tier2()

        assert len(reg.all_specs()) == 0
        assert len(reg.packages()) == 0
