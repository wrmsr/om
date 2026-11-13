import contextlib
import contextvars
import functools
import itertools
import math
import operator
import string.templatelib
import typing as ta

from omcore import lang

from .errors import HyWrapperError


# The reader depends on models, so is imported lazily here.
if ta.TYPE_CHECKING:
    from .reader import hyreader as reader_hyreader
    from .reader import mangling as reader_mangling
    from .reader import reader as reader_reader
else:
    reader_hyreader = lang.proxy_import('.reader.hyreader', __package__)
    reader_mangling = lang.proxy_import('.reader.mangling', __package__)
    reader_reader = lang.proxy_import('.reader.reader', __package__)


_ModelWrapper: ta.TypeAlias = ta.Callable[[ta.Any, '_ModelWrapping'], 'Object']


##


_PRETTY: contextvars.ContextVar[bool] = contextvars.ContextVar(f'{__name__}._PRETTY', default=True)


@contextlib.contextmanager
def pretty(pretty: bool = True) -> ta.Iterator[None]:
    """Context manager to temporarily enable or disable pretty-printing of Hy model reprs in the current context."""

    token = _PRETTY.set(pretty)
    try:
        yield
    finally:
        _PRETTY.reset(token)


def repr_indent(obj: object) -> str:
    return repr(obj).replace('\n', '\n  ')


## Base


class Object:
    """
    An abstract base class for Hy models, which represent forms.

    The position properties (`start_line`, `end_line`, `start_column`, `end_column`) are each 1-based and inclusive. For
    example, a symbol `abc` starting at the first column would have `start_column` 1 and `end_column` 3.
    """

    _start_line: int
    _end_line: int
    _start_column: int
    _end_column: int

    source: str | None
    filename: str | None
    reader: reader_hyreader.HyReader

    properties: ta.ClassVar[ta.Sequence[str]] = (
        '_start_line',
        '_end_line',
        '_start_column',
        '_end_column',
    )

    def replace(self, other: Object, recursive: bool = False) -> ta.Self:
        """Copy any of the position properties of `other` which are unset on this model, and return this model."""

        if not isinstance(other, Object):
            raise TypeError(f"Can't replace a non Hy object '{other!r}' with a Hy object '{self!r}'")

        for attr in self.properties:
            if not hasattr(self, attr) and hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

        return self

    @property
    def start_line(self) -> int:
        return getattr(self, '_start_line', 1)

    @start_line.setter
    def start_line(self, value: int) -> None:
        self._start_line = value

    @property
    def start_column(self) -> int:
        return getattr(self, '_start_column', 1)

    @start_column.setter
    def start_column(self, value: int) -> None:
        self._start_column = value

    @property
    def end_line(self) -> int:
        return getattr(self, '_end_line', 1)

    @end_line.setter
    def end_line(self, value: int) -> None:
        self._end_line = value

    @property
    def end_column(self) -> int:
        return getattr(self, '_end_column', 1)

    @end_column.setter
    def end_column(self, value: int) -> None:
        self._end_column = value

    def __repr__(self) -> str:
        return f'hy.models.{self.__class__.__name__}({super().__repr__()})'

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        # We need this in case another superclass of our subclass overrides `__ne__`.
        return object.__ne__(self, other)

    def __hash__(self) -> int:
        return super().__hash__()


def is_unpack(kind: str, x: object) -> bool:
    return isinstance(x, Expression) and len(x) > 0 and x[0] == Symbol('unpack-' + kind)


## Atoms


class String(Object, str):  # type: ignore[misc]  # Models use Object.replace rather than str.replace.
    """
    Represents a literal string (:class:`str`).

    :ivar brackets: The custom delimiter used by the bracket string that parsed to this object, or :data:`None` if it
      wasn't a bracket string. The outer square brackets and ``#`` aren't included, so the ``brackets`` attribute of the
      literal ``#[[hello]]`` is the empty string.
    """

    __match_args__ = ('_as_str',)
    __slots__ = ()

    brackets: str | None

    def __new__(cls, s: object = None, brackets: str | None = None) -> ta.Self:
        value = super().__new__(cls, s)
        if brackets is not None and f']{brackets}]' in value:
            raise ValueError(f'Syntactically illegal bracket string: {s!r}')

        value.brackets = brackets
        return value

    def __repr__(self) -> str:
        brackets = '' if self.brackets is None else f', brackets={self.brackets!r}'
        return f'hy.models.String({super(Object, self).__repr__()}{brackets})'

    def __add__(self, other: str) -> ta.Self:
        return self.__class__(super().__add__(other))

    @property
    def _as_str(self) -> str:
        return str(self)


class Bytes(Object, bytes):  # type: ignore[misc]  # Models use Object.replace rather than bytes.replace.
    """Represents a literal bytestring (:class:`bytes`)."""

    __match_args__ = ('_as_bytes',)

    @property
    def _as_bytes(self) -> bytes:
        return bytes(self)


class Symbol(Object, str):  # type: ignore[misc]  # Models use Object.replace rather than str.replace.
    """
    Represents a symbol.

    Symbol objects behave like strings under operations like :hy:func:`get <hy.pyops.get>`, :func:`len`, and
    :class:`bool`; in particular, ``(bool (hy.models.Symbol "False"))`` is true. Use :hy:func:`hy.eval` to evaluate a
    symbol.
    """

    __match_args__ = ('_as_str',)
    __slots__ = ()

    def __new__(cls, s: object, from_parser: bool = False) -> Symbol:  # noqa: PYI034
        s = str(s)

        if not from_parser:
            # Check that the symbol is syntactically legal.
            sym = reader_hyreader.as_identifier(s)
            if not isinstance(sym, Symbol):
                raise ValueError(f'Syntactically illegal symbol: {s!r}')
            return sym

        return super().__new__(cls, s)

    @property
    def _as_str(self) -> str:
        return str(self)


@functools.total_ordering
class Keyword(Object):
    """
    Represents a keyword, such as ``:foo``.

    :ivar name: The string content of the keyword, not including the leading ``:``. No mangling is performed.
    """

    __match_args__ = ('name',)

    _sentinel: ta.ClassVar[object] = object()

    name: str

    def __init__(self, value: object, from_parser: bool = False) -> None:
        super().__init__()

        value = str(value)

        # Unless it came from the parser, check that the keyword is syntactically legal.
        if (
            not from_parser and
            value and
            (
                '.' in value or
                any(reader_reader.isnormalizedspace(c) for c in value) or
                not reader_hyreader.HyReader.NON_IDENT.isdisjoint(value)
            )
        ):
            raise ValueError(f'Syntactically illegal keyword: {":" + value!r}')

        self.name = value

    def __repr__(self) -> str:
        return f'hy.models.{self.__class__.__name__}({self.name!r})'

    def __str__(self) -> str:
        return f':{self.name}'

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Keyword):
            return NotImplemented
        return self.name == other.name

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Keyword):
            return NotImplemented
        return self.name != other.name

    def __lt__(self, other: object) -> bool:
        """Keywords behave like strings under comparison operators, but are incomparable to actual ``str`` objects."""

        if not isinstance(other, Keyword):
            return NotImplemented
        return self.name < other.name

    def __bool__(self) -> bool:
        """The empty keyword ``:`` is false. All others are true."""

        return bool(self.name)

    def __call__(self, data: ta.Any, default: ta.Any = _sentinel) -> ta.Any:
        """
        Get the element of ``data`` named ``(hy.mangle self.name)``. Thus, ``(:foo bar)`` is equivalent to ``(get bar
        "foo")`` (which is different from ``(get bar :foo)``; dictionary keys are typically strings, not
        :class:`hy.models.Keyword` objects).

        The optional second parameter is a default value; if provided, any :class:`KeyError` from :hy:func:`get
        <hy.pyops.get>` will be caught, and the default returned instead.
        """

        try:
            return data[reader_mangling.mangle(self.name)]
        except KeyError:
            if default is Keyword._sentinel:
                raise
            return default


## Numbers


def strip_digit_separators(number: ta.Any) -> ta.Any:
    # Don't strip a `_` or `,` if it's the first character, as `_42` and `,42` aren't valid numbers.
    if isinstance(number, str) and len(number) > 1:
        return number[0] + number[1:].replace('_', '').replace(',', '')

    return number


def check_inf_nan_cap(arg: object, value: float) -> None:
    if not isinstance(arg, str):
        return

    if math.isinf(value) and 'i' in arg.lower() and 'Inf' not in arg:
        raise ValueError('Inf must be capitalized as "Inf"')
    if math.isnan(value) and 'NaN' not in arg:
        raise ValueError('NaN must be capitalized as "NaN"')


class Integer(Object, int):
    """Represents a literal integer (:class:`int`)."""

    __match_args__ = ('_as_int',)

    def __new__(cls, number: object, *_args: ta.Any, **_kwargs: ta.Any) -> ta.Self:
        stripped = strip_digit_separators(number)

        # `base=0` fails on decimal integers with a leading 0, so it's only used for strings which aren't plain digits.
        if isinstance(number, str) and not number.isdigit():
            value = int(stripped, base=0)
        else:
            value = int(stripped)

        return super().__new__(cls, value)

    @property
    def _as_int(self) -> int:
        return int(self)


class Float(Object, float):
    """Represents a literal floating-point real number (:class:`float`)."""

    __match_args__ = ('_as_float',)

    def __new__(cls, num: object, *_args: ta.Any, **_kwargs: ta.Any) -> ta.Self:
        value = super().__new__(cls, strip_digit_separators(num))
        check_inf_nan_cap(num, value)
        return value

    @property
    def _as_float(self) -> float:
        return float(self)


class Complex(Object, complex):
    """
    Represents a literal floating-point complex number (:class:`complex`). If ``real`` is itself a :class:`complex`
    object, its imaginary part is extracted and added to the imaginary part of the new model, but ``imag``, if provided,
    must be real.
    """

    __match_args__ = ('real', 'imag')

    def __new__(
            cls,
            real: ta.Any,
            imag: ta.Any = 0,
            *_args: ta.Any,
            **_kwargs: ta.Any,
    ) -> ta.Self:
        if isinstance(real, str):
            value = super().__new__(cls, strip_digit_separators(real))

            p1, _, p2 = real.lstrip('+-').replace('-', '+').partition('+')
            check_inf_nan_cap(p1, value.imag if 'j' in p1.lower() else value.real)
            if p2:
                check_inf_nan_cap(p2, value.imag)

            return value

        if isinstance(imag, complex):
            raise TypeError('`imag` must be real')

        if isinstance(real, complex):
            # This is deprecated by Python 3.14's `complex`, so extract the imaginary part before passing through.
            real, imag = real.real, imag + real.imag

        return super().__new__(cls, real, imag)


## Sequences


class Sequence(Object, tuple[ta.Any, ...]):
    """
    An abstract base class for sequence-like forms. Sequence models can be operated on like tuples: you can iterate over
    them, index into them, and append them with ``+``, but you can't add, remove, or replace elements. Appending a
    sequence to another iterable object reuses the class of the left-hand-side object, which is useful when e.g. you
    want to concatenate models in a macro.

    When you're recursively descending through a tree of models, testing a model with ``(isinstance x
    hy.models.Sequence)`` is useful for deciding whether to iterate over ``x``. You can also use the Hyrule function
    :hy:func:`coll? <hyrule.coll?>` for this purpose.
    """

    __slots__ = ()

    _extra_kwargs: ta.ClassVar[tuple[str, ...]] = ()

    def replace(self, other: Object, recursive: bool = True) -> ta.Self:
        """
        As :meth:`Object.replace`, but if ``recursive``, a copy of this model is returned, with the replacement applied
        to each of its (wrapped) children.
        """

        if not recursive:
            return Object.replace(self, other)

        new = type(self)(
            (replace_hy_obj(x, other) for x in self),
            **{k: getattr(self, k) for k in self._extra_kwargs},
        )

        return Object.replace(Object.replace(new, self), other)

    def __add__(self, other: tuple[ta.Any, ...] | list[ta.Any]) -> ta.Self:
        return self.__class__(super().__add__(tuple(other) if isinstance(other, list) else other))

    def __getitem__(self, item: ta.SupportsIndex | slice) -> ta.Any:
        ret = super().__getitem__(item)

        if isinstance(item, slice):
            return self.__class__(ret)

        return ret

    def __repr__(self) -> str:
        return self._pretty_str() if _PRETTY.get() else super().__repr__()

    def __str__(self) -> str:
        return self._pretty_str()

    def _pretty_str(self) -> str:
        with pretty():
            if not self:
                return f'hy.models.{self.__class__.__name__}()'

            items = ',\n  '.join(map(repr_indent, self))
            return f'hy.models.{self.__class__.__name__}([\n  {items}])'


class FComponent(Sequence):
    """
    An analog of :class:`ast.FormattedValue`. The first node in the contained sequence is the value being formatted. The
    rest of the sequence contains the nodes in the format spec (if any).
    """

    _extra_kwargs = ('conversion', 'expression', 'is_tstring')

    conversion: str | None
    expression: str | None
    is_tstring: bool

    def __new__(
            cls,
            s: ta.Iterable[ta.Any] | None = None,
            conversion: str | None = None,
            expression: str | None = None,
            is_tstring: bool = False,
    ) -> ta.Self:
        value = super().__new__(cls, ta.cast('ta.Iterable[ta.Any]', s))
        value.conversion = conversion
        value.expression = expression
        value.is_tstring = is_tstring
        return value

    def replace(self, other: Object, recursive: bool = True) -> ta.Self:
        super().replace(other, recursive)

        for attr in self._extra_kwargs:
            if hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

        return self

    def __repr__(self) -> str:
        return (
            f'hy.models.FComponent({super(Object, self).__repr__()}, '
            f'conversion={self.conversion!r}, '
            f'expression={self.expression!r}, '
            f'is_tstring={self.is_tstring!r})'
        )


def _string_in_fstring_node(string: str, node: Object) -> bool:
    if isinstance(node, String):
        return string in node

    if isinstance(node, (FComponent, FString)):
        return any(_string_in_fstring_node(string, child) for child in node)

    return False


def _join_adjacent_fstring_strings(nodes: ta.Iterable[ta.Any]) -> ta.Iterator[ta.Any]:
    for is_string, group in itertools.groupby(nodes, lambda x: isinstance(x, String)):
        if is_string:
            yield functools.reduce(operator.add, group)
        else:
            yield from group


class FString(Sequence):
    """
    Represents a format string or template string as an iterable collection of :class:`hy.models.String` and
    :class:`hy.models.FComponent`. The design mimics :class:`ast.JoinedStr`.

    :ivar brackets: As in :class:`hy.models.String`.
    :ivar is_tstring: Whether this represents a template string, rather than a format string.
    """

    _extra_kwargs = ('brackets', 'is_tstring')

    brackets: str | None
    is_tstring: bool

    def __new__(
            cls,
            s: ta.Iterable[ta.Any] | None = None,
            brackets: str | None = None,
            is_tstring: bool = False,
    ) -> ta.Self:
        # Adjacent string nodes are joined for the sake of equality testing.
        value = super().__new__(cls, _join_adjacent_fstring_strings(ta.cast('ta.Iterable[ta.Any]', s)))

        if brackets is not None and _string_in_fstring_node(f']{brackets}]', value):
            raise ValueError(f'Syntactically illegal bracket string: {s!r}')

        value.brackets = brackets
        value.is_tstring = is_tstring
        return value

    def __repr__(self) -> str:
        return self._suffixize(super().__repr__())

    def __str__(self) -> str:
        return self._suffixize(super().__str__())

    def _suffixize(self, x: str) -> str:
        if self.brackets is None and not self.is_tstring:
            return x

        args = []
        if self.brackets is not None:
            args.append(f'brackets={self.brackets!r}')
        if self.is_tstring:
            args.append(f'is_tstring={self.is_tstring!r}')

        x = x[:-1]  # Clip off the final close paren.
        return x + ('' if x[-1] == '(' else ', ') + ', '.join(args) + ')'


class List(Sequence):
    """
    Represents a literal :class:`list`.

    Many macros use this model type specially, for something other than defining a :class:`list`. For example,
    :hy:func:`defn` expects its function parameters as a square-bracket-delimited list, and :hy:func:`for` expects a
    list of iteration clauses.
    """


class Dict(Sequence):
    """
    Represents a literal :class:`dict`. ``keys``, ``values``, and ``items`` methods are provided, each returning a list,
    although this model type does none of the normalization of a real :class:`dict`. In the case of an odd number of
    child models, ``keys`` returns the last child whereas ``values`` and ``items`` ignore it.
    """

    def _pretty_str(self) -> str:
        with pretty():
            if not self:
                return 'hy.models.Dict()'

            pairs = []
            for k, v in zip(self[::2], self[1::2]):
                kr, vr = repr_indent(k), repr_indent(v)
                pairs.append(f'{kr},\n  {vr}\n  ' if '\n' in kr + vr else f'{kr}, {vr}')

            if len(self) % 2 == 1:
                pairs.append(f'{repr_indent(self[-1])}  # odd\n')

            items = ',\n  '.join(pairs)
            return f'hy.models.Dict([\n  {items}])'

    def keys(self) -> list[ta.Any]:
        return list(self[0::2])

    def values(self) -> list[ta.Any]:
        return list(self[1::2])

    def items(self) -> list[tuple[ta.Any, ta.Any]]:
        return list(zip(self.keys(), self.values()))


class Expression(Sequence):
    """Represents a parenthesized Hy expression."""


class Set(Sequence):
    """Represents a literal :class:`set`. Unlike actual sets, the model retains duplicates and the order of elements."""


class Tuple(Sequence):
    """Represents a literal :class:`tuple`."""


## Lazy


class Lazy(Object):
    """
    The output of :hy:func:`hy.read-many`. It represents a sequence of forms, and can be treated as an iterator. Reading
    each form lazily, only after evaluating the previous form, is necessary to handle reader macros correctly; see
    :hy:func:`hy.read-many`.
    """

    def __init__(self, gen: ta.Iterator[Object]) -> None:
        super().__init__()

        self._gen = gen

    def __iter__(self) -> ta.Iterator[Object]:
        yield from self._gen

    def __next__(self) -> Object:
        return self._gen.__next__()


## Wrapping


class _ModelWrapping:
    """State for a single top-level `as_model` call, used to detect self-referential structures."""

    def __init__(self) -> None:
        super().__init__()

        self._seen: set[int] = set()

    def wrap(self, x: object) -> Object:
        if id(x) in self._seen:
            raise HyWrapperError(f'Self-referential structure detected in {x!r}')

        wrapper = _MODEL_WRAPPERS.get(type(x))
        new = wrapper(x, self) if wrapper is not None else x
        if not isinstance(new, Object):
            raise HyWrapperError(f"Don't know how to wrap {type(x)!r}: {x!r}")

        if isinstance(x, Object):
            new = new.replace(x, recursive=False)

        return new

    def wrap_all(
            self,
            container: object,
            items: ta.Iterable[ta.Any],
            f: ta.Callable[[ta.Iterable[Object]], Object],
    ) -> Object:
        self._seen.add(id(container))
        try:
            return f(self.wrap(x) for x in items)
        finally:
            self._seen.discard(id(container))


def recwrap(f: ta.Callable[[ta.Iterable[Object]], Object]) -> _ModelWrapper:
    """Make a wrapper for a collection, constructing a model with `f` from its wrapped items."""

    def wrapper(xs: ta.Iterable[ta.Any], w: _ModelWrapping) -> Object:
        return w.wrap_all(xs, xs, f)

    return wrapper


def _wrap_interpolation(interp: string.templatelib.Interpolation, w: _ModelWrapping) -> Object:
    return FComponent(
        [w.wrap(interp.value), w.wrap(interp.format_spec)],
        conversion=interp.conversion,
        expression=interp.expression,
        is_tstring=True,
    )


def _wrap_fstring(fstr: FString, w: _ModelWrapping) -> Object:
    return FString(
        (w.wrap(x) for x in fstr),
        brackets=fstr.brackets,
        is_tstring=fstr.is_tstring,
    )


def _wrap_dict(d: ta.Mapping[ta.Any, ta.Any], w: _ModelWrapping) -> Object:
    return w.wrap_all(d, (x for kv in d.items() for x in kv), Dict)


# Keyed by exact type. Instances of model types not listed here are kept as they are.
_MODEL_WRAPPERS: ta.Mapping[type, _ModelWrapper] = {
    bool: lambda x, _: Symbol('True') if x else Symbol('False'),
    type(None): lambda x, _: Symbol('None'),

    str: lambda x, _: String(x),
    bytes: lambda x, _: Bytes(x),
    int: lambda x, _: Integer(x),
    float: lambda x, _: Float(x),
    complex: lambda x, _: Complex(x),

    FComponent: recwrap(FComponent),
    string.templatelib.Interpolation: _wrap_interpolation,
    FString: _wrap_fstring,
    string.templatelib.Template: recwrap(lambda els: FString(els, is_tstring=True)),

    List: recwrap(List),
    list: recwrap(List),
    Dict: recwrap(Dict),
    dict: _wrap_dict,
    Expression: recwrap(Expression),
    Set: recwrap(Set),
    set: recwrap(Set),
    Tuple: recwrap(Tuple),
    tuple: recwrap(Tuple),
}


def as_model(x: object) -> Object:
    """
    Convert ``x`` and any elements thereof into :ref:`models <models>` recursively. This function is called implicitly
    by Hy in many situations, such as when inserting the expansion of a macro into the surrounding code, so you don't
    often need to call it. One use is to ensure that models are used on both sides of a comparison::

      (= 7 '7)                ; => False
      (= (hy.as-model 7) '7)  ; => True

    It's an error to call ``hy.as-model`` on an object that contains itself, or an object that isn't representable as a
    Hy literal, such as a function.
    """

    return _ModelWrapping().wrap(x)


def replace_hy_obj(obj: object, other: Object) -> Object:
    return as_model(obj).replace(other)
