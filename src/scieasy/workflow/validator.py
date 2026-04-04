"""Workflow validation -- type compatibility, cycles, missing connections."""

from __future__ import annotations

from scieasy.blocks.base.ports import InputPort, OutputPort, validate_connection
from scieasy.blocks.registry import BlockRegistry, BlockSpec
from scieasy.engine.dag import CycleError, build_dag, topological_sort
from scieasy.workflow.definition import WorkflowDefinition


def _parse_port_ref(ref: str) -> tuple[str, str] | None:
    """Split a ``"node_id:port_name"`` reference into its two parts.

    Returns ``None`` when the format is invalid (not exactly two non-empty
    parts separated by a single colon).
    """
    parts = ref.split(":")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def _find_port(
    ports: list[object],
    name: str,
) -> InputPort | OutputPort | None:
    """Return the port whose ``name`` attribute matches, or ``None``."""
    for port in ports:
        if isinstance(port, (InputPort, OutputPort)) and port.name == name:
            return port
    return None


def validate_workflow(
    workflow: WorkflowDefinition,
    registry: BlockRegistry | None = None,
) -> list[str]:
    """Validate a workflow definition and return a list of diagnostic messages.

    Checks include:

    1. **Structural** -- duplicate node IDs, empty workflow.
    2. **Edge format** -- ``node_id:port_name`` colon-separated format.
    3. **Edge node references** -- source / target nodes exist.
    4. **Cycle detection** -- delegates to :func:`~scieasy.engine.dag.build_dag`
       and :func:`~scieasy.engine.dag.topological_sort`.
    5. **Type compatibility** -- port type matching via
       :func:`~scieasy.blocks.base.ports.validate_connection` (only when
       *registry* is provided).
    6. **Dangling required input ports** -- required ``InputPort`` instances
       without an incoming edge (only when *registry* is provided).

    Parameters
    ----------
    workflow:
        A ``WorkflowDefinition`` instance to validate.
    registry:
        An optional ``BlockRegistry`` used for type-compatibility and
        dangling-port checks.  When ``None``, those checks are skipped.

    Returns
    -------
    list[str]
        A (possibly empty) list of human-readable validation error or warning
        messages.  An empty list indicates a valid workflow.
    """
    errors: list[str] = []

    # ------------------------------------------------------------------
    # Check 1: Structural validation
    # ------------------------------------------------------------------
    seen_ids: set[str] = set()
    for node in workflow.nodes:
        if node.id in seen_ids:
            errors.append(f"Duplicate node id: '{node.id}'")
        seen_ids.add(node.id)

    if not workflow.nodes:
        return errors  # empty workflow is valid

    # ------------------------------------------------------------------
    # Check 2 & 3: Edge format and node reference validation
    # ------------------------------------------------------------------
    has_edge_errors = False
    for edge in workflow.edges:
        src_parsed = _parse_port_ref(edge.source)
        tgt_parsed = _parse_port_ref(edge.target)
        if src_parsed is None or tgt_parsed is None:
            errors.append(
                f"Edge '{edge.source}' -> '{edge.target}': invalid port reference format (expected 'node_id:port_name')"
            )
            has_edge_errors = True
            continue  # skip further checks on this malformed edge

        # --------------------------------------------------------------
        # Check 3: Edge node reference validation
        # --------------------------------------------------------------
        src_node_id, _ = src_parsed
        tgt_node_id, _ = tgt_parsed
        if src_node_id not in seen_ids:
            errors.append(f"Edge references unknown node '{src_node_id}'")
            has_edge_errors = True
        if tgt_node_id not in seen_ids:
            errors.append(f"Edge references unknown node '{tgt_node_id}'")
            has_edge_errors = True

    # ------------------------------------------------------------------
    # Check 4: Cycle detection (skipped when edges are malformed)
    # ------------------------------------------------------------------
    if not has_edge_errors:
        try:
            dag = build_dag(workflow)
            topological_sort(dag)
        except CycleError:
            errors.append("Workflow contains a cycle")

    # ------------------------------------------------------------------
    # Registry-dependent checks (5 & 6)
    # ------------------------------------------------------------------
    if registry is None:
        return errors

    specs = registry.all_specs()
    node_map = {node.id: node for node in workflow.nodes}

    # ------------------------------------------------------------------
    # Check 5: Type compatibility on edges
    # ------------------------------------------------------------------
    for edge in workflow.edges:
        src_parsed = _parse_port_ref(edge.source)
        tgt_parsed = _parse_port_ref(edge.target)
        if src_parsed is None or tgt_parsed is None:
            continue  # already reported in Check 2

        src_node_id, src_port_name = src_parsed
        tgt_node_id, tgt_port_name = tgt_parsed

        src_node = node_map.get(src_node_id)
        tgt_node = node_map.get(tgt_node_id)
        if src_node is None or tgt_node is None:
            continue  # already reported in Check 3

        src_spec = specs.get(src_node.block_type)
        if src_spec is None:
            errors.append(
                f"Warning: block type '{src_node.block_type}' not in registry, "
                f"skipping type check for node '{src_node_id}'"
            )
            continue

        tgt_spec = specs.get(tgt_node.block_type)
        if tgt_spec is None:
            errors.append(
                f"Warning: block type '{tgt_node.block_type}' not in registry, "
                f"skipping type check for node '{tgt_node_id}'"
            )
            continue

        src_port = _find_port(src_spec.output_ports, src_port_name)
        if src_port is None:
            errors.append(f"Warning: port '{src_port_name}' not found on block '{src_node.block_type}'")
            continue

        tgt_port = _find_port(tgt_spec.input_ports, tgt_port_name)
        if tgt_port is None:
            errors.append(f"Warning: port '{tgt_port_name}' not found on block '{tgt_node.block_type}'")
            continue

        if isinstance(src_port, OutputPort) and isinstance(tgt_port, InputPort):
            ok, reason = validate_connection(src_port, tgt_port)
            if not ok:
                errors.append(f"Edge '{edge.source}' -> '{edge.target}': {reason}")

    # ------------------------------------------------------------------
    # Check 6: Dangling required input ports
    # ------------------------------------------------------------------
    # Build a map of which input ports are connected per node.
    connected_inputs: dict[str, set[str]] = {node.id: set() for node in workflow.nodes}
    for edge in workflow.edges:
        tgt_parsed = _parse_port_ref(edge.target)
        if tgt_parsed is not None:
            tgt_node_id, tgt_port_name = tgt_parsed
            if tgt_node_id in connected_inputs:
                connected_inputs[tgt_node_id].add(tgt_port_name)

    for node in workflow.nodes:
        spec: BlockSpec | None = specs.get(node.block_type)
        if spec is None:
            continue  # unknown block type — already warned in Check 5

        for port in spec.input_ports:
            if isinstance(port, InputPort) and port.required and port.name not in connected_inputs[node.id]:
                errors.append(f"Node '{node.id}': required input port '{port.name}' has no incoming connection")

    return errors
