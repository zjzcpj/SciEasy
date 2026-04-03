"""Integration test — simplified multimodal workflow: load -> process -> merge -> export."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.engine.events import EventBus
from scieasy.engine.scheduler import DAGScheduler
from scieasy.workflow.definition import EdgeDef, NodeDef, WorkflowDefinition
from tests.engine.conftest import make_test_registry

# --- Simulation blocks for multimodal workflow ---


class LoadRamanBlock(Block):
    """Simulates loading a Raman spectrum dataset."""

    name: ClassVar[str] = "LoadRaman"
    input_ports: ClassVar[list[InputPort]] = []
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="spectrum", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        # Simulate loaded Raman data as a list of values.
        return {"spectrum": [1.0, 2.0, 3.0, 4.0, 5.0]}


class LoadImageBlock(Block):
    """Simulates loading a microscopy image."""

    name: ClassVar[str] = "LoadImage"
    input_ports: ClassVar[list[InputPort]] = []
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="image", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        # Simulate image as 2D grid values.
        return {"image": [[10, 20], [30, 40]]}


class SmoothSpectrumBlock(Block):
    """Simulates a smoothing/preprocessing step on spectral data."""

    name: ClassVar[str] = "SmoothSpectrum"
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="spectrum", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="smoothed", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        spec = inputs["spectrum"]
        window = config.get("window", 3)
        # Simple moving average.
        smoothed = []
        for i in range(len(spec)):
            start = max(0, i - window // 2)
            end = min(len(spec), i + window // 2 + 1)
            smoothed.append(sum(spec[start:end]) / (end - start))
        return {"smoothed": smoothed}


class SegmentImageBlock(Block):
    """Simulates image segmentation."""

    name: ClassVar[str] = "SegmentImage"
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="image", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="mask", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        image = inputs["image"]
        threshold = config.get("threshold", 25)
        # Simple thresholding.
        mask = [[1 if px > threshold else 0 for px in row] for row in image]
        return {"mask": mask}


class MergeResultsBlock(Block):
    """Merges spectral and image results into a combined report."""

    name: ClassVar[str] = "MergeResults"
    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="smoothed", accepted_types=[]),
        InputPort(name="mask", accepted_types=[]),
    ]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="report", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {
            "report": {
                "spectrum_summary": sum(inputs["smoothed"]) / len(inputs["smoothed"]),
                "segmented_pixels": sum(sum(row) for row in inputs["mask"]),
                "combined": True,
            }
        }


class ExportBlock(Block):
    """Simulates exporting the final report."""

    name: ClassVar[str] = "Export"
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="report", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="path", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"path": f"/output/{config.get('filename', 'result.json')}"}


class TestMultimodalWorkflow:
    """Simplified Appendix A scenario: load -> process -> merge -> export."""

    @pytest.mark.asyncio
    async def test_full_multimodal_pipeline(self) -> None:
        registry = make_test_registry(
            LoadRamanBlock,
            LoadImageBlock,
            SmoothSpectrumBlock,
            SegmentImageBlock,
            MergeResultsBlock,
            ExportBlock,
        )

        wf = WorkflowDefinition(
            id="multimodal-test",
            description="Raman + Microscopy multimodal pipeline",
            nodes=[
                NodeDef(id="load_raman", block_type="LoadRaman"),
                NodeDef(id="load_image", block_type="LoadImage"),
                NodeDef(id="smooth", block_type="SmoothSpectrum", config={"params": {"window": 3}}),
                NodeDef(id="segment", block_type="SegmentImage", config={"params": {"threshold": 25}}),
                NodeDef(id="merge", block_type="MergeResults"),
                NodeDef(id="export", block_type="Export", config={"params": {"filename": "report.json"}}),
            ],
            edges=[
                EdgeDef(source="load_raman:spectrum", target="smooth:spectrum"),
                EdgeDef(source="load_image:image", target="segment:image"),
                EdgeDef(source="smooth:smoothed", target="merge:smoothed"),
                EdgeDef(source="segment:mask", target="merge:mask"),
                EdgeDef(source="merge:report", target="export:report"),
            ],
        )

        bus = EventBus()
        scheduler = DAGScheduler(wf, registry=registry, event_bus=bus)
        outputs = await scheduler.execute()

        # Verify all nodes executed.
        assert len(outputs) == 6

        # Verify the pipeline produced correct results.
        report = outputs["merge"]["report"]
        assert report["combined"] is True
        assert report["segmented_pixels"] == 2  # 30 and 40 > 25.
        assert isinstance(report["spectrum_summary"], float)

        assert outputs["export"]["path"] == "/output/report.json"

        # Verify event stream.
        event_types = [e.event_type for e in bus.history]
        assert event_types[0] == "workflow_started"
        assert event_types[-1] == "workflow_complete"
        assert event_types.count("block_state_changed") >= 6
