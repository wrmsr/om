import inspect
import typing as ta

from ... import check
from ... import lang
from ... import reflect as rfl
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import FactoryPair
from ..api.types import Marshaler
from ..api.types import Unmarshaler
from .infos import FieldInfo
from .infos import FieldInfos
from .specs import ObjectSpec


##


def _get_namedtuple_cls(rty: rfl.Type) -> type | None:
    if (
            isinstance(rty, rfl.Instance) and
            (cls := rfl.get_runtime_type_or_none(rty)) is not None and
            issubclass(cls, tuple) and
            ta.NamedTuple in rfl.get_orig_bases(cls)
    ):
        return cls
    return None


def _is_namedtuple_cls(ty: type) -> bool:
    return issubclass(ty, tuple) and ta.NamedTuple in rfl.get_orig_bases(ty)


def get_namedtuple_field_infos(ty: type) -> FieldInfos:
    check.arg(_is_namedtuple_cls(ty), ty)

    sig = inspect.signature(ty)

    ret: list[FieldInfo] = []
    for param in sig.parameters.values():
        ret.append(FieldInfo(
            name=param.name,
            type=param.annotation,

            marshal_name=param.name,
            unmarshal_names=[param.name],
        ))

    return FieldInfos(ret)


##


class NamedtupleFactory(FactoryPair):
    """Sniffs typed namedtuple types, resolves them to ObjectSpecs, and re-enters construction with the spec."""

    def _sniff_spec(self, spec: Spec) -> ObjectSpec | None:
        if not isinstance(spec, rfl.Type):
            return None

        if (cls := _get_namedtuple_cls(spec)) is None:
            return None

        check.state(not lang.is_abstract_class(cls))

        return ObjectSpec(
            ty=cls,
            fields=get_namedtuple_field_infos(cls),
        )

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if (osp := self._sniff_spec(spec)) is None:
            return None

        return lambda: ctx.make_marshaler(osp)

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if (osp := self._sniff_spec(spec)) is None:
            return None

        return lambda: ctx.make_unmarshaler(osp)


NamedtupleMarshalerFactory = NamedtupleFactory
NamedtupleUnmarshalerFactory = NamedtupleFactory
