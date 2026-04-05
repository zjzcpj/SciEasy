"""Tests for BlockRegistry — Tier 1 scan, hot reload, Tier 2 entry_points."""

from __future__ import annotations

from pathlib import Path

import pytest

from scieasy.blocks.base.state import BlockState
from scieasy.blocks.io.adapter_registry import AdapterRegistry
from scieasy.blocks.registry import BlockRegistry


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
