import io
import re

import pytest

from ..braces import split_braces
from ..errors import Error
from ..langs import LANG_BASH
from ..langs import LANG_MIR_BSD_KORN
from ..langs import LANG_POSIX
from ..langs import LANG_ZSH
from ..nodes import ArithmCmd
from ..nodes import BinaryArithm
from ..nodes import Block
from ..nodes import BraceExp
from ..nodes import CallExpr
from ..nodes import CaseClause
from ..nodes import DblQuoted
from ..nodes import ForClause
from ..nodes import FuncDecl
from ..nodes import IfClause
from ..nodes import Lit
from ..nodes import ParamExp
from ..nodes import Subshell
from ..nodes import TestClause as ShTestClause
from ..nodes import WhileClause
from ..nodes import Word
from ..parser import LangError
from ..parser import ParseError
from ..parser import Parser
from ..pattern import ENTIRE_STRING
from ..pattern import FILENAMES
from ..pattern import PatternSyntaxError
from ..pattern import has_meta
from ..pattern import quote_meta
from ..pattern import regexp
from ..quote import QUOTE_ERR_MKSH
from ..quote import QUOTE_ERR_NULL
from ..quote import QUOTE_ERR_POSIX
from ..quote import QuoteError
from ..quote import quote
from ..tokens import BinAritOperator
from ..walk import debug_print
from ..walk import walk


def test_parse_simple_command_and_byte_positions():
    file = Parser().parse(io.StringIO('écho "hello $name"'), 'example.sh')

    assert file.name == 'example.sh'
    assert len(file.stmts) == 1
    call = file.stmts[0].cmd
    assert isinstance(call, CallExpr)
    assert len(call.args) == 2

    command = call.args[0].parts[0]
    assert isinstance(command, Lit)
    assert command.value == 'écho'
    assert (command.pos().offset(), command.pos().line(), command.pos().col()) == (0, 1, 1)
    assert (command.end().offset(), command.end().line(), command.end().col()) == (5, 1, 6)

    quoted = call.args[1].parts[0]
    assert isinstance(quoted, DblQuoted)
    assert isinstance(quoted.parts[1], ParamExp)
    assert quoted.parts[1].param.value == 'name'


@pytest.mark.parametrize(
    ('source', 'command_type'),
    [
        ('(foo; bar)', Subshell),
        ('{ foo; }', Block),
        ('if a; then b; else c; fi', IfClause),
        ('while a; do b; done', WhileClause),
        ('for i in 1 2 3; do echo $i; done', ForClause),
        ('case $x in a|b) echo ab ;; c) echo c ;& esac', CaseClause),
        ('foo() { echo hi; }', FuncDecl),
        ('((a == 2))', ArithmCmd),
        ('[[ -n $x && $x == foo* ]]', ShTestClause),
    ],
)
def test_parse_compound_commands(source, command_type):
    file = Parser().parse(source)

    assert len(file.stmts) == 1
    assert isinstance(file.stmts[0].cmd, command_type)


def test_parse_assignments_arrays_process_substitutions_and_heredocs():
    file = Parser().parse(
        'name=value arr=(one two)\n'
        'echo <(cat input) "$name" <<EOF\n'
        'hello $name\n'
        'EOF\n',
    )

    assignments = file.stmts[0].cmd
    assert isinstance(assignments, CallExpr)
    assert assignments.assigns[0].name.value == 'name'
    assert assignments.assigns[0].value.lit() == 'value'
    assert assignments.assigns[1].name.value == 'arr'
    assert [elem.value.lit() for elem in assignments.assigns[1].array.elems] == ['one', 'two']

    call = file.stmts[1].cmd
    assert isinstance(call, CallExpr)
    assert len(file.stmts[1].redirs) == 1
    heredoc = file.stmts[1].redirs[0]
    assert heredoc.word.lit() == 'EOF'
    assert isinstance(heredoc.hdoc.parts[1], ParamExp)


def test_parse_arithmetic_precedence_and_associativity():
    expr = Parser().parse_arithmetic('a = 3, ++a, a--')

    assert isinstance(expr, BinaryArithm)
    assert expr.op == BinAritOperator.COMMA
    assert isinstance(expr.x, BinaryArithm)
    assert expr.x.op == BinAritOperator.COMMA
    assert isinstance(expr.x.x, BinaryArithm)
    assert expr.x.x.op == BinAritOperator.ASSGN

    precedence = Parser().parse_arithmetic('1 + 2 * 3 ** 4')
    assert isinstance(precedence, BinaryArithm)
    assert precedence.op == BinAritOperator.ADD
    assert isinstance(precedence.y, BinaryArithm)
    assert precedence.y.op == BinAritOperator.MUL
    assert isinstance(precedence.y.y, BinaryArithm)
    assert precedence.y.y.op == BinAritOperator.POW


def test_parse_words_document_and_stop_at():
    words = Parser().parse_words('foo "bar baz"\n$qux')

    assert len(words) == 3
    assert words[0].lit() == 'foo'
    assert isinstance(words[1].parts[0], DblQuoted)
    assert isinstance(words[2].parts[0], ParamExp)

    document = Parser().parse_document(' foo  $bar\n\n')
    assert document is not None
    assert isinstance(document.parts[1], ParamExp)

    stopped = Parser(stop_at='$$').parse('echo foo;$$ ignored')
    stopped_call = stopped.stmts[0].cmd
    assert isinstance(stopped_call, CallExpr)
    assert [word.lit() for word in stopped_call.args] == ['echo', 'foo']


def test_parser_can_be_reused_without_leaking_state():
    parser = Parser(keep_comments=True)

    first = parser.parse('# first\necho one')
    second = parser.parse('# second\necho two')

    assert first.stmts[0].comments[0].text == ' first'
    assert second.stmts[0].comments[0].text == ' second'
    first_call = first.stmts[0].cmd
    second_call = second.stmts[0].cmd
    assert isinstance(first_call, CallExpr)
    assert isinstance(second_call, CallExpr)
    assert first_call.args[1].lit() == 'one'
    assert second_call.args[1].lit() == 'two'


def test_parse_errors_language_variants_and_recovery():
    with pytest.raises(ParseError) as exc_info:
        Parser().parse('if true')
    assert exc_info.value.pos.string() == '1:1'
    assert exc_info.value.incomplete
    assert 'must be followed by then' in exc_info.value.text

    with pytest.raises(ParseError) as exc_info:
        Parser().parse_arithmetic('3 +')
    assert exc_info.value.pos.string() == '1:3'
    assert '+ must be followed by an expression' in exc_info.value.text

    with pytest.raises(LangError) as exc_info:
        Parser(lang=LANG_POSIX).parse('arr=(one two)')
    assert exc_info.value.feature == 'arrays'
    assert exc_info.value.lang_used == LANG_POSIX
    assert exc_info.value.langs == [LANG_BASH, LANG_MIR_BSD_KORN, LANG_ZSH]

    recovered = Parser(recover_errors=2).parse('(foo |')
    subshell = recovered.stmts[0].cmd
    assert isinstance(subshell, Subshell)
    assert subshell.rparen.is_recovered()
    binary = subshell.stmts[0].cmd
    assert binary.y.pos().is_recovered()


def test_zsh_nested_parameter_expansions():
    file = Parser(lang=LANG_ZSH).parse('${${foo#head}%tail} ${#"${foo}"} ${$(echo footail)%tail}')

    call = file.stmts[0].cmd
    assert isinstance(call, CallExpr)
    first = call.args[0].parts[0]
    assert isinstance(first, ParamExp)
    assert isinstance(first.nested_param, ParamExp)
    assert first.nested_param.exp.op.string() == '#'
    assert first.exp.op.string() == '%'
    second = call.args[1].parts[0]
    assert isinstance(second.nested_param, DblQuoted)

    with pytest.raises(LangError):
        Parser().parse('${${foo}}')


def test_comments_walk_and_debug_print():
    file = Parser(keep_comments=True).parse('# before\necho "$name" # after\n# last\n')

    assert [comment.text for comment in file.stmts[0].comments] == [' before', ' after']
    assert [comment.text for comment in file.last] == [' last']

    seen = []

    def visit(node):
        if node is None:
            return False
        seen.append(type(node))
        return True

    walk(file, visit)
    assert CallExpr in seen
    assert DblQuoted in seen
    assert ParamExp in seen

    out = io.StringIO()
    debug_print(out, file)
    assert out.getvalue().startswith('File {\n')
    assert 'ParamExp {' in out.getvalue()


@pytest.mark.parametrize(
    ('value', 'lang', 'expected'),
    [
        ('', LANG_BASH, "''"),
        ('plain', LANG_BASH, 'plain'),
        ('hello world', LANG_BASH, "'hello world'"),
        ("a'b", LANG_BASH, '"a\'b"'),
        ('\a\b\f\n\r\t\v', LANG_BASH, r"$'\a\b\f\n\r\t\v'"),
        ('\x1b\x1caaa', LANG_MIR_BSD_KORN, r"$'\x1b\x1c'$'aaa'"),
    ],
)
def test_quote(value, lang, expected):
    assert quote(value, lang) == expected


@pytest.mark.parametrize(
    ('value', 'lang', 'offset', 'message'),
    [
        ('null\x00', LANG_BASH, 4, QUOTE_ERR_NULL),
        ('posix\x1b', LANG_POSIX, 5, QUOTE_ERR_POSIX),
        ('mksh16\U00086199', LANG_MIR_BSD_KORN, 6, QUOTE_ERR_MKSH),
    ],
)
def test_quote_errors(value, lang, offset, message):
    error = quote(value, lang)

    assert isinstance(error, Error)
    assert isinstance(error, QuoteError)
    assert error.offset == offset
    assert error.s == message


def test_patterns():
    expression = regexp('foo/*', FILENAMES | ENTIRE_STRING)

    assert re.compile(expression).fullmatch('foo/bar')
    assert not re.compile(expression).fullmatch('foo/.hidden')
    assert has_meta(r'foo*')
    assert not has_meta(r'foo\*')
    assert quote_meta(r'foo*[bar]') == r'foo\*\[bar]'

    with pytest.raises(PatternSyntaxError):
        regexp('[z-a]', 0)


def test_split_braces():
    word = Word(parts=[Lit(value='a{b{x,y},c}d{1..3}')])

    assert split_braces(word)
    braces = [part for part in word.parts if isinstance(part, BraceExp)]
    assert len(braces) == 2
    assert [element.lit() for element in braces[0].elems] == ['', 'c']
    nested = braces[0].elems[0].parts[1]
    assert isinstance(nested, BraceExp)
    assert [element.lit() for element in nested.elems] == ['x', 'y']
    assert braces[1].sequence
    assert [element.lit() for element in braces[1].elems] == ['1', '3']
