"""Tests for the POST /api/ai/suggest-workflow endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestSuggestWorkflow501:
    """Tests that endpoint returns proper error without AI configured."""

    def test_suggest_workflow_501_when_no_provider(self, client: TestClient) -> None:
        """Call endpoint without AI configured, expect a 501 response."""
        response = client.post(
            "/api/ai/suggest-workflow",
            json={
                "data_description": "csv table with 100 rows",
                "goal": "cluster samples",
            },
        )
        # Without an API key set, the planner raises ValueError which
        # is caught and returned as 501
        assert response.status_code == 501
        body = response.json()
        assert "detail" in body


class TestSuggestWorkflowSuccess:
    """Tests that endpoint returns correct shape when planner succeeds."""

    @patch("scieasy.ai.synthesis.workflow_planner.plan_workflow")
    def test_suggest_workflow_success(self, mock_plan: MagicMock, client: TestClient) -> None:
        """Mock the planner, verify response shape."""
        mock_plan.return_value = {
            "nodes": [
                {
                    "id": "node-1",
                    "block_type": "IOBlock",
                    "config": {},
                    "layout": {"x": 100, "y": 100},
                },
                {
                    "id": "node-2",
                    "block_type": "TransformBlock",
                    "config": {},
                    "layout": {"x": 300, "y": 100},
                },
            ],
            "edges": [{"source": "node-1", "target": "node-2"}],
            "explanation": "Load data then transform.",
            "metadata": {"transport": "collection"},
        }

        response = client.post(
            "/api/ai/suggest-workflow",
            json={
                "data_description": "CSV table with measurements",
                "goal": "normalise and filter outliers",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert "workflow" in body
        assert "explanation" in body
        assert isinstance(body["workflow"], dict)
        assert "nodes" in body["workflow"]
        assert "edges" in body["workflow"]
        assert body["explanation"] == "Load data then transform."


class TestOtherEndpointsUnchanged:
    """Verify the other AI endpoints are not broken."""

    def test_generate_block_returns_error_without_ai(self, client: TestClient) -> None:
        """generate-block returns 503 when AI deps are not installed."""
        response = client.post(
            "/api/ai/generate-block",
            json={"description": "make a block"},
        )
        # 503 when AI optional deps missing, 501 if still a stub
        assert response.status_code in (501, 503)
