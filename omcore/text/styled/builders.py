"""Mutable builders for immutable styled text."""
from ... import lang
from .styles import StyleLike
from .styles import StylePatch
from .styles import as_style_ref
from .texts import StyledText
from .texts import StyledTextLike
from .texts import StyleSpan
from .texts import _normalize_style_range


##


class StyledTextBuilder(lang.Final):
    """A mutable local builder that produces immutable `StyledText` values."""

    def __init__(self) -> None:
        super().__init__()

        self._parts: list[str] = []
        self._spans: list[StyleSpan] = []
        self._length = 0

    def __bool__(self) -> bool:
        return bool(self._length)

    def __len__(self) -> int:
        return self._length

    @property
    def position(self) -> int:
        return self._length

    def clear(self) -> None:
        self._parts.clear()
        self._spans.clear()
        self._length = 0

    def append(
            self,
            value: StyledTextLike,
            style: StyleLike | None = None,
    ) -> StyledTextBuilder:
        """
        Append text, optionally under an outer style.

        An appended `StyledText` retains its own spans above the outer style, matching ordinary nested-style behavior.
        """

        if isinstance(value, str):
            value = StyledText(value)
        elif not isinstance(value, StyledText):
            raise TypeError(value)

        offset = self._length
        self._parts.append(value.text)
        self._length += len(value.text)

        if value.text and style is not None:
            ref = as_style_ref(style)
            if not isinstance(ref, StylePatch) or not ref.is_empty:
                self._spans.append(StyleSpan(offset, self._length, ref))

        self._spans.extend(span.shift(offset) for span in value.spans)
        return self

    def stylize(
            self,
            style: StyleLike,
            start: int = 0,
            end: int | None = None,
    ) -> StyledTextBuilder:
        """Apply a new highest-priority style to a range already in the builder."""

        start, end = _normalize_style_range(self._length, start, end)
        if start == end:
            return self

        ref = as_style_ref(style)
        if not isinstance(ref, StylePatch) or not ref.is_empty:
            self._spans.append(StyleSpan(start, end, ref))
        return self

    def build(self) -> StyledText:
        """Build an immutable value without modifying the builder."""

        return StyledText(''.join(self._parts), tuple(self._spans))
