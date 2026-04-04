"""YAML serialisation -- load and save workflow definitions."""

from __future__ import annotations

from pathlib import Path

import yaml

from scieasy.workflow.definition import WorkflowDefinition
from scieasy.workflow.schema import WorkflowFileModel, WorkflowModel


def load_yaml(path: str | Path) -> WorkflowDefinition:
    """Deserialise a workflow definition from a YAML file.

    Parameters
    ----------
    path:
        Path to the YAML file to read.

    Returns
    -------
    WorkflowDefinition
        A validated ``WorkflowDefinition`` instance.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    yaml.YAMLError
        If the file is not valid YAML.
    pydantic.ValidationError
        If the YAML content does not match the expected schema.
    """
    text = Path(path).read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    validated = WorkflowFileModel.model_validate(raw)
    return validated.workflow.to_definition()


def save_yaml(workflow: WorkflowDefinition, path: str | Path) -> None:
    """Serialise a workflow definition to a YAML file.

    Parameters
    ----------
    workflow:
        The workflow object to persist.
    path:
        Destination file path (will be created or overwritten).
    """
    model = WorkflowModel.from_definition(workflow)
    file_model = WorkflowFileModel(workflow=model)
    data = file_model.model_dump(exclude_none=True)
    Path(path).write_text(
        yaml.safe_dump(data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
