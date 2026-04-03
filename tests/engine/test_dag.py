"""Tests for DAG construction and topological sort."""

from __future__ import annotations

import pytest

from scieasy.engine.dag import build_dag, topological_sort
from scieasy.workflow.definition import EdgeDef, NodeDef, WorkflowDefinition


class TestBuildDag:
    """build_dag() — construct DAGNode graph from WorkflowDefinition."""

    def test_single_node_no_edges(self) -> None:
        wf = WorkflowDefinition(
            nodes=[NodeDef(id="A", block_type="Loader")],
            edges=[],
        )
        dag = build_dag(wf)
        assert "A" in dag
        assert dag["A"].block_type == "Loader"
        assert dag["A"].dependencies == set()
        assert dag["A"].dependents == set()

    def test_linear_chain(self) -> None:
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="Load"),
                NodeDef(id="B", block_type="Process"),
                NodeDef(id="C", block_type="Save"),
            ],
            edges=[
                EdgeDef(source="A:out", target="B:in"),
                EdgeDef(source="B:out", target="C:in"),
            ],
        )
        dag = build_dag(wf)
        assert dag["B"].dependencies == {"A"}
        assert dag["A"].dependents == {"B"}
        assert dag["C"].dependencies == {"B"}
        assert dag["B"].dependents == {"C"}

    def test_branching_dag(self) -> None:
        """A -> B and A -> C (fan-out)."""
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="Load"),
                NodeDef(id="B", block_type="ProcessA"),
                NodeDef(id="C", block_type="ProcessB"),
            ],
            edges=[
                EdgeDef(source="A:out", target="B:in"),
                EdgeDef(source="A:out", target="C:in"),
            ],
        )
        dag = build_dag(wf)
        assert dag["A"].dependents == {"B", "C"}
        assert dag["B"].dependencies == {"A"}
        assert dag["C"].dependencies == {"A"}

    def test_diamond_dag(self) -> None:
        """A -> B, A -> C, B -> D, C -> D."""
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="Load"),
                NodeDef(id="B", block_type="Left"),
                NodeDef(id="C", block_type="Right"),
                NodeDef(id="D", block_type="Merge"),
            ],
            edges=[
                EdgeDef(source="A:out", target="B:in"),
                EdgeDef(source="A:out", target="C:in"),
                EdgeDef(source="B:out", target="D:left"),
                EdgeDef(source="C:out", target="D:right"),
            ],
        )
        dag = build_dag(wf)
        assert dag["D"].dependencies == {"B", "C"}
        assert dag["D"].input_edges == {
            "left": ("B", "out"),
            "right": ("C", "out"),
        }

    def test_port_edge_mapping(self) -> None:
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="Load"),
                NodeDef(id="B", block_type="Process"),
            ],
            edges=[EdgeDef(source="A:data", target="B:spectrum")],
        )
        dag = build_dag(wf)
        assert dag["B"].input_edges["spectrum"] == ("A", "data")
        assert dag["A"].output_edges["data"] == [("B", "spectrum")]

    def test_unknown_source_node_raises(self) -> None:
        wf = WorkflowDefinition(
            nodes=[NodeDef(id="A", block_type="Load")],
            edges=[EdgeDef(source="X:out", target="A:in")],
        )
        with pytest.raises(ValueError, match="unknown source node"):
            build_dag(wf)

    def test_unknown_target_node_raises(self) -> None:
        wf = WorkflowDefinition(
            nodes=[NodeDef(id="A", block_type="Load")],
            edges=[EdgeDef(source="A:out", target="X:in")],
        )
        with pytest.raises(ValueError, match="unknown target node"):
            build_dag(wf)

    def test_invalid_port_ref_raises(self) -> None:
        wf = WorkflowDefinition(
            nodes=[NodeDef(id="A", block_type="Load"), NodeDef(id="B", block_type="Process")],
            edges=[EdgeDef(source="A_out", target="B:in")],
        )
        with pytest.raises(ValueError, match="Invalid port reference"):
            build_dag(wf)

    def test_config_preserved(self) -> None:
        wf = WorkflowDefinition(
            nodes=[NodeDef(id="A", block_type="Load", config={"path": "/data"})],
        )
        dag = build_dag(wf)
        assert dag["A"].config == {"path": "/data"}


class TestTopologicalSort:
    """topological_sort() — Kahn's algorithm with cycle detection."""

    def test_single_node(self) -> None:
        wf = WorkflowDefinition(nodes=[NodeDef(id="A", block_type="X")])
        dag = build_dag(wf)
        assert topological_sort(dag) == ["A"]

    def test_linear_order(self) -> None:
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="X"),
                NodeDef(id="B", block_type="X"),
                NodeDef(id="C", block_type="X"),
            ],
            edges=[
                EdgeDef(source="A:o", target="B:i"),
                EdgeDef(source="B:o", target="C:i"),
            ],
        )
        dag = build_dag(wf)
        order = topological_sort(dag)
        assert order == ["A", "B", "C"]

    def test_diamond_order(self) -> None:
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="X"),
                NodeDef(id="B", block_type="X"),
                NodeDef(id="C", block_type="X"),
                NodeDef(id="D", block_type="X"),
            ],
            edges=[
                EdgeDef(source="A:o", target="B:i"),
                EdgeDef(source="A:o", target="C:i"),
                EdgeDef(source="B:o", target="D:i"),
                EdgeDef(source="C:o", target="D:i"),
            ],
        )
        dag = build_dag(wf)
        order = topological_sort(dag)
        assert order[0] == "A"
        assert order[-1] == "D"
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_cycle_detection(self) -> None:
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="X"),
                NodeDef(id="B", block_type="X"),
            ],
            edges=[
                EdgeDef(source="A:o", target="B:i"),
                EdgeDef(source="B:o", target="A:i"),
            ],
        )
        dag = build_dag(wf)
        with pytest.raises(ValueError, match="Cycle detected"):
            topological_sort(dag)

    def test_self_loop_detection(self) -> None:
        wf = WorkflowDefinition(
            nodes=[NodeDef(id="A", block_type="X")],
            edges=[EdgeDef(source="A:o", target="A:i")],
        )
        dag = build_dag(wf)
        with pytest.raises(ValueError, match="Cycle detected"):
            topological_sort(dag)

    def test_disconnected_nodes(self) -> None:
        wf = WorkflowDefinition(
            nodes=[
                NodeDef(id="A", block_type="X"),
                NodeDef(id="B", block_type="X"),
                NodeDef(id="C", block_type="X"),
            ],
            edges=[],
        )
        dag = build_dag(wf)
        order = topological_sort(dag)
        assert set(order) == {"A", "B", "C"}
