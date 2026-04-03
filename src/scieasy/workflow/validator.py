"""Workflow validation -- type compatibility, cycles, missing connections."""

from __future__ import annotations

from typing import Any


def validate_workflow(workflow: Any) -> list[str]:
    """Validate a workflow definition and return a list of diagnostic messages.

    Checks may include cycle detection, missing connections, port type
    compatibility, and schema conformance.

    Parameters
    ----------
    workflow:
        A ``WorkflowDefinition`` instance to validate.

    Returns
    -------
    list[str]
        A (possibly empty) list of human-readable validation error messages.
        An empty list indicates a valid workflow.
    """
    raise NotImplementedError
