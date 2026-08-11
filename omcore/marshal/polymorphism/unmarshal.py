import abc
import collections.abc
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ... import reflect as rfl
from ..api.contexts import UnmarshalContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Unmarshaler
from ..api.types import UnmarshalerFactory
from ..api.values import Value
from .api import DisjointPolymorphism
from .api import FieldTypeTagging
from .api import LazySubtype
from .api import Polymorphism
from .api import PolymorphismTagError
from .api import SubtypeInfos
from .api import TypeTagging
from .api import WrapperTypeTagging
from .matching import get_disjoint_polymorphism_subtypes
from .matching import get_polymorphism_subtypes
from .resolving import resolve_polymorphism
from .specs import DisjointPolymorphismSpec
from .specs import PolymorphismSpec


##


class PolymorphismUnmarshaler(Unmarshaler, lang.Abstract):
    @abc.abstractmethod
    def get_unmarshaler_map(self) -> ta.Mapping[str, Unmarshaler]:
        raise NotImplementedError


class _BasePolymorphismUnmarshaler(PolymorphismUnmarshaler, lang.Abstract):
    def __init__(
            self,
            m: ta.Mapping[str, Unmarshaler],
    ) -> None:
        super().__init__()

        self._m = m

    def get_unmarshaler_map(self) -> ta.Mapping[str, Unmarshaler]:
        return self._m

    def _do_unmarshal(self, ctx: UnmarshalContext, tag: str, iv: Value) -> ta.Any | None:
        try:
            u = self._m[tag]
        except KeyError:
            raise PolymorphismTagError(tag) from None
        return u.unmarshal(ctx, iv)


class WrapperPolymorphismUnmarshaler(_BasePolymorphismUnmarshaler):
    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any | None:
        ma = check.isinstance(v, collections.abc.Mapping)
        [(tag, iv)] = ma.items()
        return self._do_unmarshal(ctx, tag, iv)


class FieldPolymorphismUnmarshaler(_BasePolymorphismUnmarshaler):
    def __init__(
            self,
            m: ta.Mapping[str, Unmarshaler],
            tf: str,
    ) -> None:
        super().__init__(m)

        self._tf = tf

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any | None:
        ma = dict(check.isinstance(v, collections.abc.Mapping))
        tag = ma.pop(self._tf)
        return self._do_unmarshal(ctx, tag, ma)


@dc.dataclass()
class _LazySubtypeUnmarshaler(Unmarshaler):
    """
    Stands in for a lazily-declared subtype's unmarshaler: the first hit of its tag imports the class - and nothing
    else's.
    """

    lz: LazySubtype

    ty: ta.Any = dc.field(init=False)

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        try:
            ty = self.ty
        except AttributeError:
            ty = self.ty = self.lz.resolve()

        # FIXME: naughty - see AnyMarshalerUnmarshaler. Deliberately unmemoized: the runtime's cache makes the re-entry
        # near-free and keeps this invalidation-correct (the lazily-imported module may itself register configs).
        u = ctx.runtime.make_unmarshaler(UnmarshalFactoryContext(runtime=ctx.runtime), ty)

        return u.unmarshal(ctx, v)


def make_polymorphism_unmarshaler(
        subtypes: SubtypeInfos,
        tt: TypeTagging,
        ctx: UnmarshalFactoryContext,
) -> Unmarshaler:
    check.not_empty(subtypes)

    m: dict[str, Unmarshaler] = {}
    for i in subtypes:
        u: Unmarshaler
        if (c := i.cls) is not None:
            u = ctx.make_unmarshaler(c)
        else:
            u = _LazySubtypeUnmarshaler(check.isinstance(i.ty, LazySubtype))
        for t in (i.tag, *i.alts):
            m[t] = u

    if isinstance(tt, WrapperTypeTagging):
        return WrapperPolymorphismUnmarshaler(m)
    elif isinstance(tt, FieldTypeTagging):
        return FieldPolymorphismUnmarshaler(m, tt.field)
    else:
        raise TypeError(tt)


@dc.dataclass(frozen=True)
class PolymorphismUnmarshalerFactory(UnmarshalerFactory):
    p: Polymorphism | DisjointPolymorphism
    tt: TypeTagging = WrapperTypeTagging()

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        sts: SubtypeInfos | None
        if isinstance(self.p, DisjointPolymorphism):
            sts = get_disjoint_polymorphism_subtypes(rty, self.p)
        else:
            sts = get_polymorphism_subtypes(rty, self.p)

        if sts is None:
            return None
        return lambda: make_polymorphism_unmarshaler(sts, self.tt, ctx)


##


class PolymorphismSpecUnmarshalerFactory(UnmarshalerFactory):
    """
    Consumes PolymorphismSpecs (and DisjointPolymorphismSpecs): resolves the spec's subtype sources and hands off to the
    trivial handlers.
    """

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if isinstance(spec, DisjointPolymorphismSpec):
            dp = DisjointPolymorphism([resolve_polymorphism(ctx, s) for s in spec.specs])
            sts = dp.merge_subtypes()
            return lambda: make_polymorphism_unmarshaler(sts, spec.tagging, ctx)

        if not isinstance(spec, PolymorphismSpec):
            return None

        poly = resolve_polymorphism(ctx, spec)
        return lambda: make_polymorphism_unmarshaler(poly.subtypes, spec.tagging, ctx)
