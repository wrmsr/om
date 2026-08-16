"""
The live markdown tail: the unsettled remainder of a streaming markdown backend, re-rendered each frame.

The commit-model pairing is the whole point: the app feeds the stream, commits whatever `pop_settled()` returns
(rendered at the current width), and stacks this control to show the rest. Backends are swappable via
`get_markdown_stream`: the zero-dep internal parser (default), omcore's pdcmark (pulldown-cmark translated), or
markdown-it - all producing the same MdBlock model.
"""
import typing as ta

from omcore import lang

from ..text.highlights import highlight_code
from ..text.markdowns import CodeHighlighter
from ..text.markdowns import MarkdownStream
from ..text.markdowns import MarkdownStreamBackend
from ..text.markdowns import MdBlock
from ..text.markdowns import render_blocks
from ..text.segments import Segment
from .bases import Control


if ta.TYPE_CHECKING:
    from ..text import markdownits
    from ..text import pdcmarks
else:
    markdownits = lang.proxy_import('..text.markdownits', __package__)
    pdcmarks = lang.proxy_import('..text.pdcmarks', __package__)


##


MARKDOWN_BACKEND_NAMES: ta.Sequence[str] = ('internal', 'pdcmark', 'markdown-it')

_MARKDOWN_BACKEND_ALIASES: ta.Mapping[str, str] = {
    'internal': 'internal',
    'pdcmark': 'pdcmark',
    'markdown-it': 'markdown-it',
    'markdownit': 'markdown-it',
    'mdit': 'markdown-it',
}


def get_markdown_stream(name: str | None = None) -> MarkdownStreamBackend:
    """
    A fresh streaming backend by name: 'internal' (zero-dep, the default), 'pdcmark' (omcore's pulldown-cmark
    translation), or 'markdown-it' (external, optional). Raises LookupError for unknown or unavailable backends.
    """

    if (resolved := _MARKDOWN_BACKEND_ALIASES.get((name or 'internal').strip().lower())) is None:
        raise LookupError(f'unknown markdown backend: {name!r}')
    if resolved == 'internal':
        return MarkdownStream()
    if resolved == 'pdcmark':
        return pdcmarks.PdcmarkStream()
    if not markdownits.markdown_it_available():
        raise LookupError('markdown-it backend requested but markdown_it is not installed')
    return markdownits.MarkdownItStream()


class MarkdownTail(Control):
    def __init__(
            self,
            *,
            backend: MarkdownStreamBackend | None = None,
            highlighter: CodeHighlighter | None = highlight_code,
    ) -> None:
        super().__init__()

        self._stream = backend if backend is not None else MarkdownStream()
        self._highlighter = highlighter

    @property
    def is_empty(self) -> bool:
        return not self._stream.tail_blocks()

    def feed(self, chunk: str) -> None:
        self._stream.feed(chunk)

    def pop_settled(self) -> list[MdBlock]:
        """Blocks that will never change again - render and commit them; they leave this control's tail."""

        return self._stream.pop_settled()

    def finalize(self) -> list[MdBlock]:
        """End of stream: drain everything remaining for the final commit."""

        return self._stream.finalize()

    def render_settled(self, blocks: ta.Sequence[MdBlock], width: int) -> list[list[Segment]]:
        return render_blocks(blocks, width, highlighter=self._highlighter)

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        return render_blocks(self._stream.tail_blocks(), width, highlighter=self._highlighter)
