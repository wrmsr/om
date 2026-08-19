# @om-precheck-allow-any-unicode
"""
A zero-dependency, line-oriented markdown subset - built for streaming llm output, not commonmark conformance.

The parser is deliberately structured around the commit model: `parse_lines` reports how many leading lines belong to
*settled* blocks (a block settles when its terminator is seen - a blank line, the next block's opening line, or a
closing code fence), and `MarkdownStream` uses that to split an incoming stream into blocks that can be committed to
scrollback forever versus a tail that re-renders live each frame.

Supported: atx headings, paragraphs, fenced code blocks (with an info string routed to a highlighter), block quotes,
flat unordered/ordered lists, thematic breaks, and the inline set (bold / italic / strike / inline code / links).
Deliberately unsupported (so far): setext headings, nested lists/quotes, tables, reference links, html.

(The optional markdown-it-py/incparse path can slot in later behind the same block/renderer types; this internal
implementation is the always-available default, per the codestyle's dependency policy.)
"""
import abc
import re
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .segments import Segment
from .segments import SegmentRows
from .styles import StyleLike
from .wraps import wrap_segments


##
# Blocks


class MdBlock(lang.Abstract):
    pass


# Inline content is styled spans (md.* tags), not raw markdown text: parser backends with real inline engines (pdcmark,
# markdown-it) produce spans directly; the internal parser builds them via `parse_inlines`. The `.of()` constructors
# take raw inline-markdown text and are what the internal parser (and tests) use.


@dc.dataclass(frozen=True)
class MdHeading(MdBlock, lang.Final):
    level: int
    spans: tuple[Segment, ...]

    @classmethod
    def of(cls, level: int, text: str) -> MdHeading:
        return cls(level, (Segment(text, f'md.h{min(level, 6)}'),) if text else ())


@dc.dataclass(frozen=True)
class MdParagraph(MdBlock, lang.Final):
    spans: tuple[Segment, ...]

    @classmethod
    def of(cls, text: str) -> MdParagraph:
        return cls(tuple(parse_inlines(text)))


@dc.dataclass(frozen=True)
class MdCode(MdBlock, lang.Final):
    info: str
    lines: tuple[str, ...]


@dc.dataclass(frozen=True)
class MdQuote(MdBlock, lang.Final):
    spans: tuple[Segment, ...]

    @classmethod
    def of(cls, text: str) -> MdQuote:
        return cls(tuple(parse_inlines(text, base='md.quote')))


@dc.dataclass(frozen=True)
class MdListItem(lang.Final):
    marker: str
    spans: tuple[Segment, ...]
    depth: int = 0  # nesting level; each level renders two columns of indent

    @classmethod
    def of(cls, marker: str, text: str, depth: int = 0) -> MdListItem:
        return cls(marker, tuple(parse_inlines(text)), depth)


@dc.dataclass(frozen=True)
class MdList(MdBlock, lang.Final):
    items: tuple[MdListItem, ...]


@dc.dataclass(frozen=True)
class MdRule(MdBlock, lang.Final):
    pass


##
# Line-level parsing


_HEADING_PAT = re.compile(r'(#{1,6})\s+(.*?)\s*#*\s*$')
_FENCE_PAT = re.compile(r'(```+|~~~+)\s*(\S*)\s*$')
_RULE_PAT = re.compile(r'(\*\s*){3,}$|(-\s*){3,}$|(_\s*){3,}$')
_QUOTE_PAT = re.compile(r'>\s?(.*)$')
_LIST_PAT = re.compile(r'([-*+]|\d{1,9}[.)])\s+(.*)$')


def _is_block_start(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    return bool(
        _HEADING_PAT.match(s) or
        _FENCE_PAT.match(s) or
        _RULE_PAT.match(s) or
        _QUOTE_PAT.match(s) or
        _LIST_PAT.match(s),
    )


def parse_lines(lines: ta.Sequence[str], *, at_eof: bool) -> tuple[list[MdBlock], int]:  # noqa: C901
    """
    Parse complete lines into blocks, returning (blocks, settled_line_count).

    Without `at_eof`, the final still-open block is withheld and its lines are not counted as settled; with it,
    everything is emitted and all lines settle.
    """

    blocks: list[MdBlock] = []
    settled = 0  # line index up to which emitted blocks (and separators) extend
    i = 0
    n = len(lines)

    def settle(upto: int) -> None:
        nonlocal settled
        settled = upto

    while i < n:
        line = lines[i]
        s = line.strip()

        if not s:
            i += 1
            settle(i)
            continue

        if (m := _HEADING_PAT.match(s)) is not None:
            blocks.append(MdHeading.of(len(m.group(1)), m.group(2)))
            i += 1
            settle(i)
            continue

        if _RULE_PAT.match(s) is not None:
            blocks.append(MdRule())
            i += 1
            settle(i)
            continue

        if (m := _FENCE_PAT.match(s)) is not None:
            fence = m.group(1)[0] * 3
            info = m.group(2)
            body: list[str] = []
            j = i + 1
            closed = False
            while j < n:
                if lines[j].strip().startswith(fence):
                    closed = True
                    break
                body.append(lines[j])
                j += 1
            if closed:
                blocks.append(MdCode(info, tuple(body)))
                i = j + 1
                settle(i)
                continue
            if at_eof:
                blocks.append(MdCode(info, tuple(body)))
                i = n
                settle(i)
                continue
            break  # open fence: everything from here is unsettled

        if _QUOTE_PAT.match(s) is not None:
            parts: list[str] = []
            j = i
            while j < n and (qm := _QUOTE_PAT.match(lines[j].strip())) is not None:
                parts.append(qm.group(1))
                j += 1
            terminated = j < n or at_eof
            if not terminated:
                break
            blocks.append(MdQuote.of(' '.join(p for p in parts if p)))
            i = j
            settle(i)
            continue

        if _LIST_PAT.match(s) is not None:
            raw_items: list[tuple[str, str, int]] = []
            indent_stack: list[int] = []
            j = i
            while j < n:
                item_s = lines[j].strip()
                if (im := _LIST_PAT.match(item_s)) is not None:
                    # Nesting depth from the marker's indentation: each new deeper indent is one more level, and
                    # dedenting pops back to the enclosing level.
                    indent = len(exp := lines[j].expandtabs(4)) - len(exp.lstrip(' '))
                    while indent_stack and indent < indent_stack[-1]:
                        indent_stack.pop()
                    if not indent_stack or indent > indent_stack[-1]:
                        indent_stack.append(indent)
                    raw_items.append((im.group(1), im.group(2), len(indent_stack) - 1))
                    j += 1
                elif item_s and not _is_block_start(lines[j]) and raw_items and lines[j][:1] in (' ', '\t'):
                    # An indented continuation joins the previous item.
                    marker, text, depth = raw_items[-1]
                    raw_items[-1] = (marker, text + ' ' + item_s, depth)
                    j += 1
                else:
                    break
            terminated = j < n or at_eof
            if not terminated:
                break
            blocks.append(MdList(tuple(MdListItem.of(marker, text, depth) for marker, text, depth in raw_items)))
            i = j
            settle(i)
            continue

        # Paragraph: accumulate until a blank line or another block's start.
        parts = [s]
        j = i + 1
        while j < n and lines[j].strip() and not _is_block_start(lines[j]):
            parts.append(lines[j].strip())
            j += 1
        terminated = j < n or at_eof
        if not terminated:
            break
        blocks.append(MdParagraph.of(' '.join(parts)))
        i = j
        settle(i)

    if at_eof:
        settle(n)
    return blocks, settled


def parse_markdown(text: str) -> list[MdBlock]:
    blocks, _ = parse_lines(text.split('\n'), at_eof=True)
    return blocks


##
# Streaming


class MarkdownStreamBackend(lang.Abstract):
    """
    A streaming markdown parser: chunks in, settled blocks + a live tail out.

    Settled blocks will never change again (commit them); `tail_blocks` is the current best-effort parse of the
    unsettled remainder (re-render it each frame); `finalize` ends the current stream, drains everything left, and
    resets for a fresh one. Backends are REUSABLE across stream cycles - long-lived holders (a chat tail fed one content
    block after another) finalize at every block boundary and keep feeding the same instance. Implementations: the
    internal line-based parser (below), pdcmark (`.pdcmark`), markdown-it (`.markdownit`).
    """

    @abc.abstractmethod
    def feed(self, chunk: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def pop_settled(self) -> list[MdBlock]:
        raise NotImplementedError

    @abc.abstractmethod
    def tail_blocks(self) -> list[MdBlock]:
        raise NotImplementedError

    @abc.abstractmethod
    def finalize(self) -> list[MdBlock]:
        raise NotImplementedError


class MarkdownStream(MarkdownStreamBackend):
    """
    The internal streaming backend: line-based settling over the internal parser.

    Only complete lines can settle; the trailing partial line always stays in the tail.
    """

    def __init__(self) -> None:
        super().__init__()

        self._buffer = ''

    @property
    def buffer(self) -> str:
        return self._buffer

    def feed(self, chunk: str) -> None:
        self._buffer += chunk

    def pop_settled(self) -> list[MdBlock]:
        lines = self._buffer.split('\n')
        complete = lines[:-1]  # the final element is the partial (possibly empty) last line
        blocks, settled = parse_lines(complete, at_eof=False)
        if settled:
            drop = sum(len(line) + 1 for line in complete[:settled])
            self._buffer = self._buffer[drop:]
        return blocks

    def tail_blocks(self) -> list[MdBlock]:
        """The unsettled remainder, parsed as if the stream ended here - for live rendering."""

        if not self._buffer:
            return []
        return parse_markdown(self._buffer)

    def finalize(self) -> list[MdBlock]:
        blocks = self.tail_blocks()
        self._buffer = ''
        return blocks


##
# Inline styling


_INLINE_PAT = re.compile(
    r'(?P<code>`+)(?P<code_text>.+?)(?P=code)'
    r'|\*\*(?P<bold>[^*]+)\*\*'
    r'|\*(?P<italic>[^*]+)\*'
    r'|__(?P<bold2>[^_]+)__'
    r'|_(?P<italic2>[^_]+)_'
    r'|~~(?P<strike>[^~]+)~~'
    r'|\[(?P<link_text>[^]]+)\]\((?P<link_url>[^)]+)\)',
)


def parse_inlines(text: str, *, base: StyleLike = None) -> list[Segment]:
    """One pass, no nesting: the outermost marker wins (terminal styling doesn't stack much anyway)."""

    segments: list[Segment] = []
    pos = 0
    for m in _INLINE_PAT.finditer(text):
        if m.start() > pos:
            segments.append(Segment(text[pos: m.start()], base))
        if m.group('code_text') is not None:
            segments.append(Segment(m.group('code_text'), 'md.code.inline'))
        elif (t := m.group('bold') or m.group('bold2')) is not None:
            segments.append(Segment(t, 'md.bold'))
        elif (t := m.group('italic') or m.group('italic2')) is not None:
            segments.append(Segment(t, 'md.italic'))
        elif m.group('strike') is not None:
            segments.append(Segment(m.group('strike'), 'md.strike'))
        elif m.group('link_text') is not None:
            segments.append(Segment(m.group('link_text'), 'md.link'))
            segments.append(Segment(' (' + m.group('link_url') + ')', 'md.link.url'))
        pos = m.end()
    if pos < len(text):
        segments.append(Segment(text[pos:], base))
    return segments


##
# Rendering


CodeHighlighter: ta.TypeAlias = ta.Callable[[str, ta.Sequence[str]], SegmentRows | None]


def _expand_tabs(line: str) -> str:
    return line.replace('\t', '    ')


def _render_code(block: MdCode, width: int, highlighter: CodeHighlighter | None) -> list[list[Segment]]:
    body_rows: SegmentRows | None = None
    if highlighter is not None and block.info:
        body_rows = highlighter(block.info, block.lines)
    if body_rows is None:
        body_rows = [[Segment(_expand_tabs(line), 'md.code')] if line else [] for line in block.lines]

    rows: list[list[Segment]] = []
    for row in body_rows:
        # Plain (untagged) highlighter output still gets the code base style; tabs expand here (display-only path); rows
        # right-fill so themes with code backgrounds paint the full block width.
        body = [
            Segment(_expand_tabs(seg.text), seg.style if seg.style is not None else 'md.code')
            for seg in row
            if seg.text
        ]
        used = sum(len(seg.text) for seg in body) + 1
        pad = max(width - used, 0)
        rows.append([Segment(' ', 'md.code'), *body, Segment(' ' * pad, 'md.code')])
    return rows


def _render_hanging(
        prefix: str,
        prefix_style: StyleLike,
        segments: ta.Sequence[Segment],
        width: int,
) -> list[list[Segment]]:
    indent = ' ' * len(prefix)
    body_width = max(width - len(prefix), 8)
    rows: list[list[Segment]] = []
    for wrap_i, wrapped in enumerate(wrap_segments(list(segments), body_width)):
        lead = Segment(prefix, prefix_style) if wrap_i == 0 else Segment(indent)
        rows.append([lead, *wrapped])
    return rows


def _retag(spans: ta.Sequence[Segment], base: str) -> list[Segment]:
    """Give untagged spans a base tag (inline styling from the parser wins where present)."""

    return [Segment(s.text, s.style if s.style is not None else base) for s in spans]


_LIST_BULLETS = '•◦▪'  # bullet glyph per nesting depth (cycling)


def render_block(
        block: MdBlock,
        width: int,
        *,
        highlighter: CodeHighlighter | None = None,
) -> list[list[Segment]]:
    if isinstance(block, MdHeading):
        tag = f'md.h{min(block.level, 6)}'
        return _render_hanging('#' * block.level + ' ', tag, _retag(block.spans, tag), width)

    if isinstance(block, MdParagraph):
        return [list(row) for row in wrap_segments(list(block.spans), width)]

    if isinstance(block, MdCode):
        return _render_code(block, width, highlighter)

    if isinstance(block, MdQuote):
        return _render_hanging('│ ', 'md.quote.marker', _retag(block.spans, 'md.quote'), width)

    if isinstance(block, MdList):
        rows: list[list[Segment]] = []
        for item in block.items:
            glyph = _LIST_BULLETS[item.depth % len(_LIST_BULLETS)]
            marker = f'{glyph} ' if item.marker in '-*+' else f'{item.marker} '
            prefix = '  ' * item.depth + marker
            rows.extend(_render_hanging(prefix, 'md.list.marker', list(item.spans), width))
        return rows

    if isinstance(block, MdRule):
        return [[Segment('─' * max(width, 1), 'md.rule')]]

    raise TypeError(block)


def render_blocks(
        blocks: ta.Sequence[MdBlock],
        width: int,
        *,
        highlighter: CodeHighlighter | None = None,
) -> list[list[Segment]]:
    """Render blocks with a single blank row between them."""

    rows: list[list[Segment]] = []
    for i, block in enumerate(blocks):
        if i:
            rows.append([])
        rows.extend(render_block(block, width, highlighter=highlighter))
    return rows
