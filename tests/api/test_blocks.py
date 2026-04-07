"""Tests for block registry API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_list_blocks_and_schema_alias_endpoints(client: TestClient) -> None:
    """The block palette and schema endpoints should expose built-in metadata."""
    response = client.get("/api/blocks/")
    assert response.status_code == 200
    payload = response.json()
    assert "blocks" in payload
    # T-TRK-003: TransformBlock was relocated to tests/fixtures/noop_block.py
    # as NoopBlock with type_name="noop". The conftest hook re-registers it
    # under the legacy "process_block" alias for backward compatibility, but
    # the canonical type_name reported by the palette endpoint is now "noop".
    assert any(block["type_name"] == "noop" for block in payload["blocks"])

    schema = client.get("/api/blocks/process_block/schema")
    assert schema.status_code == 200
    schema_payload = schema.json()
    assert schema_payload["name"] == "Process Block"
    assert schema_payload["category"] == "process"
    assert schema_payload["config_schema"]["properties"]["sleep_seconds"]["ui_priority"] == 1
    assert any(entry["name"] == "DataObject" for entry in schema_payload["type_hierarchy"])

    alias = client.get("/api/blocks/process_block")
    assert alias.status_code == 200
    assert alias.json() == schema_payload


def test_validate_connection_endpoint_uses_registry_type_information(client: TestClient) -> None:
    """Connection validation should accept compatible ports and reject mismatches."""
    compatible = client.post(
        "/api/blocks/validate-connection",
        json={
            "source_block": "io_block",
            "source_port": "data",
            "target_block": "process_block",
            "target_port": "input",
        },
    )
    assert compatible.status_code == 200
    assert compatible.json()["compatible"] is True

    incompatible = client.post(
        "/api/blocks/validate-connection",
        json={
            "source_block": "process_block",
            "source_port": "output",
            "target_block": "Merge",
            "target_port": "left",
        },
    )
    assert incompatible.status_code == 200
    assert incompatible.json()["compatible"] is False
    assert incompatible.json()["reason"]


# ----------------------------------------------------------------------------
# Stage 10.1 Part 2 — skipped test stubs authored by Agent A.
#
# Agent B will remove the skip markers and implement these in Part 2.
# See docs/design/stage-10-1-palette.md §4.1 for the test plan.
# ----------------------------------------------------------------------------


@pytest.mark.skip(reason="Agent B implements in Stage 10.1 Part 2")
def test_list_blocks_includes_source_and_package_name(client: TestClient) -> None:
    """GET /api/blocks/ response items contain ``source`` and ``package_name``.

    After Agent B populates the fields in ``_summary``, every block in the
    palette listing must expose these two keys (even if ``package_name`` is
    an empty string for builtins).
    """


@pytest.mark.skip(reason="Agent B implements in Stage 10.1 Part 2")
def test_list_blocks_source_values_enumerated(client: TestClient) -> None:
    """Every block reports ``source`` in {"builtin", "package", "custom"}.

    After the source value rename, no block should report ``"tier1"`` or
    ``"entry_point"``. The valid domain is the three-value enum documented
    in docs/design/stage-10-1-palette.md §3.2.3.
    """
