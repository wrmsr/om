"""
The pdcmark streaming backend: omcore's pure-python pulldown-cmark translation driving the shared MdBlock model.

pdcmark's `StreamingParser` contract is exactly this layer's contract - committed events are append-only, the tentative
tail replaces itself, and any chunking of input commits the same stream a oneshot parse would - so the adapter here is
pure event->block conversion. Committed events buffer until a complete top-level group closes (a block's Start..End, or
a standalone event), since block conversion needs whole groups.

Flattenings (the render model is deliberately simpler than commonmark): nested quote/item content joins into the
parent's inline spans, with non-paragraph children (code blocks in quotes, etc.) emitted as sibling blocks; nested lists
merge into their parent list with increased item depth; tables render as pipe-joined rows. Hard breaks soften to
spaces (blocks re-wrap).
"""
import typing as ta

from omcore import dataclasses as dc
from omcore.text import pdcmark

from .markdown import MarkdownStreamBackend
from .markdown import MdBlock
from .markdown import MdCode
from .markdown import MdHeading
from .markdown import MdList
from .markdown import MdListItem
from .markdown import MdParagraph
from .markdown import MdQuote
from .markdown import MdRule
from .segments import Segment


##


_INLINE_TAG_STYLES: ta.Sequence[tuple[type, str]] = (
    (pdcmark.Strong, 'md.bold'),
    (pdcmark.Emphasis, 'md.italic'),
    (pdcmark.Strikethrough, 'md.strike'),
    (pdcmark.Link, 'md.link'),
    (pdcmark.Image, 'md.link'),
)


def _inline_style(tag: ta.Any) -> str | None:
    for tag_type, style in _INLINE_TAG_STYLES:
        if isinstance(tag, tag_type):
            return style
    return None


def _join_spans(groups: ta.Sequence[ta.Sequence[Segment]]) -> tuple[Segment, ...]:
    out: list[Segment] = []
    for group in groups:
        if not group:
            continue
        if out:
            out.append(Segment(' '))
        out.extend(group)
    return tuple(out)


class _EventWalker:
    """Index-walks a complete event group list, converting to MdBlocks."""

    def __init__(self, events: ta.Sequence[pdcmark.Event]) -> None:
        super().__init__()

        self._events = list(events)
        self._i = 0

    def _next(self) -> pdcmark.Event | None:
        if self._i >= len(self._events):
            return None
        e = self._events[self._i]
        self._i += 1
        return e

    ##

    def _inline_spans(self, end_tag: ta.Any) -> tuple[Segment, ...]:
        """Collect inline content until the End event carrying `end_tag`'s type at our depth."""

        spans: list[Segment] = []
        stack: list[str | None] = []
        while (e := self._next()) is not None:
            if isinstance(e, pdcmark.End) and type(e.tag) is type(end_tag) and not stack:
                break
            if isinstance(e, pdcmark.Start):
                stack.append(_inline_style(e.tag))
            elif isinstance(e, pdcmark.End):
                style = stack.pop() if stack else None
                if style == 'md.link' and isinstance(e.tag, (pdcmark.Link, pdcmark.Image)) and e.tag.dest_url:
                    spans.append(Segment(f' ({e.tag.dest_url})', 'md.link.url'))
            elif isinstance(e, pdcmark.Text):
                if e.text:
                    spans.append(Segment(e.text.replace('\n', ' '), next(
                        (s for s in reversed(stack) if s is not None), None)))
            elif isinstance(e, pdcmark.Code):
                spans.append(Segment(e.text, 'md.code.inline'))
            elif isinstance(e, (pdcmark.SoftBreak, pdcmark.HardBreak)):
                spans.append(Segment(' '))
            elif isinstance(e, pdcmark.InlineHtml):
                if e.text:
                    spans.append(Segment(e.text.replace('\n', ' ')))
            elif isinstance(e, pdcmark.TaskListMarker):
                spans.append(Segment('[x] ' if e.checked else '[ ] ', 'md.list.marker'))
        return tuple(spans)

    def _code_lines(self, end_tag: ta.Any) -> tuple[str, ...]:
        text = ''
        while (e := self._next()) is not None:
            if isinstance(e, pdcmark.End) and type(e.tag) is type(end_tag):
                break
            if isinstance(e, (pdcmark.Text, pdcmark.Html)):
                text += e.text
        return tuple(text.rstrip('\n').split('\n')) if text else ()

    def _children_until(self, end_tag: ta.Any) -> list[MdBlock]:
        blocks: list[MdBlock] = []
        while (e := self._next()) is not None:
            if isinstance(e, pdcmark.End) and type(e.tag) is type(end_tag):
                break
            if (block_list := self._convert_one(e)) is not None:
                blocks.extend(block_list)
        return blocks

    def _list_items(self, list_tag: pdcmark.List) -> list[MdListItem]:
        items: list[MdListItem] = []
        index = list_tag.start if list_tag.start is not None else None
        while (e := self._next()) is not None:
            if isinstance(e, pdcmark.End) and isinstance(e.tag, pdcmark.List):
                break
            if isinstance(e, pdcmark.Start) and isinstance(e.tag, pdcmark.Item):
                children = self._children_until(e.tag)
                spans_groups: list[ta.Sequence[Segment]] = []
                nested: list[MdListItem] = []
                for child in children:
                    if isinstance(child, MdParagraph):
                        spans_groups.append(child.spans)
                    elif isinstance(child, MdList):
                        # Nested lists merge into the parent, one level deeper.
                        nested.extend(dc.replace(it, depth=it.depth + 1) for it in child.items)
                    elif isinstance(child, (MdHeading, MdQuote)):
                        spans_groups.append(child.spans)
                marker = f'{index}.' if index is not None else '-'
                if index is not None:
                    index += 1
                items.append(MdListItem(marker, _join_spans(spans_groups)))
                items.extend(nested)
        return items

    def _table_rows(self, table_tag: pdcmark.Table) -> list[MdBlock]:
        rows: list[MdBlock] = []
        cells: list[tuple[Segment, ...]] = []
        while (e := self._next()) is not None:
            if isinstance(e, pdcmark.End) and isinstance(e.tag, pdcmark.Table):
                break
            if isinstance(e, pdcmark.Start) and isinstance(e.tag, pdcmark.TableCell):
                cells.append(self._inline_spans(e.tag))
            elif isinstance(e, pdcmark.End) and isinstance(e.tag, (pdcmark.TableRow, pdcmark.TableHead)):
                spans: list[Segment] = []
                for ci, cell in enumerate(cells):
                    if ci:
                        spans.append(Segment(' | ', 'md.rule'))
                    spans.extend(cell)
                rows.append(MdParagraph(tuple(spans)))
                cells = []
        return rows

    ##

    def _convert_one(self, e: pdcmark.Event) -> list[MdBlock] | None:  # noqa: C901
        if isinstance(e, pdcmark.Rule):
            return [MdRule()]

        if isinstance(e, pdcmark.Html):
            return [MdCode('html', tuple(e.text.rstrip('\n').split('\n')))] if e.text.strip() else []

        if not isinstance(e, pdcmark.Start):
            return None

        tag = e.tag
        if isinstance(tag, pdcmark.Paragraph):
            return [MdParagraph(self._inline_spans(tag))]
        if isinstance(tag, pdcmark.Heading):
            return [MdHeading(tag.level, self._inline_spans(tag))]
        if isinstance(tag, pdcmark.FencedCodeBlock):
            return [MdCode(tag.info.strip(), self._code_lines(tag))]
        if isinstance(tag, pdcmark.IndentedCodeBlock):
            return [MdCode('', self._code_lines(tag))]
        if isinstance(tag, pdcmark.HtmlBlock):
            lines = self._code_lines(tag)
            return [MdCode('html', lines)] if any(line.strip() for line in lines) else []
        if isinstance(tag, pdcmark.BlockQuote):
            children = self._children_until(tag)
            spans_groups = [c.spans for c in children if isinstance(c, MdParagraph)]
            extras = [c for c in children if not isinstance(c, MdParagraph)]
            out: list[MdBlock] = []
            if spans_groups:
                out.append(MdQuote(_join_spans(spans_groups)))
            out.extend(extras)
            return out
        if isinstance(tag, pdcmark.List):
            return [MdList(tuple(self._list_items(tag)))]
        if isinstance(tag, pdcmark.Table):
            return self._table_rows(tag)

        # Unknown/inline Start at block level: skip through to its End defensively.
        self._children_until(tag)
        return []

    def convert(self) -> list[MdBlock]:
        blocks: list[MdBlock] = []
        while (e := self._next()) is not None:
            if (block_list := self._convert_one(e)) is not None:
                blocks.extend(block_list)
        return blocks


def events_to_blocks(events: ta.Sequence[pdcmark.Event]) -> list[MdBlock]:
    return _EventWalker(events).convert()


##


def _complete_group_split(events: ta.Sequence[pdcmark.Event]) -> int:
    """The index up to which events form complete top-level groups (every Start matched by its End)."""

    depth = 0
    split = 0
    for i, e in enumerate(events):
        if isinstance(e, pdcmark.Start):
            depth += 1
        elif isinstance(e, pdcmark.End):
            depth = max(depth - 1, 0)
        if depth == 0:
            split = i + 1
    return split


class PdcmarkStream(MarkdownStreamBackend):
    def __init__(self, options: ta.Any | None = None) -> None:
        super().__init__()

        self._parser = pdcmark.StreamingParser(**({'options': options} if options is not None else {}))
        self._pending: list[pdcmark.Event] = []  # committed events not yet forming a complete group
        self._tentative: list[pdcmark.Event] = []
        self._finished = False

    def feed(self, chunk: str) -> None:
        if self._finished or not chunk:
            return
        out = self._parser.feed(chunk)
        self._pending.extend(out.committed)
        self._tentative = list(out.tentative)

    def pop_settled(self) -> list[MdBlock]:
        split = _complete_group_split(self._pending)
        if not split:
            return []
        complete, self._pending = self._pending[:split], self._pending[split:]
        return events_to_blocks(complete)

    def tail_blocks(self) -> list[MdBlock]:
        # Incomplete committed groups plus the parser's tentative view of the open remainder.
        if not self._pending and not self._tentative:
            return []
        return events_to_blocks([*self._pending, *self._tentative])

    def finalize(self) -> list[MdBlock]:
        if not self._finished:
            out = self._parser.finish()
            self._pending.extend(out.committed)
            self._finished = True
        events, self._pending = self._pending, []
        self._tentative = []
        return events_to_blocks(events)
