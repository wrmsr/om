"""Link / image resolution tests - the pass between tokenization and emphasis."""
from omcore import dataclasses as dc

from .... import pdcmark as m
from ...blocks.leaves import BufferedLine
from ...blocks.refdefs import LinkDef
from ...blocks.refdefs import RefDefs
from ...brokenlinks import BrokenLink
from ...brokenlinks import BrokenLinkResolution
from ...brokenlinks import BrokenLinkResolver
from ...events import LinkType
from ...options import COMMONMARK
from ...rendering.html import render_html
from ..links import Fuel
from ..links import _flatten_to_text  # noqa
from ..links import resolve_links
from ..nodes import LinkGroup
from ..nodes import TextNode
from ..tokenize import tokenize_block


def _resolve(text: str, refdefs: RefDefs | None = None, fuel: Fuel | None = None):
    tokenized = tokenize_block((BufferedLine(text=text, line_start=0, line_next=len(text) + 1),))
    return resolve_links(
        tokenized.nodes,
        refdefs=refdefs if refdefs is not None else RefDefs(),
        fuel=fuel if fuel is not None else Fuel(remaining=100_000),
        retokenize=tokenized.retokenize,
    )


def _html(text: str) -> str:
    return render_html(m.parse(text)).strip()


# Group formation


def test_inline_link_group():
    nodes = _resolve('[foo](/url "title")')
    assert len(nodes) == 1
    g = nodes[0]
    assert isinstance(g, LinkGroup)
    assert g.link_type is LinkType.INLINE and g.dest_url == '/url' and g.title == 'title'
    assert not g.is_image
    assert [n.text for n in g.children if isinstance(n, TextNode)] == ['foo']


def test_image_group():
    nodes = _resolve('![alt](/img)')
    g = nodes[0]
    assert isinstance(g, LinkGroup) and g.is_image and g.dest_url == '/img'


def test_reference_and_collapsed_and_shortcut():
    refdefs = RefDefs()
    refdefs.add('r', LinkDef(dest='/u', title=''))
    for src, lt in [
        ('[foo][r]', LinkType.REFERENCE),
        ('[r][]', LinkType.COLLAPSED),
        ('[r]', LinkType.SHORTCUT),
    ]:
        nodes = _resolve(src, refdefs=refdefs)
        g = nodes[0]
        assert isinstance(g, LinkGroup) and g.link_type is lt and g.dest_url == '/u', src


def test_unmatched_closer_is_text():
    nodes = _resolve('no ] here')
    assert all(isinstance(n, TextNode) for n in nodes)
    assert ''.join(n.text for n in nodes) == 'no ] here'


def test_unmatched_opener_is_text():
    nodes = _resolve('[dangling')
    assert all(isinstance(n, TextNode) for n in nodes)
    assert ''.join(n.text for n in nodes) == '[dangling'


# The no-nested-links rule


def test_no_nested_links():
    # The inner link wins; the outer brackets become literal text.
    assert _html('[a [b](/u) c](/v)') == '<p>[a <a href="/u">b</a> c](/v)</p>'


def test_image_inside_link_ok():
    assert _html('[![alt](/img)](/url)') == '<p><a href="/url"><img src="/img" alt="alt" /></a></p>'


def test_failed_outer_suffix_becomes_link():
    # CM 528 shape: the outer link fails (contains a link), its [ref] suffix re-parses as a fresh link.
    src = '[ref]: /uri\n\n[foo [bar](/uri)][ref]'
    assert _html(src) == '<p>[foo <a href="/uri">bar</a>]<a href="/uri">ref</a></p>'


def test_failed_suffix_interior_gets_inline_parse():
    # A `]` with no opener re-parses its consumed suffix, so emphasis inside it still resolves.
    assert _html('](*em*)') == '<p>](<em>em</em>)</p>'


# Label derivation


def test_flatten_label_keeps_delims():
    # Refdef label `foo *bar*` must match a shortcut use with literal asterisks (emphasis is not yet resolved).
    refdefs = RefDefs()
    refdefs.add('foo *bar*', LinkDef(dest='/u', title=''))
    nodes = _resolve('[foo *bar*]', refdefs=refdefs)
    g = nodes[0]
    assert isinstance(g, LinkGroup) and g.dest_url == '/u'


def test_flatten_includes_code_and_nested_groups():
    tokenized = tokenize_block((BufferedLine(text='a `co` *b* c', line_start=0, line_next=13),))
    assert _flatten_to_text(tokenized.nodes) == 'a co *b* c'


# Fuel


def test_fuel_exhaustion_blocks_resolution():
    refdefs = RefDefs()
    refdefs.add('r', LinkDef(dest='/' + 'x' * 100, title=''))
    nodes = _resolve('[r]', refdefs=refdefs, fuel=Fuel(remaining=10))
    assert all(isinstance(n, TextNode) for n in nodes)


# Broken-link resolver


class _Resolver(BrokenLinkResolver):
    def __init__(self) -> None:
        super().__init__()

        self.seen: list[BrokenLink] = []

    def resolve(self, link: BrokenLink) -> BrokenLinkResolution | None:
        self.seen.append(link)
        if link.reference == 'known':
            return BrokenLinkResolution(dest_url='/fallback', title='t')
        return None


def test_broken_link_resolver_supplies_destination():
    r = _Resolver()
    opts = dc.replace(COMMONMARK, broken_link_resolver=r)
    events = m.parse('[known]', opts)
    links = [e.tag for e in events if isinstance(e, m.Start) and isinstance(e.tag, m.Link)]
    assert len(links) == 1
    link = links[0]
    assert isinstance(link, m.Link)
    assert link.dest_url == '/fallback' and link.link_type is LinkType.SHORTCUT_UNKNOWN
    assert [b.reference for b in r.seen] == ['known']


def test_broken_link_resolver_none_leaves_text():
    r = _Resolver()
    opts = dc.replace(COMMONMARK, broken_link_resolver=r)
    out = render_html(m.parse('[unknown]', opts))
    assert '<a' not in out and '[unknown]' in out
