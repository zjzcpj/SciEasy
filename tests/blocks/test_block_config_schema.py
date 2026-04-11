"""Tests for Block.config_schema ClassVar and registry propagation."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.registry import _spec_from_class
from scieasy.core.types.collection import Collection


class TestBlockConfigSchema:
    """Tests for config_schema on Block base and subclasses."""

    def test_base_block_has_default_empty_schema(self) -> None:
        assert Block.config_schema == {"type": "object", "properties": {}}

    def test_io_block_schema_contains_path(self) -> None:
        # T-TRK-004 / ADR-028 §D1: the new IOBlock config_schema is
        # intentionally minimal — only ``path`` survives. The legacy
        # ``direction`` and ``format`` properties were removed when the
        # adapter dispatch layer was deleted. ``direction`` is now a
        # ClassVar on subclasses (``input`` / ``output``), not user
        # config.
        from scieasy.blocks.io.io_block import IOBlock

        schema = IOBlock.config_schema
        assert schema["type"] == "object"
        assert "path" in schema["properties"]
        assert "path" in schema.get("required", [])

    def test_code_block_schema_contains_language(self) -> None:
        from scieasy.blocks.code.code_block import CodeBlock

        schema = CodeBlock.config_schema
        assert "language" in schema["properties"]
        assert "python" in schema["properties"]["language"]["enum"]

    def test_spec_from_class_includes_config_schema(self) -> None:
        class MyBlock(Block):
            name: ClassVar[str] = "Test Block"
            config_schema: ClassVar[dict[str, Any]] = {
                "type": "object",
                "properties": {"threshold": {"type": "number"}},
            }

            def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
                return {}

        spec = _spec_from_class(MyBlock, source="test")
        assert spec.config_schema["properties"]["threshold"]["type"] == "number"

    def test_appblock_schema_executable_path_and_output_dir(self) -> None:
        """Issue #571: AppBlock config_schema has Executable Path (file_browser, priority 0)
        and Save Outputs At (directory_browser, priority 1)."""
        from scieasy.blocks.app.app_block import AppBlock

        schema = AppBlock.config_schema
        props = schema["properties"]
        # app_command renamed to "Executable Path" with file_browser
        assert props["app_command"]["title"] == "Executable Path"
        assert props["app_command"]["ui_widget"] == "file_browser"
        assert props["app_command"]["ui_priority"] == 0
        # output_dir is "Save Outputs At" with directory_browser, priority 1
        assert props["output_dir"]["title"] == "Save Outputs At"
        assert props["output_dir"]["ui_widget"] == "directory_browser"
        assert props["output_dir"]["ui_priority"] == 1

    def test_spec_from_class_default_when_no_schema(self) -> None:
        class PlainBlock(Block):
            name: ClassVar[str] = "Plain"

            def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
                return {}

        spec = _spec_from_class(PlainBlock, source="test")
        # ADR-030: _merge_config_schema always produces a ``required`` key.
        assert spec.config_schema == {"type": "object", "properties": {}, "required": []}
