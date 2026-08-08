"""
TODO:
 - Namer: ta.TypeAlias = ta.Callable[[str], str] ?
  - this interface is ~intentionally~ limited, but custom overrides would be useful
"""
import dataclasses as dc
import typing as ta

from ... import check
from ... import lang
from ... import typedvalues as tv
from .configs import Config


##


class Naming(Config, tv.UniqueTypedValue, lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class CasingNaming(Naming, lang.Final):
    casing: lang.StringCasing | lang.NamedStringCasing


#


@ta.overload
def as_naming(naming: Naming | lang.NamedStringCasing) -> Naming: ...


@ta.overload
def as_naming(naming: Naming | lang.NamedStringCasing | None) -> Naming | None: ...


def as_naming(naming):
    if naming is None:
        return None
    elif isinstance(naming, Naming):
        return naming
    else:
        return CasingNaming(lang.as_string_casing(naming))


##


def translate_name(n: str, e: Naming) -> str:
    check.non_empty_str(n)
    check.not_equal(set(n), {'_'})

    n1 = n.lstrip('_')
    pfx = '_' * (len(n) - len(n1))
    n2 = n1.rstrip('_')
    sfx = '_' * (len(n1) - len(n2))
    ps = lang.split_string_casing(n2)

    if isinstance(e, CasingNaming):
        cs = lang.as_string_casing(e.casing)
    else:
        raise TypeError(e)

    r = cs.join(*ps)

    return pfx + r + sfx
