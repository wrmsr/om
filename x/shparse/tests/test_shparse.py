import dataclasses as dc
import io
import re

import pytest

from omcore import check

from ..braces import split_braces
from ..errors import Error
from ..langs import LANG_BASH
from ..langs import LANG_MIR_BSD_KORN
from ..langs import LANG_POSIX
from ..langs import LANG_ZSH
from ..nodes import COL_MAX
from ..nodes import LINE_MAX
from ..nodes import OFFSET_MAX
from ..nodes import ArithmCmd
from ..nodes import BinaryArithm
from ..nodes import BinaryCmd
from ..nodes import Block
from ..nodes import BraceExp
from ..nodes import CallExpr
from ..nodes import CaseClause
from ..nodes import CmdSubst
from ..nodes import Comment
from ..nodes import DblQuoted
from ..nodes import DeclClause
from ..nodes import ForClause
from ..nodes import FuncDecl
from ..nodes import IfClause
from ..nodes import Lit
from ..nodes import Node
from ..nodes import ParamExp
from ..nodes import Pos
from ..nodes import Subshell
from ..nodes import TestClause as ShTestClause
from ..nodes import WhileClause
from ..nodes import Word
from ..nodes import new_pos
from ..nodes import pos_add_col
from ..parser import LangError
from ..parser import ParseError
from ..parser import Parser
from ..parser import is_keyword
from ..parser import valid_name
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
from ..walk import preorder
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
    assert check.not_none(quoted.parts[1].param).value == 'name'


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
    assert check.not_none(assignments.assigns[0].name).value == 'name'
    assert check.not_none(assignments.assigns[0].value).lit() == 'value'
    assert check.not_none(assignments.assigns[1].name).value == 'arr'
    array = check.not_none(assignments.assigns[1].array)
    assert [check.not_none(elem.value).lit() for elem in array.elems] == ['one', 'two']

    call = file.stmts[1].cmd
    assert isinstance(call, CallExpr)
    assert len(file.stmts[1].redirs) == 1
    heredoc = file.stmts[1].redirs[0]
    assert check.not_none(heredoc.word).lit() == 'EOF'
    assert isinstance(check.not_none(heredoc.hdoc).parts[1], ParamExp)


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


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('foo bar', ['foo', 'bar']),
        ('$foo $', ['', '$']),
        ('echo foo $$', ['echo', 'foo']),
        ('$$', []),
        ('echo foo\n$$\n', ['echo', 'foo']),
        ('echo foo; $$', ['echo', 'foo']),
        ('echo foo;$$', ['echo', 'foo']),
        ("echo '$$'", ['echo', '']),
    ],
)
def test_parse_stop_at_corpus(source, expected):
    file = Parser(stop_at='$$').parse(source)

    if not expected:
        assert file.stmts == []
        return
    call = file.stmts[0].cmd
    assert isinstance(call, CallExpr)
    assert [word.lit() for word in call.args] == expected


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        ('', False),
        ('foo', True),
        ('Foo', True),
        ('_foo', True),
        ('3foo', False),
        ('foo3', True),
    ],
)
def test_valid_name(value, expected):
    assert valid_name(value) is expected


@pytest.mark.parametrize('value', ['!', '[[', 'case', 'coproc', 'if', 'time', '{', '}'])
def test_is_keyword(value):
    assert is_keyword(value)


@pytest.mark.parametrize('value', ['', 'echo', 'foo-bar', '((foo))'])
def test_is_not_keyword(value):
    assert not is_keyword(value)


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
    assert 'must be followed by `then`' in exc_info.value.text

    with pytest.raises(ParseError) as exc_info:
        Parser().parse_arithmetic('3 +')
    assert exc_info.value.pos.string() == '1:3'
    assert '`+` must be followed by an expression' in exc_info.value.text

    with pytest.raises(LangError) as lang_exc_info:
        Parser(lang=LANG_POSIX).parse('arr=(one two)')
    assert lang_exc_info.value.feature == 'arrays'
    assert lang_exc_info.value.lang_used == LANG_POSIX
    assert lang_exc_info.value.langs == [LANG_BASH, LANG_MIR_BSD_KORN, LANG_ZSH]

    recovered = Parser(recover_errors=2).parse('(foo |')
    subshell = recovered.stmts[0].cmd
    assert isinstance(subshell, Subshell)
    assert subshell.rparen.is_recovered()
    binary = subshell.stmts[0].cmd
    assert isinstance(binary, BinaryCmd)
    assert check.not_none(binary.y).pos().is_recovered()


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('foo\n', False),
        ('foo;', False),
        ('\n', False),
        ('badsyntax)', False),
        ("foo 'incomp", True),
        ('foo "incomp', True),
        ('foo ${incomp', True),
        ("foo; 'incomp", True),
        ('foo; "incomp', True),
        (' (incomp', True),
    ],
)
def test_parse_error_incomplete(source, expected):
    try:
        Parser().parse(source)
    except ParseError as exc:
        assert exc.incomplete is expected  # noqa: PT017
    else:
        assert not expected


def _count_recovered(value):
    if isinstance(value, Pos):
        return int(value.is_recovered())
    if dc.is_dataclass(value):
        return sum(_count_recovered(getattr(value, field.name)) for field in dc.fields(value))
    if isinstance(value, list):
        return sum(_count_recovered(item) for item in value)
    return 0


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('foo;', 0),
        ('foo', 0),
        ("'incomp", 1),
        ("foo; 'incomp", 1),
        ('{ incomp', 1),
        ('(incomp', 1),
        ('(incomp; foo', 1),
        ('$(incomp', 1),
        ('((incomp', 1),
        ('$((incomp', 1),
        ('$[incomp', 1),
        ('if foo', 3),
        ('if foo; then bar', 1),
        ('for i in 1 2 3; echo $i; done', 1),
        ('"incomp', 1),
        ('`incomp', 1),
        ('incomp >', 1),
        ('${incomp', 1),
        ('incomp | ', 1),
        ('incomp || ', 1),
        ('incomp && ', 1),
        ('(one | { two >', 3),
        ('(one > ; two | ); { three', 3),
    ],
)
def test_parse_recover_errors(source, expected):
    file = Parser(recover_errors=3).parse(source)

    assert file.stmts
    assert not file.stmts[0].pos().is_recovered()
    assert _count_recovered(file) == expected

    def check_positions(node):
        if node is None:
            return True
        for pos in (node.pos(), node.end()):
            assert not (pos.is_valid() and pos.is_recovered())
            if not pos.is_valid():
                assert (pos.offset(), pos.line(), pos.col()) == (0, 0, 0)
        return True

    walk(file, check_positions)


def test_parse_recovery_does_not_hide_fatal_syntax_errors():
    with pytest.raises(ParseError):
        Parser(recover_errors=3).parse('badsyntax)')


def test_input_name_and_position_edge_cases():
    with pytest.raises(ParseError) as exc_info:
        Parser().parse('(', 'some-file.sh')
    assert str(exc_info.value) == 'some-file.sh:1:1: `(` must be followed by a statement list'

    file = Parser().parse('`\\\\foo`\n\x00foo\x00bar\n')
    call = file.stmts[0].cmd
    assert isinstance(call, CallExpr)
    command_substitution = call.args[0].parts[0]
    assert isinstance(command_substitution, CmdSubst)
    assert command_substitution.stmts
    inner_call = command_substitution.stmts[0].cmd
    assert isinstance(inner_call, CallExpr)
    literal = inner_call.args[0].parts[0]
    assert isinstance(literal, Lit)
    assert literal.value == '\\foo'
    assert literal.pos().string() == '1:3'
    assert literal.end().string() == '1:7'
    assert file.stmts[1].pos().string() == '2:2'
    assert file.stmts[1].end().string() == '2:9'


@pytest.mark.parametrize(
    ('pos', 'amount', 'expected_string', 'expected_offset'),
    [
        (new_pos(10, 5, 3), 2, '5:5', 12),
        (new_pos(10, 5, 3), -2, '5:1', 8),
        (new_pos(10, 5, 0), 2, '5:?', 12),
        (new_pos(10, 5, COL_MAX), 2, '5:?', 12),
        (new_pos(10, 5, 1), -2, '5:?', 8),
        (new_pos(OFFSET_MAX, 5, 3), 2, '5:5', OFFSET_MAX),
        (new_pos(0, 1, 1), -2, '1:?', 0),
    ],
)
def test_pos_add_col(pos, amount, expected_string, expected_offset):
    result = pos_add_col(pos, amount)

    assert result.is_valid()
    assert result.string() == expected_string
    assert result.offset() == expected_offset


@pytest.mark.parametrize(
    'source',
    [
        'echo a\u0080b',
        "echo 'a\u0080b'",
        'echo "a\u0080b"',
        'echo a\u0081b',
        "echo 'a\u0081b'",
        'echo "a\u0081b"',
        'echo a\ufffeb',
        'echo a\uffffb',
    ],
)
def test_parse_high_control_and_noncharacter_runes(source):
    Parser().parse(source)


def test_node_end_positions():
    file = Parser().parse('declare -A x=([index]=)')
    declaration = file.stmts[0].cmd
    assert isinstance(declaration, DeclClause)
    assert check.not_none(declaration.args[1].array).elems[0].end().offset() == 22

    file = Parser(keep_comments=True).parse('# lead\nfoo # trail\n')
    assert file.end().offset() == 18

    file = Parser().parse('declare a[1]')
    declaration = file.stmts[0].cmd
    assert isinstance(declaration, DeclClause)
    assert declaration.args[0].end().offset() == 12

    file = Parser(lang=LANG_MIR_BSD_KORN).parse('for i in a; { b; }')
    clause = file.stmts[0].cmd
    assert isinstance(clause, ForClause)
    assert clause.end().offset() == 18

    file = Parser(lang=LANG_MIR_BSD_KORN).parse('case x { a) b ;; }')
    case_clause = file.stmts[0].cmd
    assert isinstance(case_clause, CaseClause)
    assert case_clause.end().offset() == 18


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('\n' * LINE_MAX + 'foo; bar', None),
        ('\n' * LINE_MAX + ')', '?:1: `)` can only be used to close a subshell'),
        ('\n' * (LINE_MAX + 5) + ')', '?:1: `)` can only be used to close a subshell'),
        (' ' * COL_MAX + ')', '1:?: `)` can only be used to close a subshell'),
        (' ' * (COL_MAX + 5) + '\n)', '2:1: `)` can only be used to close a subshell'),
        ('\n' * (LINE_MAX - 1) + ')', f'{LINE_MAX}:1: `)` can only be used to close a subshell'),
        (' ' * (COL_MAX - 1) + ')', f'1:{COL_MAX}: `)` can only be used to close a subshell'),
    ],
)
def test_parse_position_overflow(source, expected):
    if expected is None:
        Parser().parse(source)
    else:
        with pytest.raises(ParseError) as exc_info:
            Parser().parse(source)
        assert str(exc_info.value) == expected


def test_zsh_nested_parameter_expansions():
    file = Parser(lang=LANG_ZSH).parse('${${foo#head}%tail} ${#"${foo}"} ${$(echo footail)%tail}')

    call = file.stmts[0].cmd
    assert isinstance(call, CallExpr)
    first = call.args[0].parts[0]
    assert isinstance(first, ParamExp)
    assert isinstance(first.nested_param, ParamExp)
    assert check.not_none(check.not_none(first.nested_param.exp).op).string() == '#'
    assert check.not_none(check.not_none(first.exp).op).string() == '%'
    second = call.args[1].parts[0]
    assert isinstance(second, ParamExp)
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


def test_walk_if_clause_comments_and_preorder():
    source = 'if a; then\n\tb\n# document the else\nelse\n\tc\n# document the fi\nfi\n'
    file = Parser(keep_comments=True).parse(source)
    comments = [node.text for node in preorder(file) if isinstance(node, Comment)]
    assert comments == [' document the else', ' document the fi']

    file = Parser(keep_comments=True).parse('echo ${foo:-bar}; { baz >f; } # comment')
    walked = []

    def visit(node):
        if node is not None:
            walked.append((type(node), node.pos().offset()))
        return True

    walk(file, visit)
    assert [(type(node), node.pos().offset()) for node in preorder(file)] == walked
    assert [(type(node), node.pos().offset()) for node in list(preorder(file))[:3]] == walked[:3]


def test_walk_rejects_an_unexpected_node_type():
    class NewNode(Node):
        def pos(self):
            return Pos()

        def end(self):
            return Pos()

    with pytest.raises(TypeError):
        walk(NewNode(), lambda node: True)


@pytest.mark.parametrize(
    ('value', 'lang', 'expected'),
    [
        ('', LANG_BASH, "''"),
        ('\a', LANG_BASH, r"$'\a'"),
        ('\b', LANG_BASH, r"$'\b'"),
        ('\f', LANG_BASH, r"$'\f'"),
        ('\n', LANG_BASH, r"$'\n'"),
        ('\r', LANG_BASH, r"$'\r'"),
        ('\t', LANG_BASH, r"$'\t'"),
        ('\v', LANG_BASH, r"$'\v'"),
        ('plain', LANG_BASH, 'plain'),
        ('hello world', LANG_BASH, "'hello world'"),
        ("a'b", LANG_BASH, '"a\'b"'),
        ('\a\b\f\n\r\t\v', LANG_BASH, r"$'\a\b\f\n\r\t\v'"),
        ('\x1b\x1caaa', LANG_BASH, r"$'\x1b\x1caaa'"),
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
        ('posix\n', LANG_POSIX, 5, QUOTE_ERR_POSIX),
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


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('a{b', False),
        ('a}b', False),
        ('{a,b{c,d}', True),
        ('{a{b', False),
        ('a{}', False),
        ('a{b}', False),
        ('a{b,c}', True),
        ('a{à,世界}', True),
        ('a{b,c}d{e,f}g', True),
        ('a{b{x,y},c}d', True),
        ('a{1,2,3,4,5}', True),
        ('a{1..', False),
        ('a{1..4', False),
        ('a{1.4}', False),
        ('{a,b}{1..4', True),
        ('a{1..4}', True),
        ('a{1..2}b{4..5}c', True),
        ('a{1..f}', False),
        ('a{c..f}', True),
        ('a{H..K}', True),
        ('a{-..f}', False),
        ('a{3..-}', False),
        ('a{1..10..3}', True),
        ('a{1..4..0}', True),
        ('a{4..1}', True),
        ('a{4..1..-2}', True),
        ('a{4..1..1}', True),
        ('{1..005}', True),
        ('{0001..05..2}', True),
        ('{0..1}', True),
        ('{00..2}', True),
        ('{01..10}', True),
        ('{-03..3..3}', True),
        ('a{1..10..-3}', True),
        ('a{10..1..3}', True),
        ('a{d..k..3}', True),
        ('a{d..k..n}', False),
        ('a{k..d..-2}', True),
        ('{1..1}', True),
        ('{1,2..3}', True),
        ('{1..2,3}', True),
        ('{1..2..3,4}', True),
        ('a{1..2..3..4}', False),
        (r'a\{1,2}', False),
        ('a{9223372036854775808..9}', False),
    ],
)
def test_split_braces_corpus(source, expected):
    word = Word(parts=[Lit(value=source)])

    split_braces(word)

    def contains_brace_exp(value):
        if isinstance(value, BraceExp):
            return True
        if isinstance(value, Word):
            return any(contains_brace_exp(part) for part in value.parts)
        return False

    assert contains_brace_exp(word) is expected
