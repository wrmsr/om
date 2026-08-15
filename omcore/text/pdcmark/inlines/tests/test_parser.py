"""Inline pipeline event-emission tests: full tokenize → links → emphasis → events, checked as event sequences."""
from .... import pdcmark as m
from ...options import GFM


def _summarize(events) -> list[str]:
    out = []
    for ev in events:
        name = type(ev).__name__
        if name in ('Start', 'End'):
            out.append(f'{name}({type(ev.tag).__name__})')
        elif name in ('Text', 'Code', 'InlineHtml'):
            out.append(f'{name}({ev.text!r})')
        else:
            out.append(name)
    return out


def _inline_events(src: str, options=None):
    events = m.parse(src, options) if options is not None else m.parse(src)
    # Strip the enclosing Start/End(Paragraph).
    return events[1:-1]


def test_emphasis_inside_link_inside_strong():
    assert _summarize(_inline_events('**a [b *c*](/u) d**')) == [
        'Start(Strong)',
        "Text('a ')",
        'Start(Link)',
        "Text('b ')",
        'Start(Emphasis)',
        "Text('c')",
        'End(Emphasis)',
        'End(Link)',
        "Text(' d')",
        'End(Strong)',
    ]


def test_autolink_triple():
    assert _summarize(_inline_events('<http://x.test>')) == [
        'Start(Link)',
        "Text('http://x.test')",
        'End(Link)',
    ]


def test_email_autolink_gets_mailto():
    events = _inline_events('<a@b.test>')
    start = events[0]
    assert type(start).__name__ == 'Start' and start.tag.dest_url == 'mailto:a@b.test'


def test_strikethrough_events():
    assert _summarize(_inline_events('a ~~b~~ c', GFM)) == [
        "Text('a ')",
        'Start(Strikethrough)',
        "Text('b')",
        'End(Strikethrough)',
        "Text(' c')",
    ]


def test_breaks_and_code():
    assert _summarize(_inline_events('a `c`  \nb\nd')) == [
        "Text('a ')",
        "Code('c')",
        'HardBreak',
        "Text('b')",
        'SoftBreak',
        "Text('d')",
    ]


def test_nested_strong_in_emphasis():
    assert _summarize(_inline_events('***x***')) == [
        'Start(Emphasis)',
        'Start(Strong)',
        "Text('x')",
        'End(Strong)',
        'End(Emphasis)',
    ]


def test_image_alt_flattening_events():
    # The renderer flattens; the event stream itself keeps the nested structure.
    assert _summarize(_inline_events('![a *b*](/img)')) == [
        'Start(Image)',
        "Text('a ')",
        'Start(Emphasis)',
        "Text('b')",
        'End(Emphasis)',
        'End(Image)',
    ]
