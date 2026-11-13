# ruff: noqa: A002
# Copyright © 2009/2023 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
Functional parsing combinators.

Parsing combinators define an internal domain-specific language (DSL) for describing the parsing rules of a grammar. The
DSL allows you to start with a few primitive parsers, then combine your parsers to get more complex ones, and finally
cover the whole grammar you want to parse.

The structure of the language:

- The `Parser` class: all the primitives and combinators of the language return `Parser` objects, and it defines the
  main `Parser.parse(tokens)` method.
- Primitive parsers: `tok(type, value)`, `a(value)`, `some(pred)`, `forward_decl()`, `finished`.
- Parser combinators: `p1 + p2`, `p1 | p2`, `p >> f`, `-p`, `maybe(p)`, `many(p)`, `oneplus(p)`, `skip(p)`.
- Abstraction: regular Python variables (`p = ...`, of type `Parser`) define new rules (non-terminals) of your grammar.

Every time you apply one of the combinators, you get a new `Parser` object. In other words, the set of `Parser` objects
is closed under the means of combination.

The parsing combinators language is taken from the book Introduction to Functional Programming
(https://www.cl.cam.ac.uk/teaching/Lectures/funprog-jrh-1996/), translated from ML into Python.
"""
import logging
import typing as ta

from omcore import dataclasses as dc

from .lexer import Token


_A = ta.TypeVar('_A')
_B = ta.TypeVar('_B')
_C = ta.TypeVar('_C')

# The function implementing a parser: given the full token sequence and the current state, returns the parsed value and
# the new state, or raises `NoParseError`.
ParserFn: ta.TypeAlias = ta.Callable[[ta.Sequence[_A], 'State'], tuple[_B, 'State']]


##


log = logging.getLogger(__name__)

# Set to True (in source) to enable the debug-level parsing log, at the cost of a layer of indirection on every parse
# step.
_DEBUG: ta.Final[bool] = False


##


@dc.dataclass(frozen=True, repr=False)
class State:
    """
    Parsing state, maintained basically for error reporting: the current position `pos` in the sequence being parsed,
    the position `max` of the rightmost token that has been consumed while parsing, and the parser which failed at that
    rightmost position.
    """

    pos: int
    max: int
    parser: Parser | ParserFn[ta.Any, ta.Any] | None = None

    def __str__(self) -> str:
        return str((self.pos, self.max))

    def __repr__(self) -> str:
        return f'State({self.pos!r}, {self.max!r})'


class NoParseError(Exception):
    def __init__(self, msg: str, state: State) -> None:
        super().__init__(msg, state)

        self.msg = msg
        self.state = state

    def __str__(self) -> str:
        return self.msg


##


class Parser(ta.Generic[_A, _B]):
    """
    A parser object that can parse a sequence of tokens of type `_A` into a value of type `_B`, or can be combined with
    other parsers using `+`, `|`, `>>`, `many()`, and other parsing combinators.

    In order to define a parser for your grammar:

    1. You start with primitive parsers by calling `a(value)`, `some(pred)`, `forward_decl()`, `finished`
    2. You use parsing combinators `p1 + p2`, `p1 | p2`, `p >> f`, `many(p)`, and others to combine parsers into a more
       complex parser
    3. You can assign complex parsers to variables to define names that correspond to the rules of your grammar

    The constructor is considered internal: use primitive parsers and parsing combinators to construct new parsers.
    """

    def __init__(self, p: Parser[_A, _B] | ParserFn[_A, _B]) -> None:
        """Wrap the parser function `p` into a `Parser` object."""

        super().__init__()

        self._name = ''
        self.define(p)

    @property
    def name(self) -> str:
        return self._name

    def named(self, name: str) -> ta.Self:
        """
        Specify the name of the parser for easier debugging, returning the parser itself. The name is used in parse
        error messages and in the debug-level parsing log.

        >>> expr = (a("x") + a("y")).named("expr")
        >>> expr.name
        'expr'

        >>> expr = a("x") + a("y")
        >>> expr.name
        "('x', 'y')"
        """

        self._name = name
        return self

    def define(self, p: Parser[_A, _B] | ParserFn[_A, _B]) -> None:
        """
        Define the parser created earlier as a forward declaration. Use `p = forward_decl()` in combination with
        `p.define(...)` to define recursive parsers - see `forward_decl()`.
        """

        # Outside of debug mode the parser function is installed directly as the instance's `run`, shadowing the logging
        # `run` method.
        f = getattr(p, 'run', p)
        if _DEBUG:
            setattr(self, '_run', f)
        else:
            setattr(self, 'run', f)

        # Note that a plain function's docstring, if it has one, becomes the parser's name.
        if (name := getattr(p, 'name', p.__doc__)) is not None:
            self.named(name)

    def run(self, tokens: ta.Sequence[_A], s: State) -> tuple[_B, State]:
        """
        Run the parser against the tokens with the specified parsing state, raising `NoParseError` if it fails to parse
        them.

        The parsing state includes the current position in the sequence being parsed, and the position of the rightmost
        token that has been consumed while parsing for better error messages.

        This is a lower-level interface used to implement parsers in terms of other parsers. Otherwise use
        `Parser.parse(tokens)`, and let the parser object take care of the parsing state.
        """

        if _DEBUG:
            log.debug('trying %s', self._name)
        return self._run(tokens, s)

    def _run(self, tokens: ta.Sequence[_A], s: State) -> tuple[_B, State]:
        raise NotImplementedError('you must define() a parser')

    @staticmethod
    def _format_error_msg(tokens: ta.Sequence[ta.Any], e: NoParseError) -> str:
        if len(tokens) > (max_pos := e.state.max):
            t = tokens[max_pos]
            if isinstance(t, Token):
                if t.start is None or t.end is None:
                    loc = ''
                else:
                    s_line, s_pos = t.start
                    e_line, e_pos = t.end
                    loc = f'{s_line},{s_pos}-{e_line},{e_pos}: '
                msg = f'{loc}{e.msg}: {t.value!r}'
            elif isinstance(t, str):
                msg = f'{e.msg}: {t!r}'
            else:
                msg = f'{e.msg}: {t}'

        else:
            msg = 'got unexpected end of input'

        if isinstance(e_parser := e.state.parser, Parser):
            msg = f'{msg}, expected: {e_parser.name}'

        return msg

    def parse(self, tokens: ta.Sequence[_A]) -> _B:
        """
        Parse the sequence of tokens and return the parsed value, raising `NoParseError` if it fails to parse them.

        Although any sequence of objects can be parsed (including a `str`, as a sequence of `str` chars), the
        recommended way is parsing sequences of `Token` objects, as produced by a regexp-based tokenizer from
        `lexer.make_tokenizer()`. This gives more readable parsing error messages (as `Token` objects contain their
        position in the source file) and good separation of the lexical and syntactic levels of the grammar.
        """

        try:
            tree, _ = self.run(tokens, State(0, 0, None))
            return tree

        except NoParseError as e:
            e.msg = self._format_error_msg(tokens, e)
            raise

    @ta.overload
    def __add__(self, other: _IgnoredParser[_A]) -> Parser[_A, _B]: ...  # type: ignore[overload-overlap]

    @ta.overload
    def __add__(self, other: Parser[_A, _C]) -> _TupleParser[_A, tuple[_B, _C]]: ...

    def __add__(
            self,
            other: _IgnoredParser[_A] | Parser[_A, _C],
    ) -> Parser[_A, _B] | _TupleParser[_A, tuple[_B, _C]]:
        """
        Sequential combination of parsers. It runs this parser, then the other parser.

        The return value of the resulting parser is a tuple of each parsed value in the sum of parsers. We merge all
        parsing results of `p1 + p2 + ... + pN` into a single tuple. It means that the parsing result may be a 2-tuple,
        a 3-tuple, a 4-tuple, etc. of parsed values. You avoid this by transforming the parsed pair into a new value
        using the `>>` combinator.

        You can also skip some parsing results in the resulting parsers by using `-p` or `skip(p)` for some parsers in
        your sum of parsers. It means that the parsing result might be a single value, not a tuple of parsed values. See
        the docs for `Parser.__neg__()` for more examples.

        >>> expr = a("x") + a("y")
        >>> expr.parse("xy")
        ('x', 'y')

        >>> expr = a("x") + a("y") + a("z")
        >>> expr.parse("xyz")
        ('x', 'y', 'z')

        >>> expr = a("x") + a("y")
        >>> expr.parse("xz")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'z', expected: 'y'
        """

        name = f'({self.name}, {other.name})'

        if isinstance(other, _IgnoredParser):
            @Parser
            def ignored_right(tokens: ta.Sequence[_A], s: State) -> tuple[_B, State]:
                v, s2 = self.run(tokens, s)
                _, s3 = other.run(tokens, s2)
                return v, s3

            return ignored_right.named(name)

        def merge(v1: ta.Any, v2: ta.Any) -> _Tuple:
            if isinstance(v1, _Tuple):
                return _Tuple((*v1, v2))
            else:
                return _Tuple((v1, v2))

        @_TupleParser
        def _add(tokens: ta.Sequence[_A], s: State) -> tuple[tuple[_B, _C], State]:
            v1, s2 = self.run(tokens, s)
            v2, s3 = other.run(tokens, s2)
            return ta.cast('tuple[_B, _C]', merge(v1, v2)), s3

        _add.named(name)
        return _add

    def __or__(self, other: Parser[_A, _C]) -> Parser[_A, _B | _C]:
        """
        Choice combination of parsers. It runs this parser and returns its result. If the parser fails, it runs the
        other parser.

        >>> expr = a("x") | a("y")
        >>> expr.parse("x")
        'x'
        >>> expr.parse("y")
        'y'
        >>> expr.parse("z")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'z', expected: 'x' or 'y'
        """

        @Parser
        def _or(tokens: ta.Sequence[_A], s: State) -> tuple[_B | _C, State]:
            try:
                return self.run(tokens, s)
            except NoParseError as e:
                state = e.state

            try:
                return other.run(tokens, State(s.pos, state.max, state.parser))
            except NoParseError as e:
                if s.pos == e.state.max:
                    e.state = State(e.state.pos, e.state.max, _or)
                raise

        return _or.named(f'{self.name} or {other.name}')

    def __rshift__(self, f: ta.Callable[[_B], _C]) -> Parser[_A, _C]:
        """
        Transform the parsing result by applying the specified function, for transforming the parsed value into another
        value before including it into the parse tree (the AST).

        >>> def make_canonical_name(s):
        ...     return s.lower()
        >>> expr = (a("D") | a("d")) >> make_canonical_name
        >>> expr.parse("D")
        'd'
        >>> expr.parse("d")
        'd'
        """

        @Parser
        def _shift(tokens: ta.Sequence[_A], s: State) -> tuple[_C, State]:
            v, s2 = self.run(tokens, s)
            return f(v), s2

        return _shift.named(self.name)

    def bind(self, f: ta.Callable[[_B], Parser[_A, _C]]) -> Parser[_A, _C]:
        """
        Bind the parser to a monadic function that returns a new parser. Also known as `>>=` in Haskell.

        Any context-free grammar can be parsed without resorting to `bind`. Due to its poor performance, only use it
        when really needed.
        """

        @Parser
        def _bind(tokens: ta.Sequence[_A], s: State) -> tuple[_C, State]:
            v, s2 = self.run(tokens, s)
            return f(v).run(tokens, s2)

        return _bind.named(f'({self.name} >>=)')

    def __neg__(self) -> _IgnoredParser[_A]:
        """
        Return a parser that parses the same tokens, but its parsing result is ignored by the sequential `+` combinator.
        You can use it for throwing away elements of concrete syntax (e.g. `","`, `";"`).

        >>> expr = -a("x") + a("y")
        >>> expr.parse("xy")
        'y'

        >>> expr = a("x") + -a("y")
        >>> expr.parse("xy")
        'x'

        >>> expr = a("x") + -a("y") + a("z")
        >>> expr.parse("xyz")
        ('x', 'z')

        >>> expr = -a("x") + a("y") + -a("z")
        >>> expr.parse("xyz")
        'y'

        >>> expr = -a("x") + a("y")
        >>> expr.parse("yz")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'y', expected: 'x'

        >>> expr = a("x") + -a("y")
        >>> expr.parse("xz")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'z', expected: 'y'

        The resulting parser should not be passed to any combinators other than `+`, and there should be at least one
        non-skipped value in a `p1 + p2 + ... + pN`. The parsed value of `-p` is an internal `_Ignored` object, not
        intended for actual use.
        """

        return _IgnoredParser(self)


class _Tuple(tuple):
    """The result of a sequence of parsers combined with `+`, to which the results of further parsers are appended."""

    __slots__ = ()


class _TupleParser(Parser[_A, _B]):
    @ta.overload  # type: ignore[override]
    def __add__(self, other: _IgnoredParser[_A]) -> _TupleParser[_A, _B]: ...

    @ta.overload
    def __add__(self, other: Parser[_A, ta.Any]) -> Parser[_A, ta.Any]: ...

    def __add__(
            self,
            other: _IgnoredParser[_A] | Parser[_A, ta.Any],
    ) -> _TupleParser[_A, _B] | Parser[_A, ta.Any]:
        return super().__add__(other)


class _Ignored:  # noqa: PLW1641
    def __init__(self, value: ta.Any) -> None:
        super().__init__()

        self.value = value

    def __repr__(self) -> str:
        return f'_Ignored({self.value!r})'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Ignored) and self.value == other.value


class _IgnoredParser(Parser[_A, ta.Any]):
    def __init__(self, p: Parser[_A, ta.Any] | ParserFn[_A, ta.Any]) -> None:
        super().__init__(p)

        run = self._run if _DEBUG else self.run

        # This must not have a docstring, which would replace the name of `p` as the parser's name.
        def ignored(tokens: ta.Sequence[_A], s: State) -> tuple[ta.Any, State]:
            v, s2 = run(tokens, s)
            return (v if isinstance(v, _Ignored) else _Ignored(v)), s2

        self.define(ignored)

    @ta.overload  # type: ignore[override]
    def __add__(self, other: _IgnoredParser[_A]) -> _IgnoredParser[_A]: ...

    @ta.overload
    def __add__(self, other: Parser[_A, _C]) -> Parser[_A, _C]: ...

    def __add__(
            self,
            other: _IgnoredParser[_A] | Parser[_A, _C],
    ) -> _IgnoredParser[_A] | Parser[_A, _C]:
        name = f'({self.name}, {other.name})'

        if isinstance(other, _IgnoredParser):
            @_IgnoredParser
            def ip(tokens: ta.Sequence[_A], s: State) -> tuple[ta.Any, State]:
                _, s2 = self.run(tokens, s)
                v, s3 = other.run(tokens, s2)
                return v, s3

            return ip.named(name)

        @Parser
        def p(tokens: ta.Sequence[_A], s: State) -> tuple[_C, State]:
            _, s2 = self.run(tokens, s)
            v, s3 = other.run(tokens, s2)
            return v, s3

        return p.named(name)


##


@Parser
def finished(tokens: ta.Sequence[ta.Any], s: State) -> tuple[None, State]:
    """A parser that throws an exception if there are any unparsed tokens left in the sequence."""

    if s.pos >= len(tokens):
        return None, s

    s2 = State(s.pos, s.max, finished if s.pos == s.max else s.parser)
    raise NoParseError('got unexpected token', s2)


finished.named('end of input')


def some(pred: ta.Callable[[_A], bool]) -> Parser[_A, _A]:
    """
    Return a parser that parses a token if it satisfies the predicate `pred`.

    >>> expr = some(lambda s: s.isalpha()).named('alpha')
    >>> expr.parse("x")
    'x'
    >>> expr.parse("y")
    'y'
    >>> expr.parse("1")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: '1', expected: alpha

    This is a fairly slow combinator. For a parser of a `Token` by its type (and maybe its value), `tok(type[, value])`
    may be used instead.
    """

    @Parser
    def _some(tokens: ta.Sequence[_A], s: State) -> tuple[_A, State]:
        if s.pos >= len(tokens):
            s2 = State(s.pos, s.max, _some if s.pos == s.max else s.parser)
            raise NoParseError('got unexpected end of input', s2)

        t = tokens[s.pos]
        if pred(t):
            pos = s.pos + 1
            s2 = State(pos, max(pos, s.max), s.parser)
            if _DEBUG:
                log.debug('*matched* %r, new state = %s', t, s2)
            return t, s2

        s2 = State(s.pos, s.max, _some if s.pos == s.max else s.parser)
        if _DEBUG and isinstance(s2.parser, Parser):
            log.debug('failed %r, state = %s, expected = %s', t, s2, s2.parser.name)
        raise NoParseError('got unexpected token', s2)

    return _some.named('some(...)')


def a(value: _A) -> Parser[_A, _A]:
    """
    Return a parser that parses a token if it's equal to `value`.

    >>> expr = a("x")
    >>> expr.parse("x")
    'x'
    >>> expr.parse("y")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: 'y', expected: 'x'
    """

    name = getattr(value, 'name', value)

    def eq_value(t: _A) -> bool:
        return t == value

    return some(eq_value).named(repr(name))


def tok(type: str, value: str | None = None) -> Parser[Token, str]:
    """
    Return a parser that parses a `Token` and returns the string value of the token. It matches any token of the
    specified `type`, or, if a `value` is given, a specific token by its type and value.

    >>> expr = tok("expr")
    >>> expr.parse([Token("expr", "foo")])
    'foo'
    >>> expr.parse([Token("expr", "bar")])
    'bar'
    >>> expr.parse([Token("op", "=")])
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: '=', expected: expr

    >>> expr = tok("op", "=")
    >>> expr.parse([Token("op", "=")])
    '='
    >>> expr.parse([Token("op", "+")])
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: '+', expected: '='
    """

    def eq_type(t: Token) -> bool:
        return t.type == type

    if value is not None:
        p = a(Token(type, value))
    else:
        p = some(eq_type).named(type)

    return (p >> (lambda t: t.value)).named(p.name)


def pure(x: _A) -> Parser[ta.Any, _A]:
    """
    Wrap any object into a parser. A pure parser doesn't touch the tokens sequence, it just returns its pure `x` value.
    Also known as `return` in Haskell.
    """

    @Parser
    def _pure(_: ta.Sequence[ta.Any], s: State) -> tuple[_A, State]:
        return x, s

    return _pure.named(f'(pure {x!r})')


def maybe(p: Parser[_A, _B]) -> Parser[_A, _B | None]:
    """
    Return a parser that returns `None` if the parser `p` fails.

    >>> expr = maybe(a("x"))
    >>> expr.parse("x")
    'x'
    >>> expr.parse("y") is None
    True
    """

    return (p | pure(None)).named(f'[ {p.name} ]')


def skip(p: Parser[_A, ta.Any]) -> _IgnoredParser[_A]:
    """An alias for `-p` - see `Parser.__neg__()`."""

    return -p


def many(p: Parser[_A, _B]) -> Parser[_A, list[_B]]:
    """
    Return a parser that applies the parser `p` as many times as it succeeds at parsing the tokens. The parsed value is
    a list of the sequentially parsed values.

    >>> expr = many(a("x"))
    >>> expr.parse("x")
    ['x']
    >>> expr.parse("xx")
    ['x', 'x']
    >>> expr.parse("xxxy")
    ['x', 'x', 'x']
    >>> expr.parse("y")
    []
    """

    @Parser
    def _many(tokens: ta.Sequence[_A], s: State) -> tuple[list[_B], State]:
        res: list[_B] = []
        try:
            while True:
                v, s = p.run(tokens, s)
                res.append(v)

        except NoParseError as e:
            s2 = State(s.pos, e.state.max, e.state.parser)
            if _DEBUG:
                log.debug('*matched* %d instances of %s, new state = %s', len(res), _many.name, s2)
            return res, s2

    return _many.named(f'{{ {p.name} }}')


def oneplus(p: Parser[_A, _B]) -> Parser[_A, list[_B]]:
    """
    Return a parser that applies the parser `p` one or more times - as opposed to `many(p)`, which applies it zero or
    more times.

    >>> expr = oneplus(a("x"))
    >>> expr.parse("x")
    ['x']
    >>> expr.parse("xx")
    ['x', 'x']
    >>> expr.parse("y")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: 'y', expected: 'x'
    """

    many_p = many(p)

    @Parser
    def _oneplus(tokens: ta.Sequence[_A], s: State) -> tuple[list[_B], State]:
        v1, s2 = p.run(tokens, s)
        v2, s3 = many_p.run(tokens, s2)
        return [v1, *v2], s3

    return _oneplus.named(f'({p.name}, {{ {p.name} }})')


def forward_decl() -> Parser[ta.Any, ta.Any]:
    """
    Return an undefined parser that can be used as a forward declaration. Use `p = forward_decl()` in combination with
    `p.define(...)` to define recursive parsers.

    >>> expr = forward_decl()
    >>> expr.define(a("x") + maybe(expr) + a("y"))
    >>> expr.parse("xxyy")
    ('x', ('x', None, 'y'), 'y')
    >>> expr.parse("xxy")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected end of input, expected: 'y'

    For static type checking, the forward declaration should be given a type hint, against which `p.define(...)` will
    be checked later:

        p: Parser[str, int] = forward_decl()
        p.define(a("x"))  # Type checker error
        p.define(a("1") >> int)  # OK
    """

    @Parser
    def f(_tokens: ta.Any, _s: ta.Any) -> ta.Any:
        raise NotImplementedError('you must define() a forward_decl somewhere')

    return f.named('forward_decl()')
