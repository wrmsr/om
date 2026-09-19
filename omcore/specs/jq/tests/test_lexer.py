import pytest

from ..errors import JqLexError
from ..lexing import Interpolation
from ..lexing import lex


##


def test_lex_core_and_comment_continuation():
    tokens = lex('.foo // 1 # hello\\\ncontinued\n| $x')
    assert [(token.kind, token.value) for token in tokens] == [
        ('.', '.'),
        ('IDENT', 'foo'),
        ('//', '//'),
        ('NUMBER', 1),
        ('|', '|'),
        ('VARIABLE', 'x'),
        ('EOF', None),
    ]


def test_lex_string_interpolation():
    token = lex('"a=\\(.x + "(") z"')[0]
    assert token.kind == 'STRING'
    assert token.value[0] == 'a='
    assert isinstance(token.value[1], Interpolation)
    assert token.value[1].source == '.x + "("'
    assert token.value[2] == ' z'


@pytest.mark.parametrize('source', ['"unterminated', '$', '"\\(1"', '@csv', '1e400'])
def test_lex_errors(source):
    with pytest.raises(JqLexError):
        lex(source)
