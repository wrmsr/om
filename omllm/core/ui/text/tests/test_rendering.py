import io

from omcore import lang
from omdev.tui import rich

from ..plain import PlainTextRenderer
from ..rendering import TextRenderingOptions
from ..rich import RichJsonStyles
from ..rich import RichTextDisplayer
from ..rich import RichTextRenderer
from ..types import DiffText
from ..types import JsonText
from ..types import JsonTextStyle
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


def _span_styles(t):
    return {t.plain[sp.start:sp.end]: str(sp.style) for sp in t.spans}


def test_rich_json_colorized_by_default():
    r = RichTextRenderer().render(JsonText({'a': 'x'}))

    assert isinstance(r, rich.Text)
    assert r.plain == '{"a": "x"}'

    spans = _span_styles(r)
    assert spans['"a"'] == 'blue'
    assert spans['"x"'] == 'green'


def test_rich_json_styles_injectable():
    r = RichTextRenderer(
        json_styles=RichJsonStyles(
            key='magenta',
            number='cyan',
            literal='bold red',
        ),
    ).render(JsonText({'a': [1, True, None]}))

    spans = _span_styles(r)
    assert spans['"a"'] == 'magenta'
    assert spans['1'] == 'cyan'
    assert spans['true'] == 'bold red'
    assert spans['null'] == 'bold red'


def test_rich_json_merges_inherited_style():
    r = RichTextRenderer().render(Text.of(JsonText({'a': 1})).style(bold=True))

    spans = _span_styles(r)
    assert spans['"a"'] == 'bold blue'
    assert spans['{'] == 'bold'


def test_rich_text_displayer():
    buf = io.StringIO()

    d = RichTextDisplayer(
        console=rich.Console(file=buf, force_terminal=False, width=80),
    )

    lang.sync_await(d.display_text(Text.of('hi ', JsonText({'a': 1}))))

    assert buf.getvalue() == 'hi {"a": 1}'


def test_json_node_style():
    t = JsonText({'a': [1, True]}, JsonTextStyle(mode='compact', five=True))

    assert str(t) == '{"a":[1,true]}'
    assert PlainTextRenderer(TextRenderingOptions(density='pretty')).render(t) == '{"a":[1,true]}'


def test_json_renderer_default_style():
    t = Text.of(JsonText({'a': [1]}))

    r = PlainTextRenderer(TextRenderingOptions(json_style=JsonTextStyle(mode='compact')))
    assert r.render(t) == '{"a":[1]}'


def test_json_node_style_overrides_renderer_default():
    t = JsonText({'a': [1]}, JsonTextStyle(mode='pretty'))

    r = PlainTextRenderer(TextRenderingOptions(json_style=JsonTextStyle(mode='compact', five=True)))
    assert r.render(t) == '{\n  "a": [\n    1\n  ]\n}'


def test_json_style_merge():
    assert JsonTextStyle(mode='compact', five=True).merge(JsonTextStyle(mode='pretty')) == \
        JsonTextStyle(mode='pretty', five=True)
    assert JsonTextStyle.DEFAULT.merge(JsonTextStyle.DEFAULT) == JsonTextStyle.DEFAULT
