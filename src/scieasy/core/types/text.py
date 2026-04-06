"""Text — plain text, markdown, or JSON content DataObject.

ADR-027 D2: this module is core-only. No domain subclasses of
:class:`Text` exist in core; any future text-format specialisations
(e.g. LaTeX, RTF) should live in a plugin package.
"""

from __future__ import annotations

from typing import Any, Self

from scieasy.core.types.base import DataObject


class Text(DataObject):
    """Textual data object (plain text, markdown, JSON, etc.).

    Attributes:
        content: The text content, if loaded.
        format: Content format identifier (e.g. ``"plain"``, ``"markdown"``,
            ``"json"``).
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
        """Construct a Text with optional content and format metadata.

        Standard :class:`DataObject` slots (``framework``, ``meta``,
        ``user``, ``storage_ref``) are passed through ``**kwargs`` to
        :meth:`DataObject.__init__`.
        """
        super().__init__(**kwargs)
        self.content = content
        self.format = format
        self.encoding = encoding

    def get_in_memory_data(self) -> Any:
        """Return text content for persistence."""
        if self.content is not None:
            return self.content
        return super().get_in_memory_data()

    # -- with_meta override (T-005's base only handles standard slots) ----

    def with_meta(self, **changes: Any) -> Self:
        """Return a new Text with the ``meta`` slot updated.

        Overrides :meth:`DataObject.with_meta` to propagate the
        Text-specific constructor arguments (``content``, ``format``,
        ``encoding``). The base implementation only propagates the four
        standard DataObject slots (``framework``, ``meta``, ``user``,
        ``storage_ref``); without this override the call would lose the
        Text-specific attributes on the returned instance.

        Raises:
            ValueError: if ``self.meta is None`` (no typed Meta to
                update). Only Text subclasses that declare a ``Meta``
                ClassVar can use :meth:`with_meta`.
        """
        if self._meta is None:
            raise ValueError(
                f"{type(self).__name__}.with_meta() requires a typed `meta` slot. "
                f"This instance has meta=None. Subclass with a class-level `Meta` "
                f"Pydantic model and pass an instance via the constructor to use "
                f"with_meta()."
            )

        from scieasy.core.meta import with_meta_changes

        new_meta = with_meta_changes(self._meta, **changes)
        new_framework = self._framework.derive()

        return type(self)(
            content=self.content,
            format=self.format,
            encoding=self.encoding,
            framework=new_framework,
            meta=new_meta,
            user=dict(self._user),
            storage_ref=self._storage_ref,
        )
