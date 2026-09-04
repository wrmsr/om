"""Horizontal rules."""
from .... import check
from ..styles import StyleLike
from ..text import StyledText
from ..text import StyledTextLike
from .fitting import truncate
from .measuring import cell_width


##


def rule(
        width: int,
        *,
        character: str = '─',
        style: StyleLike | None = None,
        title: StyledTextLike | None = None,
) -> StyledText:
    """A rule of exactly `width` cells, optionally with a centered title set off by single spaces."""

    check.arg(isinstance(character, str) and len(character) == 1 and cell_width(character) == 1)
    if width <= 0:
        return StyledText()

    if title is None:
        return StyledText.assemble((character * width, style))

    value = truncate(title, max(width - 2, 0))
    remaining = max(width - cell_width(value) - 2, 0)
    left = remaining // 2
    return StyledText.assemble(
        (character * left, style),
        (' ', style),
        value,
        (' ', style),
        (character * (remaining - left), style),
    )
