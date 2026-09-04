"""Tab expansion and indentation guides."""
from .... import check
from ...widths import char_width
from ..styles import StyleLike
from ..text import StyledText
from ..text import StyledTextLike
from ..text import StyleSpan
from .measuring import cell_width


##


def expand_tabs(text: StyledTextLike, tab_size: int = 8) -> StyledText:
    """Replace tabs with spaces to the next tab stop, measured in cells; the spaces carry the tab's styles."""

    check.arg(tab_size >= 1)

    value = StyledText.of(text)
    if '\t' not in value.text:
        return value

    out: list[str] = []
    offsets = [0] * (len(value.text) + 1)
    column = 0
    length = 0
    for index, char in enumerate(value.text):
        offsets[index] = length
        if char == '\t':
            spaces = tab_size - (column % tab_size)
            out.append(' ' * spaces)
            column += spaces
            length += spaces
        else:
            out.append(char)
            column = 0 if char == '\n' else column + char_width(char)
            length += 1
    offsets[len(value.text)] = length

    spans = tuple(
        StyleSpan(offsets[span.start], offsets[span.end], span.style)
        for span in value.spans
        if offsets[span.end] > offsets[span.start]
    )
    return StyledText(''.join(out), spans)


def indent_guides(
        text: StyledTextLike,
        tab_size: int,
        *,
        style: StyleLike,
        character: str = '│',
) -> StyledText:
    """Mark each tab stop within the leading spaces with a guide character carrying `style`."""

    check.arg(tab_size >= 1)
    check.arg(isinstance(character, str) and len(character) == 1 and cell_width(character) == 1)

    value = StyledText.of(text)
    leading = len(value.text) - len(value.text.lstrip(' '))
    if leading < tab_size:
        return value

    chars = list(value.text)
    for position in range(0, leading, tab_size):
        chars[position] = character

    guided = StyledText(''.join(chars), value.spans)
    for position in range(0, leading, tab_size):
        guided = guided.styled(style, position, position + 1)
    return guided
