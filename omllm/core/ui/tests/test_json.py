from ..json import render_json_texts
from ..json import render_obj_json_text
from ..text import ConcatText
from ..text import DiffText
from ..text import JsonText
from ..text import MarkdownText
from ..text import StyleText
from ..text import Text
from ..text import TextStyle


def test_render():
    t = render_obj_json_text({
        'hi': ['there', '!'],
    })

    assert str(t) == '{"hi": ["there", "!"]}'


def test_render_json_texts_replaces_json_nodes():
    t = Text.of('a ', JsonText({'k': 1}), ' b')

    r = render_json_texts(t)

    assert '"k"' in str(r)
    assert isinstance(r, ConcatText)
    assert not any(isinstance(c, JsonText) for c in r.l)


def test_render_json_texts_passes_through_foreign_leaves():
    d = DiffText(old='x\n', new='y\n')
    m = MarkdownText('# hi')

    t = Text.of('a ', JsonText([1]), ' b ', d, m)

    r = render_json_texts(t)

    assert isinstance(r, ConcatText)
    assert d in list(r.l)
    assert m in list(r.l)


def test_render_json_texts_merges_styles():
    t = StyleText(JsonText('hi'), TextStyle(bold=True))

    r = render_json_texts(t)

    assert isinstance(r, StyleText)
    assert r.y == TextStyle(color='green', bold=True)
    assert str(r) == '"hi"'
