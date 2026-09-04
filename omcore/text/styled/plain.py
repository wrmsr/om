"""Plain-text rendering."""
from .documents import StyledContent
from .documents import StyledDocument
from .text import StyledText


##


def render_plain(text: StyledContent) -> str:
    if isinstance(text, StyledDocument):
        return text.plain
    return StyledText.of(text).plain
