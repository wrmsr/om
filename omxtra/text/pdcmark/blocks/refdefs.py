"""
Reference link definition table + refdef parsing.

Refdefs are collected as paragraphs close. When the paragraph buffer starts with one or more
refdef-shaped sequences of lines, those lines are consumed, the refdef is registered, and only the
remaining lines (if any) emit as paragraph content.

A refdef spans 1, 2, or 3 lines:

  - `[label]: dest "title"`
  - `[label]: dest` / `"title"`
  - `[label]:` / `dest` / `"title"`

(Plus combinations - title is optional; dest and title can each follow the label or sit on their
own line.) See CommonMark §4.7 for the full grammar. Cf. pulldown-cmark/src/firstpass.rs::FirstPass::parse_refdef_total.
"""
import typing as ta

from omcore import dataclasses as dc

from ..scanning.links import normalize_link_label
from ..scanning.links import scan_link_destination
from ..scanning.links import scan_link_label
from ..scanning.links import scan_link_title


##


@dc.dataclass(frozen=True)
class LinkDef:
    dest: str
    title: str


# pulldown-cmark/src/parse.rs::RefDefs - same role (label-keyed table with case-insensitive normalization). We use a
# plain dict; pulldown wraps a HashMap<LinkLabel, LinkDef>.
class RefDefs:
    def __init__(self) -> None:
        super().__init__()

        self._table: dict[str, LinkDef] = {}

    def add(self, label: str, link_def: LinkDef) -> bool:
        """Register a refdef. First wins per CommonMark; returns True if added, False if `label` was already defined."""

        if label in self._table:
            return False
        self._table[label] = link_def
        return True

    def get(self, label: str) -> LinkDef | None:
        return self._table.get(label)

    def __contains__(self, label: str) -> bool:
        return label in self._table

    def __len__(self) -> int:
        return len(self._table)

    def copy(self) -> RefDefs:
        """An independent copy (LinkDefs are immutable and shared)."""

        new = RefDefs()
        new._table = dict(self._table)  # noqa
        return new


##


@dc.dataclass(frozen=True)
class RefDefMatch:
    lines_consumed: int
    label: str
    link_def: LinkDef


# pulldown-cmark/src/firstpass.rs::FirstPass::parse_refdef_total - full multi-line version.
def try_consume_refdef(lines: ta.Sequence[str], start: int) -> RefDefMatch | None:
    """
    Try to parse a refdef beginning at `lines[start]`. Returns a RefDefMatch on success, or None if the lines starting
    here are not a valid refdef.

    The candidate lines are joined and scanned as one text: labels and titles may span lines (the lines come from a
    paragraph buffer, so none is blank). The label starts the first line (up to 3 spaces of indent); the destination
    follows the colon on the same or the next line; the optional title must be separated from the destination by
    whitespace, may run over further lines, and the remainder of its final line must be blank. If a title candidate
    fails, the refdef is still valid without one when the destination's own line is otherwise clean.
    """

    if start >= len(lines):
        return None

    text = '\n'.join(lines[start:])
    n = len(text)

    j = 0
    while j < n and text[j] == ' ' and j < 3:
        j += 1
    if j >= n or text[j] != '[':
        return None
    label_scan = scan_link_label(text, j)
    if label_scan is None or label_scan.end >= n or text[label_scan.end] != ':':
        return None
    norm = normalize_link_label(label_scan.raw)
    if not norm:
        return None

    pos = _skip_ws(text, label_scan.end + 1, max_newlines=1)
    if pos is None or pos >= n:
        return None
    dest_scan = scan_link_destination(text, pos)
    if dest_scan is None:
        return None
    dest_end = dest_scan.end

    # Optional title. `tpos > dest_end` enforces the required whitespace separation - a quote glued straight onto the
    # destination makes the line garbage, not a title.
    tpos = _skip_ws(text, dest_end, max_newlines=1)
    if tpos is not None and tpos > dest_end and tpos < n and text[tpos] in '"\'(':
        title_scan = scan_link_title(text, tpos)
        if title_scan is not None:
            nl = text.find('\n', title_scan.end)
            tail = text[title_scan.end:nl if nl >= 0 else n]
            if tail.strip() == '':
                return RefDefMatch(
                    lines_consumed=text.count('\n', 0, title_scan.end) + 1,
                    label=norm,
                    link_def=LinkDef(dest=dest_scan.dest, title=title_scan.title),
                )

    # No (usable) title: the remainder of the destination's line must be whitespace.
    nl = text.find('\n', dest_end)
    tail = text[dest_end:nl if nl >= 0 else n]
    if tail.strip() != '':
        return None
    return RefDefMatch(
        lines_consumed=text.count('\n', 0, dest_end) + 1,
        label=norm,
        link_def=LinkDef(dest=dest_scan.dest, title=''),
    )


def _skip_ws(text: str, pos: int, *, max_newlines: int) -> int | None:
    """Skip spaces / tabs and up to `max_newlines` newlines; None if the newline budget is exceeded."""

    n = len(text)
    newlines = 0
    while pos < n:
        c = text[pos]
        if c == ' ' or c == '\t':
            pos += 1
        elif c == '\n':
            newlines += 1
            if newlines > max_newlines:
                return None
            pos += 1
        else:
            break
    return pos


