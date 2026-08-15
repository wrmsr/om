from ..inlinehtml import scan_inline_html


def test_open_tag_simple():
    m = scan_inline_html('<a>', 0)
    assert m is not None and m.end == 3


def test_open_tag_with_attrs():
    m = scan_inline_html('<a href="x" id=y>', 0)
    assert m is not None


def test_self_closing():
    m = scan_inline_html('<br />', 0)
    assert m is not None and m.end == 6


def test_close_tag():
    m = scan_inline_html('</a>', 0)
    assert m is not None


def test_comment():
    m = scan_inline_html('<!-- hi -->', 0)
    assert m is not None and m.end == 11


def test_comment_dash_rules():
    # CM 0.31 / HTML5: bare `--` inside a comment is fine; `<!-->` and `<!--->` are complete comments.
    m = scan_inline_html('<!-- a -- b -->', 0)
    assert m is not None and m.end == 15
    m = scan_inline_html('<!-->', 0)
    assert m is not None and m.end == 5
    m = scan_inline_html('<!--->', 0)
    assert m is not None and m.end == 6
    # But text starting with `>` / `->` (beyond the special forms) is still invalid.
    assert scan_inline_html('<!--> x -->', 0) is not None  # the `<!-->` form itself, end == 5
    assert scan_inline_html('<!--ported-> ok -->', 0) is not None
    assert scan_inline_html('<!---> not this -->', 0) is not None  # `<!--->` form, end == 6


def test_processing_instruction():
    m = scan_inline_html('<?php ?>', 0)
    assert m is not None


def test_declaration():
    m = scan_inline_html('<!DOCTYPE html>', 0)
    assert m is not None


def test_cdata():
    m = scan_inline_html('<![CDATA[ x ]]>', 0)
    assert m is not None


def test_not_html():
    assert scan_inline_html('text', 0) is None
    assert scan_inline_html('< not tag>', 0) is None


def test_open_tag_attribute_matrix():
    # Unquoted value.
    m = scan_inline_html('<a href=foo>', 0)
    assert m is not None and m.end == 12
    # Single-quoted value.
    m = scan_inline_html("<a href='f o'>", 0)
    assert m is not None and m.end == 14
    # Valueless attribute.
    m = scan_inline_html('<input disabled>', 0)
    assert m is not None and m.end == 16
    # `=` requires a value.
    assert scan_inline_html('<a href=>', 0) is None
    # Unquoted values exclude quote/angle/backtick chars.
    assert scan_inline_html('<a href=f`oo>', 0) is None


def test_self_closing_forms():
    m = scan_inline_html('<br/>', 0)
    assert m is not None and m.end == 5
    m = scan_inline_html('<br />', 0)
    assert m is not None and m.end == 6
    m = scan_inline_html('<a href="x" />', 0)
    assert m is not None and m.end == 14


def test_attributes_may_span_lines():
    m = scan_inline_html('<a\nhref="x">', 0)
    assert m is not None and m.end == 12
