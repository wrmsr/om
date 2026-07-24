# ruff: noqa: SLF001
import enum
import typing as ta

from .... import check
from .... import inject as inj
from .... import lang


##


class PytestScope(enum.StrEnum):
    SESSION = 'session'
    PACKAGE = 'package'
    MODULE = 'module'
    CLASS = 'class'
    FUNCTION = 'function'


class Scopes(lang.Namespace, lang.Final):
    Session = inj.SeededScope(PytestScope.SESSION)
    Package = inj.SeededScope(PytestScope.PACKAGE)
    Module = inj.SeededScope(PytestScope.MODULE)
    Class = inj.SeededScope(PytestScope.CLASS)
    Function = inj.SeededScope(PytestScope.FUNCTION)


SCOPES_BY_PYTEST_SCOPE: ta.Mapping[PytestScope, inj.SeededScope] = {
    check.isinstance(a.tag, PytestScope): a
    for n, a in Scopes.__dict__.items()
    if isinstance(a, inj.SeededScope)
}
