"""The module-level functions of `re`: each compiles its pattern, through a cache, and hands on to the Pattern."""
import re
import typing as ta

from .matches import Match
from .patterns import Pattern


##


class _PatternCache:
    """
    Compiled patterns by what they were compiled from, as `re` keeps. It is emptied when it fills, and is not locked:
    the worst two threads compiling the same pattern at once can do is compile it twice.
    """

    def __init__(self, max_size: int = 512) -> None:
        super().__init__()

        self._max_size = max_size
        self._patterns: dict[tuple[type, ta.Any, int], Pattern] = {}

    def get(self, pattern: ta.Any, flags: int) -> Pattern:
        if isinstance(pattern, Pattern):
            if flags:
                raise ValueError('cannot process flags argument with a compiled pattern')
            return pattern

        flags = int(flags)
        key = (type(pattern), pattern, flags)
        try:
            return self._patterns[key]
        except (KeyError, TypeError):
            pass

        compiled: Pattern = Pattern(pattern, flags)

        if len(self._patterns) >= self._max_size:
            self._patterns.clear()
        self._patterns[key] = compiled
        return compiled

    def clear(self) -> None:
        self._patterns.clear()


_PATTERN_CACHE = _PatternCache()


##


def compile(pattern: ta.AnyStr | Pattern[ta.AnyStr], flags: int = 0) -> Pattern[ta.AnyStr]:  # noqa
    return _PATTERN_CACHE.get(pattern, flags)


def purge() -> None:
    _PATTERN_CACHE.clear()


def escape(pattern: ta.AnyStr) -> ta.AnyStr:
    # What `re` escapes, and how, is as good for PCRE2: a backslash before anything which is not a letter or a digit
    # makes it stand for itself.
    return re.escape(pattern)


#


def search(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        string: ta.AnyStr,
        flags: int = 0,
) -> Match[ta.AnyStr] | None:
    return compile(pattern, flags).search(string)


def match(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        string: ta.AnyStr,
        flags: int = 0,
) -> Match[ta.AnyStr] | None:
    return compile(pattern, flags).match(string)


def fullmatch(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        string: ta.AnyStr,
        flags: int = 0,
) -> Match[ta.AnyStr] | None:
    return compile(pattern, flags).fullmatch(string)


def finditer(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        string: ta.AnyStr,
        flags: int = 0,
) -> ta.Iterator[Match[ta.AnyStr]]:
    return compile(pattern, flags).finditer(string)


def findall(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        string: ta.AnyStr,
        flags: int = 0,
) -> list[ta.Any]:
    return compile(pattern, flags).findall(string)


def split(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        string: ta.AnyStr,
        maxsplit: int = 0,
        flags: int = 0,
) -> list[ta.Any]:
    return compile(pattern, flags).split(string, maxsplit)


def sub(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        repl: ta.Any,
        string: ta.AnyStr,
        count: int = 0,
        flags: int = 0,
) -> ta.AnyStr:
    return compile(pattern, flags).sub(repl, string, count)


def subn(
        pattern: ta.AnyStr | Pattern[ta.AnyStr],
        repl: ta.Any,
        string: ta.AnyStr,
        count: int = 0,
        flags: int = 0,
) -> tuple[ta.AnyStr, int]:
    return compile(pattern, flags).subn(repl, string, count)
