"""
The live markdown tail: the unsettled remainder of a streaming markdown backend, re-rendered each frame.

The commit-model pairing is the whole point: the app feeds the stream, commits whatever `pop_settled()` returns
(rendered at the current width), and stacks this control to show the rest. Backends are swappable via
`get_markdown_stream`: omcore's pdcmark (pulldown-cmark translated - the default; omcore is always present), the even
tinier zero-dep internal line parser, or markdown-it - all producing the same MdBlock model.
"""
import typing as ta

from ..text.highlights.base import highlight_code
from ..text.markdown.backends import get_markdown_stream
from ..text.markdown.base import MarkdownCodeHighlighter
from ..text.markdown.base import MarkdownStreamBackend
from ..text.markdown.base import MdBlock
from ..text.markdown.base import render_markdown_blocks
from ..text.segments import Segment
from .base import Control


##


class MarkdownTail(Control):
    def __init__(
            self,
            *,
            backend: MarkdownStreamBackend | None = None,
            highlighter: MarkdownCodeHighlighter | None = highlight_code,
    ) -> None:
        super().__init__()

        self._stream = backend if backend is not None else get_markdown_stream()
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
        """
        End of the current stream: drain everything remaining for the final commit. The tail is reusable - the next
        `feed` starts a fresh stream cycle (backends reset on finalize per their contract).
        """

        return self._stream.finalize()

    def render_settled(self, blocks: ta.Sequence[MdBlock], width: int) -> list[list[Segment]]:
        return render_markdown_blocks(blocks, width, highlighter=self._highlighter)

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        return render_markdown_blocks(self._stream.tail_blocks(), width, highlighter=self._highlighter)
