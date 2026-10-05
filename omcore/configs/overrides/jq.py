"""
Shape-aware application of jq filters.

jq reads any Mapping or Sequence as an object or array, and makes every one of its updates - all forms of assignment
and deletion - out of two operations on its values: setting and removing a single item of a single container. So the
tree is handed to jq as views which carry their shapes and paths along with them (and hand them down to whatever is read
out of them), and those two operations are overridden to conform whatever is written into a view to the shape it has
for it. Everything else a filter does in between - arithmetic, construction, function calls - is left to work on plain
values exactly as it would otherwise: it is only where they land that matters.

Only this module imports jq, and nothing imports this module until a jq filter is actually applied.
"""
import collections.abc
import itertools
import typing as ta

from ...specs import jq
from .conforming import conform_value
from .errors import OverrideJqError
from .errors import OverridePathError
from .paths import IndexSegment
from .paths import KeySegment
from .paths import OverridePath
from .paths import PathSegment
from .shapes import ANY_SHAPE
from .shapes import AnyShape
from .shapes import Shape
from .shapes import unlazy_shape
from .stepping import step_shape
from .trees import own_tree


##


def _segment(key: str | int) -> PathSegment:
    return KeySegment(key, quoted=True) if isinstance(key, str) else IndexSegment(key)


class _ShapedView:
    """A read-only view of a plain container of the tree, knowing its shape and where in the tree it is."""

    def __init__(self, node: ta.Any, shape: Shape, path: OverridePath) -> None:
        super().__init__()

        self._node = node
        self._shape = shape
        self._path = path

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._node!r})'

    @property
    def node(self) -> ta.Any:
        return self._node

    @property
    def shape(self) -> Shape:
        return self._shape

    @property
    def path(self) -> OverridePath:
        return self._path

    def _view_item(self, key: str | int) -> ta.Any:
        if not isinstance(item := self._node[key], (dict, list)):
            return item

        try:
            shape = step_shape(self._shape, key, node=self._node, path=self._path).shape
        except OverridePathError:
            # Reading something at odds with its shape is no offense.
            shape = ANY_SHAPE
        return _view(item, shape, (*self._path, _segment(key)))


class _ShapedMapping(_ShapedView, collections.abc.Mapping[str, ta.Any]):
    def __getitem__(self, key: str) -> ta.Any:
        return self._view_item(key)

    def __iter__(self) -> ta.Iterator[str]:
        return iter(self._node)

    def __len__(self) -> int:
        return len(self._node)


class _ShapedSequence(_ShapedView, collections.abc.Sequence[ta.Any]):
    def __getitem__(self, index: ta.Any) -> ta.Any:
        if isinstance(index, slice):
            return [self._view_item(i) for i in range(*index.indices(len(self._node)))]

        if not (-len(self._node) <= index < len(self._node)):
            raise IndexError(index)
        return self._view_item(index % len(self._node))

    def __len__(self) -> int:
        return len(self._node)


def _view(node: ta.Any, shape: Shape, path: OverridePath) -> ta.Any:
    if isinstance(node, dict):
        return _ShapedMapping(node, unlazy_shape(shape), path)
    elif isinstance(node, list):
        return _ShapedSequence(node, unlazy_shape(shape), path)
    else:
        return node


##


class ShapedJqValueOps(jq.JqValueOps):
    def with_item(self, container: ta.Any, key: str | int, item: ta.Any) -> ta.Any:
        if not isinstance(container, _ShapedView):
            return super().with_item(container, key, item)

        step = step_shape(container.shape, key, node=container.node, path=container.path)

        if isinstance(item, _ShapedView) and item.shape is unlazy_shape(step.shape):
            # Already of this very shape: it's either what the tree already held or was conformed as it was written.
            item = item.node
        else:
            item = conform_value(item, step.shape, (*container.path, _segment(key)))

        node: ta.Any
        if isinstance(key, str):
            node = {} if step.exclusive else dict(container.node)
            node[key] = item
        else:
            node = list(container.node)
            for i in range(len(node), key):
                # jq pads with nulls, which had then better be something the shape allows.
                node.append(conform_value(None, step.shape, (*container.path, IndexSegment(i))))
            node[key:key + 1] = [item]
        return _view(node, container.shape, container.path)

    def without_item(self, container: ta.Any, key: str | int) -> ta.Any:
        if not isinstance(container, _ShapedView):
            return super().without_item(container, key)

        node = type(container.node)(container.node)
        del node[key]
        return _view(node, container.shape, container.path)


##


def apply_jq_filter(tree: ta.Any, source: str, shape: Shape = ANY_SHAPE) -> ta.Any:
    """
    Applies a jq filter to a tree, returning the single new tree it must output - as plain dicts and lists sharing
    nothing with the given one.
    """

    shaped = not isinstance(shape := unlazy_shape(shape), AnyShape)

    try:
        program = jq.compile_jq(source, value_ops=ShapedJqValueOps() if shaped else None)
        outs = list(itertools.islice(program.evaluate(_view(tree, shape, ()) if shaped else tree), 2))
    except jq.JqError as e:
        raise OverrideJqError(f'jq filter {source!r} failed: {e!r}') from e

    if len(outs) != 1:
        raise OverrideJqError(f'jq filter {source!r} must produce exactly one output')
    [out] = outs

    if isinstance(out, _ShapedView) and not out.path and out.shape is shape:
        # Still the root, however many times over: everything written into it was conformed as it was written.
        return own_tree(out.node)

    # Otherwise the root was put together some other way (`. * {...}`, `{...}`), and all of it is yet to be conformed.
    return conform_value(out, shape)
