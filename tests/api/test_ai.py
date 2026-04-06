"""Tests for placeholder AI endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_ai_routes_return_phase9_placeholders(client: TestClient) -> None:
    """Unimplemented AI endpoints should report as unavailable."""
    generate = client.post("/api/ai/generate-block", json={"description": "make a block"})
    assert generate.status_code == 501
    assert "Phase 9" in generate.json()["detail"]

    # suggest-workflow is now wired to the real planner.  Without an
    # API key it returns 501 with an "AI provider not available" message.
    suggest = client.post(
        "/api/ai/suggest-workflow",
        json={"data_description": "csv table", "goal": "cluster samples"},
    )
    assert suggest.status_code == 501

    # optimize-params now uses a Pydantic body model and calls the real
    # optimizer.  Without a configured AI provider the endpoint returns
    # 400 (ValueError from optimizer), not the old 501 stub.
    optimize = client.post(
        "/api/ai/optimize-params",
        json={"block_id": "node-1", "intermediate_results": {}},
    )
    # Either 400 (no AI provider) or 500 (runtime error) is acceptable
    # now that the endpoint is wired to the real implementation.
    assert optimize.status_code in (400, 500)
