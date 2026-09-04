"""
Syntax highlighting: source lines in, styled lines out.

The protocol is deliberately small and text-shaped. Incremental variants (an editor feeding document edits) extend it
rather than replace it, and a full-retokenize implementation of the same protocol is always the zero-dependency
fallback. Highlighters emit the shared semantic `code.*` style names and never choose colors - themes do.

Included zero-dep highlighters: python (stdlib tokenize, error-tolerant - malformed source falls back to plain) and
unified diffs. pygments is the optional, quarantined implementation covering the long-tail catalog.
"""
import abc
import builtins
import io
import keyword
import tokenize
import typing as ta

from ... import lang
from .. import styled as st


if ta.TYPE_CHECKING:
    from . import pygments
else:
    pygments = lang.proxy_import('.pygments', __package__)


type HighlightedLines = ta.Sequence[st.StyledText]


##


class Highlighter(lang.Abstract):
    @abc.abstractmethod
    def highlight(self, lines: ta.Sequence[str]) -> HighlightedLines:
        """One styled line per input line, with identical text; unhighlighted text carries no spans."""

        raise NotImplementedError


##


class _SpanSink:
    """Accumulates (start_col, end_col, tag) spans per line and assembles styled lines."""

    def __init__(self, lines: ta.Sequence[str]) -> None:
        super().__init__()

        self._lines = lines
        self._spans: list[list[tuple[int, int, str]]] = [[] for _ in lines]

    def add(self, row: int, start: int, end: int, tag: str) -> None:
        if 0 <= row < len(self._spans) and end > start:
            self._spans[row].append((start, end, tag))

    def add_multiline(self, start: tuple[int, int], end: tuple[int, int], tag: str) -> None:
        (srow, scol), (erow, ecol) = start, end
        if srow == erow:
            self.add(srow, scol, ecol, tag)
            return
        self.add(srow, scol, len(self._lines[srow]) if srow < len(self._lines) else scol, tag)
        for row in range(srow + 1, erow):
            if row < len(self._lines):
                self.add(row, 0, len(self._lines[row]), tag)
        self.add(erow, 0, ecol, tag)

    def lines(self) -> list[st.StyledText]:
        out: list[st.StyledText] = []
        for line, spans in zip(self._lines, self._spans):
            spans.sort()
            styled: list[st.StyleSpan] = []
            pos = 0
            for start, end, tag in spans:
                start = max(start, pos)
                if start >= end:
                    continue
                styled.append(st.StyleSpan.of(start, end, tag))
                pos = end
            out.append(st.StyledText(line, tuple(styled)))
        return out


##


_BUILTIN_NAMES: ta.AbstractSet[str] = frozenset(dir(builtins))

_STRING_TOKEN_TYPES: ta.AbstractSet[int] = frozenset([
    tokenize.STRING,
    tokenize.FSTRING_START,
    tokenize.FSTRING_MIDDLE,
    tokenize.FSTRING_END,
])


class PythonHighlighter(Highlighter):
    """stdlib-tokenize based. Streams and broken snippets are the norm: any tokenize error falls back to plain."""

    def highlight(self, lines: ta.Sequence[str]) -> HighlightedLines:
        # NB: no tab expansion - output columns must stay source-true (editors map them back to document positions).
        # Display-layer tab handling is the grid lowering's job.
        sink = _SpanSink(lines)
        source = '\n'.join(lines) + '\n'

        prev_was_def = False
        try:
            for tok in tokenize.generate_tokens(io.StringIO(source).readline):
                # tokenize rows are 1-based.
                start = (tok.start[0] - 1, tok.start[1])
                end = (tok.end[0] - 1, tok.end[1])

                tag: str | None = None

                if tok.type == tokenize.COMMENT:
                    tag = 'code.comment'

                elif tok.type in _STRING_TOKEN_TYPES:
                    tag = 'code.string'

                elif tok.type == tokenize.NUMBER:
                    tag = 'code.number'

                elif tok.type == tokenize.NAME:
                    if keyword.iskeyword(tok.string) or keyword.issoftkeyword(tok.string):
                        tag = 'code.keyword'

                    elif prev_was_def:
                        tag = 'code.def'

                    elif tok.string in _BUILTIN_NAMES:
                        tag = 'code.builtin'

                elif tok.type == tokenize.OP and tok.string == '@':
                    tag = 'code.decorator'

                prev_was_def = tok.type == tokenize.NAME and tok.string in ('def', 'class')

                if tag is not None:
                    sink.add_multiline(start, end, tag)

        except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
            return [st.StyledText(line) for line in lines]

        return sink.lines()


class DiffHighlighter(Highlighter):
    def highlight(self, lines: ta.Sequence[str]) -> HighlightedLines:
        out: list[st.StyledText] = []
        for line in lines:
            tag: str | None = None

            if line.startswith(('+++', '---', 'diff ', 'index ')):
                tag = 'code.diff.meta'

            elif line.startswith('@@'):
                tag = 'code.diff.hunk'

            elif line.startswith('+'):
                tag = 'code.diff.add'

            elif line.startswith('-'):
                tag = 'code.diff.del'

            value = st.StyledText(line)
            out.append(value.styled(tag) if tag is not None else value)

        return out


##


_HIGHLIGHTER_ALIASES: ta.Mapping[str, str] = {
    'python': 'python',
    'python3': 'python',
    'py': 'python',
    'diff': 'diff',
    'patch': 'diff',
    'udiff': 'diff',
}


def _make_highlighters() -> ta.Mapping[str, Highlighter]:
    return {
        'python': PythonHighlighter(),
        'diff': DiffHighlighter(),
    }


_HIGHLIGHTERS: ta.Mapping[str, Highlighter] = _make_highlighters()


def get_highlighter(info: str) -> Highlighter | None:
    """Internal zero-dep highlighters take precedence; pygments (optional) covers the long-tail catalog."""

    if (name := _HIGHLIGHTER_ALIASES.get(info.strip().lower())) is not None:
        return _HIGHLIGHTERS[name]
    return pygments.get_pygments_highlighter(info)


def highlight_code(info: str, lines: ta.Sequence[str]) -> HighlightedLines | None:
    """The code-block adapter: None when no highlighter covers `info`."""

    if (highlighter := get_highlighter(info)) is None:
        return None
    return highlighter.highlight(lines)
