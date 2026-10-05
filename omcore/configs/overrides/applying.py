"""
The engine: applies ops, in order, to a plain tree of dicts, lists and scalars. It needs no shape to do so - the tree
itself says what is a map and what is a list - but when given one it walks it in step with the tree, using it to type
values and to reject keys the shape does not have.
"""
import collections.abc
import itertools
import os.path
import typing as ta

from ... import lang
from ..formats import DEFAULT_CONFIG_FILE_LOADER
from ..formats import ObjConfigData
from .errors import OverrideFileError
from .errors import OverrideJqError
from .errors import OverrideOpError
from .errors import OverridePathError
from .literals import RawList
from .literals import RawMap
from .literals import RawNode
from .literals import parse_raw_value
from .ops import ConstOpValue
from .ops import FileOpValue
from .ops import JqOp
from .ops import MergeOp
from .ops import OpValue
from .ops import OverrideOp
from .ops import RawOpValue
from .ops import RemoveOp
from .ops import SetOp
from .parsing import parse_override
from .paths import AppendSegment
from .paths import IndexSegment
from .paths import KeySegment
from .paths import OverridePath
from .paths import PathSegment
from .paths import SelectSegment
from .paths import describe_path
from .paths import render_segment
from .paths import try_parse_int_key
from .resolving import ValueResolver
from .resolving import scalar_matches
from .shapes import ANY_SHAPE
from .shapes import Shape
from .shapes import get_container_type
from .stepping import step_shape


with lang.auto_proxy_import(globals()):
    from ...specs import jq


##


def own_tree(v: ta.Any) -> ta.Any:
    """Deep-copies a tree into plain, unaliased dicts and lists."""

    if isinstance(v, collections.abc.Mapping):
        return {k: own_tree(e) for k, e in v.items()}
    elif isinstance(v, (str, bytes, bytearray)):
        return v
    elif isinstance(v, collections.abc.Sequence):
        return [own_tree(e) for e in v]
    else:
        return v


def load_override_file(path: str) -> ta.Any:
    d = DEFAULT_CONFIG_FILE_LOADER.load_file(os.path.expanduser(path))
    return d.obj if isinstance(d, ObjConfigData) else d.as_map()


##


def _describe_node(v: ta.Any) -> str:
    if isinstance(v, (RawMap, collections.abc.Mapping)):
        return 'a map'
    elif isinstance(v, (RawList, list, tuple)):
        return 'a list'
    elif v is None:
        return 'null'
    else:
        return 'a scalar'


def _get_map_items(v: ta.Any) -> ta.Iterable[tuple[str, ta.Any]] | None:
    if isinstance(v, RawMap):
        return v.items
    elif isinstance(v, collections.abc.Mapping):
        return v.items()
    else:
        return None


def _get_list_items(v: ta.Any) -> ta.Iterable[ta.Any] | None:
    if isinstance(v, RawList):
        return v.items
    elif isinstance(v, (list, tuple)):
        return v
    else:
        return None


def _is_selected(e: ta.Any, seg: SelectSegment) -> bool:
    for k in seg.keys:
        if not isinstance(e, dict) or k not in e:
            return False
        e = e[k]
    return scalar_matches(e, seg.value)


class _Slot:
    """A place in the tree: a key of a map or an index of a list, which may or may not presently hold anything."""

    def __init__(
            self,
            container: dict | list,
            key: ta.Any,
            *,
            exists: bool,
            shape: Shape,
            path: OverridePath,
            exclusive: bool = False,
    ) -> None:
        super().__init__()

        self._container = container
        self._key = key

        self.exists = exists
        self.shape = shape
        self.path = path
        self._exclusive = exclusive

    def get(self) -> ta.Any:
        return self._container[self._key]

    def set(self, v: ta.Any) -> None:
        if isinstance(c := self._container, dict):
            if self._exclusive:
                c.clear()
            c[self._key] = v
        elif self._key == len(c):
            c.append(v)
        else:
            c[self._key] = v
        self.exists = True


##


class OverrideApplier:
    def __init__(
            self,
            shape: Shape | None = None,
            *,
            guess_unknown: bool = False,
            file_loader: ta.Callable[[str], ta.Any] | None = None,
    ) -> None:
        super().__init__()

        self._shape = shape if shape is not None else ANY_SHAPE
        self._resolver = ValueResolver(guess_unknown=guess_unknown)
        self._file_loader = file_loader if file_loader is not None else load_override_file

    #

    def _select(self, node: list, seg: SelectSegment, path: OverridePath) -> int:
        if len(ms := [i for i, e in enumerate(node) if _is_selected(e, seg)]) != 1:
            raise OverridePathError(
                f'Expected exactly one element matching {render_segment(seg)!r} at {describe_path(path)}, '
                f'found {len(ms)}',
            )
        return ms[0]

    def _locate(self, node: dict | list, seg: PathSegment, path: OverridePath) -> tuple[str | int, bool]:
        if isinstance(node, dict):
            if not isinstance(seg, KeySegment):
                raise OverridePathError(
                    f'Cannot apply {render_segment(seg, first=True)!r} to a map at {describe_path(path)}',
                )
            return seg.name, seg.name in node

        idx: int | None
        if isinstance(seg, AppendSegment):
            return len(node), False
        elif isinstance(seg, SelectSegment):
            return self._select(node, seg, path), True
        elif isinstance(seg, IndexSegment):
            idx = seg.index
        elif isinstance(seg, KeySegment):
            if (idx := try_parse_int_key(seg)) is None:
                raise OverridePathError(f'Cannot apply key {seg.name!r} to a list at {describe_path(path)}')
        else:
            raise TypeError(seg)

        if not (-len(node) <= idx < len(node)):
            raise OverridePathError(
                f'Index {idx} out of range at {describe_path(path)}: it has {len(node)} elements',
            )
        return idx % len(node), True

    def _enter(self, slot: _Slot, seg: PathSegment, *, create: bool = False) -> dict | list:
        """Gets the container at a slot - creating it if permitted and necessary - to be navigated by a segment."""

        if (node := slot.get() if slot.exists else None) is None:
            if not create:
                raise OverridePathError(f'Nothing at {describe_path(slot.path)}')
            ct = get_container_type(slot.shape) or (dict if isinstance(seg, KeySegment) else list)
            slot.set(node := ct())

        elif not isinstance(node, (dict, list)):
            raise OverridePathError(f'Cannot navigate into {_describe_node(node)} at {describe_path(slot.path)}')

        return node

    def _descend(self, slot: _Slot, seg: PathSegment, *, create: bool = False) -> _Slot:
        node = self._enter(slot, seg, create=create)
        key, exists = self._locate(node, seg, slot.path)
        step = step_shape(slot.shape, key, node=node, path=slot.path)
        return _Slot(
            node,
            key,
            exists=exists,
            shape=step.shape,
            path=(*slot.path, seg),
            exclusive=step.exclusive,
        )

    def _walk(self, slot: _Slot, path: OverridePath, *, create: bool = False) -> _Slot:
        for seg in path:
            slot = self._descend(slot, seg, create=create)
        return slot

    #

    def _load_value(self, value: OpValue) -> ta.Any:
        if isinstance(value, RawOpValue):
            return parse_raw_value(value.text)

        elif isinstance(value, FileOpValue):
            try:
                return self._file_loader(value.path)
            except Exception as e:  # noqa
                raise OverrideFileError(f'Cannot load file {value.path!r}: {e!r}') from e

        elif isinstance(value, ConstOpValue):
            return value.value

        else:
            raise TypeError(value)

    def _set(self, slot: _Slot, v: ta.Any) -> None:
        if isinstance(v, RawNode):
            v = self._resolver.resolve(v, slot.shape, slot.path)
        else:
            v = own_tree(v)
        slot.set(v)

    def _merge(self, slot: _Slot, v: ta.Any, *, nested: bool = False) -> None:
        cur = slot.get() if slot.exists else None

        if isinstance(cur, dict) and (items := _get_map_items(v)) is not None:
            for k, cv in items:
                self._merge(self._descend(slot, KeySegment(k, quoted=True)), cv, nested=True)

        elif isinstance(cur, list) and not nested and (elems := _get_list_items(v)) is not None:
            for e in elems:
                self._set(self._descend(slot, AppendSegment()), e)

        elif cur is None or nested:
            self._set(slot, v)

        else:
            raise OverrideOpError(
                f'Cannot merge {_describe_node(v)} into {_describe_node(cur)} at {describe_path(slot.path)}',
            )

    def _remove(self, root: _Slot, path: OverridePath) -> None:
        if not path:
            raise OverrideOpError('Cannot remove the root')

        slot = self._walk(root, path[:-1])
        node = self._enter(slot, path[-1])
        key, exists = self._locate(node, path[-1], slot.path)

        # Something which is there can always be removed, whatever its shape has to say about it: it's how what one
        # alternative of a shape leaves behind gets cleaned up after switching to another.
        if exists:
            del node[key]  # type: ignore[arg-type]

        # Something which is not there is already at its default - so long as it was something to begin with.
        elif not step_shape(slot.shape, key, node=node, path=slot.path).declared:
            raise OverridePathError(f'Nothing at {describe_path(path)}')

    def _apply_jq(self, tree: ta.Any, op: JqOp) -> ta.Any:
        try:
            outs = list(itertools.islice(jq.compile_jq(op.filter).evaluate(tree), 2))
        except jq.JqError as e:
            raise OverrideJqError(f'jq filter {op.filter!r} failed: {e!r}') from e

        if len(outs) != 1:
            raise OverrideJqError(f'jq filter {op.filter!r} must produce exactly one output')

        # jq outputs may share structure, both with their input and within themselves.
        return own_tree(outs[0])

    #

    def apply(self, tree: ta.Any, ops: ta.Iterable[OverrideOp | str]) -> ta.Any:
        """Returns a new tree, leaving the given one untouched."""

        holder = [own_tree(tree)]
        root = _Slot(holder, 0, exists=True, shape=self._shape, path=())

        for op in ops:
            if isinstance(op, str):
                op = parse_override(op)

            if isinstance(op, SetOp):
                self._set(self._walk(root, op.path, create=True), self._load_value(op.value))
            elif isinstance(op, MergeOp):
                self._merge(self._walk(root, op.path, create=True), self._load_value(op.value))
            elif isinstance(op, RemoveOp):
                self._remove(root, op.path)
            elif isinstance(op, JqOp):
                holder[0] = self._apply_jq(holder[0], op)
            else:
                raise TypeError(op)

        return holder[0]


def apply_overrides(
        tree: ta.Any,
        ops: ta.Iterable[OverrideOp | str],
        shape: Shape | None = None,
        **kwargs: ta.Any,
) -> ta.Any:
    return OverrideApplier(shape, **kwargs).apply(tree, ops)
