"""
List-machine edge semantics: tight/loose blank attribution, empty items, marker splits, lazy remainders, and the
verbatim-leaf guard. Shapes here were cross-checked against markdown-it / the CM spec.
"""
from .... import pdcmark as m
from ...options import GFM
from ...rendering.html import render_html


def _html(src: str, options=None) -> str:
    return render_html(m.parse(src, options) if options is not None else m.parse(src))


# Tight / loose blank attribution


def test_blank_in_nested_item_loosens_only_inner():
    assert _html('- a\n  - b\n\n    c\n- d\n') == (
        '<ul>\n<li>a\n<ul>\n<li>\n<p>b</p>\n<p>c</p>\n</li>\n</ul>\n</li>\n<li>d</li>\n</ul>\n'
    )


def test_blank_before_outer_content_loosens_outer_only():
    assert _html('- a\n  - b\n\n  c\n') == (
        '<ul>\n<li>\n<p>a</p>\n<ul>\n<li>b</li>\n</ul>\n<p>c</p>\n</li>\n</ul>\n'
    )


def test_blank_inside_fence_stays_tight():
    assert _html('- a\n- ```\n  b\n\n  ```\n- c\n') == (
        '<ul>\n<li>a</li>\n<li>\n<pre><code>b\n\n</code></pre>\n</li>\n<li>c</li>\n</ul>\n'
    )


def test_blank_inside_nested_blockquote_stays_tight():
    assert _html('* a\n  > b\n  >\n* c\n') == (
        '<ul>\n<li>a\n<blockquote>\n<p>b</p>\n</blockquote>\n</li>\n<li>c</li>\n</ul>\n'
    )


def test_blank_interior_to_indented_code_stays_tight():
    assert _html('-     b\n\n      c\n- d\n') == (
        '<ul>\n<li>\n<pre><code>b\n\nc\n</code></pre>\n</li>\n<li>d</li>\n</ul>\n'
    )


def test_blank_between_items_loosens():
    assert _html('- a\n\n- b\n') == '<ul>\n<li>\n<p>a</p>\n</li>\n<li>\n<p>b</p>\n</li>\n</ul>\n'


def test_blank_before_nested_list_loosens_outer():
    assert _html('- a\n\n  - b\n') == (
        '<ul>\n<li>\n<p>a</p>\n<ul>\n<li>b</li>\n</ul>\n</li>\n</ul>\n'
    )


def test_trailing_blank_stays_tight():
    assert _html('- a\n- b\n\n') == '<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n'


# Empty items


def test_empty_marker_lines_stay_tight():
    assert _html('- foo\n-\n- bar\n') == '<ul>\n<li>foo</li>\n<li></li>\n<li>bar</li>\n</ul>\n'


def test_empty_item_then_blank_ends_item():
    assert _html('-\n\n  foo\n') == '<ul>\n<li></li>\n</ul>\n<p>foo</p>\n'


def test_empty_item_cannot_interrupt_paragraph():
    assert _html('foo\n*\n\nfoo\n1.\n') == '<p>foo\n*</p>\n<p>foo\n1.</p>\n'


def test_empty_item_in_lazy_position_interrupts():
    assert _html('> foo\n*\n') == '<blockquote>\n<p>foo</p>\n</blockquote>\n<ul>\n<li></li>\n</ul>\n'


# Marker splits


def test_different_ordered_delimiter_splits_list():
    assert _html('1. foo\n2. bar\n3) baz\n') == (
        '<ol>\n<li>foo</li>\n<li>bar</li>\n</ol>\n<ol start="3">\n<li>baz</li>\n</ol>\n'
    )


def test_different_bullet_splits_list():
    assert _html('- foo\n* bar\n') == '<ul>\n<li>foo</li>\n</ul>\n<ul>\n<li>bar</li>\n</ul>\n'


def test_ordered_nonone_interrupts_in_lazy_position():
    assert _html('> foo\n2. bar\n') == (
        '<blockquote>\n<p>foo</p>\n</blockquote>\n<ol start="2">\n<li>bar</li>\n</ol>\n'
    )


def test_ordered_nonone_does_not_interrupt_paragraph():
    assert _html('foo\n2. bar\n') == '<p>foo\n2. bar</p>\n'


# Lazy continuation remainder


def test_lazy_continuation_strips_matched_markers():
    assert _html('> 1. > Blockquote\n> continued here.\n') == (
        '<blockquote>\n<ol>\n<li>\n<blockquote>\n<p>Blockquote\ncontinued here.</p>\n'
        '</blockquote>\n</li>\n</ol>\n</blockquote>\n'
    )


# Verbatim leaves swallow container markers


def test_fence_content_keeps_container_markers():
    assert _html('```\n> x\n- y\n```\n') == '<pre><code>&gt; x\n- y\n</code></pre>\n'


def test_fence_in_item_keeps_quote_lines():
    assert _html('- ```\n  > b\n  ```\n') == (
        '<ul>\n<li>\n<pre><code>&gt; b\n</code></pre>\n</li>\n</ul>\n'
    )


# Tables end at the first blank line


def test_blank_line_closes_table():
    out = _html('| a |\n| --- |\n| 1 |\n\nx\n', GFM)
    assert out.endswith('</table>\n<p>x</p>\n')
    assert '<td>x</td>' not in out


# Tab carry across container / code boundaries


def test_tab_carry_materializes_in_item_code():
    assert _html('- foo\n\n\t\tbar\n') == (
        '<ul>\n<li>\n<p>foo</p>\n<pre><code>  bar\n</code></pre>\n</li>\n</ul>\n'
    )


def test_tab_carry_materializes_in_quote_code():
    assert _html('>\t\tfoo\n') == '<blockquote>\n<pre><code>  foo\n</code></pre>\n</blockquote>\n'


def test_tab_carry_materializes_after_marker():
    assert _html('-\t\tfoo\n') == '<ul>\n<li>\n<pre><code>  foo\n</code></pre>\n</li>\n</ul>\n'


# Blank lines inside code blocks keep their post-indent whitespace


def test_indented_code_interior_blank_keeps_spaces():
    assert _html('    chunk1\n      \n      chunk2\n') == (
        '<pre><code>chunk1\n  \n  chunk2\n</code></pre>\n'
    )


def test_fenced_code_blank_lines_keep_spaces():
    assert _html('```\n\n  \n```\n') == '<pre><code>\n  \n</code></pre>\n'


# HTML block starts on a fresh line inside a list item


def test_html_block_newline_inside_item():
    assert _html('- <div>\n- foo\n') == '<ul>\n<li>\n<div>\n</li>\n<li>foo</li>\n</ul>\n'
