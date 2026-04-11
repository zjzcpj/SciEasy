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
        is_collection=getattr(port, "is_collection", False),
    )


def _config_schema_for_block(spec: Any) -> dict[str, Any]:
    return spec.config_schema or {"type": "object", "properties": {}}


def _map_source(raw: str) -> str:
    """Map internal source labels to palette-friendly values.

    tier1 -> "custom" (project-local hot-loaded blocks)
    entry_point / monorepo -> "package" (installed plugin blocks)
    builtin -> "builtin" (core blocks)
    """
    if raw == "tier1":
        return "custom"
    if raw in ("entry_point", "monorepo"):
        return "package"
    if raw == "builtin":
        return "builtin"
    return raw


def _is_plugin_package(name: str) -> bool:
    """Return True if *name* looks like an external plugin package.

    Convention: plugin packages are named ``scieasy-blocks-<domain>``
    (e.g. ``scieasy-blocks-imaging``).  Everything else (individual
    entry-point names like ``ai_block``, ``code_block``, or empty
    strings) is a core block and should be grouped under the default
    "SciEasy Core" header in the palette.
    """
    return name.startswith("scieasy-blocks-")


def _summary(spec: Any) -> BlockSummary:
    raw_pkg = getattr(spec, "package_name", "") or ""
    # Only keep the package_name for genuine plugin packages so the
    # frontend groups core blocks together under "SciEasy Core".
    package_name = raw_pkg if _is_plugin_package(raw_pkg) else ""
    return BlockSummary(
        name=spec.name,
        type_name=spec.type_name,
        base_category=spec.base_category,
        subcategory=spec.subcategory,
        description=spec.description,
        version=spec.version,
        input_ports=[_port_response(port, direction="input") for port in spec.input_ports],
        output_ports=[_port_response(port, direction="output") for port in spec.output_ports],
        direction=spec.direction or None,
        source=_map_source(getattr(spec, "source", "") or ""),
        package_name=package_name,
        variadic_inputs=bool(getattr(spec, "variadic_inputs", False)),
        variadic_outputs=bool(getattr(spec, "variadic_outputs", False)),
    )


@router.get("/", response_model=BlockListResponse)
async def list_blocks(registry: BlockRegistryDep) -> BlockListResponse:
    """Return the full block palette available in the current registry."""
    blocks = [_summary(spec) for spec in registry.all_specs().values()]
    blocks.sort(key=lambda item: (item.base_category, item.subcategory, item.name))
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
        # ADR-029 D11: variadic port type constraints for frontend port editor.
        allowed_input_types=list(getattr(spec, "allowed_input_types", []) or []),
        allowed_output_types=list(getattr(spec, "allowed_output_types", []) or []),
        # ADR-029 Addendum 1: port count limits for variadic blocks.
        min_input_ports=getattr(spec, "min_input_ports", None),
        max_input_ports=getattr(spec, "max_input_ports", None),
        min_output_ports=getattr(spec, "min_output_ports", None),
        max_output_ports=getattr(spec, "max_output_ports", None),
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
