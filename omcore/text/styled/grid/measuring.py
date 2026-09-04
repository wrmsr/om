"""Cell measurement of styled text."""
from ...widths import char_width
from ...widths import str_width
from ..text import StyledText
from ..text import StyledTextLike


##


def cell_width(text: StyledTextLike) -> int:
    """The display width in terminal cells."""

    return str_width(text if isinstance(text, str) else StyledText.of(text).text)


def fit_offset(text: str, width: int) -> int:
    """The largest code point offset whose prefix fits in `width` cells."""

    current = 0
    for offset, char in enumerate(text):
        current += char_width(char)
        if current > width:
            return offset
    return len(text)
