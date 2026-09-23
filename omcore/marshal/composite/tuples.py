import collections.abc
import typing as ta

from ... import check
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


##


@dc.dataclass(frozen=True)
class FixedTupleMarshaler(Marshaler):
    es: tuple[Marshaler, ...]

    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        o = check.isinstance(o, tuple)
        if len(o) != len(self.es):
            raise ValueError(f'Expected tuple of length {len(self.es)}, got {len(o)}')
        return [e.marshal(ctx, item) for e, item in zip(self.es, o)]


@dc.dataclass(frozen=True)
class VariadicTupleMarshaler(Marshaler):
    e: Marshaler

    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        return [self.e.marshal(ctx, item) for item in check.isinstance(o, tuple)]


class TupleMarshalerFactory(MarshalerFactoryMethodClass):
    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_fixed(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.TupleType):
            return None
        rty = spec

        return lambda: FixedTupleMarshaler(tuple(ctx.make_marshaler(item) for item in rty.items))

    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_variadic(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Instance) or spec.runtime_type is not tuple or len(spec.args) != 1:
            return None
        rty = spec

        return lambda: VariadicTupleMarshaler(ctx.make_marshaler(check.single(rty.args)))

    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_concrete(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Instance) or spec.runtime_type is not tuple or spec.args:
            return None
        return lambda: VariadicTupleMarshaler(ctx.make_marshaler(ta.Any))


##


@dc.dataclass(frozen=True)
class FixedTupleUnmarshaler(Unmarshaler):
    es: tuple[Unmarshaler, ...]

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> tuple:
        if isinstance(v, str):
            raise TypeError(v)
        items = tuple(check.isinstance(v, collections.abc.Iterable))
        if len(items) != len(self.es):
            raise ValueError(f'Expected tuple of length {len(self.es)}, got {len(items)}')
        return tuple(e.unmarshal(ctx, item) for e, item in zip(self.es, items))


@dc.dataclass(frozen=True)
class VariadicTupleUnmarshaler(Unmarshaler):
    e: Unmarshaler

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> tuple:
        if isinstance(v, str):
            raise TypeError(v)
        return tuple(self.e.unmarshal(ctx, item) for item in check.isinstance(v, collections.abc.Iterable))


class TupleUnmarshalerFactory(UnmarshalerFactoryMethodClass):
    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_fixed(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.TupleType):
            return None
        rty = spec

        return lambda: FixedTupleUnmarshaler(tuple(ctx.make_unmarshaler(item) for item in rty.items))

    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_variadic(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Instance) or spec.runtime_type is not tuple or len(spec.args) != 1:
            return None
        rty = spec

        return lambda: VariadicTupleUnmarshaler(ctx.make_unmarshaler(check.single(rty.args)))

    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_concrete(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Instance) or spec.runtime_type is not tuple or spec.args:
            return None
        return lambda: VariadicTupleUnmarshaler(ctx.make_unmarshaler(ta.Any))
