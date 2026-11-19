import ast
import dataclasses as dc
import typing as ta

from .frontend import Program
from .frontend import Scope
from .values import _MISSING
from .values import ObjectRef
from .values import Value


##


@dc.dataclass(frozen=True, slots=True)
class Environment:
    program: Program
    scope: Scope
    namespace: ObjectRef
    globals: ObjectRef
    parent: Environment | None = None
    class_cell: ObjectRef | None = None
    first_arg_name: str | None = None


@dc.dataclass(frozen=True, slots=True)
class FunctionData:
    node: ast.FunctionDef | ast.Lambda
    environment: Environment
    defaults: tuple[Value, ...]
    kwdefaults: ta.Mapping[str, Value]
    annotations: ObjectRef | None = None
    module: Value = None


@dc.dataclass(frozen=True, slots=True)
class ClassData:
    name: str
    namespace: ObjectRef
    bases: tuple[ObjectRef, ...]
    mro: tuple[ObjectRef, ...] = ()
    bases_value: ObjectRef | None = None
    mro_value: ObjectRef | None = None


@dc.dataclass(frozen=True, slots=True)
class InstanceData:
    cls: ObjectRef
    namespace: ObjectRef


@dc.dataclass(frozen=True, slots=True)
class BoundMethodData:
    function: Value
    receiver: Value


@dc.dataclass(frozen=True, slots=True)
class SuperData:
    start: ObjectRef
    receiver: Value
    owner: ObjectRef | None


@dc.dataclass(frozen=True, slots=True)
class PropertyData:
    getter: Value = None
    setter: Value = None
    deleter: Value = None
    doc: Value = None
    doc_explicit: bool = False


@dc.dataclass(frozen=True, slots=True)
class BuiltinData:
    name: str
    receiver: Value = _MISSING


@dc.dataclass(frozen=True, slots=True)
class RangeData:
    start: int
    stop: int
    step: int


@dc.dataclass(frozen=True, slots=True)
class IteratorData:
    target: Value
    exhausted: bool = False
    index: int = 0
    keys: tuple[Value, ...] | None = None
    size: int | None = None


@dc.dataclass(frozen=True, slots=True)
class ExceptionData:
    cls: ObjectRef
    args: tuple[Value, ...]
    cause: Value = None
    context: Value = None
    suppress_context: bool = False
    traceback: tuple[tuple[str, int, str], ...] = ()
    namespace: ObjectRef | None = None


@dc.dataclass(frozen=True, slots=True)
class Task:
    kind: str
    env: Environment
    node: ast.AST | None = None
    data: ta.Any = None
    base: int = 0


@dc.dataclass(frozen=True, slots=True)
class Outcome:
    kind: str
    value: Value = None


@dc.dataclass()
class Execution:
    tasks: list[Task] = dc.field(default_factory=list)
    values: list[Value] = dc.field(default_factory=list)
    exceptions: list[ObjectRef] = dc.field(default_factory=list)
    generator: ObjectRef | None = None
    resume_mode: str = 'next'


@dc.dataclass()
class GeneratorData:
    execution: Execution
    started: bool = False
    running: bool = False
    closed: bool = False
    waiting: str = ''
    packet: Outcome = dc.field(default_factory=lambda: Outcome('send'))


@dc.dataclass()
class ThreadState:
    executions: list[Execution] = dc.field(default_factory=list)
    call_depth: int = 0
    done: bool = True
    result: Value = None
    error: ObjectRef | None = None


@dc.dataclass(frozen=True, slots=True)
class HeapObject:
    kind: str
    data: ta.Any


@dc.dataclass(frozen=True)
class Checkpoint:
    owner: object
    objects: ta.Mapping[int, HeapObject]
    thread: ThreadState
    modules: ta.Mapping[str, ObjectRef]


## Runtime interface and mutable implementation


@dc.dataclass(frozen=True, slots=True)
class CallArguments:
    function: Value
    positional: tuple[Value, ...] = ()
    keywords: tuple[tuple[str, Value], ...] = ()
    index: int = 0


@dc.dataclass(frozen=True, slots=True)
class LoopState:
    node: ast.For | ast.While
    iterator: Value = None


@dc.dataclass(frozen=True, slots=True)
class WithState:
    node: ast.With
    index: int
    exit: Value


@dc.dataclass(frozen=True, slots=True)
class CollectionState:
    iterator: Value
    result: ObjectRef
    limit: int | None = None


@dc.dataclass(frozen=True, slots=True)
class ComprehensionState:
    node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp
    result: Value
    level: int = 0
    iterator: Value = None
    condition: int = 0


@dc.dataclass(frozen=True, slots=True)
class SourceModule:
    source: str
    filename: str = '<guest module>'


@dc.dataclass(frozen=True, slots=True)
class AnnotationData:
    environment: Environment
    entries: tuple[tuple[str, ast.expr], ...]
    cached: ObjectRef | None = None


@dc.dataclass(frozen=True, slots=True)
class AdapterData:
    kind: str
    iterators: tuple[Value, ...]
    function: Value = None
    index: int = 0
    strict: bool = False
    extra: Value = None
    exhausted: bool = False


@dc.dataclass(frozen=True, slots=True)
class ReductionState:
    name: str
    iterator: Value
    value: Value
    value_key: Value
    key: Value
    default: Value
    compensation: float | None = None


@dc.dataclass(frozen=True, slots=True)
class SortState:
    source: ObjectRef
    decorated: ObjectRef
    output: ObjectRef
    key: Value
    reverse: bool
    index: int = 0
