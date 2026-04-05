"""Tests for workflow CRUD and execution endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from tests.api.helpers import build_linear_workflow, wait_for_block_state, wait_for_workflow_completion

from scieasy.api.runtime import ApiRuntime


def test_workflow_crud_round_trips_yaml_layout(client: TestClient, opened_project: Path) -> None:
    """Workflow CRUD should persist YAML and round-trip layout metadata."""
    payload = build_linear_workflow(opened_project, workflow_id="crud-flow")

    created = client.post("/api/workflows/", json=payload)
    assert created.status_code == 200
    assert created.json()["nodes"][0]["layout"] == {"x": 20.0, "y": 40.0}

    workflow_file = opened_project / "workflows" / "crud-flow.yaml"
    assert workflow_file.exists()
    assert "layout:" in workflow_file.read_text(encoding="utf-8")

    fetched = client.get("/api/workflows/crud-flow")
    assert fetched.status_code == 200
    assert fetched.json()["metadata"]["kind"] == "linear"

    payload["description"] = "updated description"
    payload["nodes"][1]["config"]["params"]["label"] = "updated"
    updated = client.put("/api/workflows/crud-flow", json=payload)
    assert updated.status_code == 200
    assert updated.json()["description"] == "updated description"

    deleted = client.delete("/api/workflows/crud-flow")
    assert deleted.status_code == 204
    assert not workflow_file.exists()


def test_workflow_execute_and_execute_from_reuses_cached_outputs(
    client: TestClient,
    runtime: ApiRuntime,
    opened_project: Path,
) -> None:
    """Workflow execution should produce checkpoints that enable execute-from."""
    payload = build_linear_workflow(opened_project, workflow_id="execute-flow")
    assert client.post("/api/workflows/", json=payload).status_code == 200

    started = client.post("/api/workflows/execute-flow/execute")
    assert started.status_code == 200
    run = wait_for_workflow_completion(runtime, "execute-flow")
    assert run.scheduler.block_states() == {"load": "done", "transform": "done", "final": "done"}

    checkpoint = run.checkpoint_manager.load("execute-flow")
    assert checkpoint is not None
    assert checkpoint.intermediate_refs

    rerun = client.post("/api/workflows/execute-flow/execute-from", json={"block_id": "final"})
    assert rerun.status_code == 200
    assert rerun.json()["reused_blocks"] == ["load", "transform"]
    assert rerun.json()["reset_blocks"] == ["final"]
    rerun_handle = wait_for_workflow_completion(runtime, "execute-flow")
    assert rerun_handle.scheduler.block_states()["final"] == "done"


def test_workflow_pause_and_resume_keeps_downstream_block_ready(
    client: TestClient,
    runtime: ApiRuntime,
    opened_project: Path,
) -> None:
    """Pause should prevent dispatch of newly ready nodes until resume is called."""
    payload = build_linear_workflow(
        opened_project,
        workflow_id="pause-flow",
        middle_sleep_seconds=0.8,
    )
    assert client.post("/api/workflows/", json=payload).status_code == 200

    assert client.post("/api/workflows/pause-flow/execute").status_code == 200
    wait_for_block_state(runtime, "pause-flow", "transform", "running")

    paused = client.post("/api/workflows/pause-flow/pause")
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    states = wait_for_block_state(runtime, "pause-flow", "final", "ready", timeout=5.0)
    assert states["transform"] == "done"

    resumed = client.post("/api/workflows/pause-flow/resume")
    assert resumed.status_code == 200
    run = wait_for_workflow_completion(runtime, "pause-flow")
    assert run.scheduler.block_states()["final"] == "done"


def test_cancel_block_and_cancel_workflow_propagate_terminal_states(
    client: TestClient,
    runtime: ApiRuntime,
    opened_project: Path,
) -> None:
    """Cancel controls should cancel active work and skip blocked descendants."""
    cancel_block_payload = build_linear_workflow(
        opened_project,
        workflow_id="cancel-block-flow",
        middle_sleep_seconds=2.0,
    )
    assert client.post("/api/workflows/", json=cancel_block_payload).status_code == 200
    assert client.post("/api/workflows/cancel-block-flow/execute").status_code == 200
    wait_for_block_state(runtime, "cancel-block-flow", "transform", "running")

    block_cancel = client.post("/api/workflows/cancel-block-flow/blocks/transform/cancel")
    assert block_cancel.status_code == 200
    wait_for_workflow_completion(runtime, "cancel-block-flow")
    block_states = runtime.workflow_runs["cancel-block-flow"].scheduler.block_states()
    assert block_states["transform"] == "cancelled"
    assert block_states["final"] == "skipped"

    cancel_workflow_payload = build_linear_workflow(
        opened_project,
        workflow_id="cancel-workflow-flow",
        middle_sleep_seconds=2.0,
    )
    assert client.post("/api/workflows/", json=cancel_workflow_payload).status_code == 200
    assert client.post("/api/workflows/cancel-workflow-flow/execute").status_code == 200
    wait_for_block_state(runtime, "cancel-workflow-flow", "transform", "running")

    workflow_cancel = client.post("/api/workflows/cancel-workflow-flow/cancel")
    assert workflow_cancel.status_code == 200
    wait_for_workflow_completion(runtime, "cancel-workflow-flow")
    workflow_states = runtime.workflow_runs["cancel-workflow-flow"].scheduler.block_states()
    assert workflow_states["transform"] == "cancelled"
    assert workflow_states["final"] == "skipped"
