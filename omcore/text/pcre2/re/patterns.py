import re
import sys
import typing as ta

from .... import dataclasses as dc
from .... import lang
from .. import _pcre2 as pcre2
from .groups import GroupInfo
from .matches import Match
from .subjects import Subject
from .templates import Template
from .templates import expand_template
from .templates import parse_template
from .translating import translate_pattern


##


_OPTIONS_BY_FLAG: ta.Mapping[re.RegexFlag, int] = {
    re.IGNORECASE: pcre2.CASELESS,
    re.MULTILINE: pcre2.MULTILINE,
    re.DOTALL: pcre2.DOTALL,
    re.VERBOSE: pcre2.EXTENDED,
}

_REPORTED_FLAGS = re.ASCII | re.DEBUG | re.IGNORECASE | re.MULTILINE | re.DOTALL | re.VERBOSE


@lang.cached_function
def _compile_context() -> pcre2.CompileContext:
    # A newline is a linefeed and nothing else, as it is to `re` whatever PCRE2 was built to take one for, and a
    # backslash followed by digits is read by `re`'s rules for telling a group reference from an octal character.
    return pcre2.CompileContext.create(
        newline=pcre2.NEWLINE_LF,
        extra_options=pcre2.EXTRA_PYTHON_OCTAL,
    )


def _read_group_index(code: pcre2.Code, *, is_str: bool) -> dict[str, int]:
    table = code.pattern_info(pcre2.INFO_NAMETABLE)
    entry_size = code.pattern_info(pcre2.INFO_NAMEENTRYSIZE)

    # Each entry is a group's number, most significant byte first, and then its zero-terminated name.
    numbers_by_name: dict[str, int] = {}
    for i in range(code.pattern_info(pcre2.INFO_NAMECOUNT)):
        entry = table[i * entry_size:(i + 1) * entry_size]
        name = entry[2:entry.index(b'\0', 2)].decode('utf-8' if is_str else 'latin-1')
        numbers_by_name[name] = int.from_bytes(entry[:2], 'big')

    # PCRE2 keeps them by name, and `re` in the order the groups appear.
    return dict(sorted(numbers_by_name.items(), key=lambda kv: kv[1]))


@dc.dataclass(frozen=True)
class _Search:
    """A subject as one search sees it: clipped to where it is to stop, and with where it is to start."""

    subject: Subject
    data: ta.Any
    byte_pos: int

    pos: int
    endpos: int


class Pattern(lang.Final, ta.Generic[ta.AnyStr]):
    """
    The counterpart of `re.Pattern`: a pattern written for `re`, compiled and matched by PCRE2.

    It is immutable, and safe to share between threads. A match context given to it applies to every match it makes,
    which is the one thing here `re` has no equivalent of: a match which exceeds one of its limits raises the binding's
    `MatchError`, where `re` would have carried on for as long as it took.
    """

    def __init__(
            self,
            pattern: ta.AnyStr,
            flags: int = 0,
            *,
            match_context: pcre2.MatchContext | None = None,
    ) -> None:
        super().__init__()

        if isinstance(pattern, str):
            is_str = True
            text = pattern
        elif isinstance(pattern, bytes):
            is_str = False
            text = pattern.decode('latin-1')
        else:
            raise TypeError('first argument must be string or compiled pattern')

        flags = int(flags)
        if flags & re.LOCALE:
            raise ValueError('the LOCALE flag is not supported')
        if is_str and flags & re.ASCII and flags & re.UNICODE:
            raise ValueError('ASCII and UNICODE flags are incompatible')
        if not is_str and flags & re.UNICODE:
            raise ValueError('cannot use UNICODE flag with a bytes pattern')
        is_unicode = is_str and not flags & re.ASCII

        translated = translate_pattern(
            text,
            is_str=is_str,
            unicode_classes=is_unicode,
            verbose=bool(flags & re.VERBOSE),
        )
        encoded = translated.pattern.encode('utf-8' if is_str else 'latin-1')

        all_flags = flags | translated.inline_flags
        if all_flags & re.ASCII and all_flags & re.UNICODE:
            raise ValueError('ASCII and UNICODE flags are incompatible')

        # ALT_CIRCUMFLEX only has any effect in multiline mode, where it is what has a `^` match after a newline which
        # ends the subject, as it does in `re` - so it is always on, for a pattern which turns that mode on by itself.
        options = pcre2.ALT_CIRCUMFLEX
        if is_str:
            options |= pcre2.UTF
        if is_unicode:
            options |= pcre2.UCP
        for flag, option in _OPTIONS_BY_FLAG.items():
            if flags & flag:
                options |= option

        try:
            code = pcre2.compile(encoded, options, _compile_context())
        except pcre2.CompileError as e:
            # Where in the pattern can only be said if the pattern PCRE2 was given is the one that was written.
            pos: int | None = None
            if translated.pattern == text and e.offset is not None:
                pos = min(len(encoded[:e.offset].decode(errors='ignore')) if is_str else e.offset, len(text))
            raise re.PatternError(pcre2.get_error_message(e.code), pattern, pos) from e

        self._pattern: ta.AnyStr = pattern
        self._given_flags = flags
        self._is_str = is_str
        self._match_context = match_context
        self._code = code

        # Flags a pattern turns on for itself are reported along with those it was given, as `re` reports them.
        self._flags = all_flags & _REPORTED_FLAGS
        if is_str and not self._flags & re.ASCII:
            self._flags |= re.UNICODE

        index = _read_group_index(code, is_str=is_str)
        self._groups = GroupInfo(
            num_groups=code.pattern_info(pcre2.INFO_CAPTURECOUNT),
            index=index,
            names={number: name for name, number in index.items()},
            close_ranks=translated.group_close_ranks,
        )

        self._templates: dict[ta.Any, Template] = {}

    #

    @property
    def pattern(self) -> ta.AnyStr:
        return self._pattern

    @property
    def flags(self) -> int:
        return self._flags

    @property
    def groups(self) -> int:
        return self._groups.num_groups

    @property
    def groupindex(self) -> ta.Mapping[str, int]:
        return self._groups.index

    #

    def _open(self, string: ta.Any, pos: int, endpos: int) -> _Search | None:
        subject = Subject(string, is_str=self._is_str)

        length = len(subject)
        pos = min(max(pos, 0), length)
        endpos = min(max(endpos, 0), length)
        if pos > endpos:
            return None

        # A search which is to stop short of the end of its subject is given a view of it which does, so that the end
        # of what it is given is the end of the subject as far as the pattern can tell.
        data = subject.data
        byte_end = subject.to_byte(endpos)
        if byte_end != len(data):
            data = memoryview(data)[:byte_end]

        return _Search(
            subject,
            data,
            subject.to_byte(pos),
            pos=pos,
            endpos=endpos,
        )

    def _scan(self, search: _Search, options: int = 0) -> ta.Iterator[ta.Sequence[int]]:
        # This is the loop PCRE2 documents for a global search, which finds what `re`'s does: after each match the
        # block says where to look next and how, which is what gets an empty match past itself. The same object is
        # given as the subject each time round, which is what lets the binding not validate it over again.
        md = pcre2.MatchData.create_from_pattern(self._code)
        start_offset = search.byte_pos
        next_options = 0
        while self._code.match(search.data, md, start_offset, options | next_options, self._match_context) >= 0:
            yield md.ovector
            if (nxt := md.next_match()) is None:
                return
            start_offset, next_options = nxt

    def _make_match(self, search: _Search, ovector: ta.Sequence[int]) -> Match[ta.AnyStr]:
        return Match(
            self,
            self._groups,
            search.subject,
            ovector,
            pos=search.pos,
            endpos=search.endpos,
        )

    def _first_match(self, string: ta.Any, pos: int, endpos: int, options: int) -> Match[ta.AnyStr] | None:
        if (search := self._open(string, pos, endpos)) is None:
            return None
        for ovector in self._scan(search, options):
            return self._make_match(search, ovector)
        return None

    #

    def search(self, string: ta.AnyStr, pos: int = 0, endpos: int = sys.maxsize) -> Match[ta.AnyStr] | None:
        return self._first_match(string, pos, endpos, 0)

    def match(self, string: ta.AnyStr, pos: int = 0, endpos: int = sys.maxsize) -> Match[ta.AnyStr] | None:
        return self._first_match(string, pos, endpos, pcre2.ANCHORED)

    def fullmatch(self, string: ta.AnyStr, pos: int = 0, endpos: int = sys.maxsize) -> Match[ta.AnyStr] | None:
        return self._first_match(string, pos, endpos, pcre2.ANCHORED | pcre2.ENDANCHORED)

    def finditer(self, string: ta.AnyStr, pos: int = 0, endpos: int = sys.maxsize) -> ta.Iterator[Match[ta.AnyStr]]:
        if (search := self._open(string, pos, endpos)) is None:
            return
        for ovector in self._scan(search):
            yield self._make_match(search, ovector)

    def findall(self, string: ta.AnyStr, pos: int = 0, endpos: int = sys.maxsize) -> list[ta.Any]:
        if (search := self._open(string, pos, endpos)) is None:
            return []

        subject = search.subject
        empty: ta.Any = '' if self._is_str else b''
        num_groups = self._groups.num_groups

        def get_group(ovector: ta.Sequence[int], number: int) -> ta.Any:
            if ovector[2 * number] < 0:
                return empty
            return subject.slice(ovector[2 * number], ovector[2 * number + 1])

        if num_groups == 0:
            return [get_group(ovector, 0) for ovector in self._scan(search)]
        elif num_groups == 1:
            return [get_group(ovector, 1) for ovector in self._scan(search)]
        else:
            return [
                tuple(get_group(ovector, number) for number in range(1, num_groups + 1))
                for ovector in self._scan(search)
            ]

    def split(self, string: ta.AnyStr, maxsplit: int = 0) -> list[ta.Any]:
        search = self._open(string, 0, sys.maxsize)
        if search is None:
            raise RuntimeError('unreachable')
        subject = search.subject

        pieces: list[ta.Any] = []
        last = 0
        for n, ovector in enumerate(self._scan(search)):
            if maxsplit and n >= maxsplit:
                break
            pieces.append(subject.slice(last, ovector[0]))
            for number in range(1, self._groups.num_groups + 1):
                if ovector[2 * number] < 0:
                    pieces.append(None)
                else:
                    pieces.append(subject.slice(ovector[2 * number], ovector[2 * number + 1]))
            last = ovector[1]

        pieces.append(subject.slice(last, len(subject.data)))
        return pieces

    #

    def _get_template(self, repl: ta.Any) -> Template:
        try:
            return self._templates[repl]
        except KeyError:
            pass

        if isinstance(repl, str) != self._is_str or not isinstance(repl, (str, bytes)):
            expected = 'str' if self._is_str else 'a bytes-like object'
            raise TypeError(f'expected {expected}, {type(repl).__name__} found')

        template = parse_template(
            repl,
            num_groups=self._groups.num_groups,
            group_index=self._groups.index,
        )

        # Kept for the next time it is used, as most replacements are, within reason.
        if len(self._templates) < 64:
            self._templates[repl] = template
        return template

    def subn(self, repl: ta.Any, string: ta.AnyStr, count: int = 0) -> tuple[ta.AnyStr, int]:
        search = self._open(string, 0, sys.maxsize)
        if search is None:
            raise RuntimeError('unreachable')
        subject = search.subject

        template: Template | None = None
        if not callable(repl):
            template = self._get_template(repl)

        pieces: list[ta.Any] = []
        last = 0
        n = 0
        for ovector in self._scan(search):
            if count and n >= count:
                break
            pieces.append(subject.slice(last, ovector[0]))

            if template is None:
                pieces.append(repl(self._make_match(search, ovector)))
            else:
                def get_group(number: int) -> ta.Any:
                    if ovector[2 * number] < 0:  # noqa
                        return None
                    return subject.slice(ovector[2 * number], ovector[2 * number + 1])  # noqa

                pieces.append(expand_template(template, get_group, is_str=self._is_str))

            last = ovector[1]
            n += 1

        pieces.append(subject.slice(last, len(subject.data)))
        return (('' if self._is_str else b'').join(pieces), n)  # type: ignore[return-value]

    def sub(self, repl: ta.Any, string: ta.AnyStr, count: int = 0) -> ta.AnyStr:
        return self.subn(repl, string, count)[0]

    #

    def __repr__(self) -> str:
        args = repr(self._pattern)
        if self._given_flags & _REPORTED_FLAGS:
            args += f', {re.RegexFlag(self._given_flags & _REPORTED_FLAGS)!r}'
        return f'{type(self).__module__.rpartition(".")[0]}.compile({args})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pattern):
            return NotImplemented
        return (
            self._pattern == other._pattern and
            self._given_flags == other._given_flags and
            self._match_context is other._match_context
        )

    def __hash__(self) -> int:
        return hash((self._pattern, self._given_flags))

    def __reduce__(self) -> ta.Any:
        if self._match_context is not None:
            raise TypeError('a Pattern with a match context cannot be pickled')
        return (Pattern, (self._pattern, self._given_flags))

    def __copy__(self) -> ta.Self:
        return self

    def __deepcopy__(self, memo: ta.Any) -> ta.Self:
        return self
