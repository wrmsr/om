"""
Oneshot `parse(text)` entry point.

Thin shim over `BlockMachine`: splits input into lines, feeds each, and finishes. Streaming consumers use
`pdcmark.streaming.StreamingParser` instead.

Honors `options.prescan_refdefs`: when True, runs a discarded first pass solely to populate the refdef table so that
links can resolve against refdefs defined later in the document. The first pass discards events; the second pass starts
with the refdefs pre-populated and emits events normally. Cf. pulldown-cmark's two-pass design, which collects refdefs
into the tree before the inline pass runs.
"""
import typing as ta

from .blocks.machine import BlockMachine
from .blocks.refdefs import RefDefs
from .events import Event
from .options import COMMONMARK
from .options import Options


##


def parse(text: str, options: Options = COMMONMARK) -> list[Event]:
    """
    Parse `text` and return a materialized list of `Event`s.

    For incremental / chunked input, use `pdcmark.StreamingParser` instead. With `options.prescan_refdefs=True`, a
    discarded first pass populates the refdef table so forward-referencing links resolve; default is False (matching
    streaming behavior).
    """

    refdefs: RefDefs | None = None
    if options.prescan_refdefs:
        refdefs = _prescan(text, options)
    bm = BlockMachine(options, refdefs=refdefs)
    events: list[Event] = []
    for line_body, line_start, line_next in _iter_lines(text):
        events.extend(bm.feed_line(line_body, line_start, line_next))
    events.extend(bm.finish(len(text)))
    return events


def _prescan(text: str, options: Options) -> RefDefs:
    """Run the BlockMachine to completion, discard the events, return the refdef table."""

    bm = BlockMachine(options)
    for line_body, line_start, line_next in _iter_lines(text):
        bm.feed_line(line_body, line_start, line_next)
    bm.finish(len(text))
    return bm.refdefs


def _iter_lines(text: str) -> ta.Iterator[tuple[str, int, int]]:
    n = len(text)
    pos = 0

    if '\r' not in text:
        # Fast path (the overwhelmingly common case): LF-only line endings, scanned with C-level find.
        while pos < n:
            lf = text.find('\n', pos)
            if lf < 0:
                yield text[pos:], pos, n
                return
            yield text[pos:lf], pos, lf + 1
            pos = lf + 1
        return

    while pos < n:
        lf = text.find('\n', pos)
        cr = text.find('\r', pos)
        if lf < 0 and cr < 0:
            yield text[pos:], pos, n
            return
        if cr >= 0 and (lf < 0 or cr < lf):
            nl_pos = cr
            nl_len = 2 if cr + 1 < n and text[cr + 1] == '\n' else 1
        else:
            nl_pos = lf
            nl_len = 1
        next_off = nl_pos + nl_len
        yield text[pos:nl_pos], pos, next_off
        pos = next_off
