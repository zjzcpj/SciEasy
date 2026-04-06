"""Tests for AI API endpoints.

The generate-block endpoint is now wired to the block generator pipeline.
Other endpoints (suggest-workflow, optimize-params) remain Phase 9 placeholders.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Placeholder endpoints (still 501)
# ---------------------------------------------------------------------------


def test_suggest_workflow_returns_501(client: TestClient) -> None:
    """suggest-workflow still returns a Phase 9 placeholder."""
    suggest = client.post(
        "/api/ai/suggest-workflow",
        json={"data_description": "csv table", "goal": "cluster samples"},
    )
    assert suggest.status_code == 501


def test_optimize_params_returns_error_without_provider(client: TestClient) -> None:
    """optimize-params returns 400/500 when no AI provider is configured.

    The endpoint is now wired to the real optimizer. Without a configured
    AI provider it returns 400 (ValueError) or 500 (RuntimeError).
    """
    optimize = client.post(
        "/api/ai/optimize-params",
        json={"block_id": "node-1", "intermediate_results": {}},
    )
    # Either 400 (no AI provider) or 500 (runtime error) is acceptable
    # now that the endpoint is wired to the real implementation.
    assert optimize.status_code in (400, 500)


# ---------------------------------------------------------------------------
# generate-block endpoint (now functional)
# ---------------------------------------------------------------------------


MOCK_VALID_CODE = "class TestBlock:\n    def run(self, inputs, config):\n        return inputs\n"


def _make_mock_result(
    code: str = MOCK_VALID_CODE,
    block_name: str = "TestBlock",
    passed: bool = True,
    category: str = "process",
    attempts: int = 1,
) -> MagicMock:
    """Create a mock GenerationResult."""
    result = MagicMock()
    result.code = code
    result.block_name = block_name
    result.validation_report = {
        "passed": passed,
        "errors": [] if passed else ["Some error"],
        "warnings": [],
    }
    result.attempts = attempts
    result.category = category
    return result


def test_generate_block_returns_503_when_ai_unavailable(client: TestClient) -> None:
    """Endpoint returns 503 when AI optional dependencies are missing.

    The endpoint performs a lazy import inside the function body:
        from scieasy.ai.generation.block_generator import generate_block as ai_generate_block

    To simulate missing AI dependencies, we set the target module to None
    in sys.modules, which causes ``from ... import ...`` to raise ImportError.
    """
    import sys

    with patch.dict(sys.modules, {"scieasy.ai.generation.block_generator": None}):
        resp = client.post(
            "/api/ai/generate-block",
            json={"description": "make a block"},
        )

    assert resp.status_code == 503
    assert "AI features require" in resp.json()["detail"]


def test_generate_block_success(client: TestClient) -> None:
    """Endpoint returns generated code on success."""
    mock_result = _make_mock_result()

    with patch(
        "scieasy.ai.generation.block_generator.generate_block",
        return_value=mock_result,
    ):
        resp = client.post(
            "/api/ai/generate-block",
            json={"description": "Apply denoising filter", "block_category": "process"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == MOCK_VALID_CODE
    assert data["block_name"] == "TestBlock"
    assert data["validation_passed"] is True
    assert data["category"] == "process"
    assert "validation_report" in data


def test_generate_block_validation_failed(client: TestClient) -> None:
    """Endpoint returns result even when validation fails (max retries exceeded)."""
    mock_result = _make_mock_result(passed=False, attempts=3)

    with patch(
        "scieasy.ai.generation.block_generator.generate_block",
        return_value=mock_result,
    ):
        resp = client.post(
            "/api/ai/generate-block",
            json={"description": "Make something"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["validation_passed"] is False


def test_generate_block_internal_error(client: TestClient) -> None:
    """Endpoint returns 500 on unexpected errors."""
    with patch(
        "scieasy.ai.generation.block_generator.generate_block",
        side_effect=RuntimeError("Unexpected failure"),
    ):
        resp = client.post(
            "/api/ai/generate-block",
            json={"description": "Make something"},
        )

    assert resp.status_code == 500
    assert "Unexpected failure" in resp.json()["detail"]


def test_generate_block_request_shape(client: TestClient) -> None:
    """Endpoint accepts the correct request body shape."""
    mock_result = _make_mock_result(category="io")

    with patch(
        "scieasy.ai.generation.block_generator.generate_block",
        return_value=mock_result,
    ):
        # With category
        resp = client.post(
            "/api/ai/generate-block",
            json={"description": "Load CSV", "block_category": "io"},
        )
        assert resp.status_code == 200
        assert resp.json()["category"] == "io"

        # Without category (optional field)
        resp = client.post(
            "/api/ai/generate-block",
            json={"description": "Load CSV"},
        )
        assert resp.status_code == 200
