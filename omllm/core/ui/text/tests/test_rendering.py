from omcore.text import styled as st

from ..plain import PlainTextRenderer
from ..rendering import TextRenderingOptions
from ..styled import StyledJsonStyles
from ..styled import StyledTextBlock
from ..styled import StyledTextRenderer
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


def test_styled_inline_only_returns_text():
    r = StyledTextRenderer().render(Text.of('a').style(color='red'))

    assert r.is_inline
    assert r.inline == st.StyledText('a', (
        st.StyleSpan.of(0, 1, 'text.color.red'),
    ))


def test_styled_blocks_are_retained():
    r = StyledTextRenderer().render(Text.of('a', MarkdownText('# h').style(italic=True), 'b'))

    assert r.inline is None
    assert r.parts == (
        st.StyledText('a'),
        StyledTextBlock(
            MarkdownText('# h'),
            (st.StylePatch(italic=True),),
        ),
        st.StyledText('b'),
    )


def test_styled_compact_degrades_blocks():
    r = StyledTextRenderer(TextRenderingOptions(density='compact')).render(
        Text.of('a ', MarkdownText('# h'), ' b'),
    )

    assert r.inline is not None
    assert r.inline.plain == 'a # h b'


def _run_styles(t: st.StyledText) -> dict[str, tuple[st.StyleRef, ...]]:
    return {run.text: run.styles for run in t.runs()}


def test_styled_json_has_semantic_styles_by_default():
    r = StyledTextRenderer().render(JsonText({'a': ['x', 1, True, None]}))

    assert r.inline is not None
    assert r.inline.plain == '{"a": ["x", 1, true, null]}'

    runs = _run_styles(r.inline)
    assert runs['"a"'] == (st.StyleName('json.key'),)
    assert runs['"x"'] == (st.StyleName('json.string'),)
    assert runs['1'] == (st.StyleName('json.number'),)
    assert runs['true'] == (st.StyleName('json.literal'),)
    assert runs['null'] == (st.StyleName('json.literal'),)


def test_styled_json_styles_injectable():
    r = StyledTextRenderer(
        json_styles=StyledJsonStyles(
            key='test.key',
            string=None,
            number=st.StylePatch(underline=True),
            literal='test.literal',
        ),
    ).render(JsonText({'a': ['x', 1, True]}))

    assert r.inline is not None
    runs = _run_styles(r.inline)
    assert runs['"a"'] == (st.StyleName('test.key'),)
    assert next(run.styles for run in r.inline.runs() if '"x"' in run.text) == ()
    assert runs['1'] == (st.StylePatch(underline=True),)
    assert runs['true'] == (st.StyleName('test.literal'),)


def test_styled_json_merges_inherited_style():
    r = StyledTextRenderer().render(Text.of(JsonText({'a': 1})).style(color='red', bold=True))

    assert r.inline is not None
    runs = _run_styles(r.inline)
    base = (st.StyleName('text.color.red'), st.StylePatch(bold=True))
    assert runs['"a"'] == (*base, st.StyleName('json.key'))
    assert runs['{'] == base


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
