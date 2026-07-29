from omcore import marshal as msh

from ..rich import ui_text_to_rich_text
from ..text import DiffText
from ..text import Text


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

    rt = ui_text_to_rich_text(d)
    assert '+B' in rt.plain

    m = msh.marshal(d, Text)
    d2 = msh.unmarshal(m, Text)
    assert d2 == d
    assert msh.marshal(d2, Text) == m


def test_diff_text_composes():
    t = Text.of([
        'changing f.py:\n',
        DiffText(old='x\n', new='y\n'),
    ])

    s = str(t)
    assert s.startswith('changing f.py:\n')
    assert '-x' in s
    assert '+y' in s
