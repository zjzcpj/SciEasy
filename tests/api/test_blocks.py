"""Tests for block registry API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_blocks_and_schema_alias_endpoints(client: TestClient) -> None:
    """The block palette and schema endpoints should expose built-in metadata."""
    response = client.get("/api/blocks/")
    assert response.status_code == 200
    payload = response.json()
    assert "blocks" in payload
    assert any(block["type_name"] == "process_block" for block in payload["blocks"])

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


def test_list_blocks_includes_package_name_field(client: TestClient) -> None:
    """Each block in the palette response should include a package_name field."""
    response = client.get("/api/blocks/")
    assert response.status_code == 200
    payload = response.json()
    for block in payload["blocks"]:
        assert "package_name" in block, f"Block {block['name']} missing package_name"
        # Built-in blocks should have empty package_name
        assert isinstance(block["package_name"], str)


def test_builtin_blocks_have_empty_package_name(client: TestClient) -> None:
    """Built-in blocks should have an empty string package_name."""
    response = client.get("/api/blocks/")
    assert response.status_code == 200
    payload = response.json()
    # All built-in blocks should have package_name == ""
    for block in payload["blocks"]:
        assert block["package_name"] == "", (
            f"Built-in block {block['name']} has non-empty package_name: {block['package_name']!r}"
        )


def test_list_packages_endpoint_returns_empty_for_builtins(client: TestClient) -> None:
    """With no external packages installed, /api/blocks/packages returns an empty list."""
    response = client.get("/api/blocks/packages")
    assert response.status_code == 200
    payload = response.json()
    assert "packages" in payload
    assert isinstance(payload["packages"], list)
    # No external packages registered in test environment
    assert payload["packages"] == []


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
