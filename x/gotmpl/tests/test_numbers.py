import pytest

from ..lex import TokenType
from ..parse import ParseError
from ..parse import Tree


@pytest.mark.parametrize(
    ('text', 'typ', 'flags', 'value'),
    [
        ('0', TokenType.NUMBER, (True, True, True, False), 0),
        ('-0', TokenType.NUMBER, (True, True, True, False), 0),
        ('+73', TokenType.NUMBER, (True, False, True, False), 73),
        ('0b10_010_01', TokenType.NUMBER, (True, True, True, False), 73),
        ('073', TokenType.NUMBER, (True, True, True, False), 0o73),
        ('0x_1p4', TokenType.NUMBER, (True, True, True, False), 16),
        ('1e19', TokenType.NUMBER, (False, True, True, False), 1e19),
        ('4i', TokenType.NUMBER, (False, False, False, True), 4j),
        ('073i', TokenType.NUMBER, (False, False, False, True), 73j),
        ('-12+0i', TokenType.COMPLEX, (True, False, True, True), -12),
        ("'パ'", TokenType.CHAR_CONSTANT, (True, True, True, False), ord('パ')),
    ],
)
def test_number_parse(text, typ, flags, value):
    number = Tree('test').new_number(0, text, typ)
    assert (number.is_int, number.is_uint, number.is_float, number.is_complex) == flags
    assert number.v == value


@pytest.mark.parametrize('text', ['+-2', '0x123.', '1e.', '0xi.', '1+2.', "'xx'"])
def test_bad_number_parse(text):
    typ = TokenType.CHAR_CONSTANT if text.startswith("'") else TokenType.NUMBER
    with pytest.raises((ParseError, ValueError)):
        Tree('test').new_number(0, text, typ)
