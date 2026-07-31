from omdev.tui import rich

from ..plain import PlainTextRenderer
from ..rendering import TextRenderingOptions
from ..rich import RichTextRenderer
from ..types import DiffText
from ..types import JsonText
from ..types import MarkdownText
from ..types import Text


def test_plain_compact_degrades_blocks():
    t = Text.of(
        'a ',
        MarkdownText('# hi\nthere'),
        ' b ',
        DiffText(old='x\n', new='y\n', path='f.py'),
    )

    s = PlainTextRenderer(TextRenderingOptions(density='compact')).render(t)
    assert s == 'a # hi there b f.py: +1 -1'


def test_plain_json_density():
    t = Text.of(JsonText({'a': [1]}))

    assert PlainTextRenderer().render(t) == '{"a": [1]}'
    assert PlainTextRenderer(TextRenderingOptions(density='compact')).render(t) == '{"a":[1]}'
    assert '\n' in PlainTextRenderer(TextRenderingOptions(density='pretty')).render(t)


def test_rich_inline_only_returns_text():
    r = RichTextRenderer().render(Text.of('a').style(color='red'))

    assert isinstance(r, rich.Text)
    assert r.plain == 'a'


def test_rich_blocks_return_group():
    r = RichTextRenderer().render(Text.of('a', MarkdownText('# h'), 'b'))

    assert isinstance(r, rich.Group)


def test_rich_compact_degrades_blocks():
    r = RichTextRenderer(TextRenderingOptions(density='compact')).render(
        Text.of('a ', MarkdownText('# h'), ' b'),
    )

    assert isinstance(r, rich.Text)
    assert r.plain == 'a # h b'
