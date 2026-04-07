"""Shared runtime services for the FastAPI layer."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import shutil
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from uuid import uuid4

import pyarrow.parquet as pq
import yaml

from scieasy.blocks.io.adapter_registry import AdapterRegistry
from scieasy.blocks.registry import BlockRegistry
from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.array import Array
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.composite import CompositeData
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.registry import TypeRegistry
from scieasy.core.types.series import Series, Spectrum
from scieasy.core.types.text import Text
from scieasy.engine.checkpoint import CheckpointManager
from scieasy.engine.events import EventBus
from scieasy.engine.resources import ResourceManager
from scieasy.engine.runners.local import LocalRunner
from scieasy.engine.runners.process_handle import ProcessRegistry
from scieasy.engine.scheduler import DAGScheduler
from scieasy.workflow.definition import EdgeDef, NodeDef, WorkflowDefinition
from scieasy.workflow.serializer import load_yaml, save_yaml

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _slugify(name: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in name).strip("-")
    return slug or "project"


def _safe_parent_dir(path: str | Path | None) -> Path:
    if path is None:
        return Path.cwd()
    return Path(path).expanduser().resolve()


def _infer_type_name_from_ref(ref: StorageReference) -> str:
    fmt = (ref.format or "").lower()
    if fmt in {"csv", "parquet"}:
        return DataFrame.__name__
    if fmt in {"txt", "json", "yaml", "yml", "md"}:
        return Text.__name__
    # T-006 / ADR-027 D2: ``Image`` lives in the imaging plugin, not
    # core. Imaging payloads are modelled as generic ``Array`` with
    # ``axes=["y", "x"]`` here; the frontend preview hook still handles
    # the "image" kind via the TIFF/PNG data-URI path below.
    if fmt in {"png", "jpg", "jpeg", "tif", "tiff"}:
        return Array.__name__
    if fmt == "zarr":
        return Array.__name__
    return Artifact.__name__


def _image_data_uri_from_matrix(values: list[list[float]]) -> str:
    """Encode a 2D float matrix as a grayscale PNG data URI.

    Uses stdlib struct + zlib to produce a minimal valid PNG.
    No external dependencies.  Universal browser support.
    """
    import struct
    import zlib

    height = len(values)
    width = len(values[0]) if values and values[0] else 0
    if width == 0 or height == 0:
        return ""
    max_val = max((v for row in values for v in row), default=1.0) or 1.0

    # Build raw scanlines: each row has a filter byte (0 = None) followed by pixel bytes.
    raw = b""
    for row in values:
        raw += b"\x00"  # PNG filter: None
        raw += bytes(max(0, min(255, int(v / max_val * 255))) for v in row)

    def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        body = chunk_type + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    # IHDR: width, height, bit-depth=8, color-type=0 (grayscale)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", ihdr_data)
    png += _png_chunk(b"IDAT", zlib.compress(raw))
    png += _png_chunk(b"IEND", b"")

    return f"data:image/png;base64,{base64.b64encode(png).decode('ascii')}"


@dataclass
class KnownProject:
    """Persisted metadata for a known project workspace."""

    id: str
    name: str
    path: str
    description: str = ""
    last_opened: str | None = None


@dataclass
class DataRecord:
    """Opaque registry entry for a previewable data object."""

    id: str
    ref: StorageReference
    type_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRun:
    """Track a live scheduler task for a workflow."""

    scheduler: DAGScheduler
    task: asyncio.Task[None]
    checkpoint_manager: CheckpointManager


class LogBroadcaster:
    """Fan-out log events to SSE subscribers."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    async def publish(
        self,
        *,
        level: str,
        message: str,
        workflow_id: str | None = None,
        block_id: str | None = None,
    ) -> None:
        payload = {
            "timestamp": _now_iso(),
            "level": level,
            "message": message,
            "workflow_id": workflow_id,
            "block_id": block_id,
        }
        for queue in list(self._subscribers):
            await queue.put(payload)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)


class ApiRuntime:
    """Shared mutable state owned by the FastAPI application."""

    def __init__(self) -> None:
        self.registry_dir = Path.home() / ".scieasy"
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.known_projects_path = self.registry_dir / "projects.json"
        self.known_projects: dict[str, KnownProject] = {}

        self.active_project: KnownProject | None = None
        self.data_catalog: dict[str, DataRecord] = {}
        self.workflow_runs: dict[str, WorkflowRun] = {}

        self.event_bus = EventBus()
        self.resource_manager = ResourceManager(event_bus=self.event_bus)
        self.process_registry = ProcessRegistry()
        self.runner = LocalRunner(event_bus=self.event_bus, registry=self.process_registry)
        self.block_registry = BlockRegistry()
        self.type_registry = TypeRegistry()
        self.log_broadcaster = LogBroadcaster()

        self._load_known_projects()
        self._configure_static_registries()
        self._bind_event_logging()

    def _configure_static_registries(self) -> None:
        self.type_registry.scan_builtins()
        self.refresh_block_registry()

    def _bind_event_logging(self) -> None:
        async def _emit_log(event: Any) -> None:
            message = event.event_type.replace("_", " ")
            workflow_id = None
            if isinstance(event.data, dict):
                workflow_id = event.data.get("workflow_id")
            await self.log_broadcaster.publish(
                level="info",
                message=message,
                workflow_id=workflow_id,
                block_id=event.block_id,
            )

        async def _register_outputs(event: Any) -> None:
            if event.event_type != "block_done":
                return
            outputs = event.data.get("outputs", {}) if isinstance(event.data, dict) else {}
            event.data["outputs"] = self.register_output_payload(outputs)

        for event_type in (
            "workflow_started",
            "workflow_completed",
            "block_running",
            "block_done",
            "block_error",
            "block_cancelled",
            "block_skipped",
        ):
            self.event_bus.subscribe(event_type, _register_outputs)
            self.event_bus.subscribe(event_type, _emit_log)

    def _load_known_projects(self) -> None:
        if not self.known_projects_path.exists():
            self.known_projects = {}
            return
        raw = json.loads(self.known_projects_path.read_text(encoding="utf-8"))
        self.known_projects = {
            entry["id"]: KnownProject(**entry)
            for entry in raw.get("projects", [])
            if isinstance(entry, dict) and entry.get("id") and entry.get("path")
        }

    def _save_known_projects(self) -> None:
        payload = {"projects": [asdict(entry) for entry in self.known_projects.values()]}
        self.known_projects_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def refresh_block_registry(self) -> None:
        registry = BlockRegistry()
        if self.active_project is not None:
            registry.add_scan_dir(Path(self.active_project.path) / "blocks")
            registry.add_scan_dir(Path.home() / ".scieasy" / "blocks")
        registry.scan()
        self.block_registry = registry

    def create_project(self, name: str, description: str = "", parent_path: str | None = None) -> KnownProject:
        parent_dir = _safe_parent_dir(parent_path)
        project_path = parent_dir / _slugify(name)
        if project_path.exists():
            raise FileExistsError(f"Project directory already exists: {project_path}")

        for subdir in (
            "workflows",
            "data/raw",
            "data/zarr",
            "data/parquet",
            "data/artifacts",
            "blocks",
            "types",
            "checkpoints",
            "lineage",
            "logs",
        ):
            (project_path / subdir).mkdir(parents=True, exist_ok=True)

        project_id = f"project-{uuid4().hex[:8]}"
        project = KnownProject(
            id=project_id,
            name=name,
            path=str(project_path),
            description=description,
            last_opened=_now_iso(),
        )
        metadata = {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": description,
                "version": "0.1.0",
                "created": _now_iso(),
            }
        }
        (project_path / "project.yaml").write_text(
            yaml.safe_dump(metadata, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        self.known_projects[project.id] = project
        self._save_known_projects()
        self.open_project(project.id)
        return project

    def list_projects(self) -> list[KnownProject]:
        self._load_known_projects()
        return sorted(self.known_projects.values(), key=lambda item: item.name.lower())

    def _load_project_from_path(self, project_path: Path) -> KnownProject:
        project_file = project_path / "project.yaml"
        if not project_file.exists():
            raise FileNotFoundError(f"Missing project.yaml in {project_path}")
        raw = yaml.safe_load(project_file.read_text(encoding="utf-8")) or {}
        project_data = raw.get("project", {}) if isinstance(raw, dict) else {}
        project_id = project_data.get("id") or f"project-{uuid4().hex[:8]}"
        entry = KnownProject(
            id=project_id,
            name=project_data.get("name") or project_path.name,
            path=str(project_path),
            description=project_data.get("description", ""),
            last_opened=_now_iso(),
        )
        self.known_projects[entry.id] = entry
        self._save_known_projects()
        return entry

    def open_project(self, project_id_or_path: str) -> KnownProject:
        candidate = self.known_projects.get(project_id_or_path)
        if candidate is None:
            decoded = Path(unquote(project_id_or_path)).expanduser()
            resolved = decoded.resolve()
            if not (resolved / "project.yaml").is_file():
                raise FileNotFoundError(f"Not a valid SciEasy project (no project.yaml): {resolved}")
            candidate = self._load_project_from_path(resolved)
        candidate.last_opened = _now_iso()
        self.known_projects[candidate.id] = candidate
        self._save_known_projects()
        self.active_project = candidate
        self.data_catalog = {}
        self.refresh_block_registry()
        return candidate

    def update_project(
        self, project_id_or_path: str, *, name: str | None = None, description: str | None = None
    ) -> KnownProject:
        project = self.open_project(project_id_or_path)
        project_file = Path(project.path) / "project.yaml"
        raw = yaml.safe_load(project_file.read_text(encoding="utf-8")) or {}
        raw.setdefault("project", {})
        if name is not None:
            raw["project"]["name"] = name
            project.name = name
        if description is not None:
            raw["project"]["description"] = description
            project.description = description
        project_file.write_text(
            yaml.safe_dump(raw, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        self.known_projects[project.id] = project
        self._save_known_projects()
        return project

    def delete_project(self, project_id_or_path: str) -> None:
        project = self.open_project(project_id_or_path)
        project_path = Path(project.path).resolve()
        if not project_path.exists():
            self.known_projects.pop(project.id, None)
            self._save_known_projects()
            return
        if project_path == Path(project_path.anchor):
            raise ValueError("Refusing to delete drive root")
        if not (project_path / "project.yaml").is_file():
            raise ValueError(f"Refusing to delete non-project directory: {project_path}")
        logger.warning("Deleting project directory: %s", project_path)
        shutil.rmtree(project_path)
        self.known_projects.pop(project.id, None)
        if self.active_project is not None and self.active_project.id == project.id:
            self.active_project = None
            self.data_catalog = {}
        self._save_known_projects()

    def project_response(self, project: KnownProject) -> dict[str, Any]:
        workflows = self.list_project_workflows(project)
        return {
            "id": project.id,
            "name": project.name,
            "path": project.path,
            "description": project.description,
            "last_opened": project.last_opened,
            "workflow_count": len(workflows),
            "workflows": workflows,
            "current_workflow_id": workflows[0] if workflows else None,
        }

    def require_active_project(self) -> KnownProject:
        if self.active_project is None:
            raise RuntimeError("No project is currently open.")
        return self.active_project

    def list_project_workflows(self, project: KnownProject | None = None) -> list[str]:
        project = project or self.require_active_project()
        workflows_dir = Path(project.path) / "workflows"
        return sorted(path.stem for path in workflows_dir.glob("*.yaml"))

    def workflow_path(self, workflow_id: str) -> Path:
        project = self.require_active_project()
        return Path(project.path) / "workflows" / f"{workflow_id}.yaml"

    def save_workflow(self, payload: dict[str, Any]) -> WorkflowDefinition:
        definition = WorkflowDefinition(
            id=payload["id"],
            version=payload.get("version", "1.0.0"),
            description=payload.get("description", ""),
            metadata=payload.get("metadata", {}),
            nodes=[
                NodeDef(
                    id=node["id"],
                    block_type=node["block_type"],
                    config=node.get("config", {}),
                    execution_mode=node.get("execution_mode"),
                    layout=node.get("layout"),
                )
                for node in payload.get("nodes", [])
            ],
            edges=[EdgeDef(source=edge["source"], target=edge["target"]) for edge in payload.get("edges", [])],
        )
        from scieasy.workflow.validator import validate_workflow

        errors = validate_workflow(definition)
        if errors:
            raise ValueError(f"Workflow validation failed: {'; '.join(str(e) for e in errors)}")

        save_yaml(definition, self.workflow_path(definition.id))
        return definition

    def load_workflow(self, workflow_id: str) -> WorkflowDefinition:
        path = self.workflow_path(workflow_id)
        if not path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")
        return load_yaml(path)

    def delete_workflow(self, workflow_id: str) -> None:
        path = self.workflow_path(workflow_id)
        if path.exists():
            path.unlink()

    def upload_file(self, filename: str, content: bytes) -> dict[str, Any]:
        project = self.require_active_project()
        safe_name = Path(filename).name  # strips all directory components
        if not safe_name or safe_name.startswith("."):
            raise ValueError(f"Invalid filename: {filename!r}")
        destination = Path(project.path) / "data" / "raw" / safe_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

        registry = AdapterRegistry()
        registry.register_defaults()
        extension = destination.suffix or ".bin"
        try:
            adapter_class = registry.get_for_extension(extension)
        except KeyError:
            from scieasy.blocks.io.adapters.generic_adapter import GenericAdapter

            adapter_class = GenericAdapter
        adapter = adapter_class()
        ref = adapter.create_reference(destination)
        record = self.register_data_ref(ref)
        return {
            "ref": record.id,
            "type_name": record.type_name,
            "metadata": record.metadata,
        }

    def register_data_ref(
        self,
        ref: StorageReference,
        *,
        type_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DataRecord:
        record = DataRecord(
            id=f"data-{uuid4().hex}",
            ref=ref,
            type_name=type_name or _infer_type_name_from_ref(ref),
            metadata=metadata or self.describe_ref(ref),
        )
        self.data_catalog[record.id] = record
        return record

    def register_output_payload(self, payload: Any) -> Any:
        if isinstance(payload, dict) and {"backend", "path"}.issubset(payload.keys()):
            ref = StorageReference(
                backend=str(payload["backend"]),
                path=str(payload["path"]),
                format=payload.get("format"),
                metadata=payload.get("metadata"),
            )
            record = self.register_data_ref(ref, metadata=self.describe_ref(ref))
            return {
                "data_ref": record.id,
                "type_name": record.type_name,
                "metadata": record.metadata,
            }
        if isinstance(payload, dict) and payload.get("_collection") is True:
            items = [self.register_output_payload(item) for item in payload.get("items", [])]
            return {
                "kind": "collection",
                "count": len(items),
                "item_type": payload.get("item_type"),
                "items": items,
            }
        if isinstance(payload, dict):
            return {key: self.register_output_payload(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self.register_output_payload(item) for item in payload]
        return payload

    def get_data_record(self, data_ref: str) -> DataRecord:
        if data_ref not in self.data_catalog:
            raise KeyError(f"Unknown data reference: {data_ref}")
        return self.data_catalog[data_ref]

    def describe_ref(self, ref: StorageReference) -> dict[str, Any]:
        path = Path(ref.path)
        metadata: dict[str, Any] = {
            "backend": ref.backend,
            "path": ref.path,
            "format": ref.format,
            "exists": path.exists(),
        }
        if path.exists():
            metadata["size_bytes"] = path.stat().st_size
        if ref.metadata:
            metadata.update(ref.metadata)
        if path.suffix.lower() == ".parquet" and path.exists():
            try:
                table = pq.read_table(path)
                metadata["columns"] = table.column_names
                metadata["row_count"] = table.num_rows
            except Exception:
                logger.debug("Failed to read parquet metadata for %s", ref.path, exc_info=True)
        return metadata

    def preview_data(self, data_ref: str) -> dict[str, Any]:
        record = self.get_data_record(data_ref)
        ref = record.ref
        path = Path(ref.path)
        suffix = path.suffix.lower()

        if record.type_name == DataFrame.__name__ or suffix in {".csv", ".parquet"}:
            if suffix == ".parquet":
                table = pq.read_table(path).slice(0, 100)
            else:
                import pyarrow.csv as pcsv

                table = pcsv.read_csv(str(path)).slice(0, 100)
            rows = table.to_pylist()
            return {
                "kind": "table",
                "columns": table.column_names,
                "rows": rows,
                "row_count": len(rows),
            }

        if record.type_name in {Text.__name__, Artifact.__name__} and suffix in {
            ".txt",
            ".json",
            ".yaml",
            ".yml",
            ".md",
        }:
            text = path.read_text(encoding="utf-8", errors="replace")
            return {
                "kind": "text",
                "content": text[:5000],
                "language": suffix.lstrip(".") or "text",
            }

        if record.type_name == Array.__name__ or suffix in {".tif", ".tiff"}:
            try:
                from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter

                image = TIFFAdapter().read(path)
                data = getattr(image, "_data", None)
                if data is not None:
                    matrix = data
                    while getattr(matrix, "ndim", 0) > 2:
                        matrix = matrix[0]
                    height = min(int(matrix.shape[0]), 64)
                    width = min(int(matrix.shape[1]), 64)
                    thumbnail = matrix[:height, :width].tolist()
                    return {
                        "kind": "image",
                        "shape": list(matrix.shape),
                        "thumbnail": thumbnail,
                        "src": _image_data_uri_from_matrix(thumbnail),
                    }
            except Exception:
                logger.debug("Failed to read TIFF preview for %s", ref.path, exc_info=True)
            return {
                "kind": "artifact",
                "path": ref.path,
                "mime_type": "image/tiff",
            }

        if record.type_name in {Series.__name__, Spectrum.__name__}:
            values = record.metadata.get("values", [])
            return {
                "kind": "chart",
                "points": [{"x": index, "y": value} for index, value in enumerate(values[:256])],
            }

        if record.type_name == CompositeData.__name__:
            return {
                "kind": "composite",
                "slots": record.metadata.get("slots", {}),
            }

        return {
            "kind": "artifact",
            "path": ref.path,
            "mime_type": path.suffix.lower().lstrip(".") or "application/octet-stream",
        }

    def _ancestors_of(self, workflow: WorkflowDefinition, block_id: str) -> set[str]:
        from scieasy.engine.dag import build_dag

        dag = build_dag(workflow)
        visited: set[str] = set()
        queue = list(dag.reverse_adjacency.get(block_id, []))
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(dag.reverse_adjacency.get(current, []))
        return visited

    def checkpoint_dir_for(self, workflow_id: str) -> Path:
        project = self.require_active_project()
        return Path(project.path) / "checkpoints" / workflow_id

    def start_workflow(self, workflow_id: str, *, execute_from: str | None = None) -> dict[str, Any]:
        workflow = self.load_workflow(workflow_id)
        checkpoint_manager = CheckpointManager(self.checkpoint_dir_for(workflow_id))
        checkpoint = checkpoint_manager.load(workflow_id) if execute_from is not None else None
        if execute_from is not None and checkpoint is None:
            raise FileNotFoundError("No checkpoint exists for execute-from")

        scheduler = DAGScheduler(
            workflow=workflow,
            event_bus=self.event_bus,
            resource_manager=self.resource_manager,
            process_registry=self.process_registry,
            runner=self.runner,
            registry=self.block_registry,
            checkpoint_manager=checkpoint_manager,
        )

        async def _run() -> None:
            if execute_from is not None:
                await self.log_broadcaster.publish(
                    level="info",
                    message=f"execute from {execute_from}",
                    workflow_id=workflow_id,
                )
                await scheduler.execute_from(execute_from)
            else:
                await self.log_broadcaster.publish(
                    level="info",
                    message="workflow execution started",
                    workflow_id=workflow_id,
                )
                await scheduler.execute()

        task = asyncio.create_task(_run())
        self.workflow_runs[workflow_id] = WorkflowRun(
            scheduler=scheduler,
            task=task,
            checkpoint_manager=checkpoint_manager,
        )

        reused_blocks: list[str] = []
        if execute_from is not None:
            reused_blocks = sorted(self._ancestors_of(workflow, execute_from))

        reset_blocks = sorted(set(node.id for node in workflow.nodes) - set(reused_blocks))
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Workflow execution has been scheduled.",
            "reused_blocks": reused_blocks,
            "reset_blocks": reset_blocks,
        }

    def get_run(self, workflow_id: str) -> WorkflowRun:
        if workflow_id not in self.workflow_runs:
            raise KeyError(f"Workflow is not running: {workflow_id}")
        return self.workflow_runs[workflow_id]
