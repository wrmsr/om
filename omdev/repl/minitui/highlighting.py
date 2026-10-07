"""
Input-box syntax highlighting for a language: tree-sitter when installed (incremental), the zero-dep or pygments
highlighters otherwise - minitui's own resolution order - wrapped to re-emit their `code.*` tags under the repl's
untinted `repl.code.*` (see `styles.py`). Fresh instances per call: tree-sitter highlighters carry incremental state.
"""
import typing as ta

from omcore.text import styled as st
from omcore.text.highlights import HighlightedLines
from omcore.text.highlights import Highlighter
from omcore.text.highlights import get_highlighter

from ...minitui.docs.edits import TextEdit
from ...minitui.docs.highlighting import IncrementalHighlighter
from ...minitui.docs.treesitter import get_tree_sitter_highlighter
from ..languages import Language
from .styles import CODE_TAG_PREFIX


##


class RetaggedHighlighter(IncrementalHighlighter):
    """Prefixes every style name the wrapped highlighter emits. Edits pass through when the inner one is incremental."""

    def __init__(self, inner: Highlighter, prefix: str) -> None:
        super().__init__()

        self._inner = inner
        self._prefix = prefix

    @property
    def inner(self) -> Highlighter:
        return self._inner

    def note_edit(self, edit: TextEdit) -> None:
        if isinstance(self._inner, IncrementalHighlighter):
            self._inner.note_edit(edit)

    def highlight(self, lines: ta.Sequence[str]) -> HighlightedLines:
        out: list[st.StyledText] = []
        for line in self._inner.highlight(lines):
            spans = tuple(
                st.StyleSpan(span.start, span.end, st.StyleName(self._prefix + span.style.name))
                if isinstance(span.style, st.StyleName) else span
                for span in line.spans
            )
            out.append(st.StyledText(line.text, spans))
        return out


def get_language_highlighter(language: Language) -> Highlighter | None:
    name = language.highlight_name
    inner = get_tree_sitter_highlighter(name) or get_highlighter(name)
    if inner is None:
        return None
    return RetaggedHighlighter(inner, CODE_TAG_PREFIX)
