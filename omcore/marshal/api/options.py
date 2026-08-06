"""
TODO:
 - MarshalOption, UnmarshalOption, check if a context got something unexpected
 - Options only apply to Factories?
  - MarshalFactoryOption, MarshalOption, UnmarshalFactoryOption, MarshalOption ?
"""
import dataclasses as dc
import typing as ta

from ... import check
from ... import lang
from ... import typedvalues as tv
from .configs import Config
from .configs import ConfigRegistry
from .configs import ConfigsGetter


##


class Option(tv.TypedValue, lang.Abstract):
    pass


Options: ta.TypeAlias = tv.TypedValues[Option]


##


_EMPTY_OPTIONS: Options = Options()


##


@dc.dataclass(frozen=True)
class DefaultOptions(tv.UniqueTypedValue, Config, lang.Final):
    v: Options

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.v!r})'

    def __post_init__(self) -> None:
        check.isinstance(self.v, tv.TypedValues)
        check.not_in(IgnoreDefaultOptions, self.v)


class IgnoreDefaultOptions(tv.UniqueTypedValue, Option, lang.Final):
    pass


##


def update_default_options(
        cr: ConfigRegistry,
        *options: Option,
        discard: ta.Literal['all'] | ta.Iterable[type] | None = None,
        mode: ta.Literal['append', 'prepend', 'override', 'default'] = 'append',
) -> ConfigRegistry:
    given = Options(*options)

    def inner(_: ConfigRegistry) -> None:
        if (defaults := cr.get().get(DefaultOptions)) is not None:
            new = defaults.v.update(*given, discard=discard, mode=mode)
        else:
            new = Options(*given)

        cr.update(None, DefaultOptions(new), mode='override')

    cr.call_atomically(inner)
    return cr


def build_effective_options(configs: ConfigsGetter, options: ta.Iterable[Option] | None = None) -> Options:
    if options:
        given = Options(*options)
    else:
        given = _EMPTY_OPTIONS

    if IgnoreDefaultOptions in given:
        return given

    if (defaults := configs().get(DefaultOptions)) is None:
        return given

    return defaults.v.update(
        *given,
        mode='override',
    )
