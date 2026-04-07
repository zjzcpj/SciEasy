"""Block palette listing and connection validation endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from scieasy.api.deps import get_block_registry, get_type_registry
from scieasy.api.schemas import (
    BlockConnectionValidation,
    BlockListResponse,
    BlockPortResponse,
    BlockSchemaResponse,
    BlockSummary,
    ConnectionValidationResponse,
    TypeHierarchyEntry,
)
from scieasy.blocks.base.ports import InputPort, OutputPort, validate_connection

router = APIRouter(prefix="/api/blocks", tags=["blocks"])
BlockRegistryDep = Annotated[Any, Depends(get_block_registry)]
TypeRegistryDep = Annotated[Any, Depends(get_type_registry)]


def _port_response(port: Any, *, direction: str) -> BlockPortResponse:
    return BlockPortResponse(
        name=port.name,
        direction=direction,
        accepted_types=[accepted.__name__ for accepted in getattr(port, "accepted_types", [])],
        required=getattr(port, "required", True),
        description=getattr(port, "description", ""),
        constraint_description=getattr(port, "constraint_description", ""),
    )


def _config_schema_for_block(spec: Any) -> dict[str, Any]:
    return spec.config_schema or {"type": "object", "properties": {}}


def _summary(spec: Any) -> BlockSummary:
    # TODO(agent-b, stage-10.1): populate ``source`` and ``package_name`` from
    # ``spec``. After the BlockSpec.source value rename lands (tier1 -> custom,
    # entry_point -> package), pass ``source=spec.source`` and
    # ``package_name=spec.package_name`` below. Agent A left the call
    # unchanged to preserve existing behavior.
    # See docs/design/stage-10-1-palette.md §3.1.4 and §3.2.4.
    return BlockSummary(
        name=spec.name,
        type_name=spec.type_name,
        category=spec.category,
        description=spec.description,
        version=spec.version,
        input_ports=[_port_response(port, direction="input") for port in spec.input_ports],
        output_ports=[_port_response(port, direction="output") for port in spec.output_ports],
    )


@router.get("/", response_model=BlockListResponse)
async def list_blocks(registry: BlockRegistryDep) -> BlockListResponse:
    """Return the full block palette available in the current registry."""
    blocks = [_summary(spec) for spec in registry.all_specs().values()]
    blocks.sort(key=lambda item: (item.category, item.name))
    return BlockListResponse(blocks=blocks)


@router.get("/{block_type}/schema", response_model=BlockSchemaResponse)
@router.get("/{block_type}", response_model=BlockSchemaResponse, include_in_schema=False)
async def get_block_schema(
    block_type: str,
    registry: BlockRegistryDep,
    type_registry: TypeRegistryDep,
) -> BlockSchemaResponse:
    """Return the JSON Schema for a block type's parameters and ports."""
    spec = registry.get_spec(block_type)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown block type: {block_type}")
    return BlockSchemaResponse(
        **_summary(spec).model_dump(),
        config_schema=_config_schema_for_block(spec),
        type_hierarchy=[
            TypeHierarchyEntry(
                name=entry.name,
                base_type=entry.base_type,
                description=entry.description,
            )
            for entry in type_registry.all_types().values()
        ],
        # ADR-028 Addendum 1 D4 / D7: surface dynamic-port descriptor and IO
        # direction to the frontend so BlockNode.tsx can render dynamic-port
        # UI and IO-specific controls without hardcoded type checks.
        dynamic_ports=spec.dynamic_ports,
        direction=spec.direction or None,
    )


@router.post("/validate-connection", response_model=ConnectionValidationResponse)
async def validate_connection_route(
    body: BlockConnectionValidation,
    registry: BlockRegistryDep,
) -> ConnectionValidationResponse:
    """Validate whether two ports can be connected."""
    source = registry.get_spec(body.source_block)
    target = registry.get_spec(body.target_block)
    if source is None or target is None:
        raise HTTPException(status_code=404, detail="Unknown block in connection validation.")

    source_port = next((port for port in source.output_ports if port.name == body.source_port), None)
    target_port = next((port for port in target.input_ports if port.name == body.target_port), None)
    if not isinstance(source_port, OutputPort) or not isinstance(target_port, InputPort):
        raise HTTPException(status_code=404, detail="Unknown source or target port.")

    compatible, reason = validate_connection(source_port, target_port)
    return ConnectionValidationResponse(compatible=compatible, reason=reason)
