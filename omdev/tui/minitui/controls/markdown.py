"""
The live markdown tail: the unsettled remainder of a streaming markdown backend, re-rendered each frame.

The commit-model pairing is the whole point: the app feeds the stream, commits whatever `pop_settled()` returns
(rendered at the current width), and stacks this control to show the rest. Backends are swappable via
`get_markdown_stream`: omcore's pdcmark (pulldown-cmark translated - the default; omcore is always present), the even
tinier zero-dep internal line parser, or markdown-it - all producing the same MdBlock model.

Blocks separate with one blank row - what `render_markdown_blocks` puts between the blocks of a single call. A stream
settles its blocks one call at a time though, so the separator across calls is this control's job: within a stream cycle
every commit after the first leads with the blank row, and so does the live tail while committed blocks precede it.
"""
import typing as ta

from omcore.text.highlights import highlight_code

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

        # Separator state for the current stream cycle: whether `render_settled` has produced rows in it yet. A cycle
        # opens with the first `feed` after construction or `finalize`, and its state outlives `finalize` by one call -
        # the caller renders finalize's blocks through `render_settled` next.
        self._cycle_open = False
        self._settled_rendered = False

    @property
    def is_empty(self) -> bool:
        return not self._stream.tail_blocks()

    def feed(self, chunk: str) -> None:
        if not self._cycle_open:
            self._cycle_open = True
            self._settled_rendered = False
        self._stream.feed(chunk)

    def pop_settled(self) -> list[MdBlock]:
        """Blocks that will never change again - render and commit them; they leave this control's tail."""

        return self._stream.pop_settled()

    def finalize(self) -> list[MdBlock]:
        """
        End of the current stream: drain everything remaining for the final commit. The tail is reusable - the next
        `feed` starts a fresh stream cycle (backends reset on finalize per their contract).
        """

        self._cycle_open = False
        return self._stream.finalize()

    def render_settled(self, blocks: ta.Sequence[MdBlock], width: int) -> list[list[Segment]]:
        """
        Rows to commit for blocks that left the tail (`pop_settled` / `finalize` output). Non-empty renders after the
        first of a stream cycle lead with the blank row separating them from the blocks committed before them.
        """

        rows = render_markdown_blocks(blocks, width, highlighter=self._highlighter)
        if rows:
            if self._settled_rendered:
                rows.insert(0, [])
            self._settled_rendered = True
        return rows

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        rows = render_markdown_blocks(self._stream.tail_blocks(), width, highlighter=self._highlighter)
        if rows and self._settled_rendered:
            rows.insert(0, [])
        return rows
