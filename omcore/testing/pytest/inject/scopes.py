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
    Session = inj.DelimitedScope(PytestScope.SESSION)
    Package = inj.DelimitedScope(PytestScope.PACKAGE)
    Module = inj.DelimitedScope(PytestScope.MODULE)
    Class = inj.DelimitedScope(PytestScope.CLASS)
    Function = inj.DelimitedScope(PytestScope.FUNCTION)


SCOPES_BY_PYTEST_SCOPE: ta.Mapping[PytestScope, inj.DelimitedScope] = {
    check.isinstance(a.tag, PytestScope): a
    for n, a in Scopes.__dict__.items()
    if isinstance(a, inj.DelimitedScope)
}
