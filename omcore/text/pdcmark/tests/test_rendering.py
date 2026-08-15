"""Focused HTML-renderer regressions (escaping contexts, href encoding, decoded scanner output)."""
from .... import dataclasses as dc
from ... import pdcmark as m
from ..options import COMMONMARK
from ..options import GFM
from ..rendering.html import render_html


def _html(src: str, options=None) -> str:
    return render_html(m.parse(src, options) if options is not None else m.parse(src)).strip()


def test_body_text_keeps_quotes():
    assert _html('a "quoted" word') == '<p>a "quoted" word</p>'


def test_code_span_keeps_quotes():
    assert _html('`say "hi"`') == '<p><code>say "hi"</code></p>'


def test_attribute_escapes_quotes():
    assert _html('[a](/u "ti\\"tle")') == '<p><a href="/u" title="ti&quot;tle">a</a></p>'


def test_href_percent_encodes_non_ascii():
    assert _html('[l](/föö)') == '<p><a href="/f%C3%B6%C3%B6">l</a></p>'


def test_entities_decode_in_dest_and_title():
    assert _html('[l](/f&ouml; "t&ouml;")') == '<p><a href="/f%C3%B6" title="tö">l</a></p>'


def test_fence_info_decodes_escapes_and_entities():
    assert _html('``` foo\\+b&ouml;\nx\n```') == (
        '<pre><code class="language-foo+bö">x\n</code></pre>'
    )


def test_unknown_entity_stays_literal():
    assert _html('&notanentity; and &copy') == '<p>&amp;notanentity; and &amp;copy</p>'


def test_intraword_strikethrough_renders():
    assert _html('a~~b~~c', GFM) == '<p>a<del>b</del>c</p>'


def test_comment_with_double_dash_is_raw_html():
    assert _html('foo <!-- a -- b --> bar') == '<p>foo <!-- a -- b --> bar</p>'


def test_prescan_resolves_forward_refs():
    opts = dc.replace(COMMONMARK, prescan_refdefs=True)
    assert _html('[ref]\n\n[ref]: /url', opts) == '<p><a href="/url">ref</a></p>'
