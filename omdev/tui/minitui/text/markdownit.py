"""
The markdown-it streaming backend: `markdown_it` tokens (via omdev's incremental parser) driving the shared MdBlock
model.

Strictly quarantined optional dependency: markdown_it is proxy-imported through omdev's incparse; availability is probed
without importing. omdev's `IncrementalMarkdownParser` supplies the stable/unstable token split - its stability rule
(everything before the second-to-last top-level token) is markdown-it's own block structure, so settling fidelity comes
from the real parser. The same flattenings as the pdcmark backend apply.
"""
import functools
import importlib.util
import typing as ta

from omcore import dataclasses as dc

from ....markdownit import incparse
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


@functools.cache
def markdown_it_available() -> bool:
    return importlib.util.find_spec('markdown_it') is not None


_INLINE_OPEN_STYLES: ta.Mapping[str, str] = {
    'strong_open': 'md.bold',
    'em_open': 'md.italic',
    's_open': 'md.strike',
    'link_open': 'md.link',
}


def _link_aware_spans(tokens: ta.Sequence[ta.Any]) -> tuple[Segment, ...]:
    """Inline child tokens -> styled spans, appending '(url)' spans when links close."""

    spans: list[Segment] = []
    stack: list[tuple[str | None, str | None]] = []  # (style, url-to-append-on-close)

    def top() -> str | None:
        return next((s for s, _ in reversed(stack) if s is not None), None)

    for tok in tokens or ():
        t = tok.type
        if t == 'link_open':
            stack.append(('md.link', dict(tok.attrs or {}).get('href')))
        elif t in _INLINE_OPEN_STYLES:
            stack.append((_INLINE_OPEN_STYLES[t], None))
        elif t.endswith('_close') and stack:
            _, url = stack.pop()
            if url:
                spans.append(Segment(f' ({url})', 'md.link.url'))
        elif t == 'text':
            if tok.content:
                spans.append(Segment(tok.content, top()))
        elif t == 'code_inline':
            spans.append(Segment(tok.content, 'md.code.inline'))
        elif t in ('softbreak', 'hardbreak'):
            spans.append(Segment(' '))
        elif t == 'image':
            alt = tok.content or 'image'
            spans.append(Segment(alt, 'md.link'))
            if (src := dict(tok.attrs or {}).get('src')):
                spans.append(Segment(f' ({src})', 'md.link.url'))
        elif t == 'html_inline':
            if tok.content:
                spans.append(Segment(tok.content.replace('\n', ' ')))
    return tuple(spans)


class _TokenWalker:
    def __init__(self, tokens: ta.Sequence[ta.Any]) -> None:
        super().__init__()

        self._tokens = list(tokens)
        self._i = 0

    def _next(self) -> ta.Any | None:
        if self._i >= len(self._tokens):
            return None
        tok = self._tokens[self._i]
        self._i += 1
        return tok

    def _inline_until(self, close_type: str) -> tuple[Segment, ...]:
        spans: tuple[Segment, ...] = ()
        while (tok := self._next()) is not None:
            if tok.type == close_type:
                break
            if tok.type == 'inline':
                spans = spans + _link_aware_spans(tok.children or ())
        return spans

    def _children_until(self, close_type: str) -> list[MdBlock]:
        blocks: list[MdBlock] = []
        while (tok := self._next()) is not None:
            if tok.type == close_type:
                break
            if (converted := self._convert_one(tok)) is not None:
                blocks.extend(converted)
        return blocks

    def _list_items(self, close_type: str, start: int | None) -> list[MdListItem]:
        items: list[MdListItem] = []
        index = start
        while (tok := self._next()) is not None:
            if tok.type == close_type:
                break
            if tok.type == 'list_item_open':
                children = self._children_until('list_item_close')
                groups: list[ta.Sequence[Segment]] = []
                nested: list[MdListItem] = []
                for child in children:
                    if isinstance(child, MdParagraph):
                        groups.append(child.spans)
                    elif isinstance(child, MdList):
                        nested.extend(dc.replace(it, depth=it.depth + 1) for it in child.items)
                    elif isinstance(child, (MdHeading, MdQuote)):
                        groups.append(child.spans)
                joined: list[Segment] = []
                for gi, group in enumerate(groups):
                    if gi:
                        joined.append(Segment(' '))
                    joined.extend(group)
                marker = f'{index}.' if index is not None else '-'
                if index is not None:
                    index += 1
                items.append(MdListItem(marker, tuple(joined)))
                items.extend(nested)
        return items

    def _convert_one(self, tok: ta.Any) -> list[MdBlock] | None:  # noqa: C901
        t = tok.type

        if t == 'heading_open':
            level = int(tok.tag[1:]) if tok.tag[1:].isdigit() else 1
            return [MdHeading(level, self._inline_until('heading_close'))]
        if t == 'paragraph_open':
            return [MdParagraph(self._inline_until('paragraph_close'))]
        if t == 'fence':
            return [MdCode((tok.info or '').strip(), tuple(tok.content.rstrip('\n').split('\n')))]
        if t == 'code_block':
            return [MdCode('', tuple(tok.content.rstrip('\n').split('\n')))]
        if t == 'blockquote_open':
            children = self._children_until('blockquote_close')
            groups = [c.spans for c in children if isinstance(c, MdParagraph)]
            extras = [c for c in children if not isinstance(c, MdParagraph)]
            joined: list[Segment] = []
            for gi, group in enumerate(groups):
                if gi:
                    joined.append(Segment(' '))
                joined.extend(group)
            out: list[MdBlock] = []
            if joined:
                out.append(MdQuote(tuple(joined)))
            out.extend(extras)
            return out
        if t == 'bullet_list_open':
            return [MdList(tuple(self._list_items('bullet_list_close', None)))]
        if t == 'ordered_list_open':
            start = int(dict(tok.attrs or {}).get('start', 1))
            return [MdList(tuple(self._list_items('ordered_list_close', start)))]
        if t == 'hr':
            return [MdRule()]
        if t == 'html_block':
            content = tok.content.rstrip('\n')
            return [MdCode('html', tuple(content.split('\n')))] if content.strip() else []

        return None

    def convert(self) -> list[MdBlock]:
        blocks: list[MdBlock] = []
        while (tok := self._next()) is not None:
            if (converted := self._convert_one(tok)) is not None:
                blocks.extend(converted)
        return blocks


def tokens_to_blocks(tokens: ta.Sequence[ta.Any]) -> list[MdBlock]:
    return _TokenWalker(tokens).convert()


##


class MarkdownItStream(MarkdownStreamBackend):
    def __init__(self) -> None:
        super().__init__()

        self._inc = incparse.IncrementalMarkdownParser()
        self._new_stable: list[ta.Any] = []
        self._unstable: list[ta.Any] = []

    def feed(self, chunk: str) -> None:
        if not chunk:
            return
        out = self._inc.feed2(chunk)
        self._new_stable.extend(out.new_stable)
        self._unstable = list(out.unstable)

    def pop_settled(self) -> list[MdBlock]:
        tokens, self._new_stable = self._new_stable, []
        return tokens_to_blocks(tokens)

    def tail_blocks(self) -> list[MdBlock]:
        return tokens_to_blocks(self._unstable)

    def finalize(self) -> list[MdBlock]:
        out = self._inc.feed2('')
        self._new_stable.extend(out.new_stable)
        tokens = [*self._new_stable, *out.unstable]
        self._new_stable = []
        self._unstable = []
        # Reusable per the backend contract: a fresh parser for the next stream cycle.
        self._inc = incparse.IncrementalMarkdownParser()
        return tokens_to_blocks(tokens)
