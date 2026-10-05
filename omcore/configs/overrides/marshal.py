"""
Derives shapes from - and thus overrides objects through - the marshal system, by inspecting the unmarshalers it
constructs. Only the commonplace handlers are understood: anything else (custom handlers, secrets, typed values, ...)
is an `UnknownShape`, which is of no consequence unless an override has a value produced for it.
"""
import typing as ta

from ... import check
from ... import marshal as msh
from .applying import OverrideApplier
from .dumping import OverrideDumpFormat
from .dumping import dump_tree
from .ops import OverrideOp
from .shapes import SCALAR_SHAPE_TYPES
from .shapes import AnyShape
from .shapes import ChoiceShape
from .shapes import LazyShape
from .shapes import ListShape
from .shapes import MapShape
from .shapes import ObjectShape
from .shapes import OptionalShape
from .shapes import ScalarShape
from .shapes import Shape
from .shapes import TaggedShape
from .shapes import TupleShape
from .shapes import UnionShape
from .shapes import UnknownShape


T = ta.TypeVar('T')


##


def _lazy(u: msh.Unmarshaler) -> Shape:
    return LazyShape(lambda: get_unmarshaler_shape(u))


def _get_primitive_shape(ty: type) -> Shape | None:
    if ty in SCALAR_SHAPE_TYPES:
        return ScalarShape(ty)
    elif ty is type(None):
        return ChoiceShape([None])
    else:
        return None


def _get_object_shape(u: msh.ObjectUnmarshaler) -> Shape:
    if u.unwrap_if_single_field is not None:
        return UnknownShape(u)

    return ObjectShape(
        {n: _lazy(fu) for n, (_, fu) in u.fields_by_unmarshal_name.items()},
        open=u.ignore_unknown or u.specials.unknown is not None,
    )


def _get_primitive_union_shape(u: msh.PrimitiveUnionUnmarshaler) -> Shape:
    # Ordered from the pickiest about its spelling to the least: a string would accept anything.
    alts: list[Shape] = [ScalarShape(ty) for ty in SCALAR_SHAPE_TYPES if ty in u.tys and ty is not str]
    if u.x is not None:
        alts.append(_lazy(u.x))
    if str in u.tys:
        alts.append(ScalarShape(str))

    if len(alts) != len(u.tys) + (u.x is not None):
        return UnknownShape(u)
    return UnionShape(alts)


def _get_mapping_shape(u: msh.MappingUnmarshaler) -> Shape:
    if not (isinstance(ke := u.ke, msh.PrimitiveMarshalerUnmarshaler) and ke.ty is str):
        return UnknownShape(u)
    return MapShape(_lazy(u.ve))


def _get_polymorphism_shape(u: msh.WrapperPolymorphismUnmarshaler | msh.FieldPolymorphismUnmarshaler) -> Shape:
    return TaggedShape(
        {t: _lazy(su) for t, su in u.get_unmarshaler_map().items()},
        tag_field=u.tag_field if isinstance(u, msh.FieldPolymorphismUnmarshaler) else None,
    )


# Keyed by exact type: a subclass of an understood handler is not itself understood.
_SHAPE_GETTERS: ta.Mapping[type, ta.Callable[[ta.Any], Shape | None]] = {
    msh.RecursiveProxyUnmarshaler: lambda u: get_unmarshaler_shape(u.get_target()),

    msh.AnyMarshalerUnmarshaler: lambda u: AnyShape(),

    msh.PrimitiveMarshalerUnmarshaler: lambda u: _get_primitive_shape(u.ty),

    msh.EnumNameUnmarshaler: lambda u: ChoiceShape(list(u.ty.__members__)),
    msh.EnumValueUnmarshaler: lambda u: ChoiceShape([m.value for m in u.ty]),

    msh.LiteralUnmarshaler: lambda u: ChoiceShape(sorted(u.vs, key=repr)),

    msh.OptionalUnmarshaler: lambda u: OptionalShape(_lazy(u.e)),

    msh.LiteralUnionUnmarshaler: lambda u: UnionShape([_lazy(u.l), _lazy(u.x)]),
    msh.PrimitiveUnionUnmarshaler: _get_primitive_union_shape,

    msh.IterableUnmarshaler: lambda u: ListShape(_lazy(u.e)),
    msh.VariadicTupleUnmarshaler: lambda u: ListShape(_lazy(u.e)),
    msh.FixedTupleUnmarshaler: lambda u: TupleShape([_lazy(e) for e in u.es]),

    msh.MappingUnmarshaler: _get_mapping_shape,

    msh.ObjectUnmarshaler: _get_object_shape,

    msh.WrapperPolymorphismUnmarshaler: _get_polymorphism_shape,
    msh.FieldPolymorphismUnmarshaler: _get_polymorphism_shape,
}


def get_unmarshaler_shape(u: msh.Unmarshaler) -> Shape:
    """
    Derives the shape of what an unmarshaler unmarshals. This is shallow: whatever the unmarshaler in turn refers to is
    only derived once walked to.
    """

    if (fn := _SHAPE_GETTERS.get(type(u))) is not None and (shape := fn(u)) is not None:
        return shape
    return UnknownShape(u)


##


class ConfigOverrider(ta.Generic[T]):
    """Overrides instances of a type by way of their marshaled form: marshal, apply, unmarshal."""

    def __init__(
            self,
            ty: ta.Any,
            *,
            marshaling: msh.Marshaling | None = None,
            guess_unknown: bool = False,
            file_loader: ta.Callable[[str], ta.Any] | None = None,
    ) -> None:
        super().__init__()

        self._ty = check.not_none(ty)
        self._marshaling = marshaling if marshaling is not None else msh.global_marshaling()

        self._shape = get_unmarshaler_shape(self._marshaling.new_unmarshal_factory_context().make_unmarshaler(ty))
        self._applier = OverrideApplier(
            self._shape,
            guess_unknown=guess_unknown,
            file_loader=file_loader,
        )

    @property
    def shape(self) -> Shape:
        return self._shape

    def marshal(self, obj: T) -> ta.Any:
        return self._marshaling.marshal(obj, self._ty)

    def apply(self, tree: ta.Any, ops: ta.Iterable[OverrideOp | str]) -> ta.Any:
        return self._applier.apply(tree, ops)

    def unmarshal(self, tree: ta.Any) -> T:
        return self._marshaling.unmarshal(tree, self._ty)

    def dump(self, tree: ta.Any, fmt: OverrideDumpFormat = 'overrides') -> str:
        return dump_tree(tree, fmt, shape=self._shape)

    def override(self, obj: T, ops: ta.Iterable[OverrideOp | str]) -> T:
        return self.unmarshal(self.apply(self.marshal(obj), ops))


def override_config(
        obj: T,
        ops: ta.Iterable[OverrideOp | str],
        ty: ta.Any = None,
        **kwargs: ta.Any,
) -> T:
    return ConfigOverrider[T](ty if ty is not None else type(obj), **kwargs).override(obj, ops)
