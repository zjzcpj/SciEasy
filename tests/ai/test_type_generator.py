"""Tests for AI type generation (type_generator module)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scieasy.ai.config import AIConfig
from scieasy.ai.generation.type_generator import (
    TypeGenerationResult,
    _extract_type_name,
    generate_type,
    infer_type_family,
)

# ---------------------------------------------------------------------------
# Sample generated code snippets for mock LLM responses
# ---------------------------------------------------------------------------

_VALID_ARRAY_CODE = """\
```python
from typing import ClassVar
from scieasy.core.types.array import Array


class RamanImage(Array):
    \"\"\"Raman hyperspectral image (y, x, wavenumber).\"\"\"

    axes: ClassVar[list[str]] = ["y", "x", "wavenumber"]
```
"""

_VALID_SERIES_CODE = """\
```python
from scieasy.core.types.series import Series


class IRSpectrum(Series):
    \"\"\"Infrared absorption spectrum.\"\"\"

    pass
```
"""

_VALID_DATAFRAME_CODE = """\
```python
from scieasy.core.types.dataframe import DataFrame


class ProteinTable(DataFrame):
    \"\"\"Proteomics quantification table.\"\"\"

    pass
```
"""

_INVALID_CODE = """\
```python
class NotADataObject:
    pass
```
"""

_SYNTAX_ERROR_CODE = """\
```python
def broken(
    pass
```
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_provider(responses: list[str]) -> MagicMock:
    """Create a mock LLM provider that returns *responses* in sequence."""
    provider = MagicMock()
    provider.generate = MagicMock(side_effect=responses)
    return provider


def _make_config() -> AIConfig:
    """Create an AIConfig suitable for testing (low retries)."""
    return AIConfig(
        provider="anthropic",
        api_key="test-key",
        max_retries=3,
    )


# ---------------------------------------------------------------------------
# Family inference tests
# ---------------------------------------------------------------------------


class TestInferTypeFamily:
    """Tests for infer_type_family()."""

    def test_image_keyword_gives_array(self) -> None:
        assert infer_type_family("A 2D microscopy image with channels") == "array"

    def test_spatial_keyword_gives_array(self) -> None:
        assert infer_type_family("spatial raster data") == "array"

    def test_spectrum_keyword_gives_series(self) -> None:
        assert infer_type_family("Raman spectrum with wavenumber axis") == "series"

    def test_chromatogram_keyword_gives_series(self) -> None:
        assert infer_type_family("liquid chromatogram trace") == "series"

    def test_table_keyword_gives_dataframe(self) -> None:
        assert infer_type_family("A table of peak annotations") == "dataframe"

    def test_column_keyword_gives_dataframe(self) -> None:
        assert infer_type_family("columnar data with m/z and intensity columns") == "dataframe"

    def test_no_keywords_defaults_to_array(self) -> None:
        assert infer_type_family("some mysterious scientific measurement") == "array"

    def test_case_insensitive(self) -> None:
        assert infer_type_family("A FLUORESCENCE IMAGE") == "array"

    def test_multiple_matches_picks_highest(self) -> None:
        # "table" + "column" + "row" = 3 dataframe keywords
        assert infer_type_family("A table with multiple columns and rows") == "dataframe"


# ---------------------------------------------------------------------------
# Type name extraction tests
# ---------------------------------------------------------------------------


class TestExtractTypeName:
    """Tests for _extract_type_name()."""

    def test_extracts_class_name(self) -> None:
        code = "class FluorescenceImage(Array):\n    pass\n"
        assert _extract_type_name(code) == "FluorescenceImage"

    def test_extracts_first_class(self) -> None:
        code = "class FirstClass(Array):\n    pass\nclass SecondClass(Series):\n    pass\n"
        assert _extract_type_name(code) == "FirstClass"

    def test_syntax_error_returns_unknown(self) -> None:
        assert _extract_type_name("def broken(:\n  pass") == "UnknownType"

    def test_no_class_returns_unknown(self) -> None:
        assert _extract_type_name("x = 1\n") == "UnknownType"


# ---------------------------------------------------------------------------
# generate_type() tests with mock LLM
# ---------------------------------------------------------------------------


class TestGenerateType:
    """Tests for generate_type() with mock LLM provider."""

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_valid_array_subclass(self, mock_get_provider: MagicMock) -> None:
        """Mock LLM returns valid Array subclass -- generation succeeds."""
        provider = _make_mock_provider([_VALID_ARRAY_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        result = generate_type(
            "A Raman hyperspectral image with y, x, wavenumber axes",
            type_family="array",
            config=config,
        )

        assert isinstance(result, TypeGenerationResult)
        assert result.type_name == "RamanImage"
        assert result.type_family == "array"
        assert result.validation_report["passed"] is True
        assert result.attempts == 1
        assert "class RamanImage" in result.code

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_valid_series_subclass(self, mock_get_provider: MagicMock) -> None:
        """Mock LLM returns valid Series subclass -- generation succeeds."""
        provider = _make_mock_provider([_VALID_SERIES_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        result = generate_type(
            "An infrared absorption spectrum",
            type_family="series",
            config=config,
        )

        assert result.type_name == "IRSpectrum"
        assert result.type_family == "series"
        assert result.validation_report["passed"] is True
        assert result.attempts == 1

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_valid_dataframe_subclass(self, mock_get_provider: MagicMock) -> None:
        """Mock LLM returns valid DataFrame subclass -- generation succeeds."""
        provider = _make_mock_provider([_VALID_DATAFRAME_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        result = generate_type(
            "A proteomics quantification table",
            type_family="dataframe",
            config=config,
        )

        assert result.type_name == "ProteinTable"
        assert result.type_family == "dataframe"
        assert result.validation_report["passed"] is True

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_family_inference_used_when_none(self, mock_get_provider: MagicMock) -> None:
        """When type_family is None, infer_type_family() is used."""
        provider = _make_mock_provider([_VALID_SERIES_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        result = generate_type(
            "A Raman spectrum with wavenumber and intensity",
            type_family=None,
            config=config,
        )

        # "spectrum" keyword triggers "series" family.
        assert result.type_family == "series"

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_retry_on_validation_failure(self, mock_get_provider: MagicMock) -> None:
        """First attempt returns invalid code, second returns valid code."""
        provider = _make_mock_provider([_INVALID_CODE, _VALID_ARRAY_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        result = generate_type(
            "A microscopy image",
            type_family="array",
            config=config,
        )

        assert result.attempts == 2
        assert result.validation_report["passed"] is True
        assert result.type_name == "RamanImage"

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_all_retries_exhausted_raises(self, mock_get_provider: MagicMock) -> None:
        """All attempts return invalid code -- RuntimeError raised."""
        provider = _make_mock_provider([_INVALID_CODE, _INVALID_CODE, _INVALID_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        with pytest.raises(RuntimeError, match="Type generation failed after"):
            generate_type(
                "A microscopy image",
                type_family="array",
                config=config,
            )

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_empty_response_retries(self, mock_get_provider: MagicMock) -> None:
        """Empty LLM response triggers retry."""
        provider = _make_mock_provider(["", _VALID_ARRAY_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        result = generate_type(
            "A microscopy image",
            type_family="array",
            config=config,
        )

        assert result.attempts == 2

    @patch("scieasy.ai.generation.type_generator.get_provider")
    def test_result_dataclass_fields(self, mock_get_provider: MagicMock) -> None:
        """TypeGenerationResult has all expected fields."""
        provider = _make_mock_provider([_VALID_ARRAY_CODE])
        mock_get_provider.return_value = provider
        config = _make_config()

        result = generate_type("An image", type_family="array", config=config)

        assert hasattr(result, "code")
        assert hasattr(result, "type_name")
        assert hasattr(result, "type_family")
        assert hasattr(result, "validation_report")
        assert hasattr(result, "attempts")
        assert isinstance(result.validation_report, dict)
        assert "passed" in result.validation_report
