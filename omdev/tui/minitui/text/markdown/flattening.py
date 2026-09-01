"""
Shared flattening for the parser backends. The render model is deliberately simpler than commonmark, so the pdcmark and
markdown-it adapters squash nested structure the same way: inline groups join with spaces, and a list item carries
inline content only - its nested lists merge into the parent one level deeper, and any other block-level child (a table,
a code block, a rule) surfaces as a sibling block that splits the list, so nothing is dropped.
"""
import typing as ta

from omcore import dataclasses as dc

from ..segments import Segment
from .base import MdBlock
from .base import MdHeading
from .base import MdList
from .base import MdListItem
from .base import MdParagraph
from .base import MdQuote


ListPart: ta.TypeAlias = MdListItem | MdBlock


##


def join_span_groups(groups: ta.Iterable[ta.Sequence[Segment]]) -> tuple[Segment, ...]:
    out: list[Segment] = []
    for group in groups:
        if not group:
            continue
        if out:
            out.append(Segment(' '))
        out.extend(group)
    return tuple(out)


def flatten_list_item(marker: str, children: ta.Sequence[MdBlock]) -> list[ListPart]:
    """
    An item's converted children -> the item itself (inline-ish children joined into its text), then in order its nested
    lists' items one level deeper and any block-level extras.
    """

    groups: list[ta.Sequence[Segment]] = []
    trailing: list[ListPart] = []
    for child in children:
        if isinstance(child, (MdParagraph, MdHeading, MdQuote)):
            groups.append(child.spans)
        elif isinstance(child, MdList):
            trailing.extend(dc.replace(it, depth=it.depth + 1) for it in child.items)
        else:
            trailing.append(child)
    return [MdListItem(marker, join_span_groups(groups)), *trailing]


def assemble_list_parts(parts: ta.Iterable[ListPart]) -> list[MdBlock]:
    """Runs of items become MdLists; block-level extras pass through between them."""

    blocks: list[MdBlock] = []
    items: list[MdListItem] = []
    for part in parts:
        if isinstance(part, MdListItem):
            items.append(part)
            continue
        if items:
            blocks.append(MdList(tuple(items)))
            items = []
        blocks.append(part)
    if items:
        blocks.append(MdList(tuple(items)))
    return blocks
