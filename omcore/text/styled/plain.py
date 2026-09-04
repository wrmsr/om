"""Plain-text rendering."""
from .text import StyledText
from .text import StyledTextLike


##


def render_plain(text: StyledTextLike) -> str:
    return StyledText.of(text).plain
