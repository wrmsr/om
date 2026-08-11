import typing as ta

from ... import lang
from ... import reflect as rfl
from ... import typedvalues as tv
from ..api.contexts import BaseContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.naming import CasingNaming
from ..api.naming import translate_name
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import Unmarshaler
from ..factories.method import MarshalerFactoryMethodClass
from ..factories.method import UnmarshalerFactoryMethodClass
from ..polymorphism.api import SubtypeInfo
from ..polymorphism.api import SubtypeInfos
from ..polymorphism.api import SuffixStripping
from ..polymorphism.api import WrapperTypeTagging
from ..polymorphism.api import polymorphism_from_subclasses
from ..polymorphism.marshal import make_polymorphism_marshaler
from ..polymorphism.unmarshal import make_polymorphism_unmarshaler


##


def _is_typed_values_union(rty: rfl.Type) -> bool:
    return (
        isinstance(rty, rfl.UnionType) and
        all(
            (cls := rfl.get_runtime_type_or_none(a)) is not None and issubclass(cls, tv.TypedValue)
            for a in rty.items
        )
    )


def _build_typed_value_union_poly(ctx: BaseContext, rty: rfl.Type) -> SubtypeInfos:
    def gus(sty: type) -> list[type]:
        # Mirrors how TypedValueMarshalerFactory builds abstract tv polymorphisms - computed directly rather than
        # scraped off a constructed handler.
        return [
            i.resolve()  # From-subclasses entries are always concrete - this never imports.
            for i in polymorphism_from_subclasses(
                sty,
                naming=CasingNaming(lang.SNAKE_CASE),
                suffix_stripping=SuffixStripping(mode='if_all'),
            ).subtypes
        ]

    tv_cls_set = tv.reflect_typed_values_impls(
        rty,
        find_abstract_subclasses=True,
        get_unsealed_subclasses=gus,
        mirror=ctx.get_mirror(),
    )

    return SubtypeInfos([
        SubtypeInfo(
            tv_cls,
            translate_name(tv_cls.__name__, CasingNaming(lang.SNAKE_CASE)),
        )
        for tv_cls in tv_cls_set
    ])


class TypedValueUnionMarshalerFactory(MarshalerFactoryMethodClass):
    @MarshalerFactoryMethodClass.make_marshaler.register
    def _make_union(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if not _is_typed_values_union(rty):
            return None

        return lambda: make_polymorphism_marshaler(
            _build_typed_value_union_poly(ctx, rty),
            WrapperTypeTagging(),
            ctx,
        )


class TypedValueUnionUnmarshalerFactory(UnmarshalerFactoryMethodClass):
    @UnmarshalerFactoryMethodClass.make_unmarshaler.register
    def _make_union(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None
        rty = spec

        if not _is_typed_values_union(rty):
            return None

        return lambda: make_polymorphism_unmarshaler(
            _build_typed_value_union_poly(ctx, rty),
            WrapperTypeTagging(),
            ctx,
        )
