"""Tests for AI block generation pipeline.

All tests use mock LLM providers -- no real API calls are made.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scieasy.ai.config import AIConfig
from scieasy.ai.generation.block_generator import (
    GenerationResult,
    _extract_block_name,
    generate_block,
    infer_category,
)

# ---------------------------------------------------------------------------
# Mock block code snippets
# ---------------------------------------------------------------------------

VALID_PROCESS_BLOCK = """\
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.blocks.base.config import BlockConfig


class DenoiseBlock(ProcessBlock):
    name = "Denoise"
    description = "Apply denoising filter"

    def run(self, inputs: dict[str, Collection],
            config: BlockConfig) -> dict[str, Collection]:
        return inputs
"""

VALID_IO_BLOCK = """\
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.collection import Collection
from scieasy.blocks.base.config import BlockConfig


class CsvLoaderBlock(IOBlock):
    name = "CsvLoader"
    description = "Load CSV data"

    def run(self, inputs: dict[str, Collection],
            config: BlockConfig) -> dict[str, Collection]:
        return {}
"""

INVALID_NO_RUN_BLOCK = """\
class BadBlock:
    name = "Bad"
    description = "Missing run method"

    def process(self):
        pass
"""

INVALID_SYNTAX_BLOCK = """\
class BrokenBlock
    def run(self):
        return
"""

FENCED_VALID_BLOCK = (
    "Here is the generated code:\n\n```python\n" + VALID_PROCESS_BLOCK + "\n```\n\nThis block applies denoising."
)

FENCED_INVALID_THEN_VALID = [
    # First response: code with no run() method
    "```python\n" + INVALID_NO_RUN_BLOCK + "\n```",
    # Second response: valid code
    "```python\n" + VALID_PROCESS_BLOCK + "\n```",
]


# ---------------------------------------------------------------------------
# Helper: mock provider
# ---------------------------------------------------------------------------


def _make_mock_provider(responses: list[str] | str) -> MagicMock:
    """Create a mock LLMProvider that returns predetermined responses."""
    provider = MagicMock()
    if isinstance(responses, str):
        provider.generate.return_value = responses
    else:
        provider.generate.side_effect = list(responses)
    return provider


def _make_test_config(max_retries: int = 3) -> AIConfig:
    """Create a test AIConfig with sensible defaults."""
    return AIConfig(
        provider="anthropic",
        api_key="test-key-not-real",
        model="test-model",
        max_retries=max_retries,
    )


# ===================================================================
# Category inference tests
# ===================================================================


class TestInferCategory:
    """Tests for infer_category()."""

    def test_io_keywords(self) -> None:
        assert infer_category("Load a CSV file from disk") == "io"
        assert infer_category("Save images to TIFF format") == "io"
        assert infer_category("Read OME-ZARR dataset") == "io"
        assert infer_category("Export results to HDF5") == "io"

    def test_process_keywords(self) -> None:
        assert infer_category("Apply Gaussian filter to images") == "process"
        assert infer_category("Segment cells using watershed") == "process"
        assert infer_category("Normalize intensity values") == "process"
        assert infer_category("Threshold and detect features") == "process"

    def test_code_keywords(self) -> None:
        assert infer_category("Execute a custom Python script") == "code"
        assert infer_category("Run inline code snippet") == "code"

    def test_app_keywords(self) -> None:
        assert infer_category("Launch napari GUI for manual review") == "app"
        assert infer_category("Open external application ImageJ") == "app"

    def test_ai_keywords(self) -> None:
        assert infer_category("Use an LLM to generate text") == "ai"
        assert infer_category("AI-powered prompt with Claude chatgpt") == "ai"

    def test_default_to_process(self) -> None:
        """Unknown descriptions default to 'process'."""
        assert infer_category("do something mysterious") == "process"
        assert infer_category("") == "process"

    def test_highest_score_wins(self) -> None:
        """When multiple categories match, the one with more hits wins."""
        # "filter" and "transform" both match process (2 hits)
        # "load" matches io (1 hit)
        assert infer_category("filter and transform loaded data") == "process"


# ===================================================================
# Block name extraction tests
# ===================================================================


class TestExtractBlockName:
    """Tests for _extract_block_name()."""

    def test_extracts_class_name(self) -> None:
        assert _extract_block_name(VALID_PROCESS_BLOCK) == "DenoiseBlock"

    def test_extracts_first_class(self) -> None:
        code = "class FirstBlock:\n    pass\nclass SecondBlock:\n    pass\n"
        assert _extract_block_name(code) == "FirstBlock"

    def test_syntax_error_returns_default(self) -> None:
        assert _extract_block_name("class Broken(\n") == "GeneratedBlock"

    def test_no_class_returns_default(self) -> None:
        assert _extract_block_name("x = 1\ny = 2\n") == "GeneratedBlock"

    def test_empty_code_returns_default(self) -> None:
        assert _extract_block_name("") == "GeneratedBlock"


# ===================================================================
# Generation pipeline tests
# ===================================================================


class TestGenerateBlock:
    """Tests for the main generate_block() function."""

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_success_on_first_attempt(self, mock_get_provider: MagicMock) -> None:
        """Valid code on first LLM call produces a successful result."""
        provider = _make_mock_provider(FENCED_VALID_BLOCK)
        mock_get_provider.return_value = provider
        config = _make_test_config()

        result = generate_block("Apply denoising filter", category="process", config=config)

        assert isinstance(result, GenerationResult)
        assert result.validation_report["passed"] is True
        assert result.block_name == "DenoiseBlock"
        assert result.attempts == 1
        assert result.category == "process"
        assert "class DenoiseBlock" in result.code
        provider.generate.assert_called_once()

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_category_inference_used_when_none(self, mock_get_provider: MagicMock) -> None:
        """Category is inferred from description when not provided."""
        provider = _make_mock_provider("```python\n" + VALID_IO_BLOCK + "\n```")
        mock_get_provider.return_value = provider
        config = _make_test_config()

        result = generate_block("Load CSV files from disk", config=config)

        assert result.category == "io"

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_explicit_category_overrides_inference(self, mock_get_provider: MagicMock) -> None:
        """Explicit category is used even if description suggests another."""
        provider = _make_mock_provider(FENCED_VALID_BLOCK)
        mock_get_provider.return_value = provider
        config = _make_test_config()

        result = generate_block("Load and filter data", category="ai", config=config)

        assert result.category == "ai"

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_retry_on_validation_failure(self, mock_get_provider: MagicMock) -> None:
        """Failed validation triggers retry with error feedback."""
        provider = _make_mock_provider(FENCED_INVALID_THEN_VALID)
        mock_get_provider.return_value = provider
        config = _make_test_config(max_retries=3)

        result = generate_block("Apply denoising", category="process", config=config)

        assert result.validation_report["passed"] is True
        assert result.attempts == 2
        assert result.block_name == "DenoiseBlock"
        assert provider.generate.call_count == 2

        # Second call should include error feedback
        second_call_prompt = provider.generate.call_args_list[1][0][0]
        assert "validation errors" in second_call_prompt

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_max_retries_exceeded(self, mock_get_provider: MagicMock) -> None:
        """All retries fail: returns last attempt with validation_passed=False."""
        bad_response = "```python\n" + INVALID_NO_RUN_BLOCK + "\n```"
        provider = _make_mock_provider([bad_response, bad_response, bad_response])
        mock_get_provider.return_value = provider
        config = _make_test_config(max_retries=3)

        result = generate_block("Make something", category="process", config=config)

        assert result.validation_report["passed"] is False
        assert result.attempts == 3
        assert result.block_name == "BadBlock"
        assert provider.generate.call_count == 3

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_empty_llm_response_retries(self, mock_get_provider: MagicMock) -> None:
        """Empty LLM response triggers retry."""
        provider = _make_mock_provider(["", FENCED_VALID_BLOCK])
        mock_get_provider.return_value = provider
        config = _make_test_config(max_retries=3)

        result = generate_block("Apply filter", category="process", config=config)

        assert result.validation_report["passed"] is True
        assert result.attempts == 2

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_system_prompt_passed_to_provider(self, mock_get_provider: MagicMock) -> None:
        """System prompt is passed to provider.generate()."""
        provider = _make_mock_provider(FENCED_VALID_BLOCK)
        mock_get_provider.return_value = provider
        config = _make_test_config()

        generate_block("Filter images", category="process", config=config)

        call_kwargs = provider.generate.call_args
        assert "system" in call_kwargs.kwargs or len(call_kwargs.args) > 1
        # Check system prompt content
        system_arg = call_kwargs.kwargs.get("system", "")
        assert "SciEasy block code generator" in system_arg
        assert "ADR-017" in system_arg
        assert "ADR-020" in system_arg
        assert "ADR-022" in system_arg

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_config_passed_to_provider(self, mock_get_provider: MagicMock) -> None:
        """AIConfig is passed through to provider.generate()."""
        provider = _make_mock_provider(FENCED_VALID_BLOCK)
        mock_get_provider.return_value = provider
        config = _make_test_config()

        generate_block("Filter images", category="process", config=config)

        call_kwargs = provider.generate.call_args.kwargs
        assert call_kwargs.get("config") is config

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_result_structure(self, mock_get_provider: MagicMock) -> None:
        """GenerationResult has all expected fields."""
        provider = _make_mock_provider(FENCED_VALID_BLOCK)
        mock_get_provider.return_value = provider
        config = _make_test_config()

        result = generate_block("Filter images", category="process", config=config)

        assert hasattr(result, "code")
        assert hasattr(result, "block_name")
        assert hasattr(result, "validation_report")
        assert hasattr(result, "attempts")
        assert hasattr(result, "category")
        assert isinstance(result.validation_report, dict)
        assert "passed" in result.validation_report
        assert "errors" in result.validation_report
        assert "warnings" in result.validation_report

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_default_config_from_env(self, mock_get_provider: MagicMock) -> None:
        """When config=None, AIConfig.from_env() is used."""
        provider = _make_mock_provider(FENCED_VALID_BLOCK)
        mock_get_provider.return_value = provider

        with patch("scieasy.ai.generation.block_generator.AIConfig") as mock_config_cls:
            mock_config_instance = _make_test_config()
            mock_config_cls.from_env.return_value = mock_config_instance

            generate_block("Filter images", category="process", config=None)

            mock_config_cls.from_env.assert_called_once()

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_unknown_category_falls_back_to_process_template(self, mock_get_provider: MagicMock) -> None:
        """Unknown category uses process template as fallback."""
        provider = _make_mock_provider(FENCED_VALID_BLOCK)
        mock_get_provider.return_value = provider
        config = _make_test_config()

        result = generate_block("Do something", category="unknown_cat", config=config)

        # Should still work -- uses process template as fallback
        assert result.category == "unknown_cat"
        assert result.validation_report["passed"] is True

    @patch("scieasy.ai.generation.block_generator.get_provider")
    def test_max_retries_one_means_single_attempt(self, mock_get_provider: MagicMock) -> None:
        """max_retries=1 means only one attempt."""
        bad_response = "```python\n" + INVALID_NO_RUN_BLOCK + "\n```"
        provider = _make_mock_provider([bad_response])
        mock_get_provider.return_value = provider
        config = _make_test_config(max_retries=1)

        result = generate_block("Make something", category="process", config=config)

        assert result.validation_report["passed"] is False
        assert result.attempts == 1
        assert provider.generate.call_count == 1


# ===================================================================
# GenerationResult dataclass tests
# ===================================================================


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_defaults(self) -> None:
        result = GenerationResult(code="x = 1", block_name="Test")
        assert result.code == "x = 1"
        assert result.block_name == "Test"
        assert result.validation_report == {}
        assert result.attempts == 1
        assert result.category == ""

    def test_full_construction(self) -> None:
        report = {"passed": True, "errors": [], "warnings": []}
        result = GenerationResult(
            code="class A:\n  def run(self): pass",
            block_name="A",
            validation_report=report,
            attempts=2,
            category="process",
        )
        assert result.validation_report["passed"] is True
        assert result.attempts == 2
        assert result.category == "process"
