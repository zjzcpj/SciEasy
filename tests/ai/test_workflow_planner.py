"""Tests for the workflow synthesis planner.

All tests mock the LLM provider to avoid external API calls.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scieasy.ai.synthesis.workflow_planner import (
    _build_block_catalog,
    _validate_workflow,
    plan_workflow,
)
from scieasy.blocks.registry import BlockRegistry, BlockSpec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry_with_blocks() -> BlockRegistry:
    """Return a BlockRegistry with a few mock block specs pre-registered."""
    registry = BlockRegistry()
    # Register manually instead of scanning (avoids importing real block classes)
    registry._registry["IOBlock"] = BlockSpec(
        name="IOBlock",
        description="Load or save data files",
        category="io",
        type_name="io_block",
        input_ports=[],
        output_ports=[{"name": "output", "accepted_types": ["any"]}],
    )
    registry._aliases["io_block"] = "IOBlock"

    registry._registry["TransformBlock"] = BlockSpec(
        name="TransformBlock",
        description="Apply a transformation to data",
        category="process",
        type_name="transform_block",
        input_ports=[{"name": "input", "accepted_types": ["any"]}],
        output_ports=[{"name": "output", "accepted_types": ["any"]}],
    )
    registry._aliases["transform_block"] = "TransformBlock"

    registry._registry["CodeBlock"] = BlockSpec(
        name="CodeBlock",
        description="Run inline code",
        category="code",
        type_name="code_block",
        input_ports=[{"name": "input", "accepted_types": ["any"]}],
        output_ports=[{"name": "output", "accepted_types": ["any"]}],
    )
    registry._aliases["code_block"] = "CodeBlock"
    return registry


def _valid_workflow_json(block_names: list[str] | None = None) -> str:
    """Return a valid workflow JSON string using given block names."""
    if block_names is None:
        block_names = ["IOBlock", "TransformBlock"]

    nodes = []
    for i, name in enumerate(block_names):
        nodes.append(
            {
                "id": f"node-{i + 1}",
                "block_type": name,
                "config": {},
                "layout": {"x": 100 + i * 200, "y": 100},
            }
        )

    edges = []
    for i in range(len(block_names) - 1):
        edges.append({"source": f"node-{i + 1}", "target": f"node-{i + 2}"})

    result = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {"transport": "collection"},
        "explanation": "Load data then transform it.",
    }
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tests: plan_workflow success
# ---------------------------------------------------------------------------


class TestPlanWorkflowSuccess:
    """Tests for successful workflow generation."""

    @patch("scieasy.ai.synthesis.workflow_planner.get_provider")
    @patch("scieasy.ai.synthesis.workflow_planner.BlockRegistry")
    @patch("scieasy.ai.synthesis.workflow_planner.AIConfig")
    def test_plan_workflow_success(
        self,
        mock_config_cls: MagicMock,
        mock_registry_cls: MagicMock,
        mock_get_provider: MagicMock,
    ) -> None:
        """Mock provider returns valid JSON, verify nodes/edges structure."""
        # Setup AIConfig mock
        mock_config = MagicMock()
        mock_config.max_retries = 3
        mock_config_cls.from_env.return_value = mock_config

        # Setup provider mock
        mock_provider = MagicMock()
        valid_response = _valid_workflow_json(["IOBlock", "TransformBlock"])
        mock_provider.generate.return_value = f"```json\n{valid_response}\n```"
        mock_get_provider.return_value = mock_provider

        # Setup registry mock -- _make_registry_with_blocks returns a real
        # BlockRegistry with pre-loaded specs. We configure the mock class
        # to return it as the instance, and override scan() to be a no-op
        # so it does not attempt real block imports.
        mock_registry = _make_registry_with_blocks()
        mock_registry.scan = MagicMock()  # type: ignore[method-assign]
        mock_registry_cls.return_value = mock_registry

        result = plan_workflow("CSV file with 1000 rows", "filter and transform data")

        assert "nodes" in result
        assert "edges" in result
        assert "explanation" in result
        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 1
        assert result["nodes"][0]["block_type"] == "IOBlock"
        assert result["nodes"][1]["block_type"] == "TransformBlock"
        assert result["edges"][0]["source"] == "node-1"
        assert result["edges"][0]["target"] == "node-2"

        # Verify provider was called
        mock_provider.generate.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: plan_workflow failures
# ---------------------------------------------------------------------------


class TestPlanWorkflowInvalidJson:
    """Tests for invalid JSON from provider."""

    @patch("scieasy.ai.synthesis.workflow_planner.get_provider")
    @patch("scieasy.ai.synthesis.workflow_planner.BlockRegistry")
    @patch("scieasy.ai.synthesis.workflow_planner.AIConfig")
    def test_plan_workflow_invalid_json(
        self,
        mock_config_cls: MagicMock,
        mock_registry_cls: MagicMock,
        mock_get_provider: MagicMock,
    ) -> None:
        """Mock returns garbage text, verify retry then RuntimeError."""
        mock_config = MagicMock()
        mock_config.max_retries = 2
        mock_config_cls.from_env.return_value = mock_config

        mock_provider = MagicMock()
        mock_provider.generate.return_value = "This is not JSON at all!!!"
        mock_get_provider.return_value = mock_provider

        mock_registry = _make_registry_with_blocks()
        mock_registry.scan = MagicMock()  # type: ignore[method-assign]
        mock_registry_cls.return_value = mock_registry

        with pytest.raises(RuntimeError, match="Failed to generate a valid workflow"):
            plan_workflow("some data", "some goal")

        # Should have retried max_retries times
        assert mock_provider.generate.call_count == 2


class TestPlanWorkflowMissingBlockType:
    """Tests for workflow with unknown block_type."""

    @patch("scieasy.ai.synthesis.workflow_planner.get_provider")
    @patch("scieasy.ai.synthesis.workflow_planner.BlockRegistry")
    @patch("scieasy.ai.synthesis.workflow_planner.AIConfig")
    def test_plan_workflow_missing_block_type(
        self,
        mock_config_cls: MagicMock,
        mock_registry_cls: MagicMock,
        mock_get_provider: MagicMock,
    ) -> None:
        """Mock returns JSON with unknown block_type, verify validation catches it."""
        mock_config = MagicMock()
        mock_config.max_retries = 1
        mock_config_cls.from_env.return_value = mock_config

        mock_provider = MagicMock()
        bad_workflow = json.dumps(
            {
                "nodes": [
                    {
                        "id": "node-1",
                        "block_type": "NonExistentBlock",
                        "config": {},
                    }
                ],
                "edges": [],
                "explanation": "Test",
            }
        )
        mock_provider.generate.return_value = bad_workflow
        mock_get_provider.return_value = mock_provider

        mock_registry = _make_registry_with_blocks()
        mock_registry.scan = MagicMock()  # type: ignore[method-assign]
        mock_registry_cls.return_value = mock_registry

        with pytest.raises(RuntimeError, match="Failed to generate a valid workflow"):
            plan_workflow("data", "goal")


class TestPlanWorkflowNoApiKey:
    """Tests for missing API key."""

    @patch("scieasy.ai.synthesis.workflow_planner.get_provider")
    @patch("scieasy.ai.synthesis.workflow_planner.AIConfig")
    def test_plan_workflow_no_api_key(
        self,
        mock_config_cls: MagicMock,
        mock_get_provider: MagicMock,
    ) -> None:
        """No env vars configured, verify graceful ValueError."""
        mock_config = MagicMock()
        mock_config_cls.from_env.return_value = mock_config
        mock_get_provider.side_effect = ValueError("No Anthropic API key provided.")

        with pytest.raises(ValueError, match="AI provider not available"):
            plan_workflow("data", "goal")


# ---------------------------------------------------------------------------
# Tests: block catalog generation
# ---------------------------------------------------------------------------


class TestBlockCatalog:
    """Tests for block catalog text generation."""

    def test_block_catalog_generation(self) -> None:
        """Verify catalog text includes registered blocks."""
        registry = _make_registry_with_blocks()
        catalog = _build_block_catalog(registry)

        assert "IOBlock" in catalog
        assert "TransformBlock" in catalog
        assert "CodeBlock" in catalog
        assert "io" in catalog
        assert "process" in catalog
        assert "code" in catalog
        assert "Load or save data files" in catalog

    def test_block_catalog_empty_registry(self) -> None:
        """Empty registry produces a placeholder message."""
        registry = BlockRegistry()
        catalog = _build_block_catalog(registry)
        assert "No blocks registered" in catalog


# ---------------------------------------------------------------------------
# Tests: validation
# ---------------------------------------------------------------------------


class TestValidateWorkflow:
    """Tests for the _validate_workflow helper."""

    def test_valid_workflow_passes(self) -> None:
        """A properly structured workflow has no validation errors."""
        registry = _make_registry_with_blocks()
        result: dict[str, Any] = json.loads(_valid_workflow_json(["IOBlock", "TransformBlock"]))
        errors = _validate_workflow(result, registry)
        assert errors == []

    def test_missing_nodes_key(self) -> None:
        """Missing 'nodes' key produces an error."""
        registry = _make_registry_with_blocks()
        errors = _validate_workflow({"edges": []}, registry)
        assert any("nodes" in e for e in errors)

    def test_missing_edges_key(self) -> None:
        """Missing 'edges' key produces an error."""
        registry = _make_registry_with_blocks()
        errors = _validate_workflow({"nodes": []}, registry)
        assert any("edges" in e for e in errors)

    def test_duplicate_node_ids(self) -> None:
        """Duplicate node IDs are caught."""
        registry = _make_registry_with_blocks()
        result: dict[str, Any] = {
            "nodes": [
                {"id": "node-1", "block_type": "IOBlock"},
                {"id": "node-1", "block_type": "TransformBlock"},
            ],
            "edges": [],
        }
        errors = _validate_workflow(result, registry)
        assert any("Duplicate" in e for e in errors)

    def test_unknown_block_type(self) -> None:
        """Unknown block_type is caught."""
        registry = _make_registry_with_blocks()
        result: dict[str, Any] = {
            "nodes": [{"id": "node-1", "block_type": "FakeBlock"}],
            "edges": [],
        }
        errors = _validate_workflow(result, registry)
        assert any("unknown block_type" in e for e in errors)

    def test_edge_references_unknown_source(self) -> None:
        """Edge with unknown source node is caught."""
        registry = _make_registry_with_blocks()
        result: dict[str, Any] = {
            "nodes": [{"id": "node-1", "block_type": "IOBlock"}],
            "edges": [{"source": "node-99", "target": "node-1"}],
        }
        errors = _validate_workflow(result, registry)
        assert any("unknown source" in e for e in errors)

    def test_edge_references_unknown_target(self) -> None:
        """Edge with unknown target node is caught."""
        registry = _make_registry_with_blocks()
        result: dict[str, Any] = {
            "nodes": [{"id": "node-1", "block_type": "IOBlock"}],
            "edges": [{"source": "node-1", "target": "node-99"}],
        }
        errors = _validate_workflow(result, registry)
        assert any("unknown target" in e for e in errors)
