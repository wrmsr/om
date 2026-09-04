"""
Syntax highlighting: code lines in, styled segment rows out.

The protocol is deliberately small and text-shaped for now; the incremental path (tree-sitter consuming Document change
events, which are already shaped like its `edit()` API) will extend it rather than replace it - a full-retokenize
implementation of the same protocol is always the zero-dependency fallback.

Included zero-dep highlighters: python (stdlib tokenize, error-tolerant - malformed source falls back to plain) and
unified diffs. pygments slots in later as an optional quarantined implementation covering the long-tail catalog.
"""
import abc
import builtins
import io
import keyword
import tokenize
import typing as ta

from omcore import lang

from ..segments import Segment
from ..segments import SegmentRows


if ta.TYPE_CHECKING:
    from . import pygments
else:
    pygments = lang.proxy_import('.pygments', __package__)


##


class Highlighter(lang.Abstract):
    @abc.abstractmethod
    def highlight(self, lines: ta.Sequence[str]) -> SegmentRows:
        """One output row per input line; untagged (plain) text uses style None."""

        raise NotImplementedError


##


class _SpanSink:
    """Accumulates (start_col, end_col, tag) spans per row and assembles segment rows."""

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

    def rows(self) -> list[list[Segment]]:
        out: list[list[Segment]] = []
        for line, spans in zip(self._lines, self._spans):
            spans.sort()
            segments: list[Segment] = []
            pos = 0
            for start, end, tag in spans:
                start = max(start, pos)
                if start >= end:
                    continue
                if start > pos:
                    segments.append(Segment(line[pos: start]))
                segments.append(Segment(line[start: end], tag))
                pos = end
            if pos < len(line):
                segments.append(Segment(line[pos:]))
            out.append(segments)
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

    def highlight(self, lines: ta.Sequence[str]) -> SegmentRows:
        # NB: no tab expansion - output columns must stay source-true (editors map them back to document positions).
        # Display-layer tab handling is the renderer's job.
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
            return [[Segment(line)] if line else [] for line in lines]

        return sink.rows()


class DiffHighlighter(Highlighter):
    def highlight(self, lines: ta.Sequence[str]) -> SegmentRows:
        rows: list[list[Segment]] = []
        for line in lines:
            if not line:
                rows.append([])
                continue

            tag: str | None = None

            if line.startswith(('+++', '---', 'diff ', 'index ')):
                tag = 'code.diff.meta'

            elif line.startswith('@@'):
                tag = 'code.diff.hunk'

            elif line.startswith('+'):
                tag = 'code.diff.add'

            elif line.startswith('-'):
                tag = 'code.diff.del'

            rows.append([Segment(line, tag)])

        return rows


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


def highlight_code(info: str, lines: ta.Sequence[str]) -> SegmentRows | None:
    """The markdowns.CodeHighlighter adapter: None when no highlighter covers `info`."""

    if (highlighter := get_highlighter(info)) is None:
        return None
    return highlighter.highlight(lines)
