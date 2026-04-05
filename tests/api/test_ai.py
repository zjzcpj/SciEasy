"""Tests for placeholder AI endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_ai_routes_return_phase9_placeholders(client: TestClient) -> None:
    """Phase 8 should expose AI endpoints but report them as unavailable."""
    generate = client.post("/api/ai/generate-block", json={"description": "make a block"})
    assert generate.status_code == 501
    assert "Phase 9" in generate.json()["detail"]

    suggest = client.post(
        "/api/ai/suggest-workflow",
        json={"data_description": "csv table", "goal": "cluster samples"},
    )
    assert suggest.status_code == 501
    assert "Phase 9" in suggest.json()["detail"]

    optimize = client.post(
        "/api/ai/optimize-params",
        params={"block_id": "node-1"},
        json={"preview": {"kind": "table"}},
    )
    assert optimize.status_code == 501
    assert "Phase 9" in optimize.json()["detail"]
