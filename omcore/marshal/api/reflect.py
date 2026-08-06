import dataclasses as dc
import typing as ta

from ... import lang
from ... import reflect as rfl
from ... import typedvalues as tv
from .configs import Config
from .configs import ConfigsGetter


##


@dc.dataclass(frozen=True)
class ReflectOverride(Config, tv.UniqueTypedValue, lang.Final):
    """
    Substitutes the registered runtime object with `obj` wherever it occurs in an annotation being reflected - at any
    level of nesting. Overrides must be registered before the first reflection through their config registry (in
    practice: during lazy init) - the runtime's mirror bakes them in.
    """

    obj: ta.Any


##


def get_rty_config_key(rty: rfl.Type) -> ta.Any | None:
    """The runtime object under which configs applying to this reflected type would have been registered."""

    if (obj := rfl.get_runtime_object_or_none(rty)) is not None:
        return obj

    if isinstance(rty, rfl.TypeAliasType) and (alias := rty.alias) is not None:
        return alias.runtime_object

    return None


##


def _make_context_mirror(configs: ConfigsGetter) -> rfl.Mirror:
    def substitutor(obj: object) -> object | None:
        try:
            cvs = configs(obj)
        except TypeError:
            # Unhashable runtime annotation objects cannot have been registered as config keys.
            return None

        if (ovr := cvs.get(ReflectOverride)) is not None:
            return ovr.obj

        return None

    # FIXME: internal import...
    from ...reflect._mirror import MirrorImpl

    return MirrorImpl(
        # parent=rfl.global_root_mirror(),
        type_reflect_substitutor=substitutor,
    )
