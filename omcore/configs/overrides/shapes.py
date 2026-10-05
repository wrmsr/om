"""
A deliberately small description of the 'wire' shape of a tree - just enough to type bare scalars and to catch
misspelled keys. Shapes are optional everywhere: `AnyShape` is the absence of one.

Shapes are derived lazily (see `LazyShape`) so that a description of something not understood (`UnknownShape`) is
harmless unless and until a value actually has to be produced for it.
"""
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang


##


class Shape(lang.Abstract, lang.Sealed):
    pass


#


@dc.dataclass(frozen=True)
class AnyShape(Shape, lang.Final):
    """Understood to be anything at all: values are guessed, and anything beneath is also anything."""


@dc.dataclass(frozen=True)
class UnknownShape(Shape, lang.Final):
    """
    Not understood. Paths may still pass through and remove things beneath one, but producing a value for one requires
    either guessing or giving up.
    """

    what: ta.Any = None


#


SCALAR_SHAPE_TYPES: tuple[type, ...] = (
    bool,
    int,
    float,
    str,
)


@dc.dataclass(frozen=True)
class ScalarShape(Shape, lang.Final):
    ty: type

    def __post_init__(self) -> None:
        check.in_(self.ty, SCALAR_SHAPE_TYPES)


@dc.dataclass(frozen=True)
class ChoiceShape(Shape, lang.Final):
    """One of a fixed set of scalar values, as with literals and enums."""

    values: ta.Sequence[ta.Any] = dc.xfield(coerce=tuple)


@dc.dataclass(frozen=True)
class OptionalShape(Shape, lang.Final):
    inner: Shape


@dc.dataclass(frozen=True)
class UnionShape(Shape, lang.Final):
    """The first alternative to accept a value or path wins."""

    alternatives: ta.Sequence[Shape] = dc.xfield(coerce=tuple)


#


@dc.dataclass(frozen=True)
class ListShape(Shape, lang.Final):
    element: Shape


@dc.dataclass(frozen=True)
class TupleShape(Shape, lang.Final):
    elements: ta.Sequence[Shape] = dc.xfield(coerce=tuple)


@dc.dataclass(frozen=True)
class MapShape(Shape, lang.Final):
    value: Shape


@dc.dataclass(frozen=True)
class ObjectShape(Shape, lang.Final):
    fields: ta.Mapping[str, Shape]

    # Keys other than those of the fields are permitted, and may be anything.
    open: bool = False


@dc.dataclass(frozen=True)
class TaggedShape(Shape, lang.Final):
    """
    One of a number of tagged alternatives. Without a tag field the tag is the sole key of a wrapping map
    (`{tag: {...}}`), with one the tag sits alongside the alternative's own keys (`{type: tag, ...}`).
    """

    by_tag: ta.Mapping[str, Shape]

    tag_field: str | None = None


#


@ta.final
class LazyShape(Shape, lang.Final):
    """A shape derived only once it is walked to."""

    _shape: Shape

    def __init__(self, fn: ta.Callable[[], Shape]) -> None:
        super().__init__()

        self._fn = fn

    def get(self) -> Shape:
        try:
            return self._shape
        except AttributeError:
            pass

        # Benignly racy: shape derivation is idempotent.
        shape = self._shape = unlazy_shape(self._fn())
        return shape


def unlazy_shape(shape: Shape) -> Shape:
    while isinstance(shape, LazyShape):
        shape = shape.get()
    return shape


##


ANY_SHAPE = AnyShape()


def describe_shape(shape: Shape) -> str:
    shape = unlazy_shape(shape)

    if isinstance(shape, ScalarShape):
        return shape.ty.__name__
    elif isinstance(shape, ChoiceShape):
        return f'one of {", ".join(map(repr, shape.values))}'
    elif isinstance(shape, OptionalShape):
        return f'{describe_shape(shape.inner)} or null'
    elif isinstance(shape, UnionShape):
        return ' or '.join(describe_shape(a) for a in shape.alternatives)
    elif isinstance(shape, (ListShape, TupleShape)):
        return 'list'
    elif isinstance(shape, (MapShape, ObjectShape, TaggedShape)):
        return 'map'
    elif isinstance(shape, AnyShape):
        return 'anything'
    elif isinstance(shape, UnknownShape):
        if (w := shape.what) is None:
            return 'unknown'
        return f'unknown ({w if isinstance(w, str) else type(w).__name__})'
    else:
        raise TypeError(shape)


def get_container_type(shape: Shape) -> type | None:
    """The type of container - dict or list - a shape calls for, if it calls for one."""

    shape = unlazy_shape(shape)

    if isinstance(shape, (ListShape, TupleShape)):
        return list
    elif isinstance(shape, (MapShape, ObjectShape, TaggedShape)):
        return dict
    elif isinstance(shape, OptionalShape):
        return get_container_type(shape.inner)
    elif isinstance(shape, UnionShape):
        return next((ct for a in shape.alternatives if (ct := get_container_type(a)) is not None), None)
    else:
        return None
