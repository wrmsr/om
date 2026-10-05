"""
Conformance of concrete values to shapes. Where resolving types text - a value yet to be given a type - this checks
values which arrive already having one, as from files and jq filters. Nothing is reinterpreted: a number is never taken
for a string, nor a string for a boolean. The only liberty taken is between ints and floats of the same value, which
JSON and jq do not tell apart.

There is nothing to conform to where the shape is anything or unknown, so no value is ever rejected there - it was
given, not guessed.
"""
import collections.abc
import typing as ta

from .errors import OverrideError
from .errors import OverrideValueError
from .errors import render_suggestion
from .paths import IndexSegment
from .paths import KeySegment
from .paths import OverridePath
from .paths import describe_path
from .shapes import AnyShape
from .shapes import ChoiceShape
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
from .shapes import describe_shape
from .shapes import unlazy_shape
from .trees import own_tree


##


def _is_number(v: ta.Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_list(v: ta.Any) -> bool:
    return isinstance(v, collections.abc.Sequence) and not isinstance(v, (str, bytes, bytearray))


def _describe_value(v: ta.Any) -> str:
    if v is None:
        return 'null'
    elif isinstance(v, bool):
        return 'true' if v else 'false'
    elif _is_number(v):
        return f'number {v!r}'
    elif isinstance(v, str):
        return f'string {v!r}'
    elif isinstance(v, collections.abc.Mapping):
        return 'a map'
    elif _is_list(v):
        return 'a list'
    else:
        return repr(v)


def _error(value: ta.Any, shape: Shape, path: OverridePath) -> OverrideValueError:
    return OverrideValueError(
        f'Expected {describe_shape(shape)} at {describe_path(path)}, got {_describe_value(value)}',
    )


def _conform_scalar(value: ta.Any, shape: ScalarShape, path: OverridePath) -> ta.Any:
    ty = shape.ty
    if ty is float:
        if _is_number(value):
            return float(value)
    elif ty is int:
        if _is_number(value) and (isinstance(value, int) or value.is_integer()):
            return int(value)
    elif type(value) is ty:
        return value
    raise _error(value, shape, path)


def _conform_choice(value: ta.Any, shape: ChoiceShape, path: OverridePath) -> ta.Any:
    for c in shape.values:
        if (_is_number(value) and _is_number(c)) or type(value) is type(c):
            if value == c:
                return c
    raise _error(value, shape, path)


def _conform_items(
        items: ta.Iterable[tuple[ta.Any, ta.Any]],
        shape: Shape,
        path: OverridePath,
) -> dict[str, ta.Any]:
    ret: dict[str, ta.Any] = {}
    for k, v in items:
        if not isinstance(k, str):
            raise OverrideValueError(f'Expected string keys at {describe_path(path)}, got {k!r}')

        vs: Shape
        if isinstance(shape, MapShape):
            vs = shape.value
        elif isinstance(shape, ObjectShape):
            try:
                vs = shape.fields[k]
            except KeyError:
                if not shape.open:
                    raise OverrideValueError(
                        f'Unknown key {k!r} at {describe_path(path)}{render_suggestion(k, shape.fields)}',
                    ) from None
                vs = AnyShape()
        else:
            vs = AnyShape()

        ret[k] = conform_value(v, vs, (*path, KeySegment(k, quoted=True)))
    return ret


def _conform_tagged(value: ta.Any, shape: TaggedShape, path: OverridePath) -> dict[str, ta.Any]:
    def get_tagged(tag: ta.Any) -> Shape:
        try:
            return shape.by_tag[tag]
        except (KeyError, TypeError):
            raise OverrideValueError(
                f'Unknown tag {tag!r} at {describe_path(path)}{render_suggestion(str(tag), shape.by_tag)}',
            ) from None

    if (tf := shape.tag_field) is None:
        if len(value) != 1:
            raise OverrideValueError(
                f'Expected a map of exactly one tag at {describe_path(path)}, got {sorted(map(str, value))!r}',
            )
        [(tag, v)] = value.items()
        return {tag: conform_value(v, get_tagged(tag), (*path, KeySegment(str(tag), quoted=True)))}

    try:
        tag = value[tf]
    except KeyError:
        raise OverrideValueError(f'Missing {tf!r} tag at {describe_path(path)}') from None
    return {tf: tag, **_conform_items(
        [(k, v) for k, v in value.items() if k != tf],
        unlazy_shape(get_tagged(tag)),
        path,
    )}


def conform_value(value: ta.Any, shape: Shape, path: OverridePath = ()) -> ta.Any:
    """Returns the value - as a tree of plain, unaliased dicts and lists - as its shape would have it."""

    shape = unlazy_shape(shape)

    if isinstance(shape, (AnyShape, UnknownShape)):
        return own_tree(value)

    elif isinstance(shape, ScalarShape):
        return _conform_scalar(value, shape, path)

    elif isinstance(shape, ChoiceShape):
        return _conform_choice(value, shape, path)

    elif isinstance(shape, OptionalShape):
        if value is None:
            return None
        return conform_value(value, shape.inner, path)

    elif isinstance(shape, UnionShape):
        for alt in shape.alternatives:
            try:
                return conform_value(value, alt, path)
            except OverrideError:
                pass
        raise _error(value, shape, path)

    elif isinstance(shape, (ListShape, TupleShape)):
        if not _is_list(value):
            raise _error(value, shape, path)

        ess: ta.Sequence[Shape]
        if isinstance(shape, TupleShape):
            if len(value) != len(ess := shape.elements):
                raise OverrideValueError(
                    f'Expected exactly {len(ess)} elements at {describe_path(path)}, got {len(value)}',
                )
        else:
            ess = [shape.element] * len(value)

        return [
            conform_value(e, es, (*path, IndexSegment(i)))
            for i, (e, es) in enumerate(zip(value, ess, strict=True))
        ]

    elif isinstance(shape, (MapShape, ObjectShape, TaggedShape)):
        if not isinstance(value, collections.abc.Mapping):
            raise _error(value, shape, path)
        if isinstance(shape, TaggedShape):
            return _conform_tagged(value, shape, path)
        return _conform_items(value.items(), shape, path)

    else:
        raise TypeError(shape)
