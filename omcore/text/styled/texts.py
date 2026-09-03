"""
Immutable styled text and its flattened run forms.

`StyledText` is an immutable plain string plus ordered, overlapping style spans. Styles are deliberately independent of
terminal escape sequences, display-cell widths, wrapping, and output targets.
"""
import typing as ta

from ... import dataclasses as dc
from ... import lang
from .styles import EMPTY_STYLE_THEME
from .styles import PLAIN_STYLE
from .styles import ResolvedStyle
from .styles import StyleLike
from .styles import StyleName
from .styles import StylePatch
from .styles import StyleRef
from .styles import StyleTheme
from .styles import as_style_ref


##


@dc.dataclass(frozen=True)
class StyleSpan(lang.Final):
    """A half-open character range carrying one style reference."""

    start: int
    end: int
    style: StyleRef

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or isinstance(self.start, bool):
            raise TypeError(self.start)
        if not isinstance(self.end, int) or isinstance(self.end, bool):
            raise TypeError(self.end)
        if self.start < 0 or self.end <= self.start:
            raise ValueError((self.start, self.end))
        if not isinstance(self.style, (StylePatch, StyleName)):
            raise TypeError(self.style)

    @classmethod
    def of(cls, start: int, end: int, style: StyleLike) -> StyleSpan:
        """Build a span while accepting an ergonomic style name string."""

        return cls(start, end, as_style_ref(style))

    def shift(self, offset: int) -> StyleSpan:
        """Return this span shifted by a character offset."""

        if not isinstance(offset, int) or isinstance(offset, bool):
            raise TypeError(offset)
        return StyleSpan(self.start + offset, self.end + offset, self.style)


@dc.dataclass(frozen=True)
class StyledTextRun(lang.Final):
    """A non-empty text run covered by one ordered stack of unresolved style references."""

    text: str
    styles: tuple[StyleRef, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError(self.text)
        if not self.text:
            raise ValueError(self.text)

        styles = tuple(self.styles)
        if not all(isinstance(style, (StylePatch, StyleName)) for style in styles):
            raise TypeError(styles)
        object.__setattr__(self, 'styles', styles)


@dc.dataclass(frozen=True)
class ResolvedStyledTextRun(lang.Final):
    """A non-empty text run with a concrete resolved style."""

    text: str
    style: ResolvedStyle = PLAIN_STYLE

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError(self.text)
        if not self.text:
            raise ValueError(self.text)
        if not isinstance(self.style, ResolvedStyle):
            raise TypeError(self.style)


type StyledTextLike = str | StyledText


def _normalize_style_range(length: int, start: int, end: int | None) -> tuple[int, int]:
    if not isinstance(start, int) or isinstance(start, bool):
        raise TypeError(start)
    if end is not None and (not isinstance(end, int) or isinstance(end, bool)):
        raise TypeError(end)

    if start < 0:
        start += length
    if end is None:
        end = length
    elif end < 0:
        end += length

    if not 0 <= start <= end <= length:
        raise ValueError((start, end))
    return start, end


@dc.dataclass(frozen=True)
class StyledText(lang.Final):
    """An immutable string with ordered, overlapping style spans."""

    text: str = ''
    spans: tuple[StyleSpan, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError(self.text)

        spans = tuple(self.spans)
        if not all(isinstance(span, StyleSpan) for span in spans):
            raise TypeError(spans)
        if any(span.end > len(self.text) for span in spans):
            raise ValueError((len(self.text), spans))

        spans = tuple(
            span
            for span in spans
            if not isinstance(span.style, StylePatch) or not span.style.is_empty
        )
        object.__setattr__(self, 'spans', spans)

    @property
    def plain(self) -> str:
        return self.text

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text)

    def __len__(self) -> int:
        return len(self.text)

    def __add__(self, other: object) -> StyledText:
        if not isinstance(other, (str, StyledText)):
            return NotImplemented
        return StyledText.of(self, other)

    def __radd__(self, other: object) -> StyledText:
        if not isinstance(other, (str, StyledText)):
            return NotImplemented
        return StyledText.of(other, self)

    @classmethod
    def of(cls, *parts: StyledTextLike) -> StyledText:
        """Concatenate strings and styled text, preserving span order and shifting their ranges."""

        if not parts:
            return cls()
        if len(parts) == 1:
            only = parts[0]
            if isinstance(only, StyledText):
                return only
            if isinstance(only, str):
                return cls(only)
            raise TypeError(only)
        return _concat_styled_text(parts)

    def join(self, parts: ta.Iterable[StyledTextLike]) -> StyledText:
        """Join strings and styled text using this value as the separator."""

        interspersed: list[StyledTextLike] = []
        first = True
        for part in parts:
            if first:
                first = False
            else:
                interspersed.append(self)
            interspersed.append(part)
        return _concat_styled_text(interspersed)

    def styled(
            self,
            style: StyleLike,
            start: int = 0,
            end: int | None = None,
    ) -> StyledText:
        """Return this value with a new highest-priority style span."""

        start, end = _normalize_style_range(len(self.text), start, end)
        if start == end:
            return self

        ref = as_style_ref(style)
        if isinstance(ref, StylePatch) and ref.is_empty:
            return self
        return StyledText(self.text, (*self.spans, StyleSpan(start, end, ref)))

    def slice(
            self,
            start: int | None = None,
            end: int | None = None,
    ) -> StyledText:
        """Return a Python-style contiguous slice with clipped and shifted spans."""

        slice_start, slice_end, _ = slice(start, end).indices(len(self.text))
        if slice_end <= slice_start:
            return StyledText()

        spans = []
        for span in self.spans:
            clipped_start = max(span.start, slice_start)
            clipped_end = min(span.end, slice_end)
            if clipped_end > clipped_start:
                spans.append(StyleSpan(
                    clipped_start - slice_start,
                    clipped_end - slice_start,
                    span.style,
                ))

        return StyledText(self.text[slice_start:slice_end], tuple(spans))

    def runs(self) -> tuple[StyledTextRun, ...]:
        """Flatten overlapping spans into text runs carrying ordered active style references."""

        if not self.text:
            return ()
        if not self.spans:
            return (StyledTextRun(self.text),)

        starts: dict[int, list[tuple[int, StyleRef]]] = {}
        ends: dict[int, list[int]] = {}
        positions = {0, len(self.text)}
        for index, span in enumerate(self.spans):
            starts.setdefault(span.start, []).append((index, span.style))
            ends.setdefault(span.end, []).append(index)
            positions.add(span.start)
            positions.add(span.end)

        ordered_positions = sorted(positions)
        active: dict[int, StyleRef] = {}
        runs: list[StyledTextRun] = []
        for index, position in enumerate(ordered_positions[:-1]):
            for span_index in ends.get(position, ()):
                active.pop(span_index, None)
            active.update(starts.get(position, ()))

            next_position = ordered_positions[index + 1]
            if next_position <= position:
                continue

            styles = tuple(active[span_index] for span_index in sorted(active))
            text = self.text[position:next_position]
            if runs and runs[-1].styles == styles:
                previous = runs[-1]
                runs[-1] = StyledTextRun(previous.text + text, styles)
            else:
                runs.append(StyledTextRun(text, styles))

        return tuple(runs)

    def resolved_runs(
            self,
            theme: StyleTheme | None = None,
            base: ResolvedStyle | None = None,
    ) -> tuple[ResolvedStyledTextRun, ...]:
        """Flatten and resolve this value, coalescing adjacent runs with equal concrete styles."""

        if theme is None:
            theme = EMPTY_STYLE_THEME
        elif not isinstance(theme, StyleTheme):
            raise TypeError(theme)

        runs: list[ResolvedStyledTextRun] = []
        for run in self.runs():
            style = theme.resolve_refs(run.styles, base)
            if runs and runs[-1].style == style:
                previous = runs[-1]
                runs[-1] = ResolvedStyledTextRun(previous.text + run.text, style)
            else:
                runs.append(ResolvedStyledTextRun(run.text, style))
        return tuple(runs)


def _concat_styled_text(parts: ta.Iterable[StyledTextLike]) -> StyledText:
    text_parts: list[str] = []
    spans: list[StyleSpan] = []
    length = 0
    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
            length += len(part)
        elif isinstance(part, StyledText):
            text_parts.append(part.text)
            spans.extend(span.shift(length) for span in part.spans)
            length += len(part.text)
        else:
            raise TypeError(part)
    return StyledText(''.join(text_parts), tuple(spans))
