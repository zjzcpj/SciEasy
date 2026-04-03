"""Artifact type — opaque files (PDF, binary, images, reports)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scieasy.core.types.base import DataObject


class Artifact(DataObject):
    """Opaque file artifact (PDF, binary blob, rendered report, etc.).

    Attributes:
        file_path: Local filesystem path to the artifact, if available.
        mime_type: MIME type of the artifact (e.g. "application/pdf").
        description: Human-readable description.
    """

    def __init__(
        self,
        *,
        file_path: Path | None = None,
        mime_type: str | None = None,
        description: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.file_path = file_path
        self.mime_type = mime_type
        self.description = description
