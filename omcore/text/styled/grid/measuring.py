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


def fit_tail_offset(text: str, width: int) -> int:
    """
    The smallest code point offset whose suffix fits in `width` cells, never starting on a zero-width character whose
    base was cut off.
    """

    current = 0
    for offset in range(len(text) - 1, -1, -1):
        current += char_width(text[offset])
        if current > width:
            offset += 1
            while offset < len(text) and not char_width(text[offset]):
                offset += 1
            return offset
    return 0
