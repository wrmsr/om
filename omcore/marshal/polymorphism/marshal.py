import abc
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ... import reflect as rfl
from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import MarshalerFactory
from ..api.values import Value
from .api import FieldTypeTagging
from .api import Polymorphism
from .api import PolymorphismSubtypeError
from .api import SubtypeInfos
from .api import TypeTagging
from .api import WrapperTypeTagging
from .matching import get_polymorphism_subtypes
from .resolving import resolve_polymorphism
from .specs import PolymorphismSpec


##


class PolymorphismMarshaler(Marshaler, lang.Abstract):
    @abc.abstractmethod
    def get_marshaler_map(self) -> ta.Mapping[type, tuple[str, Marshaler]]:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class WrapperPolymorphismMarshaler(PolymorphismMarshaler):
    m: ta.Mapping[type, tuple[str, Marshaler]]

    def get_marshaler_map(self) -> ta.Mapping[type, tuple[str, Marshaler]]:
        return self.m

    def marshal(self, ctx: MarshalContext, o: ta.Any | None) -> Value:
        ot = type(o)
        try:
            tag, m = self.m[ot]
        except KeyError:
            raise PolymorphismSubtypeError(ot) from None
        return {tag: m.marshal(ctx, o)}


@dc.dataclass(frozen=True)
class FieldPolymorphismMarshaler(PolymorphismMarshaler):
    m: ta.Mapping[type, tuple[str, Marshaler]]
    tf: str

    def get_marshaler_map(self) -> ta.Mapping[type, tuple[str, Marshaler]]:
        return self.m

    def marshal(self, ctx: MarshalContext, o: ta.Any | None) -> Value:
        ot = type(o)
        try:
            tag, m = self.m[ot]
        except KeyError:
            raise PolymorphismSubtypeError(ot) from None
        return {self.tf: tag, **m.marshal(ctx, o)}  # type: ignore


def make_polymorphism_marshaler(
        subtypes: SubtypeInfos,
        tt: TypeTagging,
        ctx: MarshalFactoryContext,
) -> Marshaler:
    check.not_empty(subtypes)

    m = {
        i.ty: (i.tag, ctx.make_marshaler(i.ty))
        for i in subtypes
    }

    if isinstance(tt, WrapperTypeTagging):
        return WrapperPolymorphismMarshaler(m)
    elif isinstance(tt, FieldTypeTagging):
        return FieldPolymorphismMarshaler(m, tt.field)
    else:
        raise TypeError(tt)


@dc.dataclass(frozen=True)
class PolymorphismMarshalerFactory(MarshalerFactory):
    p: Polymorphism
    tt: TypeTagging = WrapperTypeTagging()

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if (sts := get_polymorphism_subtypes(rty, self.p)) is None:
            return None
        return lambda: make_polymorphism_marshaler(sts, self.tt, ctx)


##


class PolymorphismSpecMarshalerFactory(MarshalerFactory):
    """Consumes PolymorphismSpecs: resolves the spec's subtype sources and hands off to the trivial handlers."""

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, PolymorphismSpec):
            return None

        poly = resolve_polymorphism(ctx, spec)
        return lambda: make_polymorphism_marshaler(poly.subtypes, spec.tagging, ctx)
