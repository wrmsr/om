"""
The optional pygments highlighter - the long-tail language catalog behind the same Highlighter protocol.

Strictly quarantined per the dependency policy: pygments is proxy-imported, availability is probed without importing,
and everything degrades to None (caller falls back to plain rendering) when it's absent or doesn't know the language.
The internal zero-dep highlighters (python, diff) take precedence in `text.highlights`; this covers everything else.
"""
import functools
import importlib.util
import typing as ta

from omcore import lang

from .highlights import Highlighter
from .highlights import SegmentRows
from .segments import Segment


with lang.auto_proxy_import(globals()):
    import pygments.lexers
    import pygments.token
    import pygments.util


##


@functools.cache
def pygments_available() -> bool:
    return importlib.util.find_spec('pygments') is not None


@functools.cache
def _tag_mapping() -> ta.Sequence[tuple[ta.Any, str]]:
    token = pygments.token
    # Most-specific first; matched via pygments' token-subsumption `in`.
    return (
        (token.Name.Decorator, 'code.decorator'),
        (token.Name.Function, 'code.def'),
        (token.Name.Class, 'code.def'),
        (token.Name.Builtin, 'code.builtin'),
        (token.Keyword, 'code.keyword'),
        (token.String, 'code.string'),
        (token.Comment, 'code.comment'),
        (token.Number, 'code.number'),
    )


def _tag_for(token_type: ta.Any) -> str | None:
    for parent, tag in _tag_mapping():
        if token_type in parent:
            return tag
    return None


class PygmentsHighlighter(Highlighter):
    def __init__(self, lexer: ta.Any) -> None:
        super().__init__()

        self._lexer = lexer

    def highlight(self, lines: ta.Sequence[str]) -> SegmentRows:
        source = '\n'.join(lines)
        rows: list[list[Segment]] = [[]]
        for token_type, value in self._lexer.get_tokens(source):
            tag = _tag_for(token_type)
            first = True
            for part in value.split('\n'):
                if not first:
                    rows.append([])
                first = False
                if part:
                    rows[-1].append(Segment(part, tag))
        # get_tokens appends a trailing newline's worth of row; trim to the input's line count.
        return rows[: len(lines)] if len(rows) > len(lines) else rows


def get_pygments_highlighter(info: str) -> Highlighter | None:
    """A Highlighter for the language `info`, or None (pygments missing, or unknown language)."""

    if not info or not pygments_available():
        return None
    try:
        lexer = pygments.lexers.get_lexer_by_name(info.strip().lower(), stripnl=False)
    except pygments.util.ClassNotFound:
        return None
    return PygmentsHighlighter(lexer)
