import typing as ta

from ... import dataclasses as dc
from .errors import JqCycleError
from .errors import JqRuntimeError
from .errors import JqStructureError
from .events import BeginArray
from .events import BeginObject
from .events import EndArray
from .events import EndObject
from .events import ObjectKey
from .events import Scalar
from .events import StructuralEvent
from .values import JqPath
from .values import JqValueOps


##


@dc.dataclass(frozen=True)
class _Visit:
    value: ta.Any


@dc.dataclass(frozen=True)
class _ArrayFrame:
    value_id: int
    iterator: ta.Iterator[ta.Any]


@dc.dataclass(frozen=True)
class _ObjectFrame:
    value_id: int
    iterator: ta.Iterator[tuple[ta.Any, ta.Any]]


_WalkFrame: ta.TypeAlias = _Visit | _ArrayFrame | _ObjectFrame


def walk_structural_events(
        value: ta.Any,
        *,
        value_ops: JqValueOps | None = None,
) -> ta.Iterator[StructuralEvent]:
    ops = value_ops if value_ops is not None else JqValueOps()
    stack: list[_WalkFrame] = [_Visit(value)]
    active: set[int] = set()

    while stack:
        frame = stack.pop()

        if isinstance(frame, _Visit):
            current = frame.value
            current_type = ops.type_name(current)
            if current_type in ('null', 'boolean', 'number', 'string'):
                yield Scalar(current)
                continue

            current_id = id(current)
            if current_id in active:
                raise JqCycleError('cyclic jq value')
            active.add(current_id)

            if current_type == 'array':
                yield BeginArray()
                stack.append(_ArrayFrame(current_id, iter(current)))
            else:
                yield BeginObject()
                stack.append(_ObjectFrame(current_id, iter(current.items())))

        elif isinstance(frame, _ArrayFrame):
            try:
                child = next(frame.iterator)
            except StopIteration:
                active.remove(frame.value_id)
                yield EndArray()
            else:
                stack.append(frame)
                stack.append(_Visit(child))

        elif isinstance(frame, _ObjectFrame):
            while True:
                try:
                    key, child = next(frame.iterator)
                except StopIteration:
                    active.remove(frame.value_id)
                    yield EndObject()
                    break
                if (adapted := ops.adapt_object_key(key)) is not None:
                    yield ObjectKey(adapted)
                    stack.append(frame)
                    stack.append(_Visit(child))
                    break

        else:
            raise TypeError(frame)


##


@dc.dataclass()
class _StreamFrame:
    kind: ta.Literal['array', 'object']
    path: JqPath
    next_index: int = 0
    pending_key: str | None = None
    child_count: int = 0
    last_child_path: JqPath | None = None


def _next_child_path(stack: list[_StreamFrame]) -> JqPath:
    if not stack:
        return ()
    parent = stack[-1]
    if parent.kind == 'array':
        return (*parent.path, parent.next_index)
    if parent.pending_key is None:
        raise JqStructureError('object value has no preceding key')
    return (*parent.path, parent.pending_key)


def _complete_child(stack: list[_StreamFrame], path: JqPath) -> None:
    if not stack:
        return
    parent = stack[-1]
    parent.child_count += 1
    parent.last_child_path = path
    if parent.kind == 'array':
        parent.next_index += 1
    else:
        parent.pending_key = None


def encode_jq_stream(events: ta.Iterable[StructuralEvent]) -> ta.Iterator[list[ta.Any]]:
    stack: list[_StreamFrame] = []

    for event in events:
        if isinstance(event, ObjectKey):
            if not stack or stack[-1].kind != 'object':
                raise JqStructureError('object key outside an object')
            frame = stack[-1]
            if frame.pending_key is not None:
                raise JqStructureError('object key has no preceding value')
            if not isinstance(event.key, str):
                raise JqStructureError('object key is not a string')
            frame.pending_key = event.key
            continue

        if isinstance(event, Scalar):
            try:
                value_type = JqValueOps().type_name(event.value)
            except JqRuntimeError as exc:
                raise JqStructureError('structural scalar contains an unsupported value') from exc
            if value_type not in ('null', 'boolean', 'number', 'string'):
                raise JqStructureError('structural scalar contains a composite value')
            path = _next_child_path(stack)
            yield [list(path), event.value]
            _complete_child(stack, path)
            continue

        if isinstance(event, BeginArray):
            stack.append(_StreamFrame('array', _next_child_path(stack)))
            continue

        if isinstance(event, BeginObject):
            stack.append(_StreamFrame('object', _next_child_path(stack)))
            continue

        if isinstance(event, (EndArray, EndObject)):
            if not stack:
                raise JqStructureError('container end outside a container')
            frame = stack[-1]
            expected = 'array' if isinstance(event, EndArray) else 'object'
            if frame.kind != expected:
                raise JqStructureError(f'ended {expected} while in {frame.kind}')
            if frame.kind == 'object' and frame.pending_key is not None:
                raise JqStructureError('dangling object key at object end')

            stack.pop()
            if frame.child_count:
                if frame.last_child_path is None:
                    raise JqStructureError('container child state is inconsistent')
                yield [list(frame.last_child_path)]
            else:
                yield [list(frame.path), [] if frame.kind == 'array' else {}]
            _complete_child(stack, frame.path)
            continue

        raise JqStructureError(f'unknown structural event: {event!r}')

    if stack:
        raise JqStructureError('incomplete structural event stream')


def tostream(value: ta.Any, *, value_ops: JqValueOps | None = None) -> ta.Iterator[list[ta.Any]]:
    yield from encode_jq_stream(walk_structural_events(value, value_ops=value_ops))
