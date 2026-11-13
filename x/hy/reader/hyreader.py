"""Character reader for parsing Hy source."""
import codecs
import contextlib
import contextvars
import itertools
import sys
import typing as ta

from ..models import Bytes
from ..models import Complex
from ..models import Dict
from ..models import Expression
from ..models import FComponent
from ..models import Float
from ..models import FString
from ..models import Integer
from ..models import Keyword
from ..models import List
from ..models import Object
from ..models import Set
from ..models import String
from ..models import Symbol
from ..models import Tuple
from ..models import as_model
from ..models import is_unpack
from .exceptions import LexException
from .exceptions import PrematureEndOfInput
from .reader import Reader
from .reader import ReaderHandler
from .reader import ReaderMeta
from .reader import isnormalizedspace


ModelT = ta.TypeVar('ModelT', bound=Object)

FStringMode: ta.TypeAlias = ta.Literal['', 'f', 't']


##


def sym(name: str) -> Symbol:
    return Symbol(name, from_parser=True)


def mkexpr(root: str | Object, *args: Object) -> Expression:
    """Note that this differs subtly from `compiler.mkexpr`."""

    return Expression((sym(root) if isinstance(root, str) else root, *args))


## Identifiers


def _as_number(ident: str) -> Integer | Float | Complex | None:
    try:
        return Integer(ident)
    except ValueError:
        pass

    try:
        return Float(ident)
    except ValueError:
        pass

    if ident not in ('j', 'J'):
        try:
            return Complex(ident)
        except ValueError:
            pass

    return None


def _as_dotted_identifier(ident: str, reader: Reader | None) -> Object:
    if not ident.strip('.'):
        # It's all dots. Return it as a symbol.
        return sym(ident)

    def err(msg: str) -> ta.NoReturn:
        if reader is None:
            raise ValueError(msg)
        raise LexException.from_reader(msg, reader)

    if ident.lstrip('.').find('..') > 0:
        err('In a dotted identifier, multiple dots in a row are only allowed at the start')
    if ident.endswith('.'):
        err("A dotted identifier can't end with a dot")

    head = '.' * (len(ident) - len(ident.lstrip('.')))
    args = [as_identifier(a, reader=reader) for a in ident.lstrip('.').split('.')]
    if any(not isinstance(a, Symbol) for a in args):
        err('The parts of a dotted identifier must be symbols')

    if not head:
        return mkexpr(sym('.'), *args)
    return mkexpr(head, Symbol('None'), *args)


def as_identifier(ident: str, reader: Reader | None = None) -> Object:
    """
    Generate a Hy model - a number, a symbol, or an expression for a dotted identifier - from the text of an
    identifier, verifying the syntax of dot notation and the validity of symbol names. The ``reader``, if given, is used
    to generate position data for errors.
    """

    if (num := _as_number(ident)) is not None:
        return num

    if '.' in ident:
        return _as_dotted_identifier(ident, reader)

    if (
        reader is None and
        (
            not ident or
            ident[0] in ':#' or
            any(isnormalizedspace(c) for c in ident) or
            not HyReader.NON_IDENT.isdisjoint(ident)
        )
    ):
        raise ValueError(f'Syntactically illegal symbol: {ident!r}')

    return sym(ident)


## Reader


# The reader currently reading (or whose output is currently being compiled), dynamically scoped to the current context.
# This is what allows reader macros defined at compile-time to be installed into the reader that's reading the rest of
# the source.
_CURRENT_READER: contextvars.ContextVar[HyReader | None] = contextvars.ContextVar(
    f'{__name__}._CURRENT_READER',
    default=None,
)


class HyReader(Reader):
    """
    A modular reader for Hy source. It inherits from :py:class:`hy.Reader`.

    When ``use_current_readers`` is true, initialize this reader with all reader macros from the calling module.
    """

    __module__ = __package__.rpartition('.')[0]

    ##
    # Components necessary for Reader implementation

    NON_IDENT: ta.ClassVar[ta.AbstractSet[str]] = set("()[]{};\"'`~")

    if ta.TYPE_CHECKING:
        # ReaderMeta supplies this decorator while executing the class body.
        reader_for = ReaderMeta._attach_reader  # noqa: SLF001

    bracketed_templates: bool
    reader_macros: dict[str, ta.Callable[[ta.Any, str], ta.Any]]

    _reading_annotation: bool

    def __init__(self, *, use_current_readers: bool = False, bracketed_templates: bool = False) -> None:
        super().__init__()

        self.bracketed_templates = bracketed_templates

        self._reading_annotation = False

        # Move any reader macros declared using `reader_for("#...")` to the macro table.
        self.reader_macros = {}
        for tag in list(self.reader_table.keys()):
            if tag[0] == '#' and tag[1:]:
                self.reader_macros[tag[1:]] = self.reader_table.pop(tag)

        if use_current_readers:
            self.reader_macros.update(
                sys._getframe(1).f_globals.get('_hy_reader_macros', {}),  # noqa: SLF001
            )

    @classmethod
    def current_reader(cls, override: HyReader | None = None, create: bool = True) -> HyReader | None:
        return override or _CURRENT_READER.get() or (cls() if create else None)

    @contextlib.contextmanager
    def as_current_reader(self) -> ta.Iterator[None]:
        token = _CURRENT_READER.set(self)
        try:
            yield
        finally:
            _CURRENT_READER.reset(token)

    @classmethod
    @contextlib.contextmanager
    def using_reader(cls, override: HyReader | None = None, create: bool = True) -> ta.Iterator[None]:
        reader = cls.current_reader(override, create)
        with reader.as_current_reader() if reader else contextlib.nullcontext():
            yield

    def fill_pos(self, model: ModelT, start: tuple[int, int]) -> ModelT:
        """
        Set position information for ``model``. ``start`` should be a (line number, column number) tuple for the start
        position, whereas the end position is set to the current cursor position.
        """

        model.start_line, model.start_column = start
        model.end_line, model.end_column = self.pos

        # `replace` will recurse into submodels and set any model positions that are still unset the same way.
        return model.replace(model)

    def read_default(self, key: str) -> Object:
        """
        Try to read an identifier. If the next character after that is ``"``, then instead parse it as a string with the
        given prefix (e.g., ``r"..."``). This is the default reader handler, for when nothing in the read table matches.
        """

        ident = key + self.read_ident()
        if self.peek_and_getc('"'):
            return self.prefixed_string('"', ident)

        return as_identifier(ident, reader=self)

    def parse(self, stream: ta.TextIO, filename: str | None = None, skip_shebang: bool = False) -> ta.Iterator[Object]:
        """Yield all models in ``stream``. The parameters are understood as in :hy:func:`hy.read-many`."""

        self._set_source(stream, filename)

        if (
            skip_shebang and
            ''.join(itertools.islice(self.peeking(eof_ok=True), len('#!'))) == '#!'
        ):
            for c in self.chars():
                if c == '\n':
                    break

        yield from self.parse_forms_until('')

    ##
    # Reading forms

    def try_parse_one_form(self) -> Object | None:
        """
        Attempt to parse a single Hy form: read one (non-space) character from the stream, then call the corresponding
        handler, returning the model it produces, if any. Handlers may return `None` to signify no parsed form (e.g.,
        for comments). Raises :exc:`hy.PrematureEndOfInput` if the end of the input is reached before a form is fully
        parsed, and a `LexException` for any other error during form parsing.
        """

        return self._try_parse_one_form()

    def _try_parse_one_form(self, *, no_annotation_union: bool = False) -> Object | None:
        with self.as_current_reader():
            try:
                self.slurp_space()
                c = self.getc()
                start = self._pos
                if not c:
                    raise PrematureEndOfInput.from_reader(
                        'Premature end of input while attempting to parse one form',
                        self,
                    )

                handler = self.reader_table.get(c)
                model = handler(self, c) if handler else self.read_default(c)
                if model is None:
                    return None

                model = self.fill_pos(model, start)
                if self._reading_annotation:
                    model = self._read_annotation_postfix(model, start, no_union=no_annotation_union)
                model.reader = self
                return model

            except LexException:
                raise

            except Exception as e:  # noqa: BLE001
                raise LexException.from_reader(
                    str(e) or 'Exception thrown attempting to parse one form',
                    self,
                ) from None

    def parse_one_form(self) -> Object:
        """
        Parse the next form in the stream and return its model. Any preceding whitespace and comments are skipped over.
        """

        model = None
        while model is None:
            model = self.try_parse_one_form()
        return model

    def parse_forms_until(self, closer: str) -> ta.Iterator[Object]:
        """
        Yield models until the character ``closer`` is seen. This method is useful for reading sequential constructs
        such as lists.
        """

        while True:
            self.slurp_space()
            if self.peek_and_getc(closer):
                break

            model = self.try_parse_one_form()
            if model is not None:
                yield model

    ##
    # Basic atoms

    @reader_for(')')
    @reader_for(']')
    @reader_for('}')
    def invalid(self, key: str) -> ta.NoReturn:
        raise LexException.from_reader(f"Ran into a '{key}' where it wasn't expected.", self)

    @reader_for(';')
    def line_comment(self, _: str) -> None:
        for c in self.chars(eof_ok=True):
            if c == '\n':
                break

    @reader_for(':')
    def keyword(self, _: str) -> Keyword:
        ident = self.read_ident()
        if '.' in ident:
            raise LexException.from_reader(
                (
                    'Cannot access attribute on anything other than a name (in order to get attributes of expressions, '
                    'use `(. <expression> <attr>)` or `(.<attr> <expression>)`)'
                ),
                self,
            )

        return Keyword(ident, from_parser=True)

    @reader_for('"')
    def prefixed_string(self, _: str, prefix: str = '') -> String | Bytes | FString:
        prefix_chars = set(prefix)
        if (
            len(prefix_chars) != len(prefix) or
            not prefix_chars < set('bfrt') or
            len(prefix_chars - set('r')) > 1
        ):
            raise LexException.from_reader(f'invalid string prefix {prefix!r}', self)

        # https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
        valid_escapes = "\n\r\\'\"abfnrtv01234567x" + ('' if 'b' in prefix else 'NuU')

        escaping = False

        def quote_closing(c: str) -> int:
            nonlocal escaping

            if c == '\\':
                escaping = not escaping
                return 0

            if c == '"' and not escaping:
                return 1

            if escaping and 'r' not in prefix and c not in valid_escapes:
                raise LexException.from_reader('invalid escape sequence \\' + c, self)

            escaping = False
            return 0

        fstring_mode: FStringMode
        if 'f' in prefix_chars:
            fstring_mode = 'f'
        elif 't' in prefix_chars:
            fstring_mode = 't'
        else:
            fstring_mode = ''

        return self.read_string_until(quote_closing, prefix, fstring_mode)

    ##
    # Special annotations

    @reader_for("'", ('quote',))
    @reader_for('`', ('quasiquote',))
    @staticmethod
    def tag_as(root: str) -> ReaderHandler:
        return lambda self, _: mkexpr(root, self.parse_one_form())

    @reader_for('~')
    def unquote(self, key: str) -> Expression:
        return mkexpr(
            'unquote' + ('-splice' if self.peek_and_getc('@') else ''),
            self.parse_one_form(),
        )

    ##
    # Sequences

    @reader_for('(', (Expression, ')'))
    @reader_for('[', (List, ']'))
    @reader_for('{', (Dict, '}'))
    @reader_for('#{', (Set, '}'))
    @reader_for('#(', (Tuple, ')'))
    @staticmethod
    def sequence(
            seq_type: ta.Callable[[ta.Iterable[Object]], Object],
            closer: str,
    ) -> ReaderHandler:
        return lambda self, _: seq_type(self.parse_forms_until(closer))

    ##
    # Reader tag-macros

    @reader_for('#')
    def tag_dispatch(self, key: str) -> Object | None:
        """
        General handler for reader macros (and tag macros). Reads a full identifier after the `#` and calls the
        corresponding handler (this allows, e.g., `#reads-multiple-forms foo bar baz`).
        """

        if not self.peekc().strip():
            raise PrematureEndOfInput.from_reader('Premature end of input while attempting dispatch', self)

        # `#^Type target` - an annotation with no whitespace after the `#^` - unless there's actually a reader macro of
        # that name.
        peeked = self.read_ident(just_peeking=True)
        if (
            len(peeked) > 1 and
            peeked[0] == '^' and
            peeked not in self.reader_macros and
            (annotate := self.reader_macros.get('^')) is not None
        ):
            self.getc()
            return annotate(self, '^')

        ident = self.read_ident() or self.getc()
        if ident in self.reader_macros:
            tree = self.reader_macros[ident](self, ident)
            return as_model(tree) if tree is not None else None

        raise LexException.from_reader(f"reader macro '{key + ident}' is not defined", self)

    @reader_for('#_')
    def discard(self, _: str) -> None:
        """Discards the next parsed form."""

        self.parse_one_form()

    @reader_for('#*')
    @reader_for('#**')
    def hash_star(self, stars: str) -> Expression:
        """Unpacking forms `#*` and `#**`, corresponding to `*` and `**` in Python."""

        return mkexpr(
            'unpack-' + {'*': 'iterable', '**': 'mapping'}[stars],
            self.parse_one_form(),
        )

    @reader_for('#^')
    def annotate(self, _: str) -> Expression:
        """Annotate a symbol, usually with a type."""

        typ = self.parse_annotation_form()
        target = self.parse_one_form()
        return mkexpr('annotate', target, typ)

    def parse_annotation_form(self) -> Object:
        """
        Parse the next form as a type annotation. The annotation may immediately follow the ``#^`` - as in ``#^int x`` -
        unless that would spell the name of a defined reader macro. Within an annotation form, Python-style postfix type
        syntax is additionally accepted:

          - A form *immediately* followed by a bracketed sequence (with no intervening whitespace) is read as a
            subscript: ``ta.Sequence[int]`` reads as ``(get ta.Sequence int)``, and ``ta.Mapping[str int]`` reads as
            ``(get ta.Mapping #(str int))``.
          - Forms *immediately* separated by ``|`` are read as a union: ``int|None`` reads as ``(| int None)``.

        These compose and nest, so ``ta.Mapping[str ta.Sequence[int|None]]|None`` is accepted. Plain Hy forms, such as
        ``(| int None)`` or ``(get ta.Sequence int)``, remain valid annotations.
        """

        was_reading_annotation = self._reading_annotation
        self._reading_annotation = True
        try:
            with self.end_identifier('|'):
                return self.parse_one_form()
        finally:
            self._reading_annotation = was_reading_annotation

    def _read_annotation_postfix(self, model: Object, start: tuple[int, int], *, no_union: bool = False) -> Object:
        while self.peekc() == '[':
            self.getc()
            items = list(self.parse_forms_until(']'))
            if not items:
                raise LexException.from_reader('Empty subscript in annotation', self)
            if any(is_unpack('mapping', x) for x in items):
                raise LexException.from_reader('Mapping unpacking is not allowed in an annotation subscript', self)

            index = items[0] if len(items) == 1 and not is_unpack('iterable', items[0]) else Tuple(items)
            model = self.fill_pos(mkexpr('get', model, index), start)

        if no_union or self.peekc() != '|':
            return model

        operands = [model]
        while self.peek_and_getc('|'):
            # Continue the flat union here rather than letting the operand's own postfix parsing nest a new one.
            operand = None
            while operand is None:
                operand = self._try_parse_one_form(no_annotation_union=True)
            operands.append(operand)

        return self.fill_pos(mkexpr('|', *operands), start)

    ##
    # Strings (these are more complicated because f-strings form their own sublanguage)

    @reader_for('#[')
    def bracketed_string(self, _: str) -> String | Bytes | FString:
        """Bracketed strings. See the Hy docs for full details."""

        delim_chars = []
        for c in self.chars():
            if c == '[':
                break
            elif c == ']':
                raise LexException.from_reader("Ran into a ']' where it wasn't expected.", self)
            delim_chars.append(c)
        delim = ''.join(delim_chars)

        fstring_mode: FStringMode
        if delim == 'f' or delim.startswith('f-'):
            fstring_mode = 'f'
        elif self.bracketed_templates and (delim == 't' or delim.startswith('t-')):
            fstring_mode = 't'
        else:
            fstring_mode = ''

        # Discard a single initial newline, if any, accounting for all three styles of newline.
        self.peek_and_getc('\x0d')
        self.peek_and_getc('\x0a')

        index = -1

        def delim_closing(c: str) -> int:
            nonlocal index

            if c == ']':
                if index == len(delim):
                    # This is the second bracket at the end of the delim.
                    return len(delim) + 2
                else:
                    # Reset state, this may be the first bracket of the closing delim.
                    index = 0

            elif 0 <= index <= len(delim):
                # We're inside a possible closing delim.
                if index < len(delim) and c == delim[index]:
                    index += 1
                else:
                    # Failed delim, reset state.
                    index = -1

            return 0

        return self.read_string_until(delim_closing, 'r', fstring_mode, brackets=delim)

    def read_string_until(
            self,
            closing: ta.Callable[[str], int],
            prefix: str,
            fstring_mode: FStringMode,
            *,
            brackets: str | None = None,
    ) -> String | Bytes | FString:
        if fstring_mode:
            components = self.read_fcomponents_until(closing, prefix, fstring_mode)
            return FString(components, brackets=brackets, is_tstring=fstring_mode == 't')

        s = self.read_chars_until(closing, prefix, fstring_mode='')
        if isinstance(s, bytes):
            return Bytes(s)

        return String(s, brackets=brackets)

    @staticmethod
    def _decode_string_chars(text: str, prefix: str) -> str | bytes:
        text = text.replace('\x0d\x0a', '\x0a').replace('\x0d', '\x0a')

        if 'b' in prefix:
            try:
                data = text.encode('ascii')
            except UnicodeEncodeError:
                raise SyntaxError('bytes can only contain ASCII literal characters') from None

            if 'r' in prefix:
                return data
            return codecs.escape_decode(data)[0]

        if 'r' in prefix:
            return text

        # Encode to ISO-8859-1 ("Latin 1") first, due to https://github.com/python/cpython/issues/65530. The formula is
        # from https://stackoverflow.com/a/57192592.
        return text.encode('ISO-8859-1', errors='backslashreplace').decode('unicode_escape')

    @ta.overload
    def read_chars_until(
            self,
            closing: ta.Callable[[str], int],
            prefix: str,
            fstring_mode: ta.Literal[''],
    ) -> str | bytes:
        ...

    @ta.overload
    def read_chars_until(
            self,
            closing: ta.Callable[[str], int],
            prefix: str,
            fstring_mode: ta.Literal['f', 't'],
    ) -> tuple[str | bytes, int]:
        ...

    def read_chars_until(
            self,
            closing: ta.Callable[[str], int],
            prefix: str,
            fstring_mode: FStringMode,
    ) -> str | bytes | tuple[str | bytes, int]:
        """
        Read characters until `closing` returns nonzero (the number of trailing closing characters to drop) or, in an
        f-string, until the start of a component. In f-string mode, that number (zero if a component was started
        instead) is returned alongside the text.
        """

        s = []
        in_named_escape = False
        for c in self.chars():
            s.append(c)

            if n_closing_chars := closing(c):
                # The string has ended.
                s = s[:-n_closing_chars]
                break

            if not fstring_mode:
                continue

            # Handle braces in f-strings.
            if c == '{':
                if 'r' not in prefix and s[-3:] == ['\\', 'N', '{']:
                    # Ignore "\N{...}".
                    in_named_escape = True
                elif not self.peek_and_getc('{'):
                    # Start an f-component if not "{{".
                    s.pop()
                    break

            elif c == '}':
                if in_named_escape:
                    in_named_escape = False
                elif not self.peek_and_getc('}'):
                    raise SyntaxError(f"{fstring_mode}-string: single '}}' is not allowed")

        res = self._decode_string_chars(''.join(s), prefix)

        if fstring_mode:
            return res, n_closing_chars
        return res

    def read_fcomponents_until(
            self,
            closing: ta.Callable[[str], int],
            prefix: str,
            fstring_mode: ta.Literal['f', 't'],
    ) -> list[String | FComponent]:
        components: list[String | FComponent] = []
        start = self.pos
        while True:
            s, closed = self.read_chars_until(closing, prefix, fstring_mode=fstring_mode)
            if s:
                components.append(self.fill_pos(String(s), start))
            if closed:
                break
            components.extend(self.read_fcomponent(prefix, fstring_mode))
        return components

    def read_fcomponent(self, prefix: str, fstring_mode: ta.Literal['f', 't']) -> list[String | FComponent]:
        """May return one or two components, since the `=` debugging syntax will create a String component."""

        start = self.pos
        values: list[String | FComponent] = []
        conversion = None
        has_debug = False

        # Read the expression, saving the text verbatim in case we encounter debug `=`.
        space_before = self.slurp_space()
        with self.saving_chars() as form_chars:
            model = self.parse_one_form()
        space_between = self.slurp_space()
        form_text = ''.join(form_chars)

        # Check for and handle debug syntax: we emit the verbatim text before we emit the value.
        if self.peek_and_getc('='):
            has_debug = True
            space_after = self.slurp_space()
            dbg_prefix = space_before + form_text + space_between + '=' + space_after
            values.append(self.fill_pos(String(dbg_prefix), start))

        # Handle the conversion code.
        if self.peek_and_getc('!'):
            conversion = self.getc()
        self.slurp_space()

        # Handle formatting options.
        format_components: list[String | FComponent] = []
        if self.peek_and_getc(':'):
            format_components = self.read_fcomponents_until(lambda c: 1 if c == '}' else 0, prefix, 'f')
        else:
            if has_debug and conversion is None:
                conversion = 'r'
            if self.getc() != '}':
                raise LexException.from_reader(f'{fstring_mode}-string: trailing junk in field', self)

        return [
            *values,
            self.fill_pos(
                FComponent(
                    (model, *format_components),
                    conversion=conversion,
                    expression=form_text,
                    is_tstring=fstring_mode == 't',
                ),
                start,
            ),
        ]
