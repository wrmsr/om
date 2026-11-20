import copy
import typing as ta

from .state import Checkpoint
from .state import GeneratorData
from .state import HeapObject
from .state import KeyOrder
from .state import ThreadState
from .values import BoundaryError
from .values import InterpreterError
from .values import ObjectRef
from .values import Value


##


class Runtime:
    """
    Nominal storage interface. No virtual-subclass registry is needed.

    read() lends READ-ONLY state, including nested payloads. All heap changes must use the mutation methods.
    Dict, namespace, set, and frozenset records can carry key positions in insertion order. Replacing values preserves
    positions, and inserting a key after deletion assigns a new position. With positions, iterators can follow new
    entries after same-size edits. Checkpoints preserve the positions.
    edit_thread()/edit_generator() are explicit write barriers: they lend exclusive mutable execution records for one
    machine step. A recording or persistent implementation can snapshot/COW at those barriers; DictRuntime does not.
    Checkpoints are legal only between complete steps, never from a capability callback.
    """

    def allocate(self, kind: str, data: ta.Any) -> ObjectRef:
        raise NotImplementedError

    def read(self, ref: ObjectRef) -> HeapObject:
        raise NotImplementedError

    def replace(self, ref: ObjectRef, data: ta.Any) -> None:
        raise NotImplementedError

    def write(
            self,
            ref: ObjectRef,
            key: ta.Any,
            value: ta.Any,
    ) -> None:
        raise NotImplementedError

    def delete(self, ref: ObjectRef, key: ta.Any) -> None:
        raise NotImplementedError

    def append(self, ref: ObjectRef, value: Value) -> None:
        raise NotImplementedError

    def edit_thread(self) -> ThreadState:
        raise NotImplementedError

    def read_thread(self) -> ThreadState:
        raise NotImplementedError

    def edit_generator(self, ref: ObjectRef) -> GeneratorData:
        raise NotImplementedError

    def modules(self) -> ta.Mapping[str, ObjectRef]:
        raise NotImplementedError

    def set_module(self, name: str, ref: ObjectRef | None) -> None:
        raise NotImplementedError

    def checkpoint(self, memo: dict[int, object]) -> Checkpoint:
        raise NotImplementedError

    def restore(self, checkpoint: Checkpoint, memo: dict[int, object]) -> None:
        raise NotImplementedError


class DictRuntime(Runtime):
    def __init__(self) -> None:
        super().__init__()

        self._owner = object()
        self._next = 0
        self._objects: dict[int, HeapObject] = {}
        self._thread = ThreadState()
        self._modules: dict[str, ObjectRef] = {}

    def allocate(self, kind: str, data: ta.Any) -> ObjectRef:
        self._next += 1
        ref = ObjectRef(self._owner, self._next)
        order = None
        if kind in ('dict', 'namespace', 'set', 'frozenset'):
            order = KeyOrder({key: i for i, key in enumerate(data)}, len(data))
        self._objects[ref.serial] = HeapObject(kind, data, order)
        return ref

    def read(self, ref: ObjectRef) -> HeapObject:
        if type(ref) is not ObjectRef or ref.owner is not self._owner or ref.serial not in self._objects:
            raise BoundaryError('foreign or stale object reference')
        return self._objects[ref.serial]

    def replace(self, ref: ObjectRef, data: ta.Any) -> None:
        obj = self.read(ref)
        order = obj.key_order
        if order is not None:
            positions = {key: pos for key, pos in order.positions.items() if key in data}
            order = KeyOrder(positions, order.next_position)
            for key in data:
                if key not in positions:
                    positions[key] = order.next_position
                    order.next_position += 1
        self._objects[ref.serial] = HeapObject(obj.kind, data, order)

    def write(
            self,
            ref: ObjectRef,
            key: ta.Any,
            value: ta.Any,
    ) -> None:
        obj = DictRuntime.read(self, ref)
        obj.data[key] = value
        order = obj.key_order
        if order is not None and key not in order.positions:
            order.positions[key] = order.next_position
            order.next_position += 1

    def delete(self, ref: ObjectRef, key: ta.Any) -> None:
        obj = DictRuntime.read(self, ref)
        del obj.data[key]
        if (order := obj.key_order) is not None:
            del order.positions[key]

    def append(self, ref: ObjectRef, value: Value) -> None:
        DictRuntime.read(self, ref).data.append(value)

    def edit_thread(self) -> ThreadState:
        return self._thread

    def read_thread(self) -> ThreadState:
        return self._thread

    def edit_generator(self, ref: ObjectRef) -> GeneratorData:
        obj = DictRuntime.read(self, ref)
        if obj.kind != 'generator':
            raise InterpreterError('not a generator record')
        return obj.data

    def modules(self) -> ta.Mapping[str, ObjectRef]:
        return self._modules

    def set_module(self, name: str, ref: ObjectRef | None) -> None:
        if ref is None:
            self._modules.pop(name, None)
        else:
            self._modules[name] = ref

    def checkpoint(self, memo: dict[int, object]) -> Checkpoint:
        (objects, thread, modules) = copy.deepcopy(
            (self._objects, self._thread, self._modules),
            memo,
        )
        return Checkpoint(self._owner, objects, thread, modules)

    def restore(self, checkpoint: Checkpoint, memo: dict[int, object]) -> None:
        if checkpoint.owner is not self._owner:
            raise BoundaryError('checkpoint belongs to another runtime')
        (self._objects, self._thread, self._modules) = ta.cast(
            'tuple[dict[int, HeapObject], ThreadState, dict[str, ObjectRef]]',
            copy.deepcopy((checkpoint.objects, checkpoint.thread, checkpoint.modules), memo),
        )
        # Never rewind serial allocation: a host-held reference from a discarded future must stay stale.
