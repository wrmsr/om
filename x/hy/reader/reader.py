# ruff: noqa: SLF001
"Tooling for reading/parsing source character-by-character."
import collections
import contextlib
import itertools
import re
import typing as ta

from ..models import Object
from .exceptions import PrematureEndOfInput


ReaderFunctionT = ta.TypeVar('ReaderFunctionT', bound=ta.Callable[..., ta.Any])
ReaderHandler: ta.TypeAlias = ta.Callable[[ta.Any, str], Object | None]


##


_whitespace = re.compile(r'[ \t\n\r\f\v]+')


def isnormalizedspace(s: str) -> bool:
    return bool(_whitespace.match(s))


class ReaderMeta(type):
    """Provides a class with a dispatch map `DEFAULT_TABLE` and a decorator `@reader_for`."""

    @classmethod
    def __prepare__(
            cls,
            name: str,
            bases: tuple[type, ...],
            /,
            **kwargs: ta.Any,
    ) -> ta.MutableMapping[str, ta.Any]:
        namespace = super().__prepare__(name, bases, **kwargs)
        namespace['reader_for'] = cls._attach_reader
        return namespace

    @staticmethod
    def _attach_reader(
            char: str,
            args: tuple[ta.Any, ...] | None = None,
    ) -> ta.Callable[[ReaderFunctionT], ReaderFunctionT]:
        def wrapper(f: ReaderFunctionT) -> ReaderFunctionT:
            handler = f if args is None else f(*args)
            setattr(f, '_readers', {**getattr(f, '_readers', {}), char: handler})
            return f

        return wrapper

    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, ta.Any]) -> ReaderMeta:
        del namespace['reader_for']
        default_table: dict[str, ReaderHandler] = {}
        for base in bases:
            if hasattr(base, 'DEFAULT_TABLE'):
                default_table |= base.DEFAULT_TABLE
        for method in namespace.values():
            if callable(method) and hasattr(method, '_readers'):
                default_table.update(method._readers)
        namespace['DEFAULT_TABLE'] = default_table
        return super().__new__(cls, name, bases, namespace)


class Reader(metaclass=ReaderMeta):
    """
    An abstract base class for reading input character-by-character.

    See :py:class:`hy.HyReader` for an example of creating a reader class.

    Attributes:
        ends_ident (set[str]):
            The set of characters that indicate the end of an identifier
        reader_table (dict[str, Callable]):
            A dictionary mapping a reader-macro key to its dispatch function
        pos (tuple[int, int]):
            A read-only (line, column) tuple indicating the current cursor position of the source being read
    """

    __module__ = __package__.rpartition('.')[0]

    NON_IDENT: ta.ClassVar[ta.AbstractSet[str]]
    DEFAULT_TABLE: ta.ClassVar[dict[str, ReaderHandler]]

    _source: str | None
    _filename: str | None
    _stream: ta.TextIO
    _peek_chars: collections.deque[str]
    _saved_chars: list[list[str]]
    _pos: tuple[int, int]
    _eof_tracker: tuple[int, int]

    def __init__(self) -> None:
        super().__init__()

        self._source = None
        self._filename = None

        self.ends_ident = set(self.NON_IDENT)
        self.reader_table = self.DEFAULT_TABLE.copy()

    def _set_source(self, stream: ta.TextIO | None = None, filename: str | None = None) -> None:
        if filename is not None:
            self._filename = filename
        if stream is not None:
            pos = stream.tell()
            self._source = stream.read()
            stream.seek(pos)

            self._stream = stream
            self._peek_chars = collections.deque()
            self._saved_chars = []
            self._pos = (1, 0)
            self._eof_tracker = self._pos

    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    @contextlib.contextmanager
    def end_identifier(self, character: str) -> ta.Iterator[None]:
        """A context manager to temporarily add a new character to the :py:attr:`ends_ident` set."""

        prev_ends_ident = self.ends_ident.copy()
        self.ends_ident.add(character)
        try:
            yield
        finally:
            self.ends_ident = prev_ends_ident

    ##
    # Character streaming

    @contextlib.contextmanager
    def saving_chars(self) -> ta.Iterator[list[str]]:
        """
        A context manager to save all read characters. The value is a list of characters, rather than a single string.
        """

        self._saved_chars.append([])
        yield self._saved_chars[-1]
        saved = self._saved_chars.pop()
        if self._saved_chars:
            # `saving_chars` is being used recursively. The characters we collected for the inner case should also be
            # saved for the outer case.
            self._saved_chars[-1].extend(saved)

    def peekc(self) -> str:
        """Peek at the next character, returning it but not consuming it."""

        if self._peek_chars:
            return self._peek_chars[-1]
        nc = self._stream.read(1)
        self._peek_chars.append(nc)
        return nc

    def peeking(self, eof_ok: bool = False) -> ta.Iterator[str]:
        """
        As :func:`chars`, but without consuming any of the returned
        characters. This method is useful for looking several characters
        ahead.
        """

        yield from reversed(self._peek_chars)
        while True:
            c = self._stream.read(1)
            if not c:
                break
            self._peek_chars.appendleft(c)
            yield c
        if not c and not eof_ok:
            raise PrematureEndOfInput.from_reader('Premature end of input while peeking', self)

    def getc(self) -> str:
        """
        Consume one character from the stream and return it. This method does the bookkeeping for position data, so all
        character consumption should go through it.
        """

        c = self.peekc()
        self._peek_chars.pop()

        if c:
            line, col = self._pos
            col += 1
            if c == '\n':
                line += 1
                col = 0
            self._pos = (line, col)

            if not isnormalizedspace(c):
                self._eof_tracker = self._pos

        if self._saved_chars:
            self._saved_chars[-1].append(c)

        return c

    def peek_and_getc(self, target: str) -> bool:
        """
        Peek at the next character and check if it's equal to ``target``, only consuming it if it's equal. A
        :py:class:`bool` is returned.
        """

        nc = self.peekc()
        if nc == target:
            self.getc()
            return True
        return False

    def chars(self, eof_ok: bool = False) -> ta.Iterator[str]:
        """
        Consume and yield characters of the stream. If ``eof_ok`` is false (the default) and the end of the stream is
        reached, raise :exc:`hy.PrematureEndOfInput`.
        """

        while True:
            c = self.getc()
            if not c:
                break
            yield c
        if not c and not eof_ok:
            raise PrematureEndOfInput.from_reader(
                'Premature end of input while streaming chars', self,
            )

    ##
    # Reading multiple characters

    def getn(self, n: int) -> str:
        """Consume and return ``n`` characters."""

        return ''.join(itertools.islice(self.chars(), n))

    def slurp_space(self) -> str:
        """Consume and return zero or more whitespace characters."""

        n = 0
        for c in self.peeking(eof_ok=True):
            if not isnormalizedspace(c):
                break
            n += 1
        return self.getn(n)

    def read_ident(self, just_peeking: bool = False) -> str:
        """
        Read characters until we hit something in :py:attr:`ends_ident`. The characters are consumed unless
        ``just_peeking`` is true.
        """

        ident = []
        for nc in self.peeking(eof_ok=True):
            if not nc or nc in self.ends_ident or isnormalizedspace(nc):
                # `not nc` means EOF, but that's okay.
                break
            ident.append(nc)
        if not just_peeking:
            self.getn(len(ident))
        return ''.join(ident)

    ##
    # Reader dispatch logic

    def dispatch(self, tag: str) -> Object | None:
        """Call the handler for the reader macro with key ``tag`` (a string). Return the model it produces, if any."""

        return self.reader_table[tag](self, tag)
