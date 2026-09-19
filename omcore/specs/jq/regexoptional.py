import typing as ta

from ... import lang
from .regex import PythonRegexEngine


if ta.TYPE_CHECKING:
    import regex
else:
    regex = lang.proxy_import('regex')


##


class RegexPackageEngine(PythonRegexEngine):
    def __init__(self) -> None:
        super().__init__(regex)
