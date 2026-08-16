"""
Document search producing charwise spans.

Literal matching with vim-flavored smartcase (all-lowercase queries match case-insensitively; any uppercase makes the
query exact). Recomputation is full-document - documents at input-textarea scale make that free; incremental
maintenance through change events is a later optimization behind the same interface.
"""
import typing as ta

from .documents import Document
from .positions import Kind
from .positions import Pos
from .positions import Span


##


def find_matches(
        document: Document,
        query: str,
        *,
        no_smartcase: bool = False,
) -> list[Span]:
    """All non-overlapping matches of `query`, in document order. Queries never match across newlines."""

    if not query or '\n' in query:
        return []

    fold = not no_smartcase and query == query.lower()
    needle = query.lower() if fold else query

    matches: list[Span] = []
    for row in range(document.line_count()):
        line = document.line(row)
        haystack = line.lower() if fold else line
        start = 0
        while (i := haystack.find(needle, start)) >= 0:
            matches.append(Span(Kind.EXCLUSIVE, Pos(row, i), Pos(row, i + len(query))))
            start = i + len(query)
    return matches


def next_match(
        matches: ta.Sequence[Span],
        pos: Pos,
        *,
        reverse: bool = False,
        include_at: bool = False,
) -> Span | None:
    """The first match after (before, if `reverse`) `pos`, wrapping around. None if there are no matches."""

    if not matches:
        return None
    if reverse:
        for span in reversed(matches):
            if span.start < pos:
                return span
        return matches[-1]
    for span in matches:
        if span.start > pos or (include_at and span.start == pos):
            return span
    return matches[0]
