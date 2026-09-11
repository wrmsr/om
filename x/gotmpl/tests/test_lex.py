from ..lex import Lexer
from ..lex import Token
from ..lex import TokenType


def _tokens(source, *, left='{{', right='}}'):
    lexer = Lexer('test', source, left_delim=left, right_delim=right)
    tokens = []
    while True:
        token = lexer.next_token()
        tokens.append(token)
        if token.typ in (TokenType.EOF, TokenType.ERROR):
            return tokens


def test_unicode_identifiers_and_byte_positions():
    tokens = _tokens('é{{.世界}}')
    assert [(token.typ, token.pos, token.val) for token in tokens] == [
        (TokenType.TEXT, 0, 'é'),
        (TokenType.LEFT_DELIM, 2, '{{'),
        (TokenType.FIELD, 4, '.世界'),
        (TokenType.RIGHT_DELIM, 11, '}}'),
        (TokenType.EOF, 13, ''),
    ]


def test_quoted_escapes_are_fully_scanned():
    tokens = _tokens(r"""{{"a\"b\\c" '\''}}""")
    assert [(token.typ, token.val) for token in tokens] == [
        (TokenType.LEFT_DELIM, '{{'),
        (TokenType.STRING, r'''"a\"b\\c"'''),
        (TokenType.SPACE, ' '),
        (TokenType.CHAR_CONSTANT, "'\\''"),
        (TokenType.RIGHT_DELIM, '}}'),
        (TokenType.EOF, ''),
    ]


def test_custom_delimiters():
    tokens = _tokens('before $$ .Value @@ after', left='$$', right='@@')
    assert [(token.typ, token.val) for token in tokens] == [
        (TokenType.TEXT, 'before '),
        (TokenType.LEFT_DELIM, '$$'),
        (TokenType.SPACE, ' '),
        (TokenType.FIELD, '.Value'),
        (TokenType.SPACE, ' '),
        (TokenType.RIGHT_DELIM, '@@'),
        (TokenType.TEXT, ' after'),
        (TokenType.EOF, ''),
    ]


def test_comment_line_tracking():
    tokens = _tokens('{{/*\ncomment\n*/}}\n{{.Value}}')
    assert tokens[-4].typ == TokenType.LEFT_DELIM
    assert tokens[-4].line == 4


def test_token_strings_use_go_quoting():
    assert str(Token(TokenType.TEXT, 0, 'a\n"b', 1)) == r'"a\n\"b"'
    assert str(Token(TokenType.TEXT, 0, '世界世界', 1)) == '"世界世界"...'
