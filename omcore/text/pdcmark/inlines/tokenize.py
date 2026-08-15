"""
First-pass inline tokenizer.

Takes a block's `BufferedLine` tuple, joins them into a logical string (with line breaks represented internally), and
walks the string producing a flat list of `InlineNode`s. Confident constructs (code spans, escapes, entities, autolinks,
inline HTML, soft / hard breaks) are resolved here; emphasis is left as `DelimNode` placeholders for the resolution
pass.

Source offsets are tracked via a small position-to-offset lookup table built during joining.

Cf. pulldown-cmark/src/parse.rs::handle_inline_pass1 - same role and same construct precedences, but operating on a
fresh joined string rather than mutating a tree.
"""
import bisect
import re
import typing as ta
import unicodedata

from .... import dataclasses as dc
from ..blocks.leaves import BufferedLine
from ..scanning.autolinks import scan_autolink
from ..scanning.entities import scan_entity
from ..scanning.escapes import is_escapable
from ..scanning.inlinehtml import scan_inline_html
from ..scanning.links import scan_link_destination
from ..scanning.links import scan_link_label
from ..scanning.links import scan_link_title
from .nodes import AutolinkNode
from .nodes import CodeNode
from .nodes import DelimNode
from .nodes import HardBreakNode
from .nodes import HtmlNode
from .nodes import InlineNode
from .nodes import LinkCloseNode
from .nodes import LinkOpenNode
from .nodes import SoftBreakNode
from .nodes import TextNode


##


@dc.dataclass(frozen=True)
class _LineInfo:
    joined_start: int  # position in joined text where this line begins
    source_start: int  # original BufferedLine.line_start
    source_next: int   # original BufferedLine.line_next
    text_len: int      # length of `text` in the joined string


@dc.dataclass(frozen=True)
class _Joined:
    text: str
    lines: tuple[_LineInfo, ...]
    line_starts: tuple[int, ...]  # parallel to `lines`; each line's joined_start, for binary search


def _build_joined(lines: tuple[BufferedLine, ...]) -> _Joined:
    # Lines are joined VERBATIM with '\n' separators. Whitespace significance around line breaks (trailing-space /
    # trailing-backslash hard breaks, next-line leading-space skipping, paragraph initial/final trimming) is decided in
    # the tokenizer walk, where text context is known - a code span or raw-HTML span crossing a line break must see the
    # raw whitespace.
    out_parts: list[str] = []
    info: list[_LineInfo] = []
    pos = 0
    last_ix = len(lines) - 1

    for i, ln in enumerate(lines):
        text = ln.text
        info.append(_LineInfo(
            joined_start=pos,
            source_start=ln.line_start,
            source_next=ln.line_next,
            text_len=len(text),
        ))
        out_parts.append(text)
        pos += len(text)
        if i < last_ix:
            out_parts.append('\n')
            pos += 1

    return _Joined(
        text=''.join(out_parts),
        lines=tuple(info),
        line_starts=tuple(li.joined_start for li in info),
    )


def _source_offset(joined: _Joined, p: int) -> int:
    """Map a joined-text position to an absolute source offset."""

    # Binary search for the line containing p. Every joined position from a line's start through its trailing newline
    # (== the next line's start - 1) belongs to that line. Since lines are joined verbatim, the mapping within a line
    # (newline included - it maps to the start of the source EOL sequence) is linear.
    ix = bisect.bisect_right(joined.line_starts, p) - 1
    li = joined.lines[ix if ix >= 0 else 0]
    return min(li.source_start + (p - li.joined_start), li.source_next)


##


# Characters that can start a non-text construct (or need per-char handling) in the main tokenizer loop. Everything
# between two of these is plain text and is consumed in bulk.
_RE_SPECIAL = re.compile(r'[\n\\&`<!\[\]*_~]')


@dc.dataclass(frozen=True)
class TokenizedBlock:
    nodes: list[InlineNode]

    # Re-runs the tokenizer walk over a joined-text span (absolute positions), bounding all scanning at the span end.
    # Link resolution uses this to give a failed link's consumed suffix a fresh inline parse of its own.
    retokenize: ta.Callable[[int, int], list[InlineNode]]

    # Raw (undecoded) joined-text slice - link resolution derives collapsed / shortcut labels from this, since CM
    # matches labels on raw source text (escapes are NOT processed: `[foo\!]` does not match a `[foo!]` refdef).
    raw_slice: ta.Callable[[int, int], str]


def tokenize_block(
        lines: tuple[BufferedLine, ...],
        *,
        strikethrough: bool = False,
        max_nested_parens: int = 32,
) -> TokenizedBlock:
    if not lines:
        return TokenizedBlock(nodes=[], retokenize=lambda start, end: [], raw_slice=lambda start, end: '')
    joined = _build_joined(lines)

    def retokenize(start: int, end: int) -> list[InlineNode]:
        # A prefix slice keeps joined positions absolute while preventing scanners from matching past the span end.
        # (Edge trimming is a whole-paragraph rule and doesn't apply to interior spans.)
        return _walk(
            joined,
            joined.text[:end],
            start,
            strikethrough=strikethrough,
            max_nested_parens=max_nested_parens,
            trim_edges=False,
        )

    return TokenizedBlock(
        nodes=_walk(
            joined,
            joined.text,
            0,
            strikethrough=strikethrough,
            max_nested_parens=max_nested_parens,
            trim_edges=True,
        ),
        retokenize=retokenize,
        raw_slice=lambda start, end: joined.text[start:end],
    )


def tokenize_inline(
        lines: tuple[BufferedLine, ...],
        *,
        strikethrough: bool = False,
        max_nested_parens: int = 32,
) -> list[InlineNode]:
    return tokenize_block(lines, strikethrough=strikethrough, max_nested_parens=max_nested_parens).nodes


def _walk(  # noqa: C901
        joined: _Joined,
        s: str,
        start: int,
        *,
        strikethrough: bool,
        max_nested_parens: int,
        trim_edges: bool,
) -> list[InlineNode]:
    nodes: list[InlineNode] = []
    n = len(s)

    # Text accumulator - flushed into a TextNode on any non-text token. Entities / escapes decode into it, so its
    # content may be shorter than the joined span it covers; source offsets always come from joined positions.
    buf: list[str] = []
    buf_start = start  # joined position where buf started (only valid if buf is non-empty)

    def flush_text(end_pos: int, *, strip_trailing: int = 0) -> None:
        if not buf:
            return
        text = ''.join(buf)
        if strip_trailing:
            # The stripped chars are literal source whitespace, bulk-appended verbatim - safe to cut by count.
            text = text[:max(len(text) - strip_trailing, 0)]
        if text:
            start_src = _source_offset(joined, buf_start)
            end_src = _source_offset(joined, end_pos)
            nodes.append(TextNode(offset=(start_src, end_src), text=text))
        buf.clear()

    def emit(node: InlineNode, at_pos: int) -> None:
        flush_text(at_pos)
        nodes.append(node)

    def line_end_source(newline_pos: int) -> int:
        line_ix = _line_index_at_newline(joined, newline_pos)
        if line_ix is not None:
            return joined.lines[line_ix].source_next
        return _source_offset(joined, newline_pos + 1)

    # CM trims a paragraph's initial whitespace before inline parsing. (Headings and table cells arrive pre-trimmed;
    # the skip is harmless there.)
    i = start
    if trim_edges:
        while i < n and s[i] in ' \t':
            i += 1

    while i < n:
        c = s[i]

        # Newline boundary - soft or hard break. Trailing spaces / tabs are removed from the text; two-plus trailing
        # spaces make the break hard. Leading whitespace of the following line belongs to the break, not the text.
        if c == '\n':
            j = i
            while j > start and s[j - 1] in ' \t':
                j -= 1
            is_hard = i - j >= 2 and s[i - 1] == ' ' and s[i - 2] == ' '
            flush_text(j, strip_trailing=i - j)
            offset = (_source_offset(joined, j), line_end_source(i))
            if is_hard:
                nodes.append(HardBreakNode(offset=offset))
            else:
                nodes.append(SoftBreakNode(offset=offset))
            i += 1
            while i < n and s[i] in ' \t':
                i += 1
            continue

        # Backslash escape.
        if c == '\\' and i + 1 < n:
            nxt = s[i + 1]
            if nxt == '\n':
                # Backslash at end of line → hard break (CM §6.9). Escaped backslashes were consumed pairwise by the
                # branch below, so a backslash surviving to this position is an odd (unescaped) one.
                flush_text(i)
                nodes.append(HardBreakNode(offset=(_source_offset(joined, i), line_end_source(i + 1))))
                i += 2
                while i < n and s[i] in ' \t':
                    i += 1
                continue

            if is_escapable(nxt):
                if not buf:
                    buf_start = i
                buf.append(nxt)
                i += 2
                continue
            # Fall through - backslash before non-escapable char is literal.

        # Entity reference.
        if c == '&':
            m = scan_entity(s, i)
            if m is not None:
                if not buf:
                    buf_start = i
                buf.append(m.decoded)
                # Stretch buf_start to point at decoded content; tracker continues from m.end.
                i = m.end
                continue

        # Code span.
        if c == '`':
            run = _backtick_run(s, i)
            close = _find_matching_backtick_close(s, i + run, run)
            if close is not None:
                content = s[i + run:close]
                content = _normalize_code_span(content)
                start_src = _source_offset(joined, i)
                end_src = _source_offset(joined, close + run)
                emit(CodeNode(offset=(start_src, end_src), text=content), i)
                i = close + run
                continue

            # No matching close - treat backticks as text.
            if not buf:
                buf_start = i
            buf.append(s[i:i + run])
            i += run
            continue

        # Autolink or inline HTML or literal `<`.
        if c == '<':
            al = scan_autolink(s, i)
            if al is not None:
                start_src = _source_offset(joined, i)
                end_src = _source_offset(joined, al.end)
                emit(AutolinkNode(offset=(start_src, end_src), target=al.target, is_email=al.is_email), i)
                i = al.end
                continue

            html_m = scan_inline_html(s, i)
            if html_m is not None:
                start_src = _source_offset(joined, i)
                end_src = _source_offset(joined, html_m.end)
                emit(HtmlNode(offset=(start_src, end_src), text=s[i:html_m.end]), i)
                i = html_m.end
                continue

        # Image open `![` (must check before plain `!`).
        if c == '!' and i + 1 < n and s[i + 1] == '[':
            start_src = _source_offset(joined, i)
            end_src = _source_offset(joined, i + 2)
            emit(LinkOpenNode(offset=(start_src, end_src), is_image=True, joined_end=i + 2), i)
            i += 2
            continue

        # Link open `[`.
        if c == '[':
            start_src = _source_offset(joined, i)
            end_src = _source_offset(joined, i + 1)
            emit(LinkOpenNode(offset=(start_src, end_src), is_image=False, joined_end=i + 1), i)
            i += 1
            continue

        # Link close `]` - also peeks ahead for the link suffix.
        if c == ']':
            close_node, consumed_to = _scan_link_suffix(s, i, joined, max_nested_parens)
            emit(close_node, i)
            i = consumed_to
            continue

        # Emphasis delimiter. `~` is only a delim if the strikethrough option is enabled.
        if c == '*' or c == '_' or (c == '~' and strikethrough):
            run_end = i
            while run_end < n and s[run_end] == c:
                run_end += 1
            prev_c = s[i - 1] if i > 0 else '\n'
            next_c = s[run_end] if run_end < n else '\n'
            can_open, can_close = _flanking(c, prev_c, next_c)
            start_src = _source_offset(joined, i)
            end_src = _source_offset(joined, run_end)
            emit(DelimNode(
                offset=(start_src, end_src),
                char=c,
                count=run_end - i,
                can_open=can_open,
                can_close=can_close,
                original_count=run_end - i,
            ), i)
            i = run_end
            continue

        # Plain text accumulation - bulk-consume through the next potentially-special character. (The current char may
        # itself be a special that fell through above, so the scan starts at i + 1; progress is always ≥ 1 char.)
        if not buf:
            buf_start = i
        m2 = _RE_SPECIAL.search(s, i + 1)
        j = m2.start() if m2 is not None else n
        buf.append(s[i:j])
        i = j

    # Final whitespace of the block is trimmed (CM paragraph raw-content rule); interior spans flush as-is.
    j = n
    if trim_edges:
        while j > 0 and s[j - 1] in ' \t':
            j -= 1
    flush_text(j, strip_trailing=n - j)
    return nodes


##


def _backtick_run(s: str, i: int) -> int:
    n = len(s)
    j = i
    while j < n and s[j] == '`':
        j += 1
    return j - i


def _find_matching_backtick_close(s: str, start: int, run_len: int) -> int | None:
    """Find the start position of a run of exactly `run_len` backticks starting at `s[start:]`."""

    n = len(s)
    i = start
    while i < n:
        # Find the next backtick.
        bt = s.find('`', i)
        if bt < 0:
            return None
        # Measure the run.
        j = bt
        while j < n and s[j] == '`':
            j += 1
        if j - bt == run_len:
            return bt
        i = j
    return None


def _normalize_code_span(content: str) -> str:
    """
    CM §6.3 normalization: turn line breaks into spaces; if there's at least one non-space char and the content starts
    AND ends with a single space, strip the surrounding spaces.
    """

    # Replace line breaks with spaces.
    content = content.replace('\n', ' ')
    if (
        len(content) >= 2
        and content[0] == ' '
        and content[-1] == ' '
        and any(c != ' ' for c in content)
    ):
        return content[1:-1]
    return content


def _flanking(c: str, prev_c: str, next_c: str) -> tuple[bool, bool]:
    """
    Compute `can_open` and `can_close` for an emphasis delimiter run.

    Direct port of CommonMark §6.4 "left-flanking" / "right-flanking" definitions plus the intraword-underscore rule.
    See pulldown-cmark/src/parse.rs::{delim_run_can_open, delim_run_can_close}.
    """

    prev_ws = _is_unicode_whitespace(prev_c)
    next_ws = _is_unicode_whitespace(next_c)
    prev_punct = _is_unicode_punct(prev_c)
    next_punct = _is_unicode_punct(next_c)

    left_flanking = (
        not next_ws
        and (not next_punct or prev_ws or prev_punct)
    )
    right_flanking = (
        not prev_ws
        and (not prev_punct or next_ws or next_punct)
    )

    if c == '_':
        # Underscore: intraword underscores are neither opening nor closing.
        can_open = left_flanking and (not right_flanking or prev_punct)
        can_close = right_flanking and (not left_flanking or next_punct)
    else:
        # `*` and (GFM) `~` use the plain flanking rules - intraword emphasis / strikethrough is allowed.
        can_open = left_flanking
        can_close = right_flanking

    return can_open, can_close


def _is_unicode_whitespace(c: str) -> bool:
    if c == '':
        return True
    if c in ' \t\n\v\f\r':
        return True
    # CM defines unicode whitespace as `Zs` plus tab/CR/LF/FF/VT (not `Zl`/`Zp`).
    return unicodedata.category(c) == 'Zs'


def _is_unicode_punct(c: str) -> bool:
    if c == '':
        return False
    # CM uses ASCII-punctuation OR Unicode P*-category.
    if c in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~':
        return True
    cat = unicodedata.category(c)
    return cat.startswith(('P', 'S'))


def _line_index_at_newline(joined: _Joined, pos: int) -> int | None:
    ix = bisect.bisect_right(joined.line_starts, pos) - 1
    if ix >= 0 and joined.lines[ix].joined_start + joined.lines[ix].text_len == pos:
        return ix
    return None


def _scan_link_suffix(
        s: str,
        close_pos: int,
        joined: _Joined,
        max_nested_parens: int,
) -> tuple[LinkCloseNode, int]:
    """
    Inspect what follows a `]` at `s[close_pos]` to determine the link-close kind.

    Returns (LinkCloseNode, new_position_in_joined). The new position is the index just past any consumed suffix syntax.
    If no suffix matches, only the `]` itself is consumed and the close node is tagged as 'shortcut' - link resolution
    will try refdefs later.

    The literal source text from `]` through the consumed suffix is captured in `raw_consumed` so a resolution failure
    can emit it back as plain text.
    """

    n = len(s)
    close_src = _source_offset(joined, close_pos)
    close_src_end = _source_offset(joined, close_pos + 1)
    after = close_pos + 1
    if after >= n:
        return LinkCloseNode(
            offset=(close_src, close_src_end),
            consumed_end=close_src_end,
            kind='shortcut',
            raw_consumed=']',
            joined_start=close_pos,
        ), after

    nxt = s[after]

    # Inline link / image: `(dest "title")`.
    if nxt == '(':
        result = _try_parse_inline_link(s, after, max_nested_parens)
        if result is not None:
            dest, title, end_pos = result
            end_src = _source_offset(joined, end_pos)
            return LinkCloseNode(
                offset=(close_src, close_src_end),
                consumed_end=end_src,
                kind='inline',
                raw_consumed=s[close_pos:end_pos],
                dest_url=dest,
                title=title,
                suffix_joined=(close_pos + 1, end_pos),
                joined_start=close_pos,
            ), end_pos
        # Fall through - `(` without a valid link → shortcut form.

    # Reference link: `[label]` or `[]`.
    if nxt == '[':
        # `[]` → collapsed.
        if after + 1 < n and s[after + 1] == ']':
            end_pos = after + 2
            end_src = _source_offset(joined, end_pos)
            return LinkCloseNode(
                offset=(close_src, close_src_end),
                consumed_end=end_src,
                kind='collapsed',
                raw_consumed=s[close_pos:end_pos],
                suffix_joined=(close_pos + 1, end_pos),
                joined_start=close_pos,
            ), end_pos

        # `[label]` → reference.
        label_scan = scan_link_label(s, after)
        if label_scan is not None:
            end_pos = label_scan.end
            end_src = _source_offset(joined, end_pos)
            return LinkCloseNode(
                offset=(close_src, close_src_end),
                consumed_end=end_src,
                kind='reference',
                raw_consumed=s[close_pos:end_pos],
                label=label_scan.raw,
                suffix_joined=(close_pos + 1, end_pos),
                joined_start=close_pos,
            ), end_pos

    # Default - shortcut form (try inner text against refdefs at resolution time).
    return LinkCloseNode(
        offset=(close_src, close_src_end),
        consumed_end=close_src_end,
        kind='shortcut',
        raw_consumed=']',
        joined_start=close_pos,
    ), after


def _try_parse_inline_link(s: str, paren_pos: int, max_nested_parens: int) -> tuple[str, str, int] | None:
    """Parse `(dest "title")` starting at the `(`. Returns (dest, title, end_pos_after_paren)."""

    n = len(s)
    i = paren_pos + 1  # past `(`

    # Optional whitespace (including up to 1 newline).
    i = _consume_link_ws(s, i, allow_nl=True)
    if i >= n:
        return None
    if s[i] == ')':
        return '', '', i + 1

    # Destination - may or may not be present.
    dest = ''
    if s[i] != ')':
        dest_scan = scan_link_destination(s, i, max_parens=max_nested_parens)
        if dest_scan is None:
            return None
        dest = dest_scan.dest
        i = dest_scan.end

    # Optional whitespace before title.
    i = _consume_link_ws(s, i, allow_nl=True)
    title = ''
    if i < n and s[i] in '"\'(':
        title_scan = scan_link_title(s, i)

        if title_scan is not None:
            # Title valid; require ws-then-`)` after.
            title = title_scan.title
            i = title_scan.end
            i = _consume_link_ws(s, i, allow_nl=True)

        else:
            # Title-shaped but invalid - fail the whole inline link.
            return None

    # (No title: `i` already sits just past the whitespace run; nothing to rewind.)

    if i >= n or s[i] != ')':
        return None

    return dest, title, i + 1


def _consume_link_ws(s: str, i: int, *, allow_nl: bool) -> int:
    n = len(s)
    saw_nl = False
    while i < n:
        c = s[i]
        if c == ' ' or c == '\t':
            i += 1
            continue
        if c == '\n' and allow_nl and not saw_nl:
            i += 1
            saw_nl = True
            continue
        break
    return i
