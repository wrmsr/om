import typing as ta

from ... import dataclasses as dc
from .errors import OverridePathError
from .errors import render_suggestion
from .paths import OverridePath
from .paths import describe_path
from .shapes import ANY_SHAPE
from .shapes import AnyShape
from .shapes import ChoiceShape
from .shapes import ListShape
from .shapes import MapShape
from .shapes import ObjectShape
from .shapes import OptionalShape
from .shapes import Shape
from .shapes import TaggedShape
from .shapes import TupleShape
from .shapes import UnionShape
from .shapes import UnknownShape
from .shapes import describe_shape
from .shapes import unlazy_shape


T = ta.TypeVar('T')


##


@dc.dataclass(frozen=True)
class ShapeStep:
    shape: Shape

    # The key is one its container's shape declares, as opposed to one it merely permits.
    declared: bool = False

    # The key cannot coexist with any other in its container.
    exclusive: bool = False


def _check_key_type(shape: Shape, key: str | int, ty: type[T], path: OverridePath) -> T:
    if not isinstance(key, ty):
        raise OverridePathError(
            f'Expected {describe_shape(shape)} but found {"list" if isinstance(key, int) else "map"} '
            f'at {describe_path(path)}',
        )
    return key


def _get_tagged(shape: TaggedShape, tag: ta.Any, path: OverridePath) -> Shape:
    try:
        return shape.by_tag[tag]
    except (KeyError, TypeError):
        pass
    raise OverridePathError(
        f'Unknown tag {tag!r} at {describe_path(path)}{render_suggestion(str(tag), shape.by_tag)}',
    )


def step_shape(
        shape: Shape,
        key: str | int,
        *,
        node: ta.Any,
        path: OverridePath,
) -> ShapeStep:
    """
    Steps from the shape of a container down to the shape of what is at the given key within it. The key has already
    been located in the actual container (the node), and the path is that of the container.
    """

    shape = unlazy_shape(shape)

    if isinstance(shape, AnyShape):
        return ShapeStep(ANY_SHAPE)

    elif isinstance(shape, UnknownShape):
        return ShapeStep(shape)

    elif isinstance(shape, OptionalShape):
        return step_shape(shape.inner, key, node=node, path=path)

    elif isinstance(shape, UnionShape):
        err: OverridePathError | None = None
        for alt in shape.alternatives:
            try:
                return step_shape(alt, key, node=node, path=path)
            except OverridePathError as e:
                err = err or e
        raise err or OverridePathError(f'Cannot navigate into {describe_shape(shape)} at {describe_path(path)}')

    elif isinstance(shape, ObjectShape):
        sk = _check_key_type(shape, key, str, path)
        try:
            return ShapeStep(shape.fields[sk], declared=True)
        except KeyError:
            pass
        if shape.open:
            return ShapeStep(ANY_SHAPE)
        raise OverridePathError(f'Unknown key {sk!r} at {describe_path(path)}{render_suggestion(sk, shape.fields)}')

    elif isinstance(shape, MapShape):
        _check_key_type(shape, key, str, path)
        return ShapeStep(shape.value)

    elif isinstance(shape, ListShape):
        _check_key_type(shape, key, int, path)
        return ShapeStep(shape.element)

    elif isinstance(shape, TupleShape):
        ik = _check_key_type(shape, key, int, path)
        if not (0 <= ik < len(shape.elements)):
            raise OverridePathError(
                f'Index {ik} out of range at {describe_path(path)}: must have exactly {len(shape.elements)} elements',
            )
        return ShapeStep(shape.elements[ik], declared=True)

    elif isinstance(shape, TaggedShape):
        sk = _check_key_type(shape, key, str, path)

        if shape.tag_field is None:
            return ShapeStep(_get_tagged(shape, sk, path), declared=True, exclusive=True)

        if sk == shape.tag_field:
            return ShapeStep(ChoiceShape(list(shape.by_tag)), declared=True)

        try:
            tag = node[shape.tag_field]
        except KeyError:
            raise OverridePathError(f'No {shape.tag_field!r} tag set at {describe_path(path)}') from None
        return step_shape(_get_tagged(shape, tag, path), sk, node=node, path=path)

    else:
        raise OverridePathError(f'Cannot navigate into {describe_shape(shape)} at {describe_path(path)}')
