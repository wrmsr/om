"""
Adversarial input tests - the link-reference expansion-bomb that motivates pulldown's `link_ref_expansion_limit` (see
pulldown-cmark issue #844 and parse.rs::ParserInner). Without the fuel guard, an input that repeatedly references the
same large refdef can balloon output size quadratically.
"""
from ..... import dataclasses as dc
from .... import pdcmark as m
from ...options import COMMONMARK
from ...rendering.html import render_html


def test_link_ref_expansion_bomb_stays_bounded():
    # `[x]: <large>` followed by N copies of `[x]` would, without fuel, produce N copies of <large> in the rendered
    # output. With fuel, expansion bails after the configured budget.
    big = 'A' * 5000
    refs = '\n[x]\n' * 200
    src = f'[x]: {big}\n{refs}'

    # Cap fuel low so we definitely exhaust.
    opts = dc.replace(COMMONMARK, link_ref_expansion_min=10_000)

    out = render_html(m.parse(src, opts))

    # Output size should be bounded by something like fuel + overhead.
    assert len(out) < 50_000, f'output ballooned to {len(out)} bytes - fuel guard not effective'


def test_link_ref_resolves_when_fuel_available():
    # Sanity: with default fuel the same shape but fewer refs works fine.
    src = '[x]: /url\n\n[x]\n'
    out = render_html(m.parse(src))
    assert '/url' in out


# Deep nesting must degrade gracefully (bounded output / capped containers), never raise RecursionError.


def test_deep_emphasis_nesting_no_crash():
    events = m.parse('*' * 2000 + 'a' + '*' * 2000)
    render_html(events)


def test_deep_bracket_nesting_no_crash():
    events = m.parse('[' * 2000 + 'a' + ']' * 2000)
    render_html(events)


def test_container_depth_is_capped():
    events = m.parse('>' * 5000 + ' hi')
    bq_starts = sum(
        1 for e in events if isinstance(e, m.Start) and isinstance(e.tag, m.BlockQuote)
    )
    assert bq_starts == COMMONMARK.max_container_depth


def test_paren_nesting_cap_configurable():
    deep = '[a](' + '(' * 40 + 'u' + ')' * 40 + ')'
    assert '<a' not in render_html(m.parse(deep))
    opts = dc.replace(COMMONMARK, max_nested_parens=64)
    assert '<a' in render_html(m.parse(deep, opts))
