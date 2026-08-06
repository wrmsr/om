import dataclasses as dc
import typing as ta

from ... import lang
from ...funcs import guard as gfs
from .contexts import MarshalContext
from .contexts import MarshalFactoryContext
from .contexts import UnmarshalContext
from .contexts import UnmarshalFactoryContext
from .specs import Spec
from .types import Marshaler
from .types import MarshalerFactory
from .types import Unmarshaler
from .types import UnmarshalerFactory
from .values import Value


MarshalerFactoryFn: ta.TypeAlias = gfs.GuardFn[[MarshalFactoryContext, Spec], Marshaler]
UnmarshalerFactoryFn: ta.TypeAlias = gfs.GuardFn[[UnmarshalFactoryContext, Spec], Unmarshaler]


##


@dc.dataclass(frozen=True)
class FuncMarshaler(Marshaler, lang.Final):
    fn: ta.Callable[[MarshalContext, ta.Any], Value]

    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        return self.fn(ctx, o)


@dc.dataclass(frozen=True)
class FuncUnmarshaler(Unmarshaler, lang.Final):
    fn: ta.Callable[[UnmarshalContext, Value], ta.Any]

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        return self.fn(ctx, v)


##


@dc.dataclass(frozen=True)
class FuncMarshalerFactory(MarshalerFactory):  # noqa
    gf: MarshalerFactoryFn

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        return self.gf(ctx, spec)


@dc.dataclass(frozen=True)
class FuncUnmarshalerFactory(UnmarshalerFactory):  # noqa
    gf: UnmarshalerFactoryFn

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        return self.gf(ctx, spec)
