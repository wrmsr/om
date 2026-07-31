from omcore import marshal as msh

from ..json import render_json_texts
from ..json import render_obj_json_text
from ..types import ConcatText
from ..types import DiffText
from ..types import JsonText
from ..types import JsonTextStyle
from ..types import MarkdownText
from ..types import StyleText
from ..types import Text
from ..types import TextStyle


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


def test_render_json_texts_respects_node_style():
    t = Text.of('a ', JsonText({'k': [1]}, JsonTextStyle(mode='compact')))

    assert str(render_json_texts(t)) == 'a {"k":[1]}'


def test_json_text_marshal_unwraps_without_style():
    t = JsonText([1, 'x'])

    m = msh.marshal(t, Text)
    assert m == {'json': [1, 'x']}
    assert msh.unmarshal(m, Text) == t


def test_json_text_marshal_with_style():
    t = JsonText([1], JsonTextStyle(mode='compact', five=True))

    m = msh.marshal(t, Text)
    assert m == {'json': {'v': [1], 'y': {'mode': 'compact', 'five': True}}}
    assert msh.unmarshal(m, Text) == t
