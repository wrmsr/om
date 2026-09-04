"""
Word wrapping over styled segments.

Wraps a single logical line (no newlines - split those first) to a column width, breaking at spaces, hard-breaking words
wider than the whole line, dropping whitespace at wrap points, and preserving per-character styles throughout.
"""
import typing as ta

from .segments import Segment
from .segments import Segments
from .styles import StyleLike
from .widths import char_width


_Char: ta.TypeAlias = tuple[str, StyleLike | None, int]  # (char, style, width)


##


def _flatten(segments: Segments) -> list[_Char]:
    return [
        (c, segment.style, char_width(c))
        for segment in segments
        for c in segment.text
    ]


def _tokenize(chars: ta.Sequence[_Char]) -> list[list[_Char]]:
    """Split into alternating runs of spaces and non-spaces."""

    tokens: list[list[_Char]] = []
    for c in chars:
        is_space = c[0] == ' '
        if tokens and (tokens[-1][0][0] == ' ') == is_space:
            tokens[-1].append(c)
        else:
            tokens.append([c])
    return tokens


def _chars_to_segments(chars: ta.Sequence[_Char]) -> list[Segment]:
    segments: list[Segment] = []
    text = ''
    style: StyleLike | None = None
    for c, c_style, _ in chars:
        if text and c_style != style:
            segments.append(Segment(text, style))
            text = ''
        style = c_style
        text += c
    if text:
        segments.append(Segment(text, style))
    return segments


def _rstrip_spaces(chars: list[_Char]) -> list[_Char]:
    end = len(chars)
    while end > 0 and chars[end - 1][0] == ' ':
        end -= 1
    return chars[:end]


def wrap_segments(segments: Segments, width: int) -> list[list[Segment]]:
    """
    Wrap one logical line of segments to `width` columns, returning the rows (at least one, possibly empty).

    Rows never exceed `width` display columns; whitespace at a wrap point is dropped, interior whitespace preserved.
    """

    if width <= 0:
        return [list(segments)]

    chars = _flatten(segments)
    if not chars:
        return [[]]

    rows: list[list[_Char]] = []
    current: list[_Char] = []
    current_w = 0

    def end_row() -> None:
        nonlocal current, current_w
        rows.append(_rstrip_spaces(current))
        current = []
        current_w = 0

    for token in _tokenize(chars):
        token_w = sum(c[2] for c in token)
        is_space = token[0][0] == ' '

        if is_space:
            if current_w + token_w > width:
                # Whitespace at the wrap point is dropped.
                end_row()
            else:
                current.extend(token)
                current_w += token_w
            continue

        if current_w + token_w <= width:
            current.extend(token)
            current_w += token_w
        elif token_w <= width:
            end_row()
            current.extend(token)
            current_w = token_w
        else:
            # A word wider than the whole line: hard-break it.
            for c in token:
                if current_w + c[2] > width and current_w > 0:
                    end_row()
                current.append(c)
                current_w += c[2]

    if current or not rows:
        end_row()
    return [_chars_to_segments(row) for row in rows]
