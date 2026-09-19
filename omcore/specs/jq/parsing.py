import typing as ta

from ... import dataclasses as dc
from . import ast
from .errors import JqParseError
from .errors import JqUnsupportedError
from .lexing import Interpolation
from .lexing import Token
from .lexing import lex


##


_INFIX: ta.Mapping[str, tuple[int, int, str]] = {
    '|': (10, 10, 'pipe'),
    ',': (20, 21, 'comma'),
    '//': (30, 30, 'alternative'),
    '=': (40, 41, 'assignment'),
    '|=': (40, 41, 'assignment'),
    '+=': (40, 41, 'assignment'),
    '-=': (40, 41, 'assignment'),
    '*=': (40, 41, 'assignment'),
    '/=': (40, 41, 'assignment'),
    '%=': (40, 41, 'assignment'),
    '//=': (40, 41, 'assignment'),
    'OR': (50, 51, 'binary'),
    'AND': (60, 61, 'binary'),
    '==': (70, 71, 'binary'),
    '!=': (70, 71, 'binary'),
    '<': (70, 71, 'binary'),
    '>': (70, 71, 'binary'),
    '<=': (70, 71, 'binary'),
    '>=': (70, 71, 'binary'),
    '+': (80, 81, 'binary'),
    '-': (80, 81, 'binary'),
    '*': (90, 91, 'binary'),
    '/': (90, 91, 'binary'),
    '%': (90, 91, 'binary'),
}

_OBJECT_KEYWORDS = frozenset({
    'AND',
    'AS',
    'BREAK',
    'CATCH',
    'DEF',
    'ELIF',
    'ELSE',
    'END',
    'FOREACH',
    'IF',
    'LABEL',
    'OR',
    'REDUCE',
    'THEN',
    'TRY',
})

##


class Parser:
    def __init__(self, source: str, *, offset: int = 0) -> None:
        super().__init__()

        self._source = source
        self._tokens = lex(source, offset=offset)
        self._index = 0

    @property
    def _current(self) -> Token:
        return self._tokens[self._index]

    def _advance(self) -> Token:
        token = self._current
        self._index += 1
        return token

    def _accept(self, kind: str) -> Token | None:
        if self._current.kind == kind:
            return self._advance()
        return None

    def _expect(self, kind: str) -> Token:
        if self._current.kind != kind:
            self._raise(f'expected {kind!r}, got {self._current.kind!r}')
        return self._advance()

    def _raise(self, message: str, token: Token | None = None) -> ta.NoReturn:
        raise JqParseError(message, offset=(self._current if token is None else token).start)

    @staticmethod
    def _span(start: int, end: int) -> ast.SourceSpan:
        return ast.SourceSpan(start, end)

    def parse(self) -> ast.Node:
        if self._current.kind == 'EOF':
            self._raise('empty jq program')
        result = self._parse_query(frozenset({'EOF'}))
        self._expect('EOF')
        return result

    def _parse_query(self, stop: frozenset[str]) -> ast.Node:
        if self._current.kind == 'DEF':
            return self._parse_definition(stop)
        if self._current.kind == 'LABEL':
            return self._parse_label(self._advance(), stop)
        return self._parse_expression(0, stop)

    def _parse_label(self, opening: Token, stop: frozenset[str]) -> ast.Label:
        variable = self._expect('VARIABLE')
        self._expect('|')
        body = self._parse_query(stop)
        return ast.Label(variable.value, body, span=self._span(opening.start, body.span.end))

    def _parse_expression(self, minimum: int, stop: frozenset[str]) -> ast.Node:
        left = self._parse_term(stop)

        while self._current.kind not in stop:
            if self._current.kind in ('?', '.', '['):
                left = self._parse_postfix(left, stop)
                continue

            if self._current.kind == 'AS':
                self._advance()
                if self._current.kind != 'VARIABLE':
                    raise JqUnsupportedError('jq destructuring bindings are not supported')
                variable = self._advance()
                self._expect('|')
                body = self._parse_query(stop)
                left = ast.Binding(left, variable.value, body, span=self._span(left.span.start, body.span.end))
                continue

            if (infix := _INFIX.get(self._current.kind)) is None:
                break
            left_binding, right_binding, category = infix
            if left_binding < minimum:
                break
            operator = self._advance()
            right = self._parse_expression(right_binding, stop)
            span = self._span(left.span.start, right.span.end)
            if category == 'pipe':
                left = ast.Pipe(left, right, span=span)
            elif category == 'comma':
                left = ast.Comma(left, right, span=span)
            elif category == 'alternative':
                left = ast.Alternative(left, right, span=span)
            elif category == 'assignment':
                left = ast.Assignment(operator.kind, left, right, span=span)
            else:
                left = ast.Binary(operator.value, left, right, span=span)

        return left

    def _parse_term(self, stop: frozenset[str]) -> ast.Node:
        token = self._advance()

        if token.kind == '.':
            result: ast.Node = ast.Identity(span=self._span(token.start, token.end))
            if self._current.kind == 'IDENT':
                key = self._advance()
                return ast.Index(
                    result,
                    ast.Literal(key.value, span=self._span(key.start, key.end)),
                    span=self._span(token.start, key.end),
                )
            if self._current.kind == 'STRING':
                string_key = self._parse_string(self._advance())
                return ast.Index(result, string_key, span=self._span(token.start, string_key.span.end))
            return result

        if token.kind == '..':
            return ast.RecursiveDescent(span=self._span(token.start, token.end))

        if token.kind == 'NUMBER':
            return ast.Literal(token.value, span=self._span(token.start, token.end))

        if token.kind == 'STRING':
            return self._parse_string(token)

        if token.kind == 'VARIABLE':
            return ast.Variable(token.value, span=self._span(token.start, token.end))

        if token.kind == 'IDENT':
            if token.value == 'null':
                return ast.Literal(None, span=self._span(token.start, token.end))
            if token.value == 'true':
                return ast.Literal(True, span=self._span(token.start, token.end))
            if token.value == 'false':
                return ast.Literal(False, span=self._span(token.start, token.end))
            if token.value == 'empty' and self._current.kind != '(':
                return ast.Empty(span=self._span(token.start, token.end))
            return self._parse_call(token)

        if token.kind == '-':
            operand = self._parse_expression(100, stop)
            return ast.Unary('-', operand, span=self._span(token.start, operand.span.end))

        if token.kind == '(':
            value = self._parse_query(frozenset({')'}))
            end = self._expect(')')
            return dc_replace_span(value, self._span(token.start, end.end))

        if token.kind == '[':
            if (end_token := self._accept(']')) is not None:
                return ast.Array(None, span=self._span(token.start, end_token.end))
            value = self._parse_query(frozenset({']'}))
            end = self._expect(']')
            return ast.Array(value, span=self._span(token.start, end.end))

        if token.kind == '{':
            return self._parse_object(token)

        if token.kind == 'IF':
            return self._parse_conditional(token)

        if token.kind == 'REDUCE':
            return self._parse_reduce(token)

        if token.kind == 'FOREACH':
            return self._parse_foreach(token)

        if token.kind == 'TRY':
            value = self._parse_expression(30, stop | frozenset({'CATCH'}))
            handler = None
            if self._accept('CATCH') is not None:
                handler = self._parse_expression(30, stop)
            end_offset = handler.span.end if handler is not None else value.span.end
            return ast.Try(value, handler, span=self._span(token.start, end_offset))

        if token.kind == 'BREAK':
            variable = self._expect('VARIABLE')
            return ast.Break(variable.value, span=self._span(token.start, variable.end))

        if token.kind == 'LABEL':
            return self._parse_label(token, stop)

        self._raise(f'unexpected token {token.kind!r}', token)
        raise RuntimeError('unreachable')

    def _parse_postfix(self, value: ast.Node, stop: frozenset[str]) -> ast.Node:
        if (optional := self._accept('?')) is not None:
            return ast.Optional(value, span=self._span(value.span.start, optional.end))

        if self._accept('.') is not None:
            if self._current.kind == 'IDENT':
                key = self._advance()
                literal_key = ast.Literal(key.value, span=self._span(key.start, key.end))
                return ast.Index(value, literal_key, span=self._span(value.span.start, key.end))
            if self._current.kind == 'STRING':
                string_key = self._parse_string(self._advance())
                return ast.Index(value, string_key, span=self._span(value.span.start, string_key.span.end))
            if self._current.kind != '[':
                self._raise('expected field or index after dot')

        self._expect('[')
        if (end := self._accept(']')) is not None:
            return ast.Iterate(value, span=self._span(value.span.start, end.end))

        start_value: ast.Node | None
        if self._accept(':') is not None:
            start_value = None
            if self._current.kind == ']':
                end_value = None
            else:
                end_value = self._parse_query(frozenset({']'}))
            end = self._expect(']')
            return ast.Slice(value, start_value, end_value, span=self._span(value.span.start, end.end))

        start_value = self._parse_query(frozenset({':', ']'}))
        if self._accept(':') is not None:
            if self._current.kind == ']':
                end_value = None
            else:
                end_value = self._parse_query(frozenset({']'}))
            end = self._expect(']')
            return ast.Slice(value, start_value, end_value, span=self._span(value.span.start, end.end))

        end = self._expect(']')
        return ast.Index(value, start_value, span=self._span(value.span.start, end.end))

    def _parse_string(self, token: Token) -> ast.String:
        parts: list[ast.StringPart] = []
        for part in token.value:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, Interpolation):
                parts.append(Parser(part.source, offset=part.offset).parse())
            else:
                raise TypeError(part)
        return ast.String(tuple(parts), span=self._span(token.start, token.end))

    def _parse_call(self, token: Token) -> ast.Call:
        arguments: list[ast.Node] = []
        end = token.end
        if self._accept('(') is not None:
            if self._current.kind != ')':
                while True:
                    arguments.append(self._parse_query(frozenset({';', ')'})))
                    if self._accept(';') is None:
                        break
            end = self._expect(')').end
        return ast.Call(token.value, tuple(arguments), span=self._span(token.start, end))

    def _parse_object_key(self) -> tuple[ast.Node, ast.Node | None]:
        token = self._advance()
        if token.kind == '(':
            key = self._parse_query(frozenset({')'}))
            self._expect(')')
            return key, None
        if token.kind == 'STRING':
            key = self._parse_string(token)
            return key, None
        if token.kind == 'VARIABLE':
            key = ast.Variable(token.value, span=self._span(token.start, token.end))
            shorthand: ast.Node | None = ast.Variable(token.value, span=self._span(token.start, token.end))
            return key, shorthand
        if token.kind == 'IDENT' or token.kind in _OBJECT_KEYWORDS:
            key = ast.Literal(token.value, span=self._span(token.start, token.end))
            shorthand = ast.Index(
                ast.Identity(span=self._span(token.start, token.start)),
                key,
                span=self._span(token.start, token.end),
            )
            return key, shorthand
        self._raise('invalid object key', token)
        raise RuntimeError('unreachable')

    def _parse_object(self, opening: Token) -> ast.Object:
        members: list[ast.ObjectMember] = []
        if (end := self._accept('}')) is not None:
            return ast.Object((), span=self._span(opening.start, end.end))

        while True:
            key, shorthand = self._parse_object_key()
            if self._accept(':') is not None:
                value = self._parse_query(frozenset({',', '}'}))
            elif shorthand is not None:
                if isinstance(key, ast.Variable):
                    key = ast.Literal(key.name, span=key.span)
                value = shorthand
            else:
                self._raise('object member requires a value')
            members.append(ast.ObjectMember(key, value))
            if self._accept(',') is None:
                break
        end = self._expect('}')
        return ast.Object(tuple(members), span=self._span(opening.start, end.end))

    def _parse_conditional(self, opening: Token) -> ast.Conditional:
        branches: list[ast.IfBranch] = []
        condition = self._parse_query(frozenset({'THEN'}))
        self._expect('THEN')
        body = self._parse_query(frozenset({'ELIF', 'ELSE', 'END'}))
        branches.append(ast.IfBranch(condition, body))
        while self._accept('ELIF') is not None:
            condition = self._parse_query(frozenset({'THEN'}))
            self._expect('THEN')
            body = self._parse_query(frozenset({'ELIF', 'ELSE', 'END'}))
            branches.append(ast.IfBranch(condition, body))
        if self._accept('ELSE') is not None:
            otherwise = self._parse_query(frozenset({'END'}))
        else:
            current = self._current
            otherwise = ast.Identity(span=self._span(current.start, current.start))
        end = self._expect('END')
        return ast.Conditional(tuple(branches), otherwise, span=self._span(opening.start, end.end))

    def _parse_binding_variable(self) -> Token:
        self._expect('AS')
        if self._current.kind != 'VARIABLE':
            raise JqUnsupportedError('jq destructuring patterns are not supported')
        return self._advance()

    def _parse_reduce(self, opening: Token) -> ast.Reduce:
        source = self._parse_expression(30, frozenset({'AS'}))
        variable = self._parse_binding_variable()
        self._expect('(')
        initial = self._parse_query(frozenset({';'}))
        self._expect(';')
        update = self._parse_query(frozenset({')'}))
        end = self._expect(')')
        return ast.Reduce(source, variable.value, initial, update, span=self._span(opening.start, end.end))

    def _parse_foreach(self, opening: Token) -> ast.Foreach:
        source = self._parse_expression(30, frozenset({'AS'}))
        variable = self._parse_binding_variable()
        self._expect('(')
        initial = self._parse_query(frozenset({';'}))
        self._expect(';')
        update = self._parse_query(frozenset({';', ')'}))
        if self._accept(';') is not None:
            extract = self._parse_query(frozenset({')'}))
        else:
            extract = ast.Identity(span=self._span(update.span.end, update.span.end))
        end = self._expect(')')
        return ast.Foreach(source, variable.value, initial, update, extract, span=self._span(opening.start, end.end))

    def _parse_definition(self, stop: frozenset[str]) -> ast.FunctionDefinition:
        opening = self._expect('DEF')
        name = self._expect('IDENT')
        parameters: list[ast.FunctionParameter] = []
        if self._accept('(') is not None:
            if self._current.kind != ')':
                while True:
                    parameter = self._advance()
                    if parameter.kind == 'VARIABLE':
                        parameters.append(ast.FunctionParameter(parameter.value, True))
                    elif parameter.kind == 'IDENT':
                        parameters.append(ast.FunctionParameter(parameter.value, False))
                    else:
                        self._raise('invalid function parameter', parameter)
                    if self._accept(';') is None:
                        break
            self._expect(')')
        self._expect(':')
        body = self._parse_query(frozenset({';'}))
        semicolon = self._expect(';')
        if self._current.kind in stop:
            next_node: ast.Node = ast.Identity(span=self._span(semicolon.end, semicolon.end))
        else:
            next_node = self._parse_query(stop)
        return ast.FunctionDefinition(
            name.value,
            tuple(parameters),
            body,
            next_node,
            span=self._span(opening.start, next_node.span.end),
        )


def dc_replace_span(node: ast.Node, span: ast.SourceSpan) -> ast.Node:
    return dc.replace(node, span=span)


def parse(source: str) -> ast.Node:
    return Parser(source).parse()
