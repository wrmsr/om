import functools
import typing as ta

from ... import check
from ... import collections as col
from ... import dataclasses as dc
from ... import reflect as rfl
from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import Unmarshaler
from ..api.values import Value
from ..factories.method import MarshalerFactoryMethodClass
from ..factories.method import UnmarshalerFactoryMethodClass
from .api import DefaultPersistentConstructors


##


@dc.dataclass(frozen=True)
class PersistentSequenceMarshaler(Marshaler):
    e: Marshaler

    def marshal(self, ctx: MarshalContext, o: col.PersistentSequence) -> Value:
        return list(map(functools.partial(self.e.marshal, ctx), o))


def _get_persistent_sequence_cls(rty: rfl.Type) -> type | None:
    if not isinstance(rty, rfl.Instance):
        return None
    if (cls := rty.runtime_type) is None or not issubclass(cls, col.PersistentSequence):
        return None
    return cls


class PersistentSequenceMarshalerFactory(MarshalerFactoryMethodClass):
    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_generic(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if _get_persistent_sequence_cls(rty) is None or len(check.isinstance(rty, rfl.Instance).args) != 1:
            return None
        return lambda: PersistentSequenceMarshaler(ctx.make_marshaler(check.single(check.isinstance(rty, rfl.Instance).args)))  # noqa

    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_concrete(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if _get_persistent_sequence_cls(rty) is None:
            return None
        return lambda: PersistentSequenceMarshaler(ctx.make_marshaler(ta.Any))


#


@dc.dataclass(frozen=True)
class PersistentSequenceUnmarshaler(Unmarshaler):
    cls: type
    e: Unmarshaler

    ctor: ta.Callable[[ta.Iterable], ta.Any] | None = None

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> col.PersistentSequence:
        if isinstance(v, str):
            raise TypeError(v)
        if (ctor := self.ctor) is None:
            if ctx.options is not None and (opt := ctx.options.get(DefaultPersistentConstructors)) is not None:
                ctor = opt.sequence
            if ctor is None:
                ctor = col.new_persistent_seq
        return ctor(map(functools.partial(self.e.unmarshal, ctx), check.isinstance(v, ta.Sequence)))


class PersistentSequenceUnmarshalerFactory(UnmarshalerFactoryMethodClass):
    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_generic(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (cls := _get_persistent_sequence_cls(rty)) is None or len(check.isinstance(rty, rfl.Instance).args) != 1:
            return None
        return lambda: PersistentSequenceUnmarshaler(cls, ctx.make_unmarshaler(check.single(check.isinstance(rty, rfl.Instance).args)))  # noqa

    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_concrete(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (cls := _get_persistent_sequence_cls(rty)) is None:
            return None
        return lambda: PersistentSequenceUnmarshaler(cls, ctx.make_unmarshaler(ta.Any))


##


@dc.dataclass(frozen=True)
class PersistentMappingMarshaler(Marshaler):
    ke: Marshaler
    ve: Marshaler

    def marshal(self, ctx: MarshalContext, o: col.PersistentMapping) -> Value:
        return {
            self.ke.marshal(ctx, uk): self.ve.marshal(ctx, uv)
            for uk, uv in check.isinstance(o, col.PersistentMapping).items()
        }


def _get_persistent_mapping_cls(rty: rfl.Type) -> type | None:
    if not isinstance(rty, rfl.Instance):
        return None
    if (cls := rty.runtime_type) is None or not issubclass(cls, col.PersistentMapping):
        return None
    return cls


class PersistentMappingMarshalerFactory(MarshalerFactoryMethodClass):
    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_generic(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if _get_persistent_mapping_cls(rty) is None or len(check.isinstance(rty, rfl.Instance).args) != 2:
            return None
        kt, vt = check.isinstance(rty, rfl.Instance).args
        return lambda: PersistentMappingMarshaler(ctx.make_marshaler(kt), ctx.make_marshaler(vt))

    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_concrete(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if _get_persistent_mapping_cls(rty) is None:
            return None
        return lambda: PersistentMappingMarshaler(a := ctx.make_marshaler(ta.Any), a)


#


@dc.dataclass(frozen=True)
class PersistentMappingUnmarshaler(Unmarshaler):
    cls: type
    ke: Unmarshaler
    ve: Unmarshaler

    ctor: ta.Callable[[ta.Iterable], ta.Any] | None = None

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> col.PersistentMapping:
        if (ctor := self.ctor) is None:
            if ctx.options is not None and (opt := ctx.options.get(DefaultPersistentConstructors)) is not None:
                ctor = opt.mapping
            if ctor is None:
                ctor = col.new_persistent_map
        return ctor((
            (self.ke.unmarshal(ctx, k), self.ve.unmarshal(ctx, v))
            for k, v in check.isinstance(v, ta.Mapping).items()
        ))


class PersistentMappingUnmarshalerFactory(UnmarshalerFactoryMethodClass):
    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_generic(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (cls := _get_persistent_mapping_cls(rty)) is None or len(check.isinstance(rty, rfl.Instance).args) != 2:
            return None
        kt, vt = check.isinstance(rty, rfl.Instance).args
        return lambda: PersistentMappingUnmarshaler(cls, ctx.make_unmarshaler(kt), ctx.make_unmarshaler(vt))

    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_concrete(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (cls := _get_persistent_mapping_cls(rty)) is None:
            return None
        return lambda: PersistentMappingUnmarshaler(cls, a := ctx.make_unmarshaler(ta.Any), a)
