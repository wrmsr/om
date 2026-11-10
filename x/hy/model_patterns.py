"""Parser combinators for pattern-matching Hy model trees."""
import functools
import itertools
import math
import operator
import typing as ta

from .funcparserlib.parser import NoParseError
from .funcparserlib.parser import Parser
from .funcparserlib.parser import State
from .funcparserlib.parser import _IgnoredParser
from .funcparserlib.parser import a
from .funcparserlib.parser import finished
from .funcparserlib.parser import many
from .funcparserlib.parser import skip
from .funcparserlib.parser import some
from .models import Bytes
from .models import Complex
from .models import Dict
from .models import Expression
from .models import Float
from .models import Integer
from .models import Keyword
from .models import List
from .models import Object
from .models import Sequence
from .models import String
from .models import Symbol
from .models import Tuple


TokenT = ta.TypeVar('TokenT')
ValueT = ta.TypeVar('ValueT')

ModelParser: ta.TypeAlias = Parser[Object, ta.Any]


##


FORM: ModelParser = some(lambda _: True).named('form')
SYM: ModelParser = some(lambda x: isinstance(x, Symbol)).named('Symbol')
KEYWORD: ModelParser = some(lambda x: isinstance(x, Keyword)).named('Keyword')
STR: ModelParser = some(lambda x: isinstance(x, String)).named('String')
LITERAL: ModelParser = some(lambda x: isinstance(x, (String, Integer, Float, Complex, Bytes))).named('literal')


def sym(wanted: str) -> _IgnoredParser[Object]:
    """
    Match and skip a symbol with a name equal to the string ``wanted``. You can begin the string with ``":"`` to check
    for a keyword instead.
    """

    return _sym(wanted, skip)


def keepsym(wanted: str) -> ModelParser:
    """As :func:`sym`, but the object is kept instead of skipped."""

    return _sym(wanted)


def _sym(wanted: str, f: ta.Callable[..., ta.Any] = lambda x: x) -> ta.Any:
    name = '`' + wanted + '`'
    if wanted.startswith(':'):
        return f(a(Keyword(wanted[1:]))).named(name)
    return f(some(lambda x: x == Symbol(wanted))).named(name)


def whole(parsers: ta.Sequence[ModelParser]) -> Parser[Object, tuple[ta.Any, ...]]:
    """
    Match the parsers in the given list one after another, then expect the end of the input. The result is always a
    tuple.
    """

    if len(parsers) == 0:
        return finished >> (lambda _: ())
    non_ignored_parsers = sum(
        not isinstance(p, _IgnoredParser)
        for p in parsers)
    if len(parsers) == 1:
        return ((parsers[0] >> (lambda r: (r,) if non_ignored_parsers else ())) +
                skip(finished))
    return ((
        functools.reduce(operator.add, parsers) >> (lambda r:
            () if non_ignored_parsers == 0 else
            (r,) if non_ignored_parsers == 1 else
            r)) +
            skip(finished))


def _grouped(
        group_type: type[Sequence],
        syntax_example: str,
        name: str | None,
        parsers: ta.Sequence[ModelParser],
) -> ModelParser:
    return (
        some(lambda x: isinstance(x, group_type)).named(name or
                                                        f'{group_type.__name__} (i.e., `{syntax_example}`)') >>
        (lambda x: group_type(whole(parsers).parse(x)).replace(x, recursive=False))
    )


def brackets(*parsers: ModelParser, name: str | None = None) -> ModelParser:
    """Match the given parsers inside square brackets (a :class:`List <hy.models.List>`)."""

    return _grouped(List, '[ … ]', name, parsers)


def in_tuple(*parsers: ModelParser, name: str | None = None) -> ModelParser:
    """Match the given parsers inside a :class:`Tuple <hy.models.Tuple>`."""

    return _grouped(Tuple, '#( … )', name, parsers)


def braces(*parsers: ModelParser, name: str | None = None) -> ModelParser:
    """Match the given parsers inside curly braces (a :class:`Dict <hy.models.Dict>`)."""

    return _grouped(Dict, '{ … }', name, parsers)


def pexpr(*parsers: ModelParser, name: str | None = None) -> ModelParser:
    """Match the given parsers inside a parenthesized :class:`Expression <hy.models.Expression>`."""

    return _grouped(Expression, '( … )', name, parsers)


def dolike(head: str) -> ModelParser:
    """Parse a :hy:func:`do`-like expression. ``head`` is a string used to construct a symbol for the head."""

    return pexpr(sym(head), many(FORM)) >> (lambda r: r[0])


def notpexpr(*disallowed_heads: str) -> ModelParser:
    """Parse any object other than an expression headed by a symbol whose name is equal to one of the given strings."""

    heads = list(map(Symbol, disallowed_heads))
    return some(
        lambda x: not (isinstance(x, Expression) and x and x[0] in heads),
    )


def unpack(kind: str, content_type: type | tuple[type, ...] | None = None) -> ModelParser:
    """
    Parse an unpacking form, returning it unchanged. ``kind`` should be ``"iterable"``, ``"mapping"``, or ``"either"``.
    If ``content_type`` is provided, the parser also checks that the unpacking form has exactly one argument and that
    argument inherits from ``content_type``.
    """

    return some(lambda x: (
        isinstance(x, Expression) and
        len(x) > 0 and
        x[0] in [
            Symbol('unpack-' + tail)
            for tail in (['iterable', 'mapping'] if kind == 'either' else [kind])
        ] and
        (
            content_type is None or
            (len(x) == 2 and isinstance(x[1], content_type))
        )
    ))


def times(lo: int, hi: float, parser: Parser[TokenT, ValueT]) -> Parser[TokenT, list[ValueT]]:
    """
    Parse ``parser`` several times (from ``lo`` to ``hi``, inclusive) in a row. ``hi`` can be ``float('inf')``. The
    result is a list no matter the number of instances.
    """

    @Parser
    def f(tokens: ta.Sequence[TokenT], s: State) -> tuple[list[ValueT], State]:
        result = []
        for _ in range(lo):
            (v, s) = parser.run(tokens, s)
            result.append(v)
        end = s.max
        try:
            for _ in itertools.repeat(1) if math.isinf(hi) else range(ta.cast(int, hi) - lo):
                (v, s) = parser.run(tokens, s)
                result.append(v)
        except NoParseError as e:
            end = e.state.max
        return result, State(s.pos, end)

    return f


class Tag(ta.NamedTuple):
    tag: str
    value: ta.Any


def tag(tag_name: str, parser: Parser[TokenT, ValueT]) -> Parser[TokenT, Tag]:
    """
    Match on ``parser`` and produce an instance of :class:`Tag` with ``tag`` set to ``tag_name`` and ``value`` set to
    result of matching ``parser``.
    """

    return parser >> (lambda x: Tag(tag_name, x))


def parse_if(pred: ta.Callable[[TokenT], bool], parser: Parser[TokenT, ValueT]) -> Parser[TokenT, ValueT]:
    """Return a parser that parses a token with ``parser`` if it satisfies the predicate ``pred``."""

    @Parser
    def _parse_if(tokens: ta.Sequence[TokenT], s: State) -> tuple[ValueT, State]:
        some(pred).run(tokens, s)
        return parser.run(tokens, s)

    return _parse_if
