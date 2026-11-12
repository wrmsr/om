"""Regressions from upstream b93cbc0..1c1a312; see _devdocs/05_Upstream.md for the audit."""
import os.path

import pytest

from ..events import Code
from ..events import End
from ..events import Item
from ..events import Link
from ..events import List
from ..events import Start
from ..options import Options
from ..parsing import parse
from ..rendering.html import render_html
from ..streaming.parser import StreamingParser
from .spec_runner import load_spec_file


def _options(case, *, prescan_refdefs=False):
    flags = set(case.keyword.removeprefix('example').replace('|', '').split())
    assert flags <= {'ENABLE_TABLES', 'ENABLE_STRIKETHROUGH', 'ENABLE_TASKLISTS', 'ENABLE_GFM'}
    return Options(
        prescan_refdefs=prescan_refdefs,
        tables='ENABLE_TABLES' in flags,
        strikethrough='ENABLE_STRIKETHROUGH' in flags,
        tasklists='ENABLE_TASKLISTS' in flags,
        gfm_blockquote_kinds='ENABLE_GFM' in flags,
    )


@pytest.fixture(scope='module')
def upstream_cases():
    return load_spec_file(os.path.join(os.path.dirname(__file__), 'upstream.txt'))


def test_upstream_html(upstream_cases):
    for case in upstream_cases:
        src = case.markdown.replace('␀', '\0')
        assert render_html(parse(src, _options(case, prescan_refdefs=True))) == case.expected_html, case


@pytest.mark.parametrize('chunk_size', [1, 3, 17])
def test_upstream_streaming(upstream_cases, chunk_size):
    for case in upstream_cases:
        src = case.markdown.replace('␀', '\0')
        opts = _options(case)
        parser = StreamingParser(opts)
        committed: list = []
        for pos in range(0, len(src), chunk_size):
            out = parser.feed(src[pos:pos + chunk_size])
            committed.extend(out.committed)
            prefix = src[:pos + chunk_size]
            assert committed + list(out.tentative) == parse(prefix, opts), (case, pos)
        committed.extend(parser.finish().committed)
        assert committed == parse(src, opts), case
        assert all(0 <= e.offset[0] <= e.offset[1] <= len(src) for e in committed), case


@pytest.mark.parametrize(('src', 'html'), [
    ('\ufeff# Heading\n', '<h1>Heading</h1>\n'),
    ('\ufeff[a]: /url\n\n[a]\n', '<p><a href="/url">a</a></p>\n'),
    ('a\ufeffb\n', '<p>a\ufeffb</p>\n'),
    ('a\n\n\ufeffb\n', '<p>a</p>\n<p>\ufeffb</p>\n'),
    ('\ufeff', ''),
    ('```\rcode\rblock\r\n```\n', '<pre><code>code\nblock\n</code></pre>\n'),
    ('<!S\r:', '<!S\n:\n'),
    ('a\r', '<p>a</p>\n'),
    ('```\r', '<pre><code></code></pre>\n'),
    ('```\na\n ', '<pre><code>a\n \n</code></pre>\n'),
    ('```\n  ', '<pre><code>  \n</code></pre>\n'),
    ('```\na\n \t ', '<pre><code>a\n \t \n</code></pre>\n'),
    ('> ```\n> a\n>', '<blockquote>\n<pre><code>a\n\n</code></pre>\n</blockquote>\n'),
    ('- ```\n  a\n   ', '<ul>\n<li>\n<pre><code>a\n \n</code></pre>\n</li>\n</ul>\n'),
    ('> <!-- x\n>', '<blockquote>\n<!-- x\n\n</blockquote>\n'),
    ('>\t<div>\n>\tx\n', '<blockquote>\n  <div>\n  x\n</blockquote>\n'),
    ('- <pre\n  ', '<ul>\n<li>\n<pre\n\n</li>\n</ul>\n'),
    ('    a\0b', '<pre><code>a\ufffdb\n</code></pre>\n'),
    ('```la\0ng\nx\n```', '<pre><code class="language-la\ufffdng">x\n</code></pre>\n'),
    ('[a](b\0c)', '<p><a href="b%EF%BF%BDc">a</a></p>\n'),
])
def test_upstream_eof_and_normalization(src, html):
    expected = parse(src)
    assert render_html(expected) == html
    # Every possible two-chunk split includes CR/LF boundaries, the BOM, and the unterminated last line.
    for split in range(len(src) + 1):
        parser = StreamingParser()
        committed: list = []
        for chunk in (src[:split], src[split:]):
            out = parser.feed(chunk)
            committed.extend(out.committed)
        committed.extend(parser.finish().committed)
        assert committed == expected, split


def test_bom_offsets():
    events = parse('\ufeff# Heading\n')
    assert isinstance(events[0], Start)
    assert isinstance(events[-1], End)
    assert events[0].offset == (1, 11)
    assert events[-1].offset == (1, 11)


@pytest.mark.parametrize(('src', 'expected_starts'), [
    ('*     indented code block\n\t+ nested list\n', [0, 0, 27, 27]),
    ('*     indented code block\n  + nested list\n', [0, 0, 28, 28]),
    ('- a\r\n\t1. b\r\n', [0, 0, 6, 6]),
    ('> - a\n>\t- b\n', [2, 2, 8, 8]),
])
def test_tab_indented_list_offsets(src, expected_starts):
    starts = [e.offset[0] for e in parse(src) if isinstance(e, Start) and isinstance(e.tag, (List, Item))]
    assert starts == expected_starts


@pytest.mark.parametrize('src', ['`` a\n  `b`\n  ``', '`a\n\t b`', '`a\r\n   b`', '> `a\r\n>   b`'])
def test_multiline_code_offsets(src):
    codes = [e for e in parse(src) if isinstance(e, Code)]
    assert len(codes) == 1
    assert codes[0].text == ('a `b`' if src.startswith('``') else 'a b')
    assert codes[0].offset == (src.index('`'), len(src))


def test_collapsed_reference_offsets():
    src = '[a]: /url\n\n[a][]'
    events = parse(src)
    links = [e for e in events if isinstance(e, (Start, End)) and isinstance(e.tag, Link)]
    assert len(links) == 2
    assert all(e.offset == (11, len(src)) for e in links)


def test_task_marker_is_tentative_until_block_closes():
    opts = Options(tasklists=True)
    parser = StreamingParser(opts)
    out = parser.feed('- [x] task\n')
    committed = list(out.committed)
    assert render_html(committed + list(out.tentative)) == render_html(parse('- [x] task\n', opts))
    out = parser.feed('  ---\n')
    committed.extend(out.committed)
    committed.extend(parser.finish().committed)
    assert committed == parse('- [x] task\n  ---\n', opts)
    assert '<input' not in render_html(committed)
