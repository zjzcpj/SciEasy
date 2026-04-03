"""YAML serialisation -- load and save workflow definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml(path: str | Path) -> Any:
    """Deserialise a workflow definition from a YAML file.

    Parameters
    ----------
    path:
        Path to the YAML file to read.

    Returns
    -------
    Any
        A ``WorkflowDefinition`` instance (or equivalent dict representation).
    """
    raise NotImplementedError


def save_yaml(workflow: Any, path: str | Path) -> None:
    """Serialise a workflow definition to a YAML file.

    Parameters
    ----------
    workflow:
        The workflow object to persist.
    path:
        Destination file path (will be created or overwritten).
    """
    raise NotImplementedError
