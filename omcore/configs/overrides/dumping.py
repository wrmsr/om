"""
Renders a tree gron-style in the override grammar itself: each line is a valid override statement which, applied to the
tree it was dumped from, changes nothing - making it something to grep for, copy, edit, and paste back as an argument.
"""
import json
import math
import typing as ta

from .errors import OverridePathError
from .literals import QUOTE_CHARS
from .literals import guess_scalar
from .parsing import FILE_PREFIX
from .paths import IndexSegment
from .paths import KeySegment
from .paths import OverridePath
from .paths import PathSegment
from .paths import render_path
from .shapes import ANY_SHAPE
from .shapes import OptionalShape
from .shapes import ScalarShape
from .shapes import Shape
from .shapes import unlazy_shape
from .stepping import step_shape


OverrideDumpFormat: ta.TypeAlias = ta.Literal['overrides', 'json']


##


def _is_bare_str(v: str, shape: Shape) -> bool:
    """Whether a string, left bare, would be taken for something other than itself by its shape."""

    if optional := isinstance(shape := unlazy_shape(shape), OptionalShape):
        shape = unlazy_shape(shape.inner)
    if isinstance(shape, ScalarShape) and shape.ty is str:
        return not (optional and v == 'null')
    return isinstance(guess_scalar(v), str)


def _render_str(v: str, shape: Shape) -> str:
    if (
            not v or
            v != v.strip() or
            not v.isprintable() or
            v[0] in QUOTE_CHARS or
            v[0] in '{[' or
            v.startswith(FILE_PREFIX) or
            not _is_bare_str(v, shape)
    ):
        return json.dumps(v)
    return v


def _render_scalar(v: ta.Any, shape: Shape) -> str:
    if v is None:
        return 'null'
    elif isinstance(v, bool):
        return 'true' if v else 'false'
    elif isinstance(v, str):
        return _render_str(v, shape)
    elif isinstance(v, float) and not math.isfinite(v):
        return 'NaN' if math.isnan(v) else ('Infinity' if v > 0 else '-Infinity')
    elif isinstance(v, (int, float)):
        return repr(v)
    else:
        return json.dumps(v)


def dump_overrides(tree: ta.Any, shape: Shape | None = None) -> ta.Iterator[str]:
    def rec(v: ta.Any, path: OverridePath, vs: Shape) -> ta.Iterator[str]:
        items: ta.Iterable[tuple[PathSegment, ta.Any, ta.Any]]
        if isinstance(v, dict) and v:
            items = [(KeySegment(str(k)), k, e) for k, e in v.items()]
        elif isinstance(v, list) and v:
            items = [(IndexSegment(i), i, e) for i, e in enumerate(v)]
        else:
            yield f'{render_path(path)}={_render_scalar(v, vs) if not isinstance(v, (dict, list)) else json.dumps(v)}'
            return

        for seg, k, e in items:
            es: Shape
            try:
                es = step_shape(vs, k, node=v, path=path).shape
            except OverridePathError:
                # A tree at odds with its shape is still dumped, just as if it had none.
                es = ANY_SHAPE
            yield from rec(e, (*path, seg), es)

    return rec(tree, (), shape if shape is not None else ANY_SHAPE)


def dump_tree(
        tree: ta.Any,
        fmt: OverrideDumpFormat = 'overrides',
        *,
        shape: Shape | None = None,
) -> str:
    if fmt == 'overrides':
        return '\n'.join(dump_overrides(tree, shape))
    elif fmt == 'json':
        return json.dumps(tree, indent=2)
    else:
        raise ValueError(fmt)
