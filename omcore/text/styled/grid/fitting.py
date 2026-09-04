"""Truncation, padding, and alignment to exact cell widths."""
import typing as ta

from .... import check
from ..styles import StyleLike
from ..text import StyledText
from ..text import StyledTextLike
from .measuring import cell_width
from .measuring import fit_offset


type Alignment = ta.Literal['left', 'center', 'right']


##


def _check_fill(fill: str) -> None:
    check.arg(isinstance(fill, str) and len(fill) == 1 and cell_width(fill) == 1)


def truncate(text: StyledTextLike, width: int, *, ellipsis: str = '') -> StyledText:
    """
    Clip to at most `width` cells, never splitting a wide character. An ellipsis, when given and it fits, replaces the
    clipped tail and carries no style of its own.
    """

    value = StyledText.of(text)
    if width <= 0:
        return StyledText()
    if cell_width(value) <= width:
        return value

    ellipsis_width = cell_width(ellipsis)
    if ellipsis and ellipsis_width < width:
        return value.slice(0, fit_offset(value.text, width - ellipsis_width)) + ellipsis
    return value.slice(0, fit_offset(value.text, width))


def pad_left(
        text: StyledTextLike,
        count: int,
        *,
        fill: str = ' ',
        style: StyleLike | None = None,
) -> StyledText:
    """Prepend `count` fill characters, styled beneath if a style is given."""

    _check_fill(fill)
    value = StyledText.of(text)
    if count <= 0:
        return value
    return StyledText.assemble((fill * count, style), value)


def pad_right(
        text: StyledTextLike,
        count: int,
        *,
        fill: str = ' ',
        style: StyleLike | None = None,
) -> StyledText:
    """Append `count` fill characters, styled beneath if a style is given."""

    _check_fill(fill)
    value = StyledText.of(text)
    if count <= 0:
        return value
    return StyledText.assemble(value, (fill * count, style))


def fit(
        text: StyledTextLike,
        width: int,
        *,
        align: Alignment = 'left',
        fill: str = ' ',
        style: StyleLike | None = None,
        ellipsis: str = '',
) -> StyledText:
    """Truncate or pad to exactly `width` cells. A style applies beneath the whole result, padding included."""

    _check_fill(fill)
    value = truncate(text, width, ellipsis=ellipsis)
    remaining = max(width - cell_width(value), 0)

    if align == 'left':
        left, right = 0, remaining
    elif align == 'right':
        left, right = remaining, 0
    elif align == 'center':
        left = remaining // 2
        right = remaining - left
    else:
        raise ValueError(align)

    return StyledText.assemble((StyledText.of(fill * left, value, fill * right), style))
