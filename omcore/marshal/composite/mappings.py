import collections.abc
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import reflect as rfl
from ..api.contexts import BaseContext
from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.options import Options
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import Unmarshaler
from ..api.values import Value
from ..factories.method import MarshalerFactoryMethodClass
from ..factories.method import UnmarshalerFactoryMethodClass
from .api import DEFAULT_MAPPING_CONCRETE_TYPES
from .api import DefaultMappingConstructors


##


def get_default_mapping_constructor(
        cls: type,
        options: Options | None = None,
) -> ta.Callable[[collections.abc.Mapping], ta.Any]:
    if options is not None and (opt := options.get(DefaultMappingConstructors)) is not None:
        opt = check.isinstance(opt, DefaultMappingConstructors)
        o_ctor: ta.Any = None
        if cls == collections.abc.Mapping:
            o_ctor = opt.mapping
        elif cls == collections.abc.MutableMapping:
            o_ctor = opt.mutable_mapping
        if o_ctor is not None:
            return o_ctor

    return DEFAULT_MAPPING_CONCRETE_TYPES.get(cls, cls)  # noqa


#


def _get_mapping_cls(rty: rfl.Type) -> type | None:
    if not isinstance(rty, rfl.Instance):
        return None
    if (cls := rty.runtime_type) is None or not issubclass(cls, collections.abc.Mapping):
        return None
    return cls


class _GenericMappingCls(ta.NamedTuple):
    cls: ta.Any
    kt: rfl.Type
    vt: rfl.Type


def _get_mapping_args(ctx: BaseContext, rty: rfl.Type) -> _GenericMappingCls | None:
    if not isinstance(rty, rfl.Instance):
        return None
    if (cls := rty.runtime_type) is None or not issubclass(cls, collections.abc.Mapping):
        return None
    mro = rty.mro()
    tt = ctx.get_mirror().get_type_info(collections.abc.Mapping)
    try:
        me = mro.by_info[tt]
    except KeyError:
        return None
    kt, vt = me.args
    return _GenericMappingCls(cls, kt, vt)


#


@dc.dataclass(frozen=True)
class MappingMarshaler(Marshaler):
    ke: Marshaler
    ve: Marshaler

    def marshal(self, ctx: MarshalContext, o: ta.Mapping) -> Value:
        return {
            self.ke.marshal(ctx, uk): self.ve.marshal(ctx, uv)
            for uk, uv in check.isinstance(o, collections.abc.Mapping).items()
        }


class MappingMarshalerFactory(MarshalerFactoryMethodClass):
    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_generic(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (gmc := _get_mapping_args(ctx, rty)) is None:
            return None
        return lambda: MappingMarshaler(ctx.make_marshaler(gmc.kt), ctx.make_marshaler(gmc.vt))

    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_concrete(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if _get_mapping_cls(rty) is None:
            return None
        return lambda: MappingMarshaler(a := ctx.make_marshaler(ta.Any), a)


#


@dc.dataclass(frozen=True)
class MappingUnmarshaler(Unmarshaler):
    cls: type
    ke: Unmarshaler
    ve: Unmarshaler

    ctor: ta.Callable[[ta.Mapping[ta.Any, ta.Any]], ta.Mapping] | None = None

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Mapping:
        dct: dict = {}
        for mk, mv in check.isinstance(v, collections.abc.Mapping).items():
            dct[self.ke.unmarshal(ctx, mk)] = self.ve.unmarshal(ctx, mv)
        if (ctor := self.ctor) is None:
            ctor = get_default_mapping_constructor(self.cls, ctx.options)
        if ctor is dict:
            return dct
        return ctor(dct)


class MappingUnmarshalerFactory(UnmarshalerFactoryMethodClass):
    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_generic(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (gmc := _get_mapping_args(ctx, rty)) is None:
            return None
        return lambda: MappingUnmarshaler(gmc.cls, ctx.make_unmarshaler(gmc.kt), ctx.make_unmarshaler(gmc.vt))

    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_concrete(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (cls := _get_mapping_cls(rty)) is None:
            return None
        return lambda: MappingUnmarshaler(cls, a := ctx.make_unmarshaler(ta.Any), a)
