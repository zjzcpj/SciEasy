"""Tests for the POST /api/ai/optimize-params endpoint."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


class TestOptimizeParamsEndpointSuccess:
    """Happy path: the optimizer returns valid suggestions."""

    def test_returns_suggestions(self, client: TestClient) -> None:
        """Mock the optimizer and verify the response shape."""
        mock_result = {
            "suggestions": {"threshold": 0.8},
            "explanation": "Higher threshold improves precision.",
        }
        # The import happens inside the endpoint handler, so we patch
        # at the source module level.
        with patch(
            "scieasy.ai.optimization.param_optimizer.optimize_params",
            return_value=mock_result,
        ):
            response = client.post(
                "/api/ai/optimize-params",
                json={
                    "block_id": "TestBlock",
                    "intermediate_results": {"accuracy": 0.9},
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert "suggestions" in body
        assert "explanation" in body
        assert body["suggestions"]["threshold"] == 0.8


class TestOptimizeParamsEndpointNoProvider:
    """AI provider is not configured -- should return an error."""

    def test_returns_400_on_value_error(self, client: TestClient) -> None:
        """ValueError from optimizer maps to 400."""
        with patch(
            "scieasy.ai.optimization.param_optimizer.optimize_params",
            side_effect=ValueError("AI provider not available: No API key"),
        ):
            response = client.post(
                "/api/ai/optimize-params",
                json={
                    "block_id": "TestBlock",
                    "intermediate_results": {},
                },
            )

        assert response.status_code == 400
        assert "AI provider not available" in response.json()["detail"]

    def test_returns_500_on_runtime_error(self, client: TestClient) -> None:
        """RuntimeError from optimizer maps to 500."""
        with patch(
            "scieasy.ai.optimization.param_optimizer.optimize_params",
            side_effect=RuntimeError("Failed after retries"),
        ):
            response = client.post(
                "/api/ai/optimize-params",
                json={
                    "block_id": "SomeBlock",
                    "intermediate_results": {},
                },
            )

        assert response.status_code == 500
        assert "Failed after retries" in response.json()["detail"]
