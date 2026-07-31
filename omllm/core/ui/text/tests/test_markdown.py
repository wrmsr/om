from omcore import marshal as msh

from ..types import MarkdownText
from ..types import StrText
from ..types import Text


def test_markdown_renders_as_block():
    m = MarkdownText('# hi')

    assert str(m) == '# hi\n'
    assert str(MarkdownText('# hi\n')) == '# hi\n'
    assert str(Text.of('status: ', m, ' done')) == 'status: \n# hi\n done'


def test_empty_markdown_is_falsy():
    m = MarkdownText('')

    assert not m
    assert str(m) == ''
    assert Text.of('x', m, 'y') == StrText('xy')


def test_markdown_marshal():
    m = MarkdownText('# hi\n')

    v = msh.marshal(m, Text)
    assert v == {'markdown': '# hi\n'}
    assert msh.unmarshal(v, Text) == m
