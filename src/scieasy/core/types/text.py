"""Text type — plain text, markdown, or JSON content."""

from __future__ import annotations

from typing import Any

from scieasy.core.types.base import DataObject


class Text(DataObject):
    """Textual data object (plain text, markdown, JSON, etc.).

    Attributes:
        content: The text content, if loaded.
        format: Content format identifier (e.g. "plain", "markdown", "json").
        encoding: Character encoding (default UTF-8).
    """

    def __init__(
        self,
        *,
        content: str | None = None,
        format: str = "plain",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.content = content
        self.format = format
        self.encoding = encoding

    def get_in_memory_data(self) -> Any:
        """Return text content for persistence."""
        if self.content is not None:
            return self.content
        return super().get_in_memory_data()
