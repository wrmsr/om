import abc
import re
import typing as ta

from ... import dataclasses as dc
from ... import lang
from .errors import JqRegexError


if ta.TYPE_CHECKING:
    import regex
else:
    regex = lang.proxy_import('regex')


##


@dc.dataclass(frozen=True)
class RegexCapture:
    offset: int
    length: int
    string: str | None
    name: str | None


@dc.dataclass(frozen=True)
class RegexMatch:
    offset: int
    length: int
    string: str
    captures: tuple[RegexCapture, ...]


class RegexEngine(lang.Abstract):
    @abc.abstractmethod
    def find(self, value: str, pattern: str, flags: str | None = None) -> ta.Iterator[RegexMatch]:
        raise NotImplementedError


##


class PythonRegexEngine(RegexEngine):
    def __init__(self, module: ta.Any) -> None:
        super().__init__()

        self._module = module

    def find(self, value: str, pattern: str, flags: str | None = None) -> ta.Iterator[RegexMatch]:
        mode = flags or ''
        unknown = set(mode) - set('gimnpsx')
        if unknown:
            raise JqRegexError(f'unsupported regex flags: {"".join(sorted(unknown))}')

        compile_flags = 0
        if 'i' in mode:
            compile_flags |= self._module.IGNORECASE
        if 'm' in mode or 'p' in mode:
            compile_flags |= self._module.MULTILINE
        if 's' in mode or 'p' in mode:
            compile_flags |= self._module.DOTALL
        if 'x' in mode:
            compile_flags |= self._module.VERBOSE

        try:
            compiled = self._module.compile(pattern, compile_flags)
        except Exception as exc:
            raise JqRegexError(str(exc)) from exc

        names = {index: name for name, index in compiled.groupindex.items()}
        try:
            matches = compiled.finditer(value)
            for match in matches:
                start, end = match.span()
                if 'n' in mode and start == end:
                    continue
                captures: list[RegexCapture] = []
                for index in range(1, compiled.groups + 1):
                    capture_start, capture_end = match.span(index)
                    if capture_start < 0:
                        captures.append(RegexCapture(-1, 0, None, names.get(index)))
                    else:
                        captures.append(RegexCapture(
                            capture_start,
                            capture_end - capture_start,
                            match.group(index),
                            names.get(index),
                        ))
                yield RegexMatch(start, end - start, match.group(), tuple(captures))
                if 'g' not in mode:
                    break
        except JqRegexError:
            raise
        except Exception as exc:
            raise JqRegexError(str(exc)) from exc


@lang.cached_function
def stdlib_regex_engine() -> RegexEngine:
    return PythonRegexEngine(re)


def regex_match_object(match: RegexMatch) -> dict[str, ta.Any]:
    return {
        'offset': match.offset,
        'length': match.length,
        'string': match.string,
        'captures': [
            {
                'offset': capture.offset,
                'length': capture.length,
                'string': capture.string,
                'name': capture.name,
            }
            for capture in match.captures
        ],
    }


def regex_capture_object(match: RegexMatch) -> dict[str, ta.Any]:
    return {
        capture.name: capture.string
        for capture in match.captures
        if capture.name is not None
    }


##


class RegexPackageEngine(PythonRegexEngine):
    def __init__(self) -> None:
        super().__init__(regex)
