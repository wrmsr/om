from omcore import marshal as msh

from ..styled import StyledTextBlock
from ..styled import StyledTextRenderer
from ..types import DiffText
from ..types import StrText
from ..types import Text


def test_diff_text():
    d = DiffText(
        old='a\nb\nc\n',
        new='a\nB\nc\n',
        path='f.py',
    )

    s = str(d)
    assert '--- f.py' in s
    assert '-b' in s
    assert '+B' in s

    rendered = StyledTextRenderer().render(d)
    assert rendered.parts == (StyledTextBlock(d),)

    m = msh.marshal(d, Text)
    d2 = msh.unmarshal(m, Text)
    assert d2 == d
    assert msh.marshal(d2, Text) == m


def test_empty_diff_is_falsey():
    d = DiffText(old='a\n', new='a\n')

    assert not d
    assert str(d) == ''
    assert Text.of('x', d, 'y') == StrText('xy')


def test_diff_marshal_omits_none_path():
    d = DiffText(old='x\n', new='y\n')

    m = msh.marshal(d, Text)
    assert m == {'diff': {'old': 'x\n', 'new': 'y\n'}}
    assert msh.unmarshal(m, Text) == d


def test_diff_text_composes():
    t = Text.of([
        'changing f.py:\n',
        DiffText(old='x\n', new='y\n'),
    ])

    s = str(t)
    assert s.startswith('changing f.py:\n')
    assert '-x' in s
    assert '+y' in s
