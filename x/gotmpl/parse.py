"""
https://github.com/golang/go/blob/3d33437c450aa74014ea1d41cd986b6ee6266984/src/text/template/parse/parse.go
"""

# Copyright 2009 The Go Authors.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#      disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#      following disclaimer in the documentation and/or other materials provided with the distribution.
#    * Neither the name of Google LLC nor the names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import math
import re
import typing as ta

from omcore import check
from omcore.text.go.quoting import UnquoteError
from omcore.text.go.quoting import unquote
from omcore.text.go.quoting import unquote_char

from .lex import LEFT_DELIM
from .lex import RIGHT_DELIM
from .lex import Lexer
from .lex import LexOptions
from .lex import Pos
from .lex import Token
from .lex import TokenType
from .nodes import ActionNode
from .nodes import BoolNode
from .nodes import BreakNode
from .nodes import ChainNode
from .nodes import CommandNode
from .nodes import CommentNode
from .nodes import ContinueNode
from .nodes import DotNode
from .nodes import ElseNode
from .nodes import EndNode
from .nodes import FieldNode
from .nodes import IfNode
from .nodes import ListNode
from .nodes import NilNode
from .nodes import Node
from .nodes import NodeType
from .nodes import NumberNode
from .nodes import PipeNode
from .nodes import RangeNode
from .nodes import StringNode
from .nodes import TemplateNode
from .nodes import TextNode
from .nodes import VariableNode
from .nodes import WithNode
from .nodes import new_identifier
from .quoting import quote_go_string


# A mode value is a set of flags (or 0). Modes control parser behavior.
MODE_PARSE_COMMENTS = 1 << 0  # parse comments and add them to AST
MODE_SKIP_FUNC_CHECK = 1 << 1  # do not check that functions are defined
MAX_STACK_DEPTH = 10_000


##


def _parse_go_int(s: str) -> int:
    sign = 1
    unsigned = s
    if unsigned.startswith(('+', '-')):
        if unsigned[0] == '-':
            sign = -1
        unsigned = unsigned[1:]
    if not unsigned:
        raise ValueError(s)
    if unsigned.startswith(('+', '-')):
        raise ValueError(s)

    base = 10
    digits = unsigned
    has_prefix = False
    if unsigned.startswith(('0x', '0X')):
        base = 16
        digits = unsigned[2:]
        has_prefix = True
    elif unsigned.startswith(('0o', '0O')):
        base = 8
        digits = unsigned[2:]
        has_prefix = True
    elif unsigned.startswith(('0b', '0B')):
        base = 2
        digits = unsigned[2:]
        has_prefix = True
    elif len(unsigned) > 1 and unsigned.startswith('0') and '.' not in unsigned:
        base = 8
        digits = unsigned[1:]
        has_prefix = True

    if has_prefix and digits.startswith('_'):
        digits = digits[1:]
    if not digits or digits.startswith('_') or digits.endswith('_') or '__' in digits:
        raise ValueError(s)
    return sign * int(digits.replace('_', ''), base)


def _parse_go_float(s: str) -> float:
    decimal = r'(?:[0-9](?:_?[0-9])*(?:\.(?:[0-9](?:_?[0-9])*)?)?|\.[0-9](?:_?[0-9])*)'
    decimal += r'(?:[eE][+-]?[0-9](?:_?[0-9])*)?'
    hex_digit = r'[0-9a-fA-F]'
    hexadecimal = (
        r'0[xX]_?'
        rf'(?:{hex_digit}(?:_?{hex_digit})*(?:\.(?:{hex_digit}(?:_?{hex_digit})*)?)?'
        rf'|\.{hex_digit}(?:_?{hex_digit})*)'
        r'[pP][+-]?[0-9](?:_?[0-9])*'
    )
    unsigned = s[1:] if s.startswith(('+', '-')) else s
    if re.fullmatch(rf'(?:{decimal}|{hexadecimal})', unsigned) is None:
        raise ValueError(s)
    clean = s.replace('_', '')
    if '0x' in clean.lower():
        value = float.fromhex(clean)
    else:
        value = float(clean)
    if not math.isfinite(value):
        raise ValueError(s)
    return value


def _parse_go_complex(s: str) -> complex:
    if not s.endswith('i'):
        raise ValueError(s)
    body = s[:-1]
    split = None
    for i, char in enumerate(body[1:], 1):
        if char in '+-' and body[i - 1] not in 'eEpP':
            split = i
    if split is None:
        value = complex(0, _parse_go_float(body))
    else:
        value = complex(_parse_go_float(body[:split]), _parse_go_float(body[split:]))
    if not math.isfinite(value.real) or not math.isfinite(value.imag):
        raise ValueError(s)
    return value


##


class ParseError(Exception):
    pass


# Tree is the representation of a single parsed template.
class Tree:
    def __init__(
        self,
        name: str,
        *funcs: dict[str, ta.Callable],
    ) -> None:
        super().__init__()

        self._name = name  # name of the template represented by the tree.
        self._funcs = list(funcs)

        self._parse_name: str = ''  # name of the top-level template during parsing, for error messages.
        self._root: ListNode | None = None  # top-level root of the tree.
        self._mode: int = 0  # parsing mode.
        self._text: str = ''  # text parsed to create the template (or its parent)

        # Parsing only; cleared after parse.
        self._lex: Lexer | None = None
        self._token: list[Token | None] = [None, None, None]  # three-token lookahead for parser.
        self._peek_count: int = 0
        self._vars: list[str] = []  # variables defined at the moment.
        self._tree_set: dict[str, Tree] = {}
        self._action_line: int = 0  # line of left delim starting action
        self._range_depth: int = 0
        self._stack_depth: int = 0

        self._left_delim = LEFT_DELIM
        self._right_delim = RIGHT_DELIM

    @property
    def name(self) -> str:
        return self._name

    @property
    def parse_name(self) -> str:
        return self._parse_name

    @property
    def root(self) -> ListNode | None:
        return self._root

    @property
    def mode(self) -> int:
        return self._mode

    @mode.setter
    def mode(self, value: int) -> None:
        self._mode = value

    @property
    def left_delim(self) -> str:
        return self._left_delim

    @property
    def right_delim(self) -> str:
        return self._right_delim

    def copy(self) -> Tree:
        tree = Tree(self._name)
        tree._parse_name = self._parse_name
        tree._root = self._root.copy_list() if self._root is not None else None
        tree._text = self._text
        tree._left_delim = self._left_delim
        tree._right_delim = self._right_delim
        return tree

    #

    def new_list(self, pos: Pos) -> ListNode:
        return ListNode(tree=self, type=NodeType.LIST, pos=pos)

    def new_text(self, pos: Pos, text: str) -> TextNode:
        return TextNode(tree=self, type=NodeType.TEXT, pos=pos, text=text)

    def new_comment(self, pos: Pos, text: str) -> CommentNode:
        return CommentNode(tree=self, type=NodeType.COMMENT, pos=pos, text=text)

    def new_pipeline(self, pos: Pos, line: int, vars: list[VariableNode]) -> PipeNode:  # noqa
        return PipeNode(tree=self, type=NodeType.PIPE, pos=pos, line=line, decl=vars)

    def new_action(self, pos: Pos, line: int, pipe: PipeNode) -> ActionNode:
        return ActionNode(tree=self, type=NodeType.ACTION, pos=pos, line=line, pipe=pipe)

    def new_command(self, pos: Pos) -> CommandNode:
        return CommandNode(tree=self, type=NodeType.COMMAND, pos=pos)

    def new_variable(self, pos: Pos, ident: str) -> VariableNode:
        return VariableNode(tree=self, type=NodeType.VARIABLE, pos=pos, ident=ident.split('.'))

    def new_dot(self, pos: Pos) -> DotNode:
        return DotNode(tree=self, type=NodeType.DOT, pos=pos)

    def new_nil(self, pos: Pos) -> NilNode:
        return NilNode(tree=self, type=NodeType.NIL, pos=pos)

    def new_field(self, pos: Pos, ident: str) -> FieldNode:
        return FieldNode(
            tree=self,
            type=NodeType.FIELD,
            pos=pos,
            ident=ident[1:].split('.'),
        )  # [1:] to drop leading period  # noqa

    def new_chain(self, pos: Pos, node: Node) -> ChainNode:
        return ChainNode(tree=self, type=NodeType.CHAIN, pos=pos, node=node)

    def new_bool(self, pos: Pos, is_true: bool) -> BoolNode:
        return BoolNode(tree=self, type=NodeType.BOOL, pos=pos, is_true=is_true)

    def new_number(self, pos: Pos, text: str, typ: TokenType) -> NumberNode:
        n = NumberNode(tree=self, type=NodeType.NUMBER, pos=pos, text=text)

        if typ == TokenType.CHAR_CONSTANT:
            rune, _, tail = unquote_char(text[1:], text[0])
            if tail != "'":
                raise ParseError(f'malformed character constant: {text}')
            n.int64 = ord(rune)
            n.is_int = True
            n.uint64 = ord(rune)
            n.is_uint = True
            n.float64 = float(ord(rune))
            n.is_float = True
            return n

        elif typ == TokenType.COMPLEX:
            # fmt.Sscan can parse the pair, so let it do the work.
            n.complex128 = _parse_go_complex(text)
            n.is_complex = True
            n.simplify()
            return n

        # Imaginary constants can only be complex unless they are zero.
        if text.endswith('i'):
            try:
                n.complex128 = complex(0, _parse_go_float(text[:-1]))
            except ValueError:
                pass
            else:
                n.is_complex = True
                n.simplify()
                return n

        # Do integer tests first so we get 0x123 etc.
        try:
            integer = _parse_go_int(text)
        except ValueError:
            integer = None

        if integer is not None and not text.startswith(('+', '-')) and 0 <= integer < 1 << 64:
            n.is_uint = True
            n.uint64 = integer
        if integer is not None and -(1 << 63) <= integer < 1 << 63:
            n.is_int = True
            n.int64 = integer
            if integer == 0:
                n.is_uint = True
                n.uint64 = 0

        if n.is_int:
            n.is_float = True
            n.float64 = float(n.int64)
        elif n.is_uint:
            n.is_float = True
            n.float64 = float(n.uint64)
        else:
            try:
                value = _parse_go_float(text)
            except ValueError:
                value = None
            if value is not None:
                if not any(char in text for char in '.eEpP'):
                    raise ParseError(f'integer overflow: {quote_go_string(text)}')
                n.is_float = True
                n.float64 = value
                if value.is_integer() and -(1 << 63) <= value < 1 << 63:
                    n.is_int = True
                    n.int64 = int(value)
                if value.is_integer() and 0 <= value < 1 << 64:
                    n.is_uint = True
                    n.uint64 = int(value)

        if not n.is_int and not n.is_uint and not n.is_float:
            raise ParseError(f'illegal number syntax: {quote_go_string(text)}')

        return n

    def new_string(self, pos: Pos, orig: str, text: str) -> StringNode:
        return StringNode(tree=self, type=NodeType.STRING, pos=pos, quoted=orig, text=text)

    def new_end(self, pos: Pos) -> EndNode:
        return EndNode(tree=self, type=NodeType.END, pos=pos)

    def new_else(self, pos: Pos, line: int) -> ElseNode:
        return ElseNode(tree=self, type=NodeType.ELSE, pos=pos, line=line)

    def new_if(self, pos: Pos, line: int, pipe: PipeNode, lst: ListNode, else_lst: ListNode | None) -> IfNode:
        return IfNode(tree=self, type=NodeType.IF, pos=pos, line=line, pipe=pipe, lst=lst, else_lst=else_lst)  # noqa

    def new_break(self, pos: Pos, line: int) -> BreakNode:
        return BreakNode(tree=self, type=NodeType.BREAK, pos=pos, line=line)

    def new_continue(self, pos: Pos, line: int) -> ContinueNode:
        return ContinueNode(tree=self, type=NodeType.CONTINUE, pos=pos, line=line)

    def new_range(self, pos: Pos, line: int, pipe: PipeNode, lst: ListNode, else_lst: ListNode | None) -> RangeNode:
        return RangeNode(tree=self, type=NodeType.RANGE, pos=pos, line=line, pipe=pipe, lst=lst, else_lst=else_lst)  # noqa

    def new_with(self, pos: Pos, line: int, pipe: PipeNode, lst: ListNode, else_lst: ListNode | None) -> WithNode:
        return WithNode(tree=self, type=NodeType.WITH, pos=pos, line=line, pipe=pipe, lst=lst, else_lst=else_lst)  # noqa

    def new_template(self, pos: Pos, line: int, name: str, pipe: PipeNode | None) -> TemplateNode:
        return TemplateNode(tree=self, type=NodeType.TEMPLATE, pos=pos, line=line, name=name, pipe=pipe)

    #

    def next(self) -> Token:
        # next returns the next token.
        if self._peek_count > 0:
            self._peek_count -= 1
        else:
            self._token[0] = check.not_none(self._lex).next_token()
        return check.not_none(self._token[self._peek_count])

    def backup(self) -> None:
        # backup backs the input stream up one token.
        self._peek_count += 1

    def backup2(self, t1: Token) -> None:
        # backup2 backs the input stream up two tokens. The zeroth token is already there.
        self._token[1] = t1
        self._peek_count = 2

    def backup3(self, t2: Token, t1: Token) -> None:  # Reverse order: we're pushing back.
        # backup3 backs the input stream up three tokens. The zeroth token is already there.
        self._token[1] = t1
        self._token[2] = t2
        self._peek_count = 3

    # peek returns but does not consume the next token.
    def peek(self) -> Token:
        if self._peek_count > 0:
            return check.not_none(self._token[self._peek_count - 1])
        self._peek_count = 1
        self._token[0] = check.not_none(self._lex).next_token()
        return check.not_none(self._token[0])

    # next_non_space returns the next non-space token.
    def next_non_space(self) -> Token:
        while True:
            token = self.next()
            if token.typ != TokenType.SPACE:
                break
        return token

    # peek_non_space returns but does not consume the next non-space token.
    def peek_non_space(self) -> Token:
        token = self.next_non_space()
        self.backup()
        return token

    # Parsing.

    def error_context(self, n: Node) -> tuple[str, str]:  # (location, context)
        # ErrorContext returns a textual representation of the location of the node in the input text. The receiver is
        # only used when the node does not have a pointer to the tree inside, which can occur in old code.
        pos = n.pos
        tree = n.tree
        if not tree:
            tree = self
        text = tree._text.encode()[:pos]
        byte_num = text.rfind(b'\n')
        if byte_num == -1:
            byte_num = pos  # On first line.
        else:
            byte_num += 1  # After the newline.
            byte_num = pos - byte_num
        line_num = 1 + text.count(b'\n')
        context = str(n)
        return f'{tree._parse_name}:{line_num}:{byte_num}', context

    def errorf(self, format_string: str, *args: ta.Any) -> ta.NoReturn:
        # errorf formats the error and terminates processing.
        self._root = None
        token = self._token[0]
        line = token.line if token is not None else 0
        message = format_string % args
        raise ParseError(f'template: {self._parse_name}:{line}: {message}')

    def error(self, err: ParseError) -> ta.NoReturn:
        # error terminates processing.
        self.errorf('%s', err)

    def expect(self, expected: TokenType, context: str) -> Token:
        # expect consumes the next token and guarantees it has the required type.
        token = self.next_non_space()
        if token.typ != expected:
            self.unexpected(token, context)
        return token

    def expect_one_of(self, expected1: TokenType, expected2: TokenType, context: str) -> Token:
        # expect_one_of consumes the next token and guarantees it has one of the required types.
        token = self.next_non_space()
        if token.typ != expected1 and token.typ != expected2:
            self.unexpected(token, context)
        return token

    def unexpected(self, token: Token, context: str) -> ta.NoReturn:
        # unexpected complains about the token and terminates processing.
        if token.typ == TokenType.ERROR:
            extra = ''
            if self._action_line != 0 and self._action_line != token.line:
                extra = f' in action started at {self._parse_name}:{self._action_line}'
                if token.val.endswith(' action'):
                    extra = extra[len(' in action') :]  # avoid "action in action"
            self.errorf('%s%s', token, extra)
        self.errorf('unexpected %s in %s', token, context)

    def start_parse(
        self,
        funcs: list[dict[str, ta.Any]],
        lex: Lexer,
        tree_set: dict[str, Tree],
    ) -> None:
        # startParse initializes the parser, using the lexer.
        self._root = None
        self._lex = lex
        self._vars = ['$']
        self._funcs = funcs
        self._tree_set = tree_set
        self._peek_count = 0
        self._stack_depth = 0
        lex._options = LexOptions(  # noqa
            emit_comment=(self._mode & MODE_PARSE_COMMENTS) != 0,
            break_ok=not self.has_function('break'),
            continue_ok=not self.has_function('continue'),
        )

    def stop_parse(self) -> None:
        # stop_parse terminates parsing.
        self._lex = None
        self._vars = []
        self._funcs = []
        self._tree_set = {}

    def parse(
        self,
        text: str,
        left_delim: str,
        right_delim: str,
        tree_set: dict[str, Tree],
        *funcs: dict[str, ta.Any],
    ) -> Tree:
        # Parse parses the template definition string to construct a representation of the template for execution. If
        # either action delimiter string is empty, the default ("{{" or "}}") is used. Embedded template definitions are
        # added to the tree_set map.
        try:
            self._parse_name = self._name
            self._left_delim = left_delim or LEFT_DELIM
            self._right_delim = right_delim or RIGHT_DELIM
            lexer = Lexer(
                self._name,
                text,
                left_delim=self._left_delim,
                right_delim=self._right_delim,
            )
            self.start_parse(list(funcs), lexer, tree_set)
            self._text = text
            self._parse()
            self.add()
            self.stop_parse()
            return self
        except Exception as e:  # noqa: BLE001 - normalize lexer and parser implementation failures.
            self.stop_parse()
            if isinstance(e, ParseError):
                raise
            raise ParseError(str(e)) from e

    def add(self) -> None:
        # add adds tree to t.tree_set.
        tree = self._tree_set.get(self._name)
        if tree is None or is_empty_tree(tree.root):
            self._tree_set[self._name] = self
            return
        if not is_empty_tree(self._root):
            self.errorf('template: multiple definition of template %s', quote_go_string(self._name))

    def _parse(self) -> None:
        # parse is the top-level parser for a template, essentially the same as TokenType.LIST except it also parses
        # {{define}} actions. It runs to EOF.
        self._root = self.new_list(self.peek().pos)
        while self.peek().typ != TokenType.EOF:
            if self.peek().typ == TokenType.LEFT_DELIM:
                delim = self.next()
                if self.next_non_space().typ == TokenType.DEFINE:
                    new_t = Tree('definition')  # name will be updated once we know it.
                    new_t._text = self._text
                    new_t._mode = self._mode
                    new_t._left_delim = self._left_delim
                    new_t._right_delim = self._right_delim
                    new_t._parse_name = self._parse_name
                    new_t.start_parse(self._funcs, check.not_none(self._lex), self._tree_set)
                    new_t.parse_definition()
                    continue
                self.backup2(delim)
            n = self.text_or_action()
            if n.type in (NodeType.END, NodeType.ELSE):
                self.errorf('unexpected %s', n)
            else:
                self._root.append(n)

    def parse_definition(self) -> None:
        # parseDefinition parses a {{define}} ...  {{end}} template definition and installs the definition in
        # t.tree_set. The "define" keyword has already been scanned.
        context = 'define clause'
        name = self.expect_one_of(TokenType.STRING, TokenType.RAW_STRING, context)
        try:
            self._name = unquote(name.val)
        except UnquoteError as err:
            self.error(ParseError(str(err)))
        self.expect(TokenType.RIGHT_DELIM, context)
        self._root, end = self.item_list()
        if end.type != NodeType.END:
            self.errorf('unexpected %s in %s', end, context)
        self.add()
        self.stop_parse()

    def item_list(self) -> tuple[ListNode, Node]:  # (list, next)
        # itemList:
        #
        #    text_or_action*
        #
        # Terminates at {{end}} or {{else}}, returned separately.
        lst = self.new_list(self.peek_non_space().pos)
        while self.peek_non_space().typ != TokenType.EOF:
            n = self.text_or_action()
            if n.type in (NodeType.END, NodeType.ELSE):
                return lst, n
            lst.append(n)
        self.errorf('unexpected EOF')
        raise AssertionError('unreachable')

    def text_or_action(self) -> Node:
        # text_or_action:
        #
        #    text | comment | action
        token = self.next_non_space()
        if token.typ == TokenType.TEXT:
            return self.new_text(token.pos, token.val)
        elif token.typ == TokenType.LEFT_DELIM:
            self._action_line = token.line
            try:
                return self.action()
            finally:
                self.clear_action_line()
        elif token.typ == TokenType.COMMENT:
            return self.new_comment(token.pos, token.val)
        else:
            self.unexpected(token, 'input')
            raise AssertionError('unreachable')

    def clear_action_line(self) -> None:
        self._action_line = 0

    def action(self) -> Node:
        # Action:
        #
        #    control
        #    command ("|" command)*
        #
        # Left delim is past. Now get actions. First word could be a keyword such as range.
        token = self.next_non_space()
        if token.typ == TokenType.BLOCK:
            return self.block_control()
        elif token.typ == TokenType.BREAK:
            return self.break_control(token.pos, token.line)
        elif token.typ == TokenType.CONTINUE:
            return self.continue_control(token.pos, token.line)
        elif token.typ == TokenType.ELSE:
            return self.else_control()
        elif token.typ == TokenType.END:
            return self.end_control()
        elif token.typ == TokenType.IF:
            return self.if_control()
        elif token.typ == TokenType.RANGE:
            return self.range_control()
        elif token.typ == TokenType.TEMPLATE:
            return self.template_control()
        elif token.typ == TokenType.WITH:
            return self.with_control()
        self.backup()
        token = self.peek()
        # Do not pop variables; they persist until 'end'.
        return self.new_action(token.pos, token.line, self.pipeline('command', TokenType.RIGHT_DELIM))

    def break_control(self, pos: Pos, line: int) -> Node:
        # Break:
        #
        #    {{break}}
        #
        # Break keyword is past.
        token = self.next_non_space()
        if token.typ != TokenType.RIGHT_DELIM:
            self.unexpected(token, '{{break}}')
        if self._range_depth == 0:
            self.errorf('{{break}} outside {{range}}')
        return self.new_break(pos, line)

    def continue_control(self, pos: Pos, line: int) -> Node:
        # Continue:
        #
        #    {{continue}}
        #
        # Continue keyword is past.
        token = self.next_non_space()
        if token.typ != TokenType.RIGHT_DELIM:
            self.unexpected(token, '{{continue}}')
        if self._range_depth == 0:
            self.errorf('{{continue}} outside {{range}}')
        return self.new_continue(pos, line)

    def pipeline(self, context: str, end: TokenType) -> PipeNode:
        # Pipeline:
        #
        #    declarations? command ('|' command)*
        token = self.peek_non_space()
        pipe = self.new_pipeline(token.pos, token.line, [])

        # Are there declarations or assignments?
        while True:
            v = self.peek_non_space()
            if v.typ == TokenType.VARIABLE:
                self.next()
                # Since space is a token, we need 3-token look-ahead here in the worst case: in "$x foo" we need to read
                # "foo" (as opposed to "=") to know that $x is an argument variable rather than a declaration. So
                # remember the token adjacent to the variable so we can push it back if necessary.
                token_after_variable = self.peek()
                next = self.peek_non_space()  # noqa

                if next.typ in (TokenType.ASSIGN, TokenType.DECLARE):
                    pipe.is_assign = next.typ == TokenType.ASSIGN
                    self.next_non_space()
                    pipe.decl.append(self.new_variable(v.pos, v.val))
                    self._vars.append(v.val)

                elif next.typ == TokenType.CHAR and next.val == ',':
                    self.next_non_space()
                    pipe.decl.append(self.new_variable(v.pos, v.val))
                    self._vars.append(v.val)
                    if context == 'range' and len(pipe.decl) < 2:
                        if self.peek_non_space().typ in (
                            TokenType.VARIABLE,
                            TokenType.RIGHT_DELIM,
                            TokenType.RIGHT_PAREN,
                        ):
                            # second initialized variable in a range pipeline
                            continue
                        else:
                            self.errorf('range can only initialize variables')
                    self.errorf('too many declarations in %s', context)

                elif token_after_variable.typ == TokenType.SPACE:
                    self.backup3(v, token_after_variable)

                else:
                    self.backup2(v)

            break

        while True:
            token = self.next_non_space()
            if token.typ == end:
                # At this point, the pipeline is complete
                self.check_pipeline(pipe, context)
                return pipe

            elif token.typ in (
                TokenType.BOOL,
                TokenType.CHAR_CONSTANT,
                TokenType.COMPLEX,
                TokenType.DOT,
                TokenType.FIELD,
                TokenType.IDENTIFIER,
                TokenType.NUMBER,
                TokenType.NIL,
                TokenType.RAW_STRING,
                TokenType.STRING,
                TokenType.VARIABLE,
                TokenType.LEFT_PAREN,
            ):
                self.backup()
                pipe.append(self.command())

            else:
                self.unexpected(token, context)

    def check_pipeline(self, pipe: PipeNode, context: str) -> None:
        # Reject empty pipelines
        if not pipe.cmds:
            self.errorf('missing value for %s', context)
        # Only the first command of a pipeline can start with a non executable operand
        for i, c in enumerate(pipe.cmds[1:]):
            if c.args[0].type in (NodeType.BOOL, NodeType.DOT, NodeType.NIL, NodeType.NUMBER, NodeType.STRING):
                # With A|B|C, pipeline stage 2 is B
                self.errorf('non executable command in pipeline stage %d', i + 2)

    def parse_control(self, context: str) -> tuple[Pos, int, PipeNode, ListNode, ListNode | None]:
        mark = len(self._vars)
        try:
            pipe = self.pipeline(context, TokenType.RIGHT_DELIM)
            if context == 'range':
                self._range_depth += 1

            lst, next = self.item_list()  # noqa
            if context == 'range':
                self._range_depth -= 1

            else_lst = None

            if next.type == NodeType.END:  # done
                pass

            elif next.type == NodeType.ELSE:
                # Special case for "else if" and "else with". If the "else" is followed immediately by an "if" or
                # "with", the else_control will have left the "if" or "with" token pending. Treat
                #
                #    {{if a}}_{{else if b}}_{{end}}
                #  {{with a}}_{{else with b}}_{{end}}
                #
                # as
                #
                #    {{if a}}_{{else}}{{if b}}_{{end}}{{end}}
                #  {{with a}}_{{else}}{{with b}}_{{end}}{{end}}.
                #
                # To do this, parse the "if" or "with" as usual and stop at it {{end}}; the subsequent{{end}} is
                # assumed. This technique works even for long if-else-if chains.
                if context == 'if' and self.peek().typ == TokenType.IF:
                    self.next()  # Consume the "if" token.
                    else_lst = self.new_list(next.pos)
                    else_lst.append(self.if_control())
                elif context == 'with' and self.peek().typ == TokenType.WITH:
                    self.next()
                    else_lst = self.new_list(next.pos)
                    else_lst.append(self.with_control())
                else:
                    else_lst, next = self.item_list()  # noqa
                    if next.type != NodeType.END:
                        self.errorf('expected end; found %s', next)

            return pipe.pos, pipe.line, pipe, lst, else_lst

        finally:
            self.pop_vars(mark)

    def if_control(self) -> Node:
        # If:
        #
        #    {{if pipeline}} itemList {{end}}
        #    {{if pipeline}} itemList {{else}} itemList {{end}}
        #
        # If keyword is past.
        return self.new_if(*self.parse_control('if'))

    def range_control(self) -> Node:
        # Range:
        #
        #    {{range pipeline}} itemList {{end}}
        #    {{range pipeline}} itemList {{else}} itemList {{end}}
        #
        # Range keyword is past.
        r = self.new_range(*self.parse_control('range'))
        return r

    def with_control(self) -> Node:
        # With:
        #
        #    {{with pipeline}} itemList {{end}}
        #    {{with pipeline}} itemList {{else}} itemList {{end}}
        #
        # If keyword is past.
        return self.new_with(*self.parse_control('with'))

    def end_control(self) -> Node:
        # End:
        #
        #    {{end}}
        #
        # End keyword is past.
        return self.new_end(self.expect(TokenType.RIGHT_DELIM, 'end').pos)

    def else_control(self) -> Node:
        # Else:
        #
        #    {{else}}
        #
        # Else keyword is past.
        peek = self.peek_non_space()
        # The "{{else if ... " and "{{else with ..." will be treated as "{{else}}{{if ..." and "{{else}}{{with ...". So
        # return the else node here.
        if peek.typ == TokenType.IF or peek.typ == TokenType.WITH:
            return self.new_else(peek.pos, peek.line)
        token = self.expect(TokenType.RIGHT_DELIM, 'else')
        return self.new_else(token.pos, token.line)

    def block_control(self) -> Node:
        # Block:
        #
        #    {{block stringValue pipeline}}
        #
        # Block keyword is past. The name must be something that can evaluate to a string. The pipeline is mandatory.
        context = 'block clause'

        token = self.next_non_space()
        name = self.parse_template_name(token, context)
        pipe = self.pipeline(context, TokenType.RIGHT_DELIM)

        block = Tree(name)  # name will be updated once we know it.
        block._text = self._text
        block._mode = self._mode
        block._left_delim = self._left_delim
        block._right_delim = self._right_delim
        block._parse_name = self._parse_name
        block.start_parse(self._funcs, check.not_none(self._lex), self._tree_set)
        block._root, end = block.item_list()
        if end.type != NodeType.END:
            self.errorf('unexpected %s in %s', end, context)
        block.add()
        block.stop_parse()

        return self.new_template(token.pos, token.line, name, pipe)

    def template_control(self) -> Node:
        # Template:
        #
        #    {{template stringValue pipeline}}
        #
        # Template keyword is past. The name must be something that can evaluate to a string.
        context = 'template clause'
        token = self.next_non_space()
        name = self.parse_template_name(token, context)
        pipe: PipeNode | None = None
        if self.next_non_space().typ != TokenType.RIGHT_DELIM:
            self.backup()
            # Do not pop variables; they persist until "end".
            pipe = self.pipeline(context, TokenType.RIGHT_DELIM)
        return self.new_template(token.pos, token.line, name, pipe)

    def parse_template_name(self, token: Token, context: str) -> str:
        if token.typ in (TokenType.STRING, TokenType.RAW_STRING):
            try:
                s = unquote(token.val)
            except UnquoteError as err:
                self.error(ParseError(str(err)))
            return s
        else:
            self.unexpected(token, context)
            raise AssertionError('unreachable')

    def command(self) -> CommandNode:
        # command:
        #
        #    operand (space operand)*
        #
        # space-separated arguments up to a pipeline character or right delimiter. we consume the pipe character but
        # leave the right delim to terminate the action.
        cmd = self.new_command(self.peek_non_space().pos)
        while True:
            self.peek_non_space()  # skip leading spaces.
            operand = self.operand()
            if operand:
                cmd.append(operand)
            token = self.next()
            if token.typ == TokenType.SPACE:
                continue
            elif token.typ in (TokenType.RIGHT_DELIM, TokenType.RIGHT_PAREN):
                self.backup()
            elif token.typ == TokenType.PIPE:
                # nothing here; break loop below
                pass
            else:
                self.unexpected(token, 'operand')
            break
        if not cmd.args:
            self.errorf('empty command')
        return cmd

    def operand(self) -> Node | None:
        # operand:
        #
        #    term .Field*
        #
        # An operand is a space-separated component of a command, a term possibly followed by field accesses. A nil
        # return means the next item is not an operand.
        node = self.term()
        if not node:
            return None
        if self.peek().typ == TokenType.FIELD:
            chain = self.new_chain(self.peek().pos, node)
            while self.peek().typ == TokenType.FIELD:
                chain.add(self.next().val)

            # Compatibility with original API: If the term is of type NodeField or NodeVariable, just put more fields on
            # the original. Otherwise, keep the Chain node.
            # Obvious parsing errors involving literal values are detected here. More complex error cases will have to
            # be handled at execution time.
            if node.type == NodeType.FIELD:
                node = self.new_field(chain.pos, chain.string())
            elif node.type == NodeType.VARIABLE:
                node = self.new_variable(chain.pos, chain.string())
            elif node.type in (NodeType.BOOL, NodeType.STRING, NodeType.NUMBER, NodeType.NIL, NodeType.DOT):
                self.errorf('unexpected . after term %s', quote_go_string(str(node)))
            else:
                node = chain
        return node

    def term(self) -> Node | None:
        # term:
        #
        #    literal (number, str, nil, boolean)
        #    function (identifier)
        #    .
        #    .Field
        #    $
        #    '(' pipeline ')'
        #
        # A term is a simple "expression". A nil return means the next item is not a term.
        token = self.next_non_space()
        if token.typ == TokenType.IDENTIFIER:
            check_func = self._mode & MODE_SKIP_FUNC_CHECK == 0
            if check_func and not self.has_function(token.val):
                self.errorf('function %s not defined', quote_go_string(token.val))
            return new_identifier(token.val).set_tree(self).set_pos(token.pos)
        elif token.typ == TokenType.DOT:
            return self.new_dot(token.pos)
        elif token.typ == TokenType.NIL:
            return self.new_nil(token.pos)
        elif token.typ == TokenType.VARIABLE:
            return self.use_var(token.pos, token.val)
        elif token.typ == TokenType.FIELD:
            return self.new_field(token.pos, token.val)
        elif token.typ == TokenType.BOOL:
            return self.new_bool(token.pos, token.val == 'true')
        elif token.typ in (TokenType.CHAR_CONSTANT, TokenType.COMPLEX, TokenType.NUMBER):
            try:
                number = self.new_number(token.pos, token.val, token.typ)
            except (ParseError, UnquoteError, ValueError, OverflowError) as err:
                self.error(ParseError(str(err)))
            return number
        elif token.typ == TokenType.LEFT_PAREN:
            if self._stack_depth >= MAX_STACK_DEPTH:
                self.errorf('max expression depth exceeded')
            self._stack_depth += 1
            try:
                return self.pipeline('parenthesized pipeline', TokenType.RIGHT_PAREN)
            finally:
                self._stack_depth -= 1
        elif token.typ in (TokenType.STRING, TokenType.RAW_STRING):
            try:
                s = unquote(token.val)
            except UnquoteError as err:
                self.error(ParseError(str(err)))
            return self.new_string(token.pos, token.val, s)
        self.backup()
        return None

    def has_function(self, name: str) -> bool:
        # has_function reports if a function name exists in the Tree's maps.
        for func_map in self._funcs:
            if not func_map:
                continue
            if name in func_map:
                return True
        return False

    def pop_vars(self, n: int) -> None:
        # pop_vars trims the variable list to the specified length
        self._vars = self._vars[:n]

    def use_var(self, pos: Pos, name: str) -> Node:
        # use_var returns a node for a variable reference. It errors if the variable is not defined.
        v = self.new_variable(pos, name)
        for var_name in self._vars:
            if var_name == v.ident[0]:
                return v
        self.errorf('undefined variable %s', quote_go_string(v.ident[0]))
        raise AssertionError('unreachable')


def is_empty_tree(n: Node | None) -> bool:
    # is_empty_tree reports whether this tree (node) is empty of everything but space or comments.
    if n is None:
        return True
    elif isinstance(n, CommentNode):
        return True
    elif isinstance(n, ListNode):
        return all(is_empty_tree(node) for node in n.nodes)
    elif isinstance(n, TextNode):
        return len(n.text.strip()) == 0
    elif isinstance(n, (ActionNode, IfNode, RangeNode, TemplateNode, WithNode)):
        return False
    raise TypeError(f'unknown node: {n}')


# Parse returns a map from template name to [Tree], created by parsing the templates described in the argument string.
# The top-level template will be given the specified name. If an error is encountered, parsing stops and an empty map is
# returned with the error.
def parse(
    name: str,
    text: str,
    left_delim: str = '',
    right_delim: str = '',
    *func_maps: dict[str, ta.Any],
    funcs: dict[str, ta.Any] | None = None,
) -> dict[str, Tree]:
    all_funcs = list(func_maps)
    if funcs is not None:
        all_funcs.append(funcs)
    tree_set: dict[str, Tree] = {}
    t = Tree(name, *all_funcs)
    t.parse(text, left_delim, right_delim, tree_set, *all_funcs)
    return tree_set
