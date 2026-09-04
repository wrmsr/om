import html
import re

import pytest

from omcore.text import styled as st

from ..html import HtmlTextRenderer
from ..html import render_html_text
from ..html import render_markdown_html
from ..rendering import TextRenderingOptions
from ..types import DiffText
from ..types import JsonText
from ..types import MarkdownText
from ..types import Text


PRE_WRAP = '<span style="white-space:pre-wrap">'


def _visible_text(rendered: str) -> str:
    return html.unescape(re.sub(r'<[^>]*>', '', rendered))


def test_empty():
    assert HtmlTextRenderer().render() == ''
    assert HtmlTextRenderer().render('') == ''


def test_inline_styles_are_baked_in():
    assert HtmlTextRenderer().render(Text.of('a').style(color='red', bold=True)) == (
        f'{PRE_WRAP}<span style="color:#d17e92;font-weight:bold">a</span></span>'
    )


def test_inline_text_is_escaped_and_whitespace_preserving():
    assert HtmlTextRenderer().render('<b>&"x"\n  y') == f'{PRE_WRAP}&lt;b&gt;&amp;"x"\n  y</span>'


def test_json_semantic_styles():
    assert HtmlTextRenderer().render(JsonText({'a': ['x', 1, True]})) == (
        f'{PRE_WRAP}'
        '{<span style="color:#57a5e2">"a"</span>: '
        '[<span style="color:#8ad4a1">"x"</span>, '
        '<span style="color:#ffc473">1</span>, '
        '<span style="color:#57a5e2">true</span>]}'
        '</span>'
    )


def test_theme_is_injectable_and_unknown_names_are_plain():
    theme = st.StyleTheme({
        'text.color.red': st.StylePatch(fg=st.parse_rgb('#ff0000'), underline=True),
    })

    assert HtmlTextRenderer(theme=theme).render(
        Text.of('a').style(color='red'),
        Text.of('b').style(color='blue'),
    ) == f'{PRE_WRAP}<span style="color:#ff0000;text-decoration-line:underline">a</span>b</span>'


def test_markdown_block_between_inline_runs():
    assert HtmlTextRenderer().render('before', MarkdownText('# Hi\n\n*x*'), 'after') == (
        f'{PRE_WRAP}before</span>'
        '<div style="white-space:normal"><h1>Hi</h1>\n<p><em>x</em></p>\n</div>'
        f'{PRE_WRAP}after</span>'
    )


def test_single_trailing_newline_before_block_is_dropped():
    assert HtmlTextRenderer().render('before\n', MarkdownText('x')) == (
        f'{PRE_WRAP}before</span><div style="white-space:normal"><p>x</p>\n</div>'
    )

    assert HtmlTextRenderer().render('before\n\n', MarkdownText('x')) == (
        f'{PRE_WRAP}before\n</span><div style="white-space:normal"><p>x</p>\n</div>'
    )

    assert HtmlTextRenderer().render('\n', MarkdownText('x')) == '<div style="white-space:normal"><p>x</p>\n</div>'


def test_markdown_block_inherits_style():
    assert HtmlTextRenderer().render(MarkdownText('x').style(italic=True, color='red')) == (
        '<div style="white-space:normal;color:#d17e92;font-style:italic"><p>x</p>\n</div>'
    )


def test_markdown_raw_html_is_literalized():
    rendered = render_markdown_html('<script>alert(1)</script>\n\nx <b>y</b> z')

    assert rendered == (
        '<pre><code class="language-html">&lt;script&gt;alert(1)&lt;/script&gt;\n</code></pre>\n'
        '<p>x &lt;b&gt;y&lt;/b&gt; z</p>\n'
    )
    assert '<script>' not in rendered
    assert '<b>' not in rendered


def test_markdown_gfm_and_forward_references():
    rendered = render_markdown_html('see [it][ref] and ~~no~~\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n[ref]: http://x/')

    assert '<a href="http://x/">it</a>' in rendered
    assert '<del>no</del>' in rendered
    assert '<table>' in rendered


def test_diff_block_is_a_styled_pre_document():
    rendered = HtmlTextRenderer(diff_width=60).render(
        'before',
        DiffText(old='a\nb\nc\n', new='a\nB\nc\n', path='f.py'),
        'after',
    )

    assert rendered.startswith(f'{PRE_WRAP}before</span><pre style="color:#f8f8f2;background-color:#0d0f0b">')
    assert rendered.endswith(f'</pre>{PRE_WRAP}after</span>')
    assert '<span style=' in rendered

    visible = _visible_text(rendered)
    assert 'f.py (1 additions, 1 removals)' in visible
    assert all(len(line) == 60 for line in visible.splitlines()[1:-1] if line)


def test_diff_block_source_text_is_literal_and_inherits_flags():
    rendered = HtmlTextRenderer(diff_width=60).render(
        DiffText(old='<b>x</b>\n', new='<i>x</i>\n', path='t.txt').style(italic=True, color='red'),
    )

    assert rendered.startswith('<pre style="color:#f8f8f2;background-color:#0d0f0b;font-style:italic">')
    assert '<b>' not in rendered
    assert '<i>' not in rendered

    visible = _visible_text(rendered)
    assert '<b>x</b>' in visible
    assert '<i>x</i>' in visible


def test_diff_width_is_validated():
    with pytest.raises(Exception):  # noqa: B017 PT011
        HtmlTextRenderer(diff_width=19)


def test_compact_density_degrades_blocks_inline():
    rendered = HtmlTextRenderer(TextRenderingOptions(density='compact')).render(
        'a ',
        MarkdownText('# h'),
        ' b ',
        DiffText(old='x\n', new='y\n', path='f.py'),
    )

    assert rendered == f'{PRE_WRAP}a # h b f.py: +1 -1</span>'


def test_fragments_concatenate():
    r = HtmlTextRenderer()

    assert r.render('hel') + r.render('lo') == f'{PRE_WRAP}hel</span>{PRE_WRAP}lo</span>'


def test_render_html_text():
    assert render_html_text('x') == f'{PRE_WRAP}x</span>'
