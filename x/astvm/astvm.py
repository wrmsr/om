"""
An experimental, closed-object-space, synchronous Python AST interpreter.

There is no guest bytecode, native guest function, native guest generator, or generic host-object fallback. This is NOT
an audited security boundary. In particular, hard memory/time containment and protection of the host parser require an
outer process sandbox. Trusted capabilities are authority grants, not automatically safe functions.

Only the host embedding API can access this module's implementation objects. Instances are single-owner and
non-reentrant. Checkpoints are in-memory and interpreter-local; external effects and cumulative resource accounting are
deliberately not rolled back.

TODO:
 - break apart into modules
 - mypyc
 - replace isinstance chains with precomputed type dict lookup - most ast node types are effectively final
 - replace horrible if str eq chains with dicts
 - ultimately -> omdev.astvm
"""
import ast
import copy
import dataclasses as dc
import operator
import re
import symtable
import sys
import typing as ta


##


type Value = ta.Union[
   None,
   bool,
   int,
   float,
   complex,
   str,
   bytes,
   ObjectRef,
   _Singleton,
]


## Values and host-visible failures


@dc.dataclass(frozen=True, slots=True)
class _Singleton:
    name: str

    def __deepcopy__(self, memo: dict[int, object]) -> '_Singleton':
        return self


_MISSING = _Singleton('missing')
_ELLIPSIS = _Singleton('Ellipsis')
_NOT_IMPLEMENTED = _Singleton('NotImplemented')

_SCALARS = (
    type(None),
    bool,
    int,
    float,
    complex,
    str,
    bytes,
)

_NUMBERS = (
    bool,
    int,
    float,
    complex,
)


@dc.dataclass(frozen=True, slots=True)
class ObjectRef:
    owner: object
    serial: int

    def __deepcopy__(self, memo: dict[int, object]) -> 'ObjectRef':
        return self


class InterpreterError(Exception):
    pass


class UnsupportedSyntaxError(InterpreterError):
    pass


class BoundaryError(InterpreterError):
    pass


class CapabilityError(InterpreterError):
    pass


class ResourceLimitError(InterpreterError):
    pass


class GuestError(InterpreterError):
    def __init__(
            self,
            name: str,
            message: str,
            exception: ObjectRef,
    ) -> None:
        super().__init__(f'{name}: {message}')

        self.name = name
        self.message = message
        self.exception = exception


class _GuestRaise(Exception):
    def __init__(self, value: ObjectRef) -> None:
        super().__init__()

        self.value = value


@dc.dataclass(frozen=True, slots=True)
class Limits:
    steps: int = 1_000_000
    objects: int = 100_000
    allocation: int = 10_000_000
    container: int = 100_000
    string: int = 1_000_000
    integer_bits: int = 16_384
    call_depth: int = 512
    source_chars: int = 200_000
    ast_nodes: int = 50_000
    ast_depth: int = 100
    conversion_depth: int = 100


class Budget:
    def __init__(self, limits: Limits | None = None) -> None:
        super().__init__()

        self.limits = limits if limits is not None else Limits()
        for field in dc.fields(self.limits):
            value = getattr(self.limits, field.name)
            if type(value) is not int or value <= 0:
                raise ValueError(f'invalid limit: {field.name}')

        self.steps = 0
        self.objects = 0
        self.allocation = 0
        self.exhausted = False

    def fail(self, reason: str) -> ta.NoReturn:
        self.exhausted = True
        raise ResourceLimitError(reason)

    def tick(self, amount: int = 1) -> None:
        self.steps += amount
        if self.exhausted or self.steps > self.limits.steps:
            self.fail('execution budget exhausted')

    def allocate(
            self,
            amount: int = 1,
            *,
            object_count: int = 0,
    ) -> None:
        self.allocation += amount
        self.objects += object_count
        if self.allocation > self.limits.allocation or self.objects > self.limits.objects:
            self.fail('allocation budget exhausted')

    def size(
            self,
            size: int,
            *,
            string: bool = False,
    ) -> None:
        limit = self.limits.string if string else self.limits.container
        if size > limit:
            self.fail('string size limit' if string else 'container size limit')

    def scalar(self, value: Value) -> Value:
        if type(value) is int and value.bit_length() > self.limits.integer_bits:
            self.fail('integer size limit')

        if type(value) in (str, bytes):
            self.size(len(value), string=True)

        return value


## Frontend. Programs and AST nodes are treated as immutable after preparation.


@dc.dataclass(frozen=True, slots=True)
class Scope:
    kind: str
    local_names: frozenset[str]
    global_names: frozenset[str]
    nonlocal_names: frozenset[str]
    generator: bool = False


@dc.dataclass(frozen=True)
class Program:
    tree: ast.Module | ast.Expression
    scopes: ta.Mapping[ast.AST, Scope]
    filename: str

    def __deepcopy__(self, memo: dict[int, object]) -> 'Program':
        return self


class _Bindings(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()

        self.names: set[str] = set()
        self.globals: set[str] = set()
        self.nonlocals: set[str] = set()
        self.generator = False

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_Global(self, node: ast.Global) -> None:
        self.globals.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocals.update(node.names)

    def visit_Yield(self, node: ast.Yield) -> None:
        self.generator = True
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self.generator = True
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name is not None:
            self.names.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split('.')[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.add(node.name)
        for item in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults]:
            if item is not None:
                self.visit(item)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for item in [*node.args.defaults, *node.args.kw_defaults]:
            if item is not None:
                self.visit(item)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.add(node.name)
        for item in [*node.decorator_list, *node.bases, *(k.value for k in node.keywords)]:
            self.visit(item)

    def _comprehension(self, node: ast.AST) -> None:
        # Assignment expressions bind outside comprehensions, but not across nested lambdas.
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)

        for gen in node.generators:
            self.visit(gen.iter)
            for condition in gen.ifs:
                self.visit(condition)

    visit_ListComp = _comprehension
    visit_SetComp = _comprehension
    visit_DictComp = _comprehension
    visit_GeneratorExp = _comprehension


class Frontend:
    _SUPPORTED = frozenset({
        'Module',
        'Expression',
        'Expr',
        'Constant',
        'Name',
        'Load',
        'Store',
        'Del',
        'List',
        'Tuple',
        'Set',
        'Dict',
        'Starred',
        'Slice',
        'Subscript',
        'Attribute',
        'BinOp',
        'UnaryOp',
        'BoolOp',
        'Compare',
        'IfExp',
        'NamedExpr',
        'Call',
        'keyword',
        'JoinedStr',
        'FormattedValue',
        'ListComp',
        'SetComp',
        'DictComp',
        'GeneratorExp',
        'comprehension',
        'Add',
        'Sub',
        'Mult',
        'Div',
        'FloorDiv',
        'Mod',
        'Pow',
        'LShift',
        'RShift',
        'BitOr',
        'BitXor',
        'BitAnd',
        'Invert',
        'Not',
        'UAdd',
        'USub',
        'And',
        'Or',
        'Eq',
        'NotEq',
        'Lt',
        'LtE',
        'Gt',
        'GtE',
        'Is',
        'IsNot',
        'In',
        'NotIn',
        'Assign',
        'AnnAssign',
        'AugAssign',
        'Delete',
        'Pass',
        'If',
        'For',
        'While',
        'Break',
        'Continue',
        'FunctionDef',
        'Lambda',
        'arguments',
        'arg',
        'Return',
        'Yield',
        'YieldFrom',
        'Global',
        'Nonlocal',
        'Raise',
        'Assert',
        'Try',
        'ExceptHandler',
        'With',
        'withitem',
        'ClassDef',
        'Import',
        'ImportFrom',
        'alias',
    })

    def __init__(self, budget: Budget) -> None:
        super().__init__()

        self._budget = budget

    def _scope(self, node: ast.AST, kind: str) -> Scope:
        scan = _Bindings()

        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for gen in node.generators:
                scan.visit(gen.target)

        elif isinstance(node, ast.Lambda):
            scan.visit(node.body)

        else:
            for child in node.body:
                scan.visit(child)

        if isinstance(node, (ast.FunctionDef, ast.Lambda)):
            args = node.args
            scan.names.update(a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs])
            if args.vararg is not None:
                scan.names.add(args.vararg.arg)
            if args.kwarg is not None:
                scan.names.add(args.kwarg.arg)

        return Scope(
            kind,
            frozenset(scan.names - scan.globals - scan.nonlocals),
            frozenset(scan.globals),
            frozenset(scan.nonlocals),
            scan.generator or isinstance(node, ast.GeneratorExp),
        )

    def _validate_context(self, tree: ast.AST) -> None:
        todo = [(tree, 'module', 0)]

        while todo:
            node, scope, loops = todo.pop()

            if isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)) and scope != 'function':
                raise SyntaxError(f'{type(node).__name__} outside function')

            if isinstance(node, (ast.Break, ast.Continue)) and not loops:
                raise SyntaxError(f'{type(node).__name__} outside loop')

            if isinstance(node, (ast.FunctionDef, ast.Lambda)):
                body = node.body if isinstance(node.body, list) else [node.body]
                todo.extend((n, 'function', 0) for n in body)
                for expr in [*node.args.defaults, *node.args.kw_defaults]:
                    if expr is not None:
                        todo.append((expr, scope, loops))
                if isinstance(node, ast.FunctionDef):
                    todo.extend((n, scope, loops) for n in node.decorator_list)
                continue

            if isinstance(node, ast.ClassDef):
                todo.extend((n, 'class', 0) for n in node.body)
                todo.extend((n, scope, loops) for n in [*node.bases, *node.decorator_list])
                continue

            if isinstance(node, (ast.While, ast.For)):
                todo.extend((n, scope, loops + 1) for n in node.body)
                todo.extend((n, scope, loops) for n in node.orelse)
                if isinstance(node, ast.While):
                    todo.append((node.test, scope, loops))
                else:
                    todo.append((node.iter, scope, loops))
                continue

            todo.extend((n, scope, loops) for n in ast.iter_child_nodes(node))

    def prepare(
            self,
            source: str,
            *,
            filename: str = '<guest>',
            expression: bool = False,
    ) -> Program:
        if type(source) is not str:
            raise TypeError('source must be an exact str')
        if len(source) > self._budget.limits.source_chars:
            self._budget.fail('source size limit')

        mode = 'eval' if expression else 'exec'
        tree = ast.parse(source, filename, mode)
        nodes: list[ast.AST] = []
        todo = [(tree, 0)]

        while todo:
            node, depth = todo.pop()
            nodes.append(node)

            if len(nodes) > self._budget.limits.ast_nodes or depth > self._budget.limits.ast_depth:
                self._budget.fail('AST size/depth limit')

            if type(node).__name__ not in self._SUPPORTED:
                raise UnsupportedSyntaxError(f'{type(node).__name__} at line {getattr(node, "lineno", 0)}')

            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.type_params:
                raise UnsupportedSyntaxError('type parameters')

            if isinstance(node, ast.ClassDef):
                if len(node.bases) > 1 or node.keywords:
                    raise UnsupportedSyntaxError('multiple inheritance and class keywords')

            if isinstance(node, ast.comprehension) and node.is_async:
                raise UnsupportedSyntaxError('asynchronous comprehension')

            if isinstance(node, ast.Import) and any('.' in a.name for a in node.names):
                raise UnsupportedSyntaxError('package imports')

            if isinstance(node, ast.ImportFrom) and (node.level or any(a.name == '*' for a in node.names)):
                raise UnsupportedSyntaxError('relative and star imports')

            if isinstance(node, ast.Constant):
                if node.value is not Ellipsis and type(node.value) not in _SCALARS:
                    raise UnsupportedSyntaxError('non-data constant')

                if node.value is not Ellipsis:
                    self._budget.scalar(node.value)

            todo.extend((n, depth + 1) for n in ast.iter_child_nodes(node))

        # The symbol-table frontend validates global/nonlocal declarations and comprehension restrictions. It does not
        # create executable code objects. Context checks above are still necessary.
        symtable.symtable(source, filename, mode)

        self._validate_context(tree)
        self._budget.allocate(len(nodes))

        scopes: dict[ast.AST, Scope] = {}

        if isinstance(tree, ast.Module):
            scopes[tree] = self._scope(tree, 'module')

        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.Lambda)):
                scopes[node] = self._scope(node, 'function')

            elif isinstance(node, ast.ClassDef):
                scopes[node] = self._scope(node, 'class')

            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                scopes[node] = self._scope(node, 'comprehension')

        return Program(tree, scopes, filename)


## Execution and object records. No record below contains a native guest callable or iterator.


@dc.dataclass(frozen=True, slots=True)
class Environment:
    program: Program
    scope: Scope
    namespace: ObjectRef
    globals: ObjectRef
    parent: ta.Optional['Environment'] = None


@dc.dataclass(frozen=True, slots=True)
class FunctionData:
    node: ast.FunctionDef | ast.Lambda
    environment: Environment
    defaults: tuple[Value, ...]
    kwdefaults: ta.Mapping[str, Value]
    annotations: ObjectRef | None = None


@dc.dataclass(frozen=True, slots=True)
class ClassData:
    name: str
    namespace: ObjectRef
    base: ObjectRef | None


@dc.dataclass(frozen=True, slots=True)
class InstanceData:
    cls: ObjectRef
    namespace: ObjectRef


@dc.dataclass(frozen=True, slots=True)
class BoundMethodData:
    function: Value
    receiver: Value


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


class Runtime:
    """
    Nominal storage interface. No virtual-subclass registry is needed.

    read() lends READ-ONLY state, including nested payloads. All heap changes must use the mutation methods.
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
        self._objects[ref.serial] = HeapObject(kind, data)
        return ref

    def read(self, ref: ObjectRef) -> HeapObject:
        if type(ref) is not ObjectRef or ref.owner is not self._owner or ref.serial not in self._objects:
            raise BoundaryError('foreign or stale object reference')
        return self._objects[ref.serial]

    def replace(self, ref: ObjectRef, data: ta.Any) -> None:
        obj = self.read(ref)
        self._objects[ref.serial] = HeapObject(obj.kind, data)

    def write(
            self,
            ref: ObjectRef,
            key: ta.Any,
            value: ta.Any,
    ) -> None:
        DictRuntime.read(self, ref).data[key] = value

    def delete(self, ref: ObjectRef, key: ta.Any) -> None:
        del DictRuntime.read(self, ref).data[key]

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
        (self._objects, self._thread, self._modules) = copy.deepcopy(  # noqa
            (checkpoint.objects, checkpoint.thread, checkpoint.modules),
            memo,
        )
        # Never rewind serial allocation: a host-held reference from a discarded future must stay stale.


## Explicit capability boundary


@dc.dataclass(frozen=True)
class HostCall:
    """
    Explicit host-call policy. Default arguments are copied ordinary data.

    guest_arguments=True passes opaque guest values to trusted adapter code. This is useful for __exit__(), whose
    exception/type arguments are not exportable data. Such callbacks must not reenter the interpreter. Return values
    always undergo the ordinary closed import check; this flag never admits native return objects.
    """

    function: ta.Callable[..., object]
    guest_arguments: bool = False


@dc.dataclass(frozen=True)
class HostObject:
    """An explicit method table, NOT an arbitrary Python object proxy. Callbacks are trusted."""

    methods: ta.Mapping[str, ta.Callable[..., object] | HostCall]
    name: str = 'capability object'


class CapabilityFailure(Exception):
    """A trusted callback may explicitly request a data-only guest exception."""

    def __init__(self, name: str, *args: object) -> None:
        super().__init__(*args)

        self.name = name


class Capabilities:
    def __init__(self) -> None:
        super().__init__()

        self._next = 0
        self._calls: dict[int, HostCall] = {}
        self._objects: dict[int, tuple[HostObject, dict[str, int]]] = {}

    def register(self, callback: ta.Callable[..., object] | HostCall) -> int:
        policy = callback if type(callback) is HostCall else HostCall(callback)
        if not callable(policy.function) or type(policy.guest_arguments) is not bool:
            raise TypeError('invalid capability call policy')

        self._next += 1
        self._calls[self._next] = policy
        return self._next

    def guest_arguments(self, identifier: int) -> bool:
        return self._calls[identifier].guest_arguments

    def register_object(self, obj: HostObject) -> tuple[str, dict[str, int]]:
        entry = self._objects.get(id(obj))
        if entry is None:
            methods = {}
            for name, callback in obj.methods.items():
                if type(name) is not str:
                    raise BoundaryError('method name must be an exact str')
                methods[name] = self.register(callback)
            entry = (obj, methods)
            self._objects[id(obj)] = entry
        return obj.name, dict(entry[1])

    def invoke(
            self,
            identifier: int,
            args: list[object],
            kwargs: dict[str, object],
    ) -> object:
        try:
            return self._calls[identifier].function(*args, **kwargs)
        except CapabilityFailure:
            raise
        except Exception as exc:
            # Unexpected host failures never become guest exceptions or guest traceback objects.
            raise CapabilityError('trusted capability failed') from exc


## Object space. Native primitives below only ever receive closed, exact data types.


@dc.dataclass(frozen=True, slots=True)
class _IdentityKey:
    serial: int


class ObjectSpace:
    _EXCEPTION_BASES = {
        'BaseException': 'object',
        'Exception': 'BaseException',
        'GeneratorExit': 'BaseException',
        'SystemExit': 'BaseException',
        'KeyboardInterrupt': 'BaseException',
        'ArithmeticError': 'Exception',
        'ZeroDivisionError': 'ArithmeticError',
        'OverflowError': 'ArithmeticError',
        'LookupError': 'Exception',
        'IndexError': 'LookupError',
        'KeyError': 'LookupError',
        'TypeError': 'Exception',
        'ValueError': 'Exception',
        'NameError': 'Exception',
        'UnboundLocalError': 'NameError',
        'AttributeError': 'Exception',
        'RuntimeError': 'Exception',
        'RecursionError': 'RuntimeError',
        'NotImplementedError': 'RuntimeError',
        'AssertionError': 'Exception',
        'StopIteration': 'Exception',
        'ImportError': 'Exception',
        'ModuleNotFoundError': 'ImportError',
        'OSError': 'Exception',
        'FileNotFoundError': 'OSError',
        'PermissionError': 'OSError',
        'EOFError': 'Exception',
    }

    _TYPE_NAMES = (
        'int',
        'bool',
        'float',
        'complex',
        'str',
        'bytes',
        'list',
        'tuple',
        'dict',
        'set',
        'frozenset',
        'range',
        'slice',
        'type',
        'NoneType',
        'function',
        'generator',
        'iterator',
        'module',
    )

    _FUNCTION_NAMES = (
        'len',
        'iter',
        'next',
        'repr',
        'ascii',
        'format',
        'abs',
        'round',
        'pow',
        'divmod',
        'min',
        'max',
        'sum',
        'all',
        'any',
        'enumerate',
        'zip',
        'reversed',
        'sorted',
        'map',
        'filter',
        'isinstance',
        'issubclass',
        'callable',
        'getattr',
        'setattr',
        'delattr',
        'hasattr',
        'globals',
        'locals',
        'vars',
        'id',
        'hash',
        'chr',
        'ord',
        'bin',
        'oct',
        'hex',
        'staticmethod',
        'classmethod',
    )

    _METHODS = {

        'list': frozenset({
            'append',
            'extend',
            'insert',
            'pop',
            'clear',
            'copy',
            'reverse',
            'remove',
            'count',
            'index',
        }),

        'dict': frozenset({
            'get',
            'keys',
            'values',
            'items',
            'pop',
            'popitem',
            'clear',
            'copy',
            'update',
            'setdefault',
        }),

        'namespace': frozenset({
            'get',
            'keys',
            'values',
            'items',
            'pop',
            'popitem',
            'clear',
            'copy',
            'update',
            'setdefault',
        }),

        'set': frozenset({
            'add',
            'discard',
            'remove',
            'pop',
            'clear',
            'copy',
            'update',
        }),

        'frozenset': frozenset({
            'copy',
        }),

        'tuple': frozenset({
            'count',
            'index',
        }),

        'str': frozenset({
            'upper',
            'lower',
            'casefold',
            'capitalize',
            'title',
            'swapcase',
            'strip',
            'lstrip',
            'rstrip',
            'split',
            'rsplit',
            'splitlines',
            'join',
            'replace',
            'startswith',
            'endswith',
            'find',
            'rfind',
            'index',
            'rindex',
            'count',
            'partition',
            'rpartition',
            'removeprefix',
            'removesuffix',
            'isalnum',
            'isalpha',
            'isascii',
            'isdecimal',
            'isdigit',
            'isidentifier',
            'islower',
            'isnumeric',
            'isprintable',
            'isspace',
            'istitle',
            'isupper',
        }),

        'bytes': frozenset({
            'hex',
            'upper',
            'lower',
            'strip',
            'lstrip',
            'rstrip',
            'startswith',
            'endswith',
            'find',
            'count',
        }),

        'generator': frozenset({
            'send',
            'throw',
            'close',
            '__iter__',
            '__next__',
        }),

        'iterator': frozenset({
            '__iter__',
            '__next__',
        }),

        'adapter': frozenset({
            '__iter__',
            '__next__',
        }),

        'range': frozenset({
            'count',
            'index',
        }),

    }

    _BINARY = {
        'Add': operator.add,
        'Sub': operator.sub,
        'Mult': operator.mul,
        'Div': operator.truediv,
        'FloorDiv': operator.floordiv,
        'Mod': operator.mod,
        'Pow': operator.pow,
        'LShift': operator.lshift,
        'RShift': operator.rshift,
        'BitOr': operator.or_,
        'BitXor': operator.xor,
        'BitAnd': operator.and_,
    }

    _ORDER = {
        'Lt': operator.lt,
        'LtE': operator.le,
        'Gt': operator.gt,
        'GtE': operator.ge,
    }

    def __init__(
            self,
            runtime: Runtime,
            budget: Budget,
            capabilities: Capabilities,
    ) -> None:
        super().__init__()

        self.runtime = runtime
        self.budget = budget
        self.capabilities = capabilities
        self._scalar_identities: dict[int, tuple[Value, int]] = {}
        self._host_objects = self.new('capability_cache', {})

        self.types: dict[str, ObjectRef] = {}
        self.builtins = self.new('namespace', {})
        self.types['object'] = self.new(
            'type',
            ClassData(
                'object',
                self.new(
                    'namespace',
                    {},
                ),
                None,
            ),
        )
        for name, base in self._EXCEPTION_BASES.items():
            self.types[name] = self.new(
                'type',
                ClassData(
                    name,
                    self.new(
                        'namespace',
                        {},
                    ),
                    self.types[base],
                ),
            )
        for name in self._TYPE_NAMES:
            base = self.types['int'] if name == 'bool' else self.types['object']
            self.types[name] = self.new(
                'type',
                ClassData(
                    name,
                    self.new(
                        'namespace',
                        {},
                    ),
                    base,
                ),
            )
        for name, value in self.types.items():
            self.runtime.write(self.builtins, name, value)

        for name in self._FUNCTION_NAMES:
            self.runtime.write(self.builtins, name, self.new('builtin', BuiltinData(name)))
        self.runtime.write(self.builtins, 'NotImplemented', _NOT_IMPLEMENTED)
        self.runtime.write(self.builtins, 'Ellipsis', _ELLIPSIS)

    def new(self, kind: str, data: ta.Any) -> ObjectRef:
        amount = len(data) if type(data) in (list, tuple, dict) else 1
        self.budget.allocate(amount + 1, object_count=1)
        return self.runtime.allocate(kind, data)

    def kind(self, value: Value) -> str:
        if type(value) is ObjectRef:
            return self.runtime.read(value).kind

        if type(value) in _SCALARS:
            return 'NoneType' if value is None else type(value).__name__

        if value is _ELLIPSIS or value is _NOT_IMPLEMENTED:
            return value.name

        raise BoundaryError('invalid value in guest object space')

    def data(self, value: ObjectRef) -> ta.Any:
        return self.runtime.read(value).data

    def error(self, name: str, *args: Value) -> ta.NoReturn:
        raise _GuestRaise(self.exception(name, tuple(args)))

    def exception(self, name: str, args: tuple[Value, ...]) -> ObjectRef:
        cls = self.types.get(name)

        if cls is None or not self.subclass(cls, self.types['BaseException']):
            raise BoundaryError(f'unknown guest exception type: {name}')

        return self.new('exception', ExceptionData(cls, args))

    def exception_name(self, ref: ObjectRef) -> str:
        return self.data(self.data(ref).cls).name

    def exception_matches(self, ref: ObjectRef, cls: Value) -> bool:
        if self.kind(cls) == 'tuple':
            return any(self.exception_matches(ref, c) for c in self.data(cls))

        if self.kind(cls) not in ('type', 'class') or not self.subclass(cls, self.types['BaseException']):
            self.error('TypeError', 'catching classes that do not inherit from BaseException is not allowed')

        return self.subclass(self.data(ref).cls, cls)

    def subclass(self, cls: ObjectRef, base: ObjectRef) -> bool:
        current: ObjectRef | None = cls

        while current is not None:
            self.budget.tick()

            if current == base:
                return True

            if self.kind(current) not in ('type', 'class'):
                return False

            current = self.data(current).base

        return False

    def type_of(self, value: Value) -> ObjectRef:
        kind = self.kind(value)

        if kind in ('instance', 'exception'):
            return self.data(value).cls

        if kind in ('class', 'type'):
            return self.types['type']

        if kind == 'namespace':
            return self.types['dict']

        if kind == 'adapter':
            return self.types['iterator']

        if kind in ('builtin', 'bound_method', 'capability'):
            return self.types['function']

        return self.types.get(kind, self.types['object'])

    def lookup_class(self, cls: ObjectRef, name: str) -> Value:
        while cls is not None:
            self.budget.tick()

            info = self.data(cls)

            namespace = self.data(info.namespace)
            if name in namespace:
                return namespace[name]

            cls = info.base

        return _MISSING

    def bind(
            self,
            value: Value,
            receiver: Value,
            cls: ObjectRef,
    ) -> Value:
        kind = self.kind(value)

        if kind == 'staticmethod':
            return self.data(value)

        if kind == 'classmethod':
            return self.new('bound_method', BoundMethodData(self.data(value), cls))

        if receiver is not _MISSING and kind == 'function':
            return self.new('bound_method', BoundMethodData(value, receiver))

        return value

    def special(self, value: Value, name: str) -> Value:
        kind = self.kind(value)

        if kind in ('instance', 'exception'):
            cls = self.data(value).cls
            found = self.lookup_class(cls, name)
            if found is not _MISSING:
                return self.bind(found, value, cls)

        if kind == 'host_object':
            methods = self.data(value)[1]
            if name in methods:
                return self.new('capability', methods[name])

        return _MISSING

    def get_attribute(self, value: Value, name: str) -> Value:
        if type(name) is not str:
            self.error('TypeError', 'attribute name must be a string')

        kind = self.kind(value)

        if name == '__class__':
            return self.type_of(value)

        if kind == 'instance':
            info = self.data(value)

            if name == '__dict__':
                return info.namespace

            own = self.data(info.namespace)
            if name in own:
                return own[name]

            found = self.lookup_class(info.cls, name)
            if found is not _MISSING:
                return self.bind(found, value, info.cls)

        elif kind in ('class', 'type'):
            info = self.data(value)

            if name == '__name__':
                return info.name

            if name == '__bases__':
                return self.new('tuple', () if info.base is None else (info.base,))

            # Do not return a writable class dictionary bypassing class attribute policy.
            found = self.lookup_class(value, name)
            if found is not _MISSING:
                return self.bind(found, _MISSING, value)

            if name == '__init__' and self.subclass(value, self.types['BaseException']):
                return self.new('builtin', BuiltinData('exception_init', value))

        elif kind == 'function':
            info = self.data(value)

            if name in ('__name__', '__qualname__'):
                return info.node.name if isinstance(info.node, ast.FunctionDef) else '<lambda>'

            if name == '__annotations__':
                return info.annotations

            if name == '__globals__':
                return info.environment.globals

            if name == '__defaults__':
                return self.new('tuple', info.defaults) if info.defaults else None

            if name == '__kwdefaults__':
                return self.make_dict(tuple(info.kwdefaults.items())) if info.kwdefaults else None

        elif kind == 'bound_method':
            if name == '__self__':
                return self.data(value).receiver

            if name == '__func__':
                return self.data(value).function

        elif kind == 'exception':
            info = self.data(value)

            if name == 'args':
                return self.new('tuple', info.args)

            if name == 'value' and self.subclass(info.cls, self.types['StopIteration']):
                return info.args[0] if info.args else None

            if name == '__cause__':
                return info.cause

            if name == '__context__':
                return info.context

            if name == '__suppress_context__':
                return info.suppress_context

            if name == '__traceback__':
                return self.traceback_value(value)

            if name == '__dict__':
                if info.namespace is None:
                    info = dc.replace(info, namespace=self.new('namespace', {}))
                    self.runtime.replace(value, info)
                return info.namespace

            if info.namespace is not None and name in self.data(info.namespace):
                return self.data(info.namespace)[name]

            found = self.lookup_class(info.cls, name)
            if found is not _MISSING:
                return self.bind(found, value, info.cls)

            if name == '__init__':
                return self.new('builtin', BuiltinData('exception_init_bound', value))

        elif kind == 'generator':
            info = self.data(value)

            if name == 'gi_running':
                return info.running

            if name == 'gi_suspended':
                return info.started and not info.closed and not info.running

            if name == 'gi_yieldfrom':
                for task in reversed(info.execution.tasks):
                    if task.kind == 'delegate_resume':
                        return task.data
                return None

        elif kind == 'range':
            if name in ('start', 'stop', 'step'):
                info = self.data(value)
                return {'start': info.start, 'stop': info.stop, 'step': info.step}[name]

        elif kind == 'slice':
            if name in ('start', 'stop', 'step'):
                return self.data(value)[{'start': 0, 'stop': 1, 'step': 2}[name]]

        elif kind == 'host_object':
            methods = self.data(value)[1]
            if name in methods:
                return self.new('capability', methods[name])

        elif kind == 'module':
            if name == '__dict__':
                return self.data(value)

            namespace = self.data(self.data(value))
            if name in namespace:
                return namespace[name]

        if name in self._METHODS.get(kind, ()):
            return self.new('builtin', BuiltinData(f'{kind}.{name}', value))

        self.error('AttributeError', f'{kind} has no supported attribute {name!r}')

    def set_attribute(
            self,
            value: Value,
            name: str,
            item: Value,
            *,
            delete: bool = False,
    ) -> None:
        if type(name) is not str:
            self.error('TypeError', 'attribute name must be a string')

        kind = self.kind(value)

        if name in (
                '__class__',
                '__dict__',
                '__bases__',
                '__mro__',
        ):
            self.error('AttributeError', 'structural attribute is read-only')

        if kind == 'instance':
            namespace = self.data(value).namespace

        elif kind == 'exception':
            info = self.data(value)

            fields = {
                'args': 'args',
                '__cause__': 'cause',
                '__context__': 'context',
                '__suppress_context__': 'suppress_context',
                '__traceback__': 'traceback',
            }

            if name in fields:
                if delete:
                    self.error('TypeError', 'exception structural fields cannot be deleted')

                if name == 'args':
                    if self.kind(item) not in ('tuple', 'list'):
                        self.error('TypeError', 'exception args currently require a list or tuple')
                    item = tuple(self.data(item))

                elif name in ('__cause__', '__context__'):
                    if item is not None and self.kind(item) != 'exception':
                        self.error('TypeError', 'exception chain must contain guest exceptions')

                elif name == '__suppress_context__':
                    if type(item) is not bool:
                        self.error('TypeError', '__suppress_context__ must be a bool')

                elif name == '__traceback__':
                    if item is not None:
                        self.error('TypeError', 'only clearing a guest traceback is supported')
                    item = ()

                changes = {fields[name]: item}
                if name == '__cause__':
                    changes['suppress_context'] = True

                self.runtime.replace(value, dc.replace(info, **changes))
                return

            if info.namespace is None:
                info = dc.replace(info, namespace=self.new('namespace', {}))
                self.runtime.replace(value, info)

            namespace = info.namespace

        elif kind == 'class':
            if name in (
                    '__del__',
                    '__getattribute__',
                    '__getattr__',
                    '__setattr__',
                    '__delattr__',
                    '__new__',
            ):
                self.error('TypeError', f'{name} is not supported')

            namespace = self.data(value).namespace

        elif kind == 'module':
            namespace = self.data(value)

        else:
            self.error('AttributeError', f'{kind} attributes are not writable')

        if delete:
            if name not in self.data(namespace):
                self.error('AttributeError', name)
            self.runtime.delete(namespace, name)

        else:
            self.runtime.write(namespace, name, item)

    def traceback_value(self, value: ObjectRef) -> Value:
        entries = self.data(value).traceback
        return self.import_value(entries) if entries else None

    def native(
            self,
            function: ta.Callable[..., object],
            *args: object,
            **kwargs: object,
    ) -> object:
        # Only internal call sites select this function. Inputs were reduced to exact primitive data.
        try:
            result = function(*args, **kwargs)

        except (ArithmeticError, ValueError, TypeError, LookupError) as exc:
            name = type(exc).__name__
            if name not in self.types:
                name = 'ValueError'

            self.error(name, str(exc))

        if type(result) in _SCALARS:
            self.budget.scalar(result)

        return result

    def key(self, value: Value, depth: int = 0) -> object:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.budget.fail('key nesting limit')

        kind = self.kind(value)

        if type(value) in _SCALARS:
            return value

        if kind == 'tuple':
            return tuple(self.key(v, depth + 1) for v in self.data(value))

        if kind == 'frozenset':
            return frozenset(self.key(v, depth + 1) for v in self.data(value).values())

        if kind in ('class', 'type', 'function', 'builtin', 'capability', 'generator'):
            return _IdentityKey(value.serial)

        if value is _ELLIPSIS or value is _NOT_IMPLEMENTED:
            return value

        self.error('TypeError', f'unhashable or unsupported key type: {kind}')

    def make_dict(self, pairs: ta.Iterable[tuple[Value, Value]]) -> ObjectRef:
        result = self.new('dict', {})
        for key, value in pairs:
            self.set_item(result, key, value)
        return result

    def length(self, value: Value) -> int:
        kind = self.kind(value)

        if type(value) in (str, bytes):
            return len(value)

        if kind in ('list', 'tuple', 'dict', 'namespace', 'set', 'frozenset'):
            return len(self.data(value))

        if kind == 'dict_view':
            return self.length(self.data(value)[0])

        if kind == 'range':
            info = self.data(value)
            if info.step > 0:
                return max(0, (info.stop - info.start + info.step - 1) // info.step)
            return max(0, (info.start - info.stop - info.step - 1) // -info.step)

        self.error('TypeError', f'{kind} has no intrinsic length')

    def truth(self, value: Value) -> bool:
        if type(value) in _SCALARS:
            return bool(value)

        kind = self.kind(value)

        if kind in ('list', 'tuple', 'dict', 'namespace', 'set', 'frozenset', 'range', 'dict_view'):
            return self.length(value) != 0

        if value is _NOT_IMPLEMENTED:
            self.error('TypeError', 'NotImplemented should not be used in a boolean context')

        return True

    def index(self, value: Value) -> int:
        if type(value) not in (int, bool):
            self.error('TypeError', 'an integer is required')
        return int(value)

    def slice_value(self, value: ObjectRef) -> slice:
        parts = self.data(value)
        return slice(*(None if v is None else self.index(v) for v in parts))

    def get_item(self, value: Value, key: Value) -> Value:
        kind = self.kind(value)

        if kind == 'dict':
            record = self.data(value).get(self.key(key), _MISSING)
            if record is _MISSING:
                self.error('KeyError', key)
            return record[1]

        if kind == 'namespace':
            if type(key) is not str:
                self.error('KeyError', key)

            data = self.data(value)
            if key not in data:
                self.error('KeyError', key)
            return data[key]

        if kind in ('list', 'tuple', 'str', 'bytes', 'range'):
            if kind == 'range':
                info = self.data(value)
                seq = range(info.start, info.stop, info.step)
            else:
                seq = self.data(value) if kind in ('list', 'tuple') else value

            if self.kind(key) == 'slice':
                result = self.native(operator.getitem, seq, self.slice_value(key))

                if kind == 'range':
                    return self.new('range', RangeData(result.start, result.stop, result.step))

                if kind in ('list', 'tuple'):
                    return self.new(kind, result)

                return result

            return self.native(operator.getitem, seq, self.index(key))

        self.error('TypeError', f'{kind} is not intrinsically subscriptable')

    def set_item(
            self,
            value: Value,
            key: Value,
            item: Value,
            *,
            delete: bool = False,
    ) -> None:
        kind = self.kind(value)

        if kind in ('dict', 'namespace', 'set'):
            if kind == 'namespace':
                if type(key) is not str:
                    self.error('TypeError', 'namespace keys must be strings')
                token, record = key, item

            else:
                token = self.key(key)
                record = key if kind == 'set' else (key, item)

            data = self.data(value)

            if delete:
                if token not in data:
                    self.error('KeyError', key)
                self.runtime.delete(value, token)

            else:
                if token not in data:
                    self.budget.size(len(data) + 1)
                    self.budget.allocate(1)
                elif kind == 'dict':
                    record = (data[token][0], item)

                self.runtime.write(value, token, record)

            return

        if kind == 'list':
            data = self.data(value)

            if self.kind(key) == 'slice':
                sl = self.slice_value(key)
                if sl.step == 0:
                    self.error('ValueError', 'slice step cannot be zero')

                if delete:
                    self.runtime.delete(value, sl)

                else:
                    if self.kind(item) not in ('list', 'tuple'):
                        raise InterpreterError('slice RHS must have been collected')

                    parts = list(self.data(item))
                    start, stop, step = sl.indices(len(data))
                    removed = len(range(start, stop, step))
                    if step != 1 and removed != len(parts):
                        self.error('ValueError', 'attempt to assign sequence of wrong size to extended slice')

                    self.budget.size(len(data) - removed + len(parts))
                    self.budget.allocate(len(parts))
                    self.runtime.write(value, sl, parts)

            else:
                index = self.index(key)
                if index < 0:
                    index += len(data)
                if not 0 <= index < len(data):
                    self.error('IndexError', 'list assignment index out of range')

                if delete:
                    self.runtime.delete(value, index)
                else:
                    self.runtime.write(value, index, item)

            return

        self.error('TypeError', f'{kind} does not support item mutation')

    def append(self, ref: ObjectRef, value: Value) -> None:
        self.budget.size(len(self.data(ref)) + 1)
        self.budget.allocate(1)
        self.runtime.append(ref, value)

    def iter_value(self, value: Value) -> Value:
        kind = self.kind(value)

        if kind in ('iterator', 'generator', 'adapter'):
            return value

        if kind == 'dict_view':
            target, _ = self.data(value)
            keys = tuple(k for k, _ in self.mapping_pairs(target))
            return self.new('iterator', IteratorData(value, keys=keys, size=len(keys)))

        if kind in ('list', 'tuple', 'str', 'bytes', 'range'):
            return self.new('iterator', IteratorData(value))

        if kind in ('dict', 'namespace', 'set', 'frozenset'):
            data = self.data(value)
            if kind == 'dict':
                keys = tuple(entry[0] for entry in data.values())
            elif kind == 'namespace':
                keys = tuple(data)
            else:
                keys = tuple(data.values())

            return self.new('iterator', IteratorData(value, keys=keys, size=len(data)))

        self.error('TypeError', f'{kind} is not iterable')

    def next_value(self, iterator: ObjectRef) -> Value:
        info = self.data(iterator)

        if info.exhausted:
            self.error('StopIteration')

        if info.size is not None and self.length(info.target) != info.size:
            self.error('RuntimeError', 'container changed size during iteration')

        if info.keys is not None:
            if info.index >= len(info.keys):
                self.runtime.replace(iterator, dc.replace(info, exhausted=True))
                self.error('StopIteration')

            value = info.keys[info.index]

            if self.kind(info.target) == 'dict_view':
                target, mode = self.data(info.target)
                if mode != 'keys':
                    item = self.get_item(target, value)
                    value = item if mode == 'values' else self.new('tuple', (value, item))

        else:
            if info.index >= self.length(info.target):
                self.runtime.replace(iterator, dc.replace(info, exhausted=True))
                self.error('StopIteration')

            value = self.get_item(info.target, info.index)

        self.runtime.replace(iterator, dc.replace(info, index=info.index + 1))
        return value

    def identity_number(self, value: Value) -> int:
        if type(value) is ObjectRef:
            self.runtime.read(value)
            return value.serial

        key = id(value)
        if key not in self._scalar_identities:
            self.budget.allocate(1, object_count=1)
            self._scalar_identities[key] = (value, -(len(self._scalar_identities) + 1))

        return self._scalar_identities[key][1]

    def identical(self, left: Value, right: Value) -> bool:
        if type(left) is ObjectRef or type(right) is ObjectRef:
            return type(left) is ObjectRef and type(right) is ObjectRef and left == right
        return left is right

    def equal(
            self,
            left: Value,
            right: Value,
            depth: int = 0,
    ) -> bool:
        self.budget.tick()

        if self.identical(left, right):
            return True

        if depth > self.budget.limits.conversion_depth:
            self.error('RecursionError', 'comparison nesting limit')

        if type(left) in _SCALARS and type(right) in _SCALARS:
            return left == right

        lk, rk = self.kind(left), self.kind(right)

        if lk == rk and lk in ('list', 'tuple'):
            a, b = self.data(left), self.data(right)
            return len(a) == len(b) and all(self.equal(x, y, depth + 1) for x, y in zip(a, b))

        if lk in ('dict', 'namespace') and rk in ('dict', 'namespace'):
            a, b = self.mapping_pairs(left), self.mapping_pairs(right)
            if len(a) != len(b):
                return False
            tokens = {self.key(k): v for k, v in b}
            return all(self.key(k) in tokens and self.equal(v, tokens[self.key(k)], depth + 1) for k, v in a)

        if lk in ('set', 'frozenset') and rk in ('set', 'frozenset'):
            return self.data(left).keys() == self.data(right).keys()

        if lk == rk == 'range':
            a, b = self.data(left), self.data(right)
            return range(a.start, a.stop, a.step) == range(b.start, b.stop, b.step)

        return False

    def compare(
            self,
            name: str,
            left: Value,
            right: Value,
            depth: int = 0,
    ) -> bool:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.error('RecursionError', 'comparison nesting limit')

        if name in ('Is', 'IsNot'):
            result = self.identical(left, right)
            return result if name == 'Is' else not result

        if name in ('Eq', 'NotEq'):
            result = self.equal(left, right)
            return result if name == 'Eq' else not result

        if type(left) in _SCALARS and type(right) in _SCALARS:
            return self.native(self._ORDER[name], left, right)

        if self.kind(left) == self.kind(right) and self.kind(left) in ('list', 'tuple'):
            a, b = self.data(left), self.data(right)
            for x, y in zip(a, b):
                if not self.equal(x, y):
                    return self.compare(name, x, y, depth + 1)

            return self._ORDER[name](len(a), len(b))

        self.error('TypeError', 'ordering is not supported between these values')

    def binary(
            self,
            name: str,
            left: Value,
            right: Value,
    ) -> Value:
        lk, rk = self.kind(left), self.kind(right)

        if (
                name == 'Add' and
                lk == rk and
                lk in ('list', 'tuple', 'str', 'bytes')
        ):
            self.budget.size(self.length(left) + self.length(right), string=lk in ('str', 'bytes'))
            if lk in ('list', 'tuple'):
                return self.new(lk, self.data(left) + self.data(right))
            self.budget.allocate(len(left) + len(right))
            return left + right

        if (
                name == 'Mult' and
                (
                        lk in ('list', 'tuple', 'str', 'bytes') or
                        rk in ('list', 'tuple', 'str', 'bytes')
                )
        ):
            seq, count = (left, right) if lk in ('list', 'tuple', 'str', 'bytes') else (right, left)
            count = max(0, self.index(count))
            kind = self.kind(seq)
            size = self.length(seq) * count
            self.budget.size(size, string=kind in ('str', 'bytes'))
            if kind in ('list', 'tuple'):
                return self.new(kind, self.data(seq) * count)
            self.budget.allocate(size)
            return seq * count

        if (
                lk in ('set', 'frozenset') and
                rk in ('set', 'frozenset') and
                name in ('BitOr', 'BitAnd', 'BitXor', 'Sub')
        ):
            a, b = self.data(left), self.data(right)
            keys = self._BINARY[name](a.keys(), b.keys())
            self.budget.size(len(keys))
            return self.new(lk, {k: a[k] if k in a else b[k] for k in keys})

        if (
                lk in ('dict', 'namespace') and
                rk in ('dict', 'namespace') and
                name == 'BitOr'
        ):
            return self.make_dict([*self.mapping_pairs(left), *self.mapping_pairs(right)])

        if (
                type(left) not in _NUMBERS or
                type(right) not in _NUMBERS
        ):
            self.error('TypeError', f'unsupported operands for {name}: {lk}, {rk}')

        if (
                name == 'Pow' and
                type(left) in (int, bool) and
                type(right) in (int, bool) and
                right >= 0
        ):
            estimate = max(1, abs(left).bit_length()) * right
            if abs(left) > 1 and estimate > self.budget.limits.integer_bits:
                self.budget.fail('power result size limit')

        if (
                name == 'LShift' and
                type(left) in (int, bool) and
                type(right) in (int, bool)
        ):
            if right >= 0 and left and left.bit_length() + right > self.budget.limits.integer_bits:
                self.budget.fail('shift result size limit')

        return self.native(self._BINARY[name], left, right)

    def mapping_pairs(self, value: Value) -> list[tuple[Value, Value]]:
        kind = self.kind(value)

        if kind == 'namespace':
            return list(self.data(value).items())

        if kind == 'dict':
            return list(self.data(value).values())

        self.error('TypeError', 'expected an intrinsic mapping')

    def representation(
            self,
            value: Value,
            *,
            string: bool = False,
            seen: set[int] | None = None,
    ) -> str:
        self.budget.tick()

        if type(value) in _SCALARS:
            return self.native(str if string else repr, value)

        if value in (_ELLIPSIS, _NOT_IMPLEMENTED):
            return value.name

        kind = self.kind(value)

        if seen is None:
            seen = set()
        if len(seen) > self.budget.limits.conversion_depth:
            self.budget.fail('representation nesting limit')

        if value.serial in seen:
            return {
                'list': '[...]',
                'dict': '{...}',
                'namespace': '{...}',
                'tuple': '(...)',
            }.get(kind, '...')

        seen.add(value.serial)

        try:
            if kind in ('list', 'tuple', 'set', 'frozenset'):
                values = self.data(value)

                if kind in ('set', 'frozenset'):
                    values = values.values()

                parts = []
                size = 0
                for part in values:
                    text = self.representation(part, seen=seen)
                    size += len(text) + 2
                    self.budget.size(size, string=True)
                    parts.append(text)

                text = ', '.join(parts)

                if kind == 'list':
                    return '[' + text + ']'

                if kind == 'tuple':
                    return '(' + text + (',' if len(parts) == 1 else '') + ')'

                if kind == 'set':
                    return '{' + text + '}' if parts else 'set()'

                return 'frozenset({' + text + '})' if parts else 'frozenset()'

            if kind in ('dict', 'namespace'):
                parts = []
                size = 0
                for key, item in self.mapping_pairs(value):
                    text = self.representation(key, seen=seen) + ': ' + self.representation(item, seen=seen)
                    size += len(text) + 2
                    self.budget.size(size, string=True)
                    parts.append(text)

                return '{' + ', '.join(parts) + '}'

            if kind in ('class', 'type'):
                return "<class '" + self.data(value).name + "'>"

            if kind == 'exception':
                info = self.data(value)

                if string:
                    if not info.args:
                        return ''

                    if len(info.args) == 1:
                        return self.representation(
                            info.args[0],
                            string=self.exception_name(value) != 'KeyError',
                            seen=seen,
                        )

                    return self.representation(self.new('tuple', info.args), seen=seen)

                parts = ', '.join(self.representation(v, seen=seen) for v in info.args)
                return self.exception_name(value) + '(' + parts + ')'

            if kind == 'range':
                info = self.data(value)
                args = f'{info.start}, {info.stop}' + (f', {info.step}' if info.step != 1 else '')
                return 'range(' + args + ')'

            if kind == 'instance':
                return '<' + self.data(self.data(value).cls).name + ' object>'

            return '<guest ' + kind + '>'

        finally:
            seen.remove(value.serial)

    def import_value(
            self,
            value: object,
            *,
            capabilities: bool = False,
            memo: dict[int, Value] | None = None,
            depth: int = 0,
    ) -> Value:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.budget.fail('boundary nesting limit')

        if type(value) in _SCALARS:
            self.budget.scalar(value)
            self.budget.allocate(len(value) if type(value) in (str, bytes) else 1)
            return value

        if value is Ellipsis:
            return _ELLIPSIS

        if value is NotImplemented:
            return _NOT_IMPLEMENTED

        if memo is None:
            memo = {}
        if id(value) in memo:
            return memo[id(value)]

        if capabilities and type(value) is HostObject:
            # Keep guest identity in the rollbackable heap, not the external capability registry.
            result = self.data(self._host_objects).get(id(value))

            if result is None:
                result = self.new('host_object', self.capabilities.register_object(value))
                self.runtime.write(self._host_objects, id(value), result)

            memo[id(value)] = result
            return result

        if type(value) not in (list, tuple, dict, set, frozenset):
            raise BoundaryError('only exact data types may cross the boundary; use an explicit capability')

        self.budget.size(len(value))

        kind = type(value).__name__
        result = self.new(kind, [] if kind in ('list', 'tuple') else {})

        memo[id(value)] = result

        if kind in ('list', 'tuple'):
            for item in value:
                imported = self.import_value(
                    item,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                self.runtime.append(result, imported)

            if kind == 'tuple':
                self.runtime.replace(result, tuple(self.data(result)))

        elif kind == 'dict':
            for key, item in value.items():
                imported_key = self.import_value(
                    key,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                imported = self.import_value(
                    item,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                self.set_item(result, imported_key, imported)

        else:
            for item in value:
                imported = self.import_value(
                    item,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                self.runtime.write(result, self.key(imported), imported)

        return result

    def export_value(
            self,
            value: Value,
            *,
            memo: dict[int, object] | None = None,
            depth: int = 0,
    ) -> object:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.budget.fail('boundary nesting limit')

        if type(value) in _SCALARS:
            return value

        if value is _ELLIPSIS:
            return Ellipsis

        if value is _NOT_IMPLEMENTED:
            return NotImplemented

        if memo is None:
            memo = {}
        if value.serial in memo:
            result = memo[value.serial]
            if result is _MISSING:
                raise BoundaryError('cyclic immutable export is not supported')
            return result

        kind = self.kind(value)

        if kind == 'list':
            result = []
            memo[value.serial] = result
            for item in self.data(value):
                result.append(self.export_value(item, memo=memo, depth=depth + 1))
            return result

        if kind in ('dict', 'namespace'):
            result = {}
            memo[value.serial] = result
            for key, item in self.mapping_pairs(value):
                result[self.export_value(key, memo=memo, depth=depth + 1)] = self.export_value(
                    item, memo=memo, depth=depth + 1,
                )
            return result

        if kind in ('tuple', 'set', 'frozenset'):
            memo[value.serial] = _MISSING
            items = self.data(value)
            if kind != 'tuple':
                items = items.values()
            parts = [self.export_value(item, memo=memo, depth=depth + 1) for item in items]
            result = {'tuple': tuple, 'set': set, 'frozenset': frozenset}[kind](parts)
            memo[value.serial] = result
            return result

        if kind == 'range':
            info = self.data(value)
            return range(info.start, info.stop, info.step)

        raise BoundaryError(f'{kind} is not exportable data; use the guest-value host API explicitly')


## Data-only AST continuations. Tags dispatch interpreter code, not a guest instruction stream.


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


class Machine:
    def __init__(
            self,
            runtime: Runtime,
            space: ObjectSpace,
            frontend: Frontend,
            programs: list[Program],
            modules: ta.Mapping[str, SourceModule | ta.Mapping[str, object]],
    ) -> None:
        super().__init__()

        self._runtime = runtime
        self._space = space
        self._budget = space.budget
        self._frontend = frontend
        self._programs = programs
        self._modules = modules
        self._thread: ThreadState | None = None
        self._task: Task | None = None

        # Method names come exclusively from this implementation class, never from guest input.
        self._handlers = {
            name.removeprefix('_task_'): method.__get__(self, type(self))
            for name, method in vars(type(self)).items()
            if name.startswith('_task_')
        }

    def _execution(self) -> Execution:
        return self._thread.executions[-1]

    def _push(self, value: Value) -> None:
        self._execution().values.append(value)

    def _pop(self) -> Value:
        return self._execution().values.pop()

    def _add(
            self,
            kind: str,
            env: Environment,
            node: ast.AST | None = None,
            data: ta.Any = None,
    ) -> None:
        self._execution().tasks.append(Task(
            kind,
            env,
            node,
            data,
            len(self._execution().values),
        ))

    def _suite(self, body: ta.Sequence[ast.stmt], env: Environment) -> None:
        for node in reversed(body):
            self._add('exec', env, node)

    def _evaluate(self, node: ast.expr, env: Environment) -> None:
        self._add('eval', env, node)

    def _invoke(
            self,
            env: Environment,
            function: Value,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value] | None = None,
    ) -> None:
        self._add('invoke', env, data=(function, args, dict(kwargs or {})))

    def _operation(
            self,
            name: str,
            env: Environment,
            *values: Value,
    ) -> None:
        self._add('operation', env, data=(name, values))

    def _many(self, nodes: ta.Sequence[ast.expr], env: Environment) -> None:
        self._add('many_next', env, data=(tuple(nodes), 0, ()))

    def _pull(
            self,
            env: Environment,
            iterator: Value,
            on_value: Task,
            on_stop: Task,
    ) -> None:
        self._add('next_guard', env, data=(on_value, on_stop))
        self._operation('next', env, iterator)

    def _collect(
            self,
            env: Environment,
            value: Value,
            limit: int | None = None,
    ) -> None:
        self._add('collect_start', env, data=limit)
        self._operation('iter', env, value)

    def _find_nonlocal(self, env: Environment, name: str) -> Environment | None:
        current = env.parent

        while current is not None:
            if current.scope.kind not in ('module', 'class'):
                if name in current.scope.global_names:
                    return None

                if name in current.scope.local_names:
                    return current

            current = current.parent

        return None

    def _read_name(self, env: Environment, name: str) -> Value:
        space = self._space
        scope = env.scope

        if name not in scope.global_names:
            local = space.data(env.namespace)
            if name in local:
                return local[name]

            if scope.kind in ('function', 'comprehension') and name in scope.local_names:
                space.error('UnboundLocalError', f"local variable '{name}' is not bound")

            if scope.kind != 'class' or name not in scope.local_names:
                parent = self._find_nonlocal(env, name)
                if parent is not None:
                    namespace = space.data(parent.namespace)
                    if name not in namespace:
                        space.error('NameError', f"free variable '{name}' is not bound")
                    return namespace[name]

        global_values = space.data(env.globals)
        if name in global_values:
            return global_values[name]

        builtin_values = space.data(space.builtins)
        if name in builtin_values:
            return builtin_values[name]

        space.error('NameError', f"name '{name}' is not defined")

    def _write_name(
            self,
            env: Environment,
            name: str,
            value: Value,
            *,
            delete: bool = False,
    ) -> None:
        space = self._space

        if name in env.scope.global_names:
            namespace = env.globals

        elif name in env.scope.nonlocal_names:
            parent = self._find_nonlocal(env, name)
            if parent is None:
                raise InterpreterError('unresolved nonlocal binding')
            namespace = parent.namespace

        else:
            namespace = env.namespace

        if delete:
            if name not in space.data(namespace):
                local_function = env.scope.kind == 'function' and namespace == env.namespace
                error = 'UnboundLocalError' if local_function else 'NameError'
                space.error(error, name)

            self._runtime.delete(namespace, name)

        else:
            self._runtime.write(namespace, name, value)

    def _active_exception(self) -> ObjectRef | None:
        for execution in reversed(self._thread.executions):
            if execution.exceptions:
                return execution.exceptions[-1]
        return None

    def _raise(self, value: ObjectRef) -> None:
        space = self._space
        info = space.data(value)

        active = self._active_exception()
        if active is not None and active != value and info.context is None:
            info = dc.replace(info, context=active)

        task = self._task
        if task is not None and task.node is not None:
            entry = (task.env.program.filename, getattr(task.node, 'lineno', 0), task.env.scope.kind)
            info = dc.replace(info, traceback=(*info.traceback, entry))

        self._runtime.replace(value, info)
        self._unwind(Outcome('raise', value))

    def _restore_exception_depth(self, depth: int) -> None:
        del self._execution().exceptions[depth:]

    def _finally(self, task: Task, outcome: Outcome) -> None:
        depth = len(self._execution().exceptions)

        if outcome.kind == 'raise':
            self._execution().exceptions.append(outcome.value)

        self._add('restore_outcome', task.env, data=(outcome, depth))
        self._suite(task.data, task.env)

    def _with_exit(self, task: Task, outcome: Outcome) -> None:
        depth = len(self._execution().exceptions)
        space = self._space

        self._add('restore_exception', task.env, data=depth)
        self._add('with_exit_result', task.env, data=outcome)

        if outcome.kind == 'raise':
            self._execution().exceptions.append(outcome.value)
            info = space.data(outcome.value)
            args = (info.cls, outcome.value, space.traceback_value(outcome.value))
        else:
            args = (None, None, None)

        self._invoke(task.env, task.data.exit, args)

    _UNWIND_KINDS: ta.ClassVar = (
        'finally',
        'except',
        'except_cleanup',
        'restore_outcome',
        'restore_exception',
        'loop',
        'function_end',
        'generator_end',
        'next_guard',
        'with_guard',
        'class_end',
        'module_end',
        'hasattr_guard',
        'delegate_guard',
        'default_next_guard',
    )

    def _unwind(self, outcome: Outcome) -> None:
        execution = self._execution()
        space = self._space

        while execution.tasks:
            self._budget.tick()

            task = execution.tasks.pop()
            kind = task.kind

            if kind in self._UNWIND_KINDS:
                del execution.values[task.base:]

            if kind == 'finally':
                self._finally(task, outcome)
                return

            if kind == 'except' and outcome.kind == 'raise':
                depth = len(execution.exceptions)
                execution.exceptions.append(outcome.value)
                self._add('restore_exception', task.env, data=depth)
                self._add('match_handler', task.env, task.node, (outcome.value, 0))
                return

            if kind == 'except_cleanup':
                self._task_except_cleanup(task)

            elif kind == 'restore_exception':
                self._restore_exception_depth(task.data)

            elif kind == 'restore_outcome':
                self._restore_exception_depth(task.data[1])

            elif kind == 'loop':
                if outcome.kind == 'break':
                    return

                if outcome.kind == 'continue':
                    self._add('loop', task.env, data=task.data)
                    return

            elif kind == 'function_end':
                self._thread.call_depth -= 1
                if outcome.kind == 'return':
                    self._push(outcome.value)
                    return

            elif kind == 'generator_end':
                if outcome.kind in ('return', 'raise'):
                    self._finish_generator(outcome)
                    return

            elif kind == 'next_guard' and outcome.kind == 'raise':
                if space.exception_matches(outcome.value, space.types['StopIteration']):
                    self._push(outcome.value)
                    execution.tasks.append(task.data[1])
                    return

            elif kind == 'default_next_guard' and outcome.kind == 'raise':
                if space.exception_matches(outcome.value, space.types['StopIteration']):
                    self._push(task.data)
                    return

            elif kind == 'hasattr_guard' and outcome.kind == 'raise':
                if space.exception_matches(outcome.value, space.types['AttributeError']):
                    self._push(task.data[0])
                    return

            elif kind == 'with_guard':
                self._with_exit(task, outcome)
                return

            elif kind == 'module_end':
                self._runtime.set_module(task.data[0], None)

        if execution.generator is not None:
            self._finish_generator(outcome)
            return

        self._thread.done = True

        if outcome.kind == 'raise':
            self._thread.error = outcome.value
        else:
            raise InterpreterError(f'unhandled control flow: {outcome.kind}')

    def _task_discard(self, task: Task) -> None:
        self._pop()

    def _task_constant(self, task: Task) -> None:
        self._push(task.data)

    def _task_many_next(self, task: Task) -> None:
        nodes, index, values = task.data
        if index == len(nodes):
            self._push(self._space.new('tuple', values))
        else:
            self._add('many_value', task.env, data=(nodes, index, values))
            self._evaluate(nodes[index], task.env)

    def _task_many_value(self, task: Task) -> None:
        nodes, index, values = task.data
        self._add('many_next', task.env, data=(nodes, index + 1, (*values, self._pop())))

    def _task_next_guard(self, task: Task) -> None:
        self._execution().tasks.append(task.data[0])

    def _task_default_next_guard(self, task: Task) -> None:
        pass

    def _task_collect_start(self, task: Task) -> None:
        state = CollectionState(self._pop(), self._space.new('list', []), task.data)
        self._add('collect_next', task.env, data=state)

    def _task_collect_next(self, task: Task) -> None:
        state = task.data
        if state.limit is not None and self._space.length(state.result) >= state.limit:
            self._push(state.result)
            return

        self._pull(
            task.env,
            state.iterator,
            Task('collect_value', task.env, data=state),
            Task('collect_stop', task.env, data=state),
        )

    def _task_collect_value(self, task: Task) -> None:
        self._space.append(task.data.result, self._pop())
        self._add('collect_next', task.env, data=task.data)

    def _task_collect_stop(self, task: Task) -> None:
        self._pop()
        self._push(task.data.result)

    def _task_eval(self, task: Task) -> None:
        node, env = task.node, task.env
        space = self._space

        if isinstance(node, ast.Constant):
            self._push(_ELLIPSIS if node.value is Ellipsis else node.value)

        elif isinstance(node, ast.Name):
            self._resolve(self._read_name(env, node.id), env)

        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            self._add('literal_next', env, node, (0, space.new('list', [])))

        elif isinstance(node, ast.Dict):
            self._add('dict_next', env, node, (0, space.new('dict', {})))

        elif isinstance(node, ast.BinOp):
            self._add('binary_values', env, node, type(node.op).__name__)
            self._many((node.left, node.right), env)

        elif isinstance(node, ast.UnaryOp):
            self._add('unary_value', env, node, type(node.op).__name__)
            self._evaluate(node.operand, env)

        elif isinstance(node, ast.BoolOp):
            self._add('bool_value', env, node, 0)
            self._evaluate(node.values[0], env)

        elif isinstance(node, ast.Compare):
            self._add('compare_left', env, node)
            self._evaluate(node.left, env)

        elif isinstance(node, ast.IfExp):
            self._add('ifexpr_value', env, node)
            self._evaluate(node.test, env)

        elif isinstance(node, ast.NamedExpr):
            self._add('named_value', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.Attribute):
            self._add('attribute_value', env, node, node.attr)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.Subscript):
            self._add('subscript_values', env, node)
            self._many((node.value, node.slice), env)

        elif isinstance(node, ast.Slice):
            parts = (node.lower, node.upper, node.step)
            self._add('slice_values', env, node)
            self._many(tuple(n if n is not None else ast.Constant(None) for n in parts), env)

        elif isinstance(node, ast.Call):
            self._add('call_function', env, node)
            self._evaluate(node.func, env)

        elif isinstance(node, ast.Lambda):
            self._define_function(node, env)

        elif isinstance(node, ast.Yield):
            self._add('yield_value', env, node)
            if node.value is None:
                self._push(None)
            else:
                self._evaluate(node.value, env)

        elif isinstance(node, ast.YieldFrom):
            self._add('yieldfrom_iterable', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            self._add('comprehension_outer', env, node)
            self._evaluate(node.generators[0].iter, env)

        elif isinstance(node, ast.JoinedStr):
            self._add('joined_values', env, node)
            self._many(node.values, env)

        elif isinstance(node, ast.FormattedValue):
            self._add('formatted_values', env, node)
            self._many((node.value, node.format_spec or ast.Constant('')), env)

        else:
            raise InterpreterError(f'validated expression has no evaluator: {type(node).__name__}')

    def _task_literal_next(self, task: Task) -> None:
        index, result = task.data

        if index == len(task.node.elts):
            kind = {ast.List: 'list', ast.Tuple: 'tuple', ast.Set: 'set'}[type(task.node)]

            if kind == 'list':
                self._push(result)

            elif kind == 'tuple':
                self._push(self._space.new('tuple', tuple(self._space.data(result))))

            else:
                output = self._space.new('set', {})
                for value in self._space.data(result):
                    self._space.set_item(output, value, None)
                self._push(output)

            return

        node = task.node.elts[index]
        self._add('literal_value', task.env, task.node, (index, result, isinstance(node, ast.Starred)))
        self._evaluate(node.value if isinstance(node, ast.Starred) else node, task.env)

    def _task_literal_value(self, task: Task) -> None:
        index, result, starred = task.data
        value = self._pop()

        if starred:
            self._add('literal_extend', task.env, task.node, (index, result))
            self._collect(task.env, value)

        else:
            self._space.append(result, value)
            self._add('literal_next', task.env, task.node, (index + 1, result))

    def _task_literal_extend(self, task: Task) -> None:
        index, result = task.data

        for value in self._space.data(self._pop()):
            self._budget.tick()
            self._space.append(result, value)

        self._add('literal_next', task.env, task.node, (index + 1, result))

    def _task_dict_next(self, task: Task) -> None:
        index, result = task.data

        if index == len(task.node.keys):
            self._push(result)
            return

        key = task.node.keys[index]
        self._add('dict_value', task.env, task.node, task.data)

        if key is None:
            self._evaluate(task.node.values[index], task.env)
        else:
            self._many((key, task.node.values[index]), task.env)

    def _task_dict_value(self, task: Task) -> None:
        index, result = task.data
        value = self._pop()

        if task.node.keys[index] is None:
            for key, item in self._space.mapping_pairs(value):
                self._budget.tick()
                self._space.set_item(result, key, item)

        else:
            key, item = self._space.data(value)
            self._space.set_item(result, key, item)

        self._add('dict_next', task.env, task.node, (index + 1, result))

    def _task_binary_values(self, task: Task) -> None:
        left, right = self._space.data(self._pop())

        self._operation('binary:' + task.data, task.env, left, right)

    def _task_unary_value(self, task: Task) -> None:
        self._operation('unary:' + task.data, task.env, self._pop())

    def _task_bool_value(self, task: Task) -> None:
        value = self._pop()

        if task.data + 1 == len(task.node.values):
            self._push(value)
            return

        self._add('bool_test', task.env, task.node, (task.data, value))
        self._operation('truth', task.env, value)

    def _task_bool_test(self, task: Task) -> None:
        index, value = task.data
        truth = self._pop()

        if truth == isinstance(task.node.op, ast.Or):
            self._push(value)

        else:
            self._add('bool_value', task.env, task.node, index + 1)
            self._evaluate(task.node.values[index + 1], task.env)

    def _task_compare_left(self, task: Task) -> None:
        self._add('compare_right', task.env, task.node, (0, self._pop()))
        self._evaluate(task.node.comparators[0], task.env)

    def _task_compare_right(self, task: Task) -> None:
        index, left = task.data
        right = self._pop()

        self._add('compare_result', task.env, task.node, (index, right))
        self._operation('compare:' + type(task.node.ops[index]).__name__, task.env, left, right)

    def _task_compare_result(self, task: Task) -> None:
        value = self._pop()
        index, right = task.data

        if index + 1 == len(task.node.ops):
            self._push(value)
            return

        self._add('compare_test', task.env, task.node, (index, right, value))
        self._operation('truth', task.env, value)

    def _task_compare_test(self, task: Task) -> None:
        index, right, result = task.data

        if not self._pop():
            self._push(result)

        else:
            self._add('compare_right', task.env, task.node, (index + 1, right))
            self._evaluate(task.node.comparators[index + 1], task.env)

    def _task_ifexpr_value(self, task: Task) -> None:
        self._add('ifexpr_test', task.env, task.node)
        self._operation('truth', task.env, self._pop())

    def _task_ifexpr_test(self, task: Task) -> None:
        self._evaluate(task.node.body if self._pop() else task.node.orelse, task.env)

    def _task_named_value(self, task: Task) -> None:
        value = self._pop()
        env = task.env

        while env.scope.kind == 'comprehension':
            env = env.parent

        self._write_name(env, task.node.target.id, value)
        self._push(value)

    def _task_attribute_value(self, task: Task) -> None:
        self._operation('getattr', task.env, self._pop(), task.data)

    def _task_subscript_values(self, task: Task) -> None:
        value, key = self._space.data(self._pop())

        self._operation('getitem', task.env, value, key)

    def _task_slice_values(self, task: Task) -> None:
        self._push(self._space.new('slice', self._space.data(self._pop())))

    def _task_joined_values(self, task: Task) -> None:
        values = self._space.data(self._pop())

        if any(type(v) is not str for v in values):
            raise InterpreterError('f-string component was not converted to a string')

        size = sum(map(len, values))

        self._budget.size(size, string=True)
        self._budget.allocate(size)
        self._push(''.join(values))

    def _task_formatted_values(self, task: Task) -> None:
        value, spec = self._space.data(self._pop())

        if task.node.conversion == -1:
            self._operation('format', task.env, value, spec)

        else:
            conversion = {ord('r'): 'repr', ord('s'): 'str', ord('a'): 'ascii'}[task.node.conversion]
            self._add('format_converted', task.env, data=spec)
            self._operation(conversion, task.env, value)

    def _task_format_converted(self, task: Task) -> None:
        self._operation('format', task.env, self._pop(), task.data)

    def _task_call_function(self, task: Task) -> None:
        self._add('call_argument', task.env, task.node, CallArguments(self._pop()))

    def _task_call_argument(self, task: Task) -> None:
        state = task.data
        node = task.node

        if state.index < len(node.args):
            arg = node.args[state.index]
            self._add('call_argument_value', task.env, node, state)
            self._evaluate(arg.value if isinstance(arg, ast.Starred) else arg, task.env)

        elif state.index < len(node.args) + len(node.keywords):
            kw = node.keywords[state.index - len(node.args)]
            self._add('call_keyword_value', task.env, node, state)
            self._evaluate(kw.value, task.env)

        else:
            self._invoke(task.env, state.function, state.positional, dict(state.keywords))

    def _task_call_argument_value(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        if isinstance(task.node.args[state.index], ast.Starred):
            self._add('call_star_values', task.env, task.node, state)
            self._collect(task.env, value)

        else:
            self._add('call_argument', task.env, task.node, dc.replace(
                state,
                index=state.index + 1,
                positional=(*state.positional, value),
            ))

    def _task_call_star_values(self, task: Task) -> None:
        state = task.data
        values = self._space.data(self._pop())

        self._budget.size(len(state.positional) + len(values))
        self._add('call_argument', task.env, task.node, dc.replace(
            state,
            index=state.index + 1,
            positional=(*state.positional, *values),
        ))

    def _task_call_keyword_value(self, task: Task) -> None:
        state = task.data
        key = task.node.keywords[state.index - len(task.node.args)].arg
        value = self._pop()
        pairs = [(key, value)] if key is not None else self._space.mapping_pairs(value)
        keywords = dict(state.keywords)

        for name, item in pairs:
            if type(name) is not str:
                self._space.error('TypeError', 'keywords must be strings')
            if name in keywords:
                self._space.error('TypeError', f'multiple values for keyword argument {name!r}')
            keywords[name] = item

        self._budget.size(len(keywords))
        self._add('call_argument', task.env, task.node, dc.replace(
            state, index=state.index + 1, keywords=tuple(keywords.items()),
        ))

    def _task_exec(self, task: Task) -> None:
        node, env = task.node, task.env

        if isinstance(node, ast.Expr):
            self._add('discard', env)
            self._evaluate(node.value, env)

        elif isinstance(node, (ast.Pass, ast.Global, ast.Nonlocal)):
            pass

        elif isinstance(node, ast.Assign):
            self._add('assignment_value', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self._add('annotated_done', env, node)
                self._add('assignment_value', env, node)
                self._evaluate(node.value, env)
            else:
                self._add('annotated_done', env, node)

        elif isinstance(node, ast.AugAssign):
            self._add('aug_location', env, node)
            self._location(node.target, env)

        elif isinstance(node, ast.Delete):
            for target in reversed(node.targets):
                self._add('assign', env, target, (_MISSING, True))

        elif isinstance(node, ast.If):
            self._add('if_value', env, node)
            self._evaluate(node.test, env)

        elif isinstance(node, ast.While):
            self._add('loop', env, data=LoopState(node))

        elif isinstance(node, ast.For):
            self._add('for_iterable', env, node)
            self._evaluate(node.iter, env)

        elif isinstance(node, ast.Break):
            self._unwind(Outcome('break'))

        elif isinstance(node, ast.Continue):
            self._unwind(Outcome('continue'))

        elif isinstance(node, ast.Return):
            self._add('return_value', env, node)
            if node.value is None:
                self._push(None)
            else:
                self._evaluate(node.value, env)

        elif isinstance(node, ast.FunctionDef):
            self._add('bind_definition', env, node, node.name)
            self._define_function(node, env)

        elif isinstance(node, ast.ClassDef):
            self._add('bind_definition', env, node, node.name)
            self._add('class_values', env, node)
            self._many((*node.decorator_list, *node.bases), env)

        elif isinstance(node, ast.Try):
            if node.finalbody:
                self._add('finally', env, data=tuple(node.finalbody))
            if node.handlers:
                self._add('except', env, node)
            self._suite(node.body, env)

        elif isinstance(node, ast.Raise):
            if node.exc is None:
                exc = self._active_exception()
                if exc is None:
                    self._space.error('RuntimeError', 'No active exception to reraise')
                self._unwind(Outcome('raise', exc))
            else:
                self._add('raise_values', env, node)
                self._many((node.exc,) if node.cause is None else (node.exc, node.cause), env)

        elif isinstance(node, ast.Assert):
            self._add('assert_value', env, node)
            self._evaluate(node.test, env)

        elif isinstance(node, ast.With):
            self._add('with_item', env, node, 0)

        elif isinstance(node, ast.Import):
            self._add('import_next', env, node, 0)

        elif isinstance(node, ast.ImportFrom):
            self._add('from_import', env, node)
            self._add('import_module', env, data=node.module)

        else:
            raise InterpreterError(f'validated statement has no evaluator: {type(node).__name__}')

    def _task_assignment_value(self, task: Task) -> None:
        value = self._pop()
        targets = task.node.targets if isinstance(task.node, ast.Assign) else [task.node.target]

        for target in reversed(targets):
            self._add('assign', task.env, target, (value, False))

    def _task_assign(self, task: Task) -> None:
        node, env = task.node, task.env
        value, delete = task.data

        if isinstance(node, ast.Name):
            self._write_name(env, node.id, value, delete=delete)

        elif isinstance(node, (ast.Tuple, ast.List)):
            if delete:
                for target in reversed(node.elts):
                    self._add('assign', env, target, (_MISSING, True))

            else:
                stars = sum(isinstance(n, ast.Starred) for n in node.elts)
                if stars > 1:
                    self._space.error('ValueError', 'multiple starred assignment targets')
                self._add('unpack_values', env, node)
                self._collect(env, value, None if stars else len(node.elts) + 1)

        elif isinstance(node, (ast.Attribute, ast.Subscript)):
            self._add('store_location', env, data=(value, delete))
            self._location(node, env)

        else:
            raise InterpreterError('invalid assignment target')

    def _task_unpack_values(self, task: Task) -> None:
        values = self._space.data(self._pop())
        targets = task.node.elts

        star = next((i for i, n in enumerate(targets) if isinstance(n, ast.Starred)), None)
        if star is None:
            if len(values) != len(targets):
                self._space.error('ValueError', 'wrong number of values to unpack')
            assignments = list(zip(targets, values))

        else:
            if len(values) < len(targets) - 1:
                self._space.error('ValueError', 'not enough values to unpack')
            tail = len(targets) - star - 1
            middle = values[star:len(values) - tail]
            assignments = [*zip(targets[:star], values[:star])]
            assignments.append((targets[star].value, self._space.new('list', list(middle))))
            if tail:
                assignments.extend(zip(targets[star + 1:], values[-tail:]))

        for target, value in reversed(assignments):
            self._add('assign', task.env, target, (value, False))

    def _location(self, node: ast.expr, env: Environment) -> None:
        if isinstance(node, ast.Name):
            self._push(self._space.new('location', ('name', env, node.id)))

        elif isinstance(node, ast.Attribute):
            self._add('attribute_location', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.Subscript):
            self._add('subscript_location', env, node)
            self._many((node.value, node.slice), env)

        else:
            raise InterpreterError('invalid augmented-assignment location')

    def _task_attribute_location(self, task: Task) -> None:
        self._push(self._space.new('location', ('attribute', self._pop(), task.node.attr)))

    def _task_subscript_location(self, task: Task) -> None:
        value, key = self._space.data(self._pop())

        self._push(self._space.new('location', ('item', value, key)))

    def _task_store_location(self, task: Task) -> None:
        location = self._space.data(self._pop())
        value, delete = task.data
        kind, receiver, key = location

        if kind == 'name':
            self._write_name(receiver, key, value, delete=delete)

        elif kind == 'attribute':
            self._space.set_attribute(receiver, key, value, delete=delete)

        else:
            self._add('discard', task.env)
            self._operation('delitem' if delete else 'setitem', task.env, receiver, key, value)

    def _task_aug_location(self, task: Task) -> None:
        location = self._pop()
        kind, receiver, key = self._space.data(location)

        self._add('aug_old_value', task.env, task.node, location)

        if kind == 'name':
            self._push(self._read_name(receiver, key))
        elif kind == 'attribute':
            self._operation('getattr', task.env, receiver, key)
        else:
            self._operation('getitem', task.env, receiver, key)

    def _task_aug_old_value(self, task: Task) -> None:
        self._add('aug_rhs', task.env, task.node, (task.data, self._pop()))
        self._evaluate(task.node.value, task.env)

    def _task_aug_rhs(self, task: Task) -> None:
        location, old = task.data
        rhs = self._pop()

        self._add('aug_result', task.env, data=location)
        self._operation('inplace:' + type(task.node.op).__name__, task.env, old, rhs)

    def _task_aug_result(self, task: Task) -> None:
        value = self._pop()

        self._push(task.data)
        self._add('store_location', task.env, data=(value, False))

    def _task_annotated_done(self, task: Task) -> None:
        node = task.node

        if task.env.scope.kind in ('module', 'class') and node.simple and isinstance(node.target, ast.Name):
            namespace = self._space.data(task.env.namespace)

            annotations = namespace.get('__annotations__')
            if annotations is None or self._space.kind(annotations) != 'annotations':
                annotations = self._space.new('annotations', AnnotationData(task.env, ()))
                self._runtime.write(task.env.namespace, '__annotations__', annotations)

            info = self._space.data(annotations)
            self._runtime.replace(annotations, dc.replace(
                info, entries=(*info.entries, (node.target.id, node.annotation)), cached=None,
            ))

    def _task_if_value(self, task: Task) -> None:
        self._add('if_test', task.env, task.node)
        self._operation('truth', task.env, self._pop())

    def _task_if_test(self, task: Task) -> None:
        self._suite(task.node.body if self._pop() else task.node.orelse, task.env)

    def _task_for_iterable(self, task: Task) -> None:
        self._add('for_iterator', task.env, task.node)
        self._operation('iter', task.env, self._pop())

    def _task_for_iterator(self, task: Task) -> None:
        self._add('loop', task.env, data=LoopState(task.node, self._pop()))

    def _task_loop(self, task: Task) -> None:
        state = task.data

        if isinstance(state.node, ast.While):
            self._add('while_value', task.env, data=state)
            self._evaluate(state.node.test, task.env)

        else:
            self._pull(
                task.env,
                state.iterator,
                Task('for_value', task.env, data=state),
                Task('for_stop', task.env, data=state),
            )

    def _task_while_value(self, task: Task) -> None:
        self._add('while_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_while_test(self, task: Task) -> None:
        state = task.data

        if self._pop():
            self._add('loop', task.env, data=state)
            self._suite(state.node.body, task.env)
        else:
            self._suite(state.node.orelse, task.env)

    def _task_for_value(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        self._add('loop', task.env, data=state)
        self._suite(state.node.body, task.env)
        self._add('assign', task.env, state.node.target, (value, False))

    def _task_for_stop(self, task: Task) -> None:
        self._pop()
        self._suite(task.data.node.orelse, task.env)

    def _task_return_value(self, task: Task) -> None:
        self._unwind(Outcome('return', self._pop()))

    def _task_finally(self, task: Task) -> None:
        self._finally(task, Outcome('normal'))

    def _task_restore_outcome(self, task: Task) -> None:
        outcome, depth = task.data

        self._restore_exception_depth(depth)

        if outcome.kind != 'normal':
            self._unwind(outcome)

    def _task_restore_exception(self, task: Task) -> None:
        self._restore_exception_depth(task.data)

    def _task_except(self, task: Task) -> None:
        self._suite(task.node.orelse, task.env)

    def _task_match_handler(self, task: Task) -> None:
        exception, index = task.data
        if index == len(task.node.handlers):
            self._unwind(Outcome('raise', exception))
            return

        handler = task.node.handlers[index]

        self._add('handler_type', task.env, task.node, task.data)

        if handler.type is None:
            self._push(self._space.types['BaseException'])
        else:
            self._evaluate(handler.type, task.env)

    def _task_handler_type(self, task: Task) -> None:
        exception, index = task.data
        cls = self._pop()

        if self._space.exception_matches(exception, cls):
            handler = task.node.handlers[index]
            if handler.name is not None:
                self._write_name(task.env, handler.name, exception)

            self._add('except_cleanup', task.env, data=handler.name)
            self._suite(handler.body, task.env)

        else:
            self._add('match_handler', task.env, task.node, (exception, index + 1))

    def _task_except_cleanup(self, task: Task) -> None:
        if task.data is not None:
            try:
                self._write_name(task.env, task.data, None, delete=True)

            except _GuestRaise as exc:
                if self._space.exception_name(exc.value) not in ('NameError', 'UnboundLocalError'):
                    raise

    def _normalize_exception(
            self,
            env: Environment,
            value: Value,
            args: tuple[Value, ...] = (),
    ) -> None:
        space = self._space
        kind = space.kind(value)

        if kind == 'exception':
            self._push(value)

        elif kind in ('class', 'type') and space.subclass(value, space.types['BaseException']):
            self._invoke(env, value, args)

        else:
            space.error('TypeError', 'exceptions must derive from BaseException')

    def _task_raise_values(self, task: Task) -> None:
        values = self._space.data(self._pop())

        self._add('raise_exception', task.env, data=values[1] if len(values) > 1 else _MISSING)
        self._normalize_exception(task.env, values[0])

    def _task_raise_exception(self, task: Task) -> None:
        exception = self._pop()

        if task.data is _MISSING:
            self._raise(exception)

        else:
            self._add('raise_cause', task.env, data=exception)
            if task.data is None:
                self._push(None)
            else:
                self._normalize_exception(task.env, task.data)

    def _task_raise_cause(self, task: Task) -> None:
        info = self._space.data(task.data)

        self._runtime.replace(task.data, dc.replace(info, cause=self._pop(), suppress_context=True))
        self._raise(task.data)

    def _task_assert_value(self, task: Task) -> None:
        self._add('assert_test', task.env, task.node)
        self._operation('truth', task.env, self._pop())

    def _task_assert_test(self, task: Task) -> None:
        if not self._pop():
            if task.node.msg is None:
                self._space.error('AssertionError')
            self._add('assert_message', task.env)
            self._evaluate(task.node.msg, task.env)

    def _task_assert_message(self, task: Task) -> None:
        self._space.error('AssertionError', self._pop())

    def _task_with_item(self, task: Task) -> None:
        if task.data == len(task.node.items):
            self._suite(task.node.body, task.env)
        else:
            self._add('with_manager', task.env, task.node, task.data)
            self._evaluate(task.node.items[task.data].context_expr, task.env)

    def _task_with_manager(self, task: Task) -> None:
        manager = self._pop()

        exit_method = self._space.special(manager, '__exit__')
        enter_method = self._space.special(manager, '__enter__')
        if enter_method is _MISSING or exit_method is _MISSING:
            self._space.error('TypeError', 'object does not support the context manager protocol')

        state = WithState(task.node, task.data, exit_method)

        self._add('with_entered', task.env, data=state)
        self._invoke(task.env, enter_method, ())

    def _task_with_entered(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        self._add('with_guard', task.env, data=state)
        self._add('with_item', task.env, state.node, state.index + 1)

        target = state.node.items[state.index].optional_vars
        if target is not None:
            self._add('assign', task.env, target, (value, False))

    def _task_with_guard(self, task: Task) -> None:
        self._with_exit(task, Outcome('normal'))

    def _task_with_exit_result(self, task: Task) -> None:
        value = self._pop()

        if task.data.kind == 'raise':
            self._add('with_suppressed', task.env, data=task.data)
            self._operation('truth', task.env, value)

        elif task.data.kind != 'normal':
            self._unwind(task.data)

    def _task_with_suppressed(self, task: Task) -> None:
        if not self._pop():
            self._unwind(task.data)

    def _define_function(self, node: ast.FunctionDef | ast.Lambda, env: Environment) -> None:
        decorators = node.decorator_list if isinstance(node, ast.FunctionDef) else []
        defaults = [*node.args.defaults, *(v for v in node.args.kw_defaults if v is not None)]

        self._add('function_values', env, node, len(decorators))
        self._many([*decorators, *defaults], env)

    def _task_function_values(self, task: Task) -> None:
        values = self._space.data(self._pop())
        args = task.node.args
        decorators = values[:task.data]
        defaults = values[task.data:task.data + len(args.defaults)]
        kwvalues = iter(values[task.data + len(args.defaults):])
        kwdefaults = {
            arg.arg: next(kwvalues)
            for arg, default in zip(args.kwonlyargs, args.kw_defaults)
            if default is not None
        }

        annotations = []
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            if arg.annotation is not None:
                annotations.append((arg.arg, arg.annotation))
        for arg in (args.vararg, args.kwarg):
            if arg is not None and arg.annotation is not None:
                annotations.append((arg.arg, arg.annotation))
        if isinstance(task.node, ast.FunctionDef) and task.node.returns is not None:
            annotations.append(('return', task.node.returns))

        thunk = self._space.new('annotations', AnnotationData(task.env, tuple(annotations)))

        function = self._space.new(
            'function',
            FunctionData(
                task.node,
                task.env,
                defaults,
                kwdefaults,
                thunk,
            ),
        )

        self._add('decorate', task.env, data=(decorators, function))

    def _task_decorate(self, task: Task) -> None:
        decorators, value = task.data

        if not decorators:
            self._push(value)
        else:
            self._add('decorated', task.env, data=decorators[:-1])
            self._invoke(task.env, decorators[-1], (value,))

    def _task_decorated(self, task: Task) -> None:
        self._add('decorate', task.env, data=(task.data, self._pop()))

    def _task_bind_definition(self, task: Task) -> None:
        self._write_name(task.env, task.data, self._pop())

    def _bind_arguments(
            self,
            info: FunctionData,
            values: tuple[Value, ...],
            keywords: ta.Mapping[str, Value],
    ) -> Environment:
        args = info.node.args
        positional = [*args.posonlyargs, *args.args]
        bindings: dict[str, Value] = {}

        if len(values) > len(positional) and args.vararg is None:
            self._space.error('TypeError', 'too many positional arguments')

        for arg, value in zip(positional, values):
            bindings[arg.arg] = value

        extra = {}
        posonly = {arg.arg for arg in args.posonlyargs}
        accepted = {arg.arg for arg in [*args.args, *args.kwonlyargs]}

        for name, value in keywords.items():
            if name in accepted:
                if name in bindings:
                    self._space.error('TypeError', f'multiple values for argument {name!r}')
                bindings[name] = value

            elif args.kwarg is not None:
                extra[name] = value

            else:
                message = (
                    'positional-only argument passed as keyword' if name in posonly else 'unexpected keyword argument'
                )
                self._space.error('TypeError', f'{message}: {name}')

        default_start = len(positional) - len(info.defaults)

        for index, arg in enumerate(positional):
            if arg.arg not in bindings:
                if index < default_start:
                    self._space.error('TypeError', f'missing positional argument {arg.arg}')
                bindings[arg.arg] = info.defaults[index - default_start]

        for arg in args.kwonlyargs:
            if arg.arg not in bindings:
                if arg.arg not in info.kwdefaults:
                    self._space.error('TypeError', f'missing keyword-only argument {arg.arg}')
                bindings[arg.arg] = info.kwdefaults[arg.arg]

        if args.vararg is not None:
            bindings[args.vararg.arg] = self._space.new('tuple', values[len(positional):])

        if args.kwarg is not None:
            bindings[args.kwarg.arg] = self._space.make_dict(tuple(extra.items()))

        namespace = self._space.new('namespace', bindings)
        parent = info.environment

        return Environment(
            parent.program,
            parent.program.scopes[info.node],
            namespace,
            parent.globals,
            parent,
        )

    def _enter_function(
            self,
            function: ObjectRef,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        info = self._space.data(function)
        env = self._bind_arguments(info, args, kwargs)

        tasks = [Task('generator_end' if env.scope.generator else 'function_end', env, info.node)]
        if isinstance(info.node, ast.Lambda):
            tasks.extend([Task('return_value', env, info.node), Task('eval', env, info.node.body)])
        else:
            tasks.extend(Task('exec', env, node) for node in reversed(info.node.body))

        if env.scope.generator:
            execution = Execution(tasks=tasks)
            generator = self._space.new('generator', GeneratorData(execution))
            self._runtime.edit_generator(generator).execution.generator = generator
            self._push(generator)

        else:
            if self._thread.call_depth >= self._budget.limits.call_depth:
                self._budget.fail('guest call depth limit')
            self._thread.call_depth += 1
            tasks[0] = dc.replace(tasks[0], base=len(self._execution().values))
            self._execution().tasks.extend(tasks)

    def _task_function_end(self, task: Task) -> None:
        self._thread.call_depth -= 1
        self._push(None)

    def _task_class_values(self, task: Task) -> None:
        values = self._space.data(self._pop())
        count = len(task.node.decorator_list)
        decorators = values[:count]
        base = values[count] if len(values) > count else self._space.types['object']

        if self._space.kind(base) not in ('class', 'type'):
            self._space.error('TypeError', 'base must be a guest class')

        if self._space.kind(base) == 'type' and base != self._space.types['object']:
            if not self._space.subclass(base, self._space.types['BaseException']):
                self._space.error('TypeError', 'subclassing intrinsic types is not supported')

        namespace = self._space.new('namespace', {
            '__module__': self._space.data(task.env.globals).get('__name__', '__main__'),
            '__qualname__': task.node.name,
        })

        env = Environment(
            task.env.program,
            task.env.program.scopes[task.node],
            namespace,
            task.env.globals,
            task.env,
        )

        self._add('class_end', env, task.node, (base, decorators))
        self._suite(task.node.body, env)

    _TASK_CLASS_END_UNSUPPORTED: ta.ClassVar = frozenset({
        '__del__',
        '__slots__',
        '__getattribute__',
        '__getattr__',
        '__setattr__',
        '__delattr__',
        '__new__',
        '__init_subclass__',
        '__class_getitem__',
        '__set_name__',
        '__get__',
        '__set__',
        '__delete__',
    })

    def _task_class_end(self, task: Task) -> None:
        namespace = self._space.data(task.env.namespace)
        unsupported = self._TASK_CLASS_END_UNSUPPORTED

        bad = unsupported.intersection(namespace)
        if bad:
            self._space.error('TypeError', 'unsupported class hooks: ' + ', '.join(sorted(bad)))

        base, decorators = task.data

        cls = self._space.new('class', ClassData(task.node.name, task.env.namespace, base))

        self._add('decorate', task.env.parent, data=(decorators, cls))

    def _task_instance_initialized(self, task: Task) -> None:
        if self._pop() is not None:
            self._space.error('TypeError', '__init__() must return None')
        self._push(task.data)

    def _resolve(self, value: Value, env: Environment) -> None:
        if self._space.kind(value) != 'annotations':
            self._push(value)
            return

        info = self._space.data(value)
        if info.cached is not None:
            self._push(info.cached)
        else:
            self._add('annotation_next', info.environment, data=(value, 0, self._space.new('dict', {})))

    def _task_annotation_next(self, task: Task) -> None:
        ref, index, result = task.data
        info = self._space.data(ref)

        if index == len(info.entries):
            self._runtime.replace(ref, dc.replace(info, cached=result))
            self._push(result)
        else:
            self._add('annotation_value', task.env, data=task.data)
            self._evaluate(info.entries[index][1], info.environment)

    def _task_annotation_value(self, task: Task) -> None:
        ref, index, result = task.data
        name = self._space.data(ref).entries[index][0]

        self._space.set_item(result, name, self._pop())
        self._add('annotation_next', task.env, data=(ref, index + 1, result))

    _TASK_OPERATION_NAMES: ta.ClassVar = (
        'truth',
        'len',
        'iter',
        'next',
        'str',
        'repr',
        'ascii',
        'format',
        'getitem',
        'setitem',
        'delitem',
    )

    _TASK_OPERATION_SPECIAL_NAMES: ta.ClassVar = {
        'truth': '__bool__',
        'len': '__len__',
        'iter': '__iter__',
        'next': '__next__',
        'str': '__str__',
        'repr': '__repr__',
        'ascii': '__repr__',
        'format': '__format__',
        'getitem': '__getitem__',
        'setitem': '__setitem__',
        'delitem': '__delitem__',
    }

    _TASK_OPERATION_EXPECTED: ta.ClassVar = {
        'truth': 'bool',
        'len': 'len',
        'iter': 'iterator',
        'str': 'str',
        'repr': 'str',
        'ascii': 'ascii',
        'format': 'str',
    }

    def _task_operation(self, task: Task) -> None:
        name, values = task.data
        env, space = task.env, self._space
        value = values[0] if values else None
        kind = space.kind(value)

        if name in self._TASK_OPERATION_NAMES:
            special_name = self._TASK_OPERATION_SPECIAL_NAMES[name]
            method = space.special(value, special_name)
            expected = self._TASK_OPERATION_EXPECTED.get(name)

            if method is _MISSING and name == 'truth':
                method = space.special(value, '__len__')
                expected = 'len_bool'

            if method is _MISSING and name == 'str':
                method = space.special(value, '__repr__')

            if method is not _MISSING:
                if expected is not None:
                    self._add('expect', env, data=expected)

                args = values[1:]
                if name in ('setitem', 'delitem'):
                    self._add('constant', env, data=None)
                    self._add('discard', env)
                    args = values[1:2] if name == 'delitem' else values[1:]

                self._invoke(env, method, args)
                return

        if name == 'truth':
            self._push(space.truth(value))

        elif name == 'len':
            length = space.length(value)
            if length > sys.maxsize:
                space.error('OverflowError', 'length does not fit in a platform index')
            self._push(length)

        elif name == 'iter':
            if kind == 'adapter':
                self._push(value)
            else:
                self._push(space.iter_value(value))

        elif name == 'next':
            if kind == 'generator':
                self._resume_generator(env, value, 'next', None)
            elif kind == 'iterator':
                self._push(space.next_value(value))
            elif kind == 'adapter':
                self._adapter_next(env, value)
            else:
                space.error('TypeError', 'object is not an iterator')

        elif name == 'getattr':
            self._resolve(space.get_attribute(value, values[1]), env)

        elif name == 'getitem':
            self._resolve(space.get_item(value, values[1]), env)

        elif name in ('setitem', 'delitem'):
            if name == 'setitem' and kind == 'list' and space.kind(values[1]) == 'slice':
                self._add('slice_assignment', env, data=values[:2])
                self._collect(env, values[2])
            else:
                space.set_item(value, values[1], values[2], delete=name == 'delitem')
                self._push(None)

        elif name.startswith(('binary:', 'inplace:', 'compare:')):
            category, op = name.split(':')
            left, right = values

            if category == 'compare' and op in ('Is', 'IsNot'):
                self._push(space.compare(op, left, right))
                return

            if category == 'compare' and op in ('In', 'NotIn'):
                self._add('contains_result', env, data=op == 'NotIn')
                method = space.special(right, '__contains__')

                if method is not _MISSING:
                    self._invoke(env, method, (left,))

                elif space.kind(right) in ('dict', 'namespace', 'set', 'frozenset'):
                    if space.kind(right) == 'namespace':
                        self._push(type(left) is str and left in space.data(right))
                    else:
                        self._push(space.key(left) in space.data(right))

                elif type(right) in (str, bytes):
                    if type(left) not in (str, bytes, int, bool):
                        space.error('TypeError', 'invalid string membership operand')
                    self._push(space.native(operator.contains, right, left))

                elif space.kind(right) == 'range' and type(left) in (bool, int):
                    info = space.data(right)
                    self._push(left in range(info.start, info.stop, info.step))

                else:
                    self._add('contains_iterator', env, data=left)
                    self._operation('iter', env, right)

                return

            if category == 'inplace' and kind == 'list' and op == 'Add':
                self._add('constant', env, data=left)
                self._add('discard', env)
                self._invoke(env, space.new('builtin', BuiltinData('list.extend', left)), (right,))
                return

            if category == 'inplace' and kind == 'list' and op == 'Mult':
                result = space.binary(op, left, right)
                self._runtime.replace(left, list(space.data(result)))
                self._push(left)
                return

            if category == 'inplace' and kind in ('dict', 'namespace') and op == 'BitOr':
                self._update_mapping(env, left, right, {}, left)
                return

            if category == 'inplace' and kind == 'set' and op in ('BitOr', 'BitAnd', 'BitXor', 'Sub'):
                result = space.binary(op, left, right)
                self._runtime.replace(left, dict(space.data(result)))
                self._push(left)
                return

            candidates = []
            if category == 'inplace':
                method = space.special(left, '__i' + self._binary_method(op) + '__')
                if method is not _MISSING:
                    candidates.append((method, (right,)))

            if category == 'compare':
                methods = {
                    'Eq': ('__eq__', '__eq__'),
                    'NotEq': ('__ne__', '__ne__'),
                    'Lt': ('__lt__', '__gt__'),
                    'LtE': ('__le__', '__ge__'),
                    'Gt': ('__gt__', '__lt__'),
                    'GtE': ('__ge__', '__le__')
                }
                lname, rname = methods[op]
            else:
                method_name = self._binary_method(op)
                lname, rname = '__' + method_name + '__', '__r' + method_name + '__'

            lm, rm = space.special(left, lname), space.special(right, rname)
            lt, rt = space.type_of(left), space.type_of(right)

            reverse_first = lt != rt and space.subclass(rt, lt)
            left_pair, right_pair = (lm, (right,)), (rm, (left,))
            for method, args in ((right_pair, left_pair) if reverse_first else (left_pair, right_pair)):
                if method is not _MISSING:
                    if method == rm and category != 'compare' and lt == rt and not reverse_first:
                        continue
                    candidates.append((method, args))

            self._add('special_next', env, data=(name, values, tuple(candidates), 0))

        elif name.startswith('unary:'):
            op = name.split(':')[1]

            if op == 'Not':
                self._add('negate_bool', env)
                self._operation('truth', env, value)
                return

            method = space.special(
                value,
                {
                    'UAdd': '__pos__',
                    'USub': '__neg__',
                    'Invert': '__invert__',
                }[op],
            )

            if method is not _MISSING:
                self._invoke(env, method, ())

            elif type(value) in _NUMBERS:
                operation = {'UAdd': operator.pos, 'USub': operator.neg, 'Invert': operator.invert}[op]
                self._push(space.native(operation, value))

            else:
                space.error('TypeError', 'invalid unary operand')

        elif name in ('str', 'repr', 'ascii'):
            text = space.representation(value, string=name == 'str')
            if name == 'ascii':
                text = text.encode('ascii', 'backslashreplace').decode('ascii')
            self._budget.size(len(text), string=True)
            self._push(text)

        elif name == 'format':
            spec = values[1]

            if type(spec) is not str:
                space.error('TypeError', 'format specification must be a string')

            if type(value) not in _SCALARS:
                if spec:
                    space.error('TypeError', 'unsupported format specification')
                self._operation('str', env, value)
                return

            for digits in re.findall(r'\d+', spec):
                if len(digits) > 7 or int(digits) > self._budget.limits.string:
                    self._budget.fail('format width/precision limit')

            text = space.native(format, value, spec)
            self._budget.allocate(len(text))
            self._push(text)

        else:
            raise InterpreterError('unknown object-space operation: ' + name)

    _BINARY_METHODS: ta.ClassVar = {
        'Add': 'add',
        'Sub': 'sub',
        'Mult': 'mul',
        'Div': 'truediv',
        'FloorDiv': 'floordiv',
        'Mod': 'mod',
        'Pow': 'pow',
        'LShift': 'lshift',
        'RShift': 'rshift',
        'BitAnd': 'and',
        'BitOr': 'or',
        'BitXor': 'xor',
    }

    @classmethod
    def _binary_method(cls, name: str) -> str:
        return cls._BINARY_METHODS[name]

    def _task_special_next(self, task: Task) -> None:
        name, values, candidates, index = task.data

        if index == len(candidates):
            category, op = name.split(':')

            if category == 'compare':
                if op == 'NotEq' and self._space.special(values[0], '__eq__') is not _MISSING:
                    self._add('negate_bool', task.env)
                    self._add('truth_result', task.env)
                    self._operation('compare:Eq', task.env, *values)

                else:
                    self._push(self._space.compare(op, *values))

            else:
                self._push(self._space.binary(op, *values))

        else:
            method, args = candidates[index]
            self._add('special_result', task.env, data=task.data)
            self._invoke(task.env, method, args)

    def _task_special_result(self, task: Task) -> None:
        value = self._pop()

        if value is _NOT_IMPLEMENTED:
            name, values, candidates, index = task.data
            self._add('special_next', task.env, data=(name, values, candidates, index + 1))

        else:
            self._push(value)

    def _task_truth_result(self, task: Task) -> None:
        self._operation('truth', task.env, self._pop())

    def _task_negate_bool(self, task: Task) -> None:
        self._push(not self._pop())

    def _task_expect(self, task: Task) -> None:
        value = self._pop()
        expected = task.data

        if expected == 'bool' and type(value) is not bool:
            self._space.error('TypeError', '__bool__ should return bool')

        if expected in ('len', 'len_bool'):
            if type(value) not in (bool, int):
                self._space.error('TypeError', '__len__ should return an integer')
            if value < 0:
                self._space.error('ValueError', '__len__ should return a nonnegative integer')
            value = bool(value) if expected == 'len_bool' else int(value)

        if expected in ('str', 'ascii'):
            if type(value) is not str:
                self._space.error('TypeError', 'string protocol method should return a string')
            if expected == 'ascii':
                value = value.encode('ascii', 'backslashreplace').decode('ascii')
            self._budget.size(len(value), string=True)

        if expected == 'iterator':
            if self._space.kind(value) not in ('iterator', 'generator', 'adapter'):
                if self._space.special(value, '__next__') is _MISSING:
                    self._space.error('TypeError', '__iter__ returned a non-iterator')

        self._push(value)

    def _task_slice_assignment(self, task: Task) -> None:
        value, key = task.data

        self._space.set_item(value, key, self._pop())
        self._push(None)

    def _task_contains_result(self, task: Task) -> None:
        if task.data:
            self._add('negate_bool', task.env)
        self._operation('truth', task.env, self._pop())

    def _task_contains_iterator(self, task: Task) -> None:
        self._add('contains_next', task.env, data=(task.data, self._pop()))

    def _task_contains_next(self, task: Task) -> None:
        value, iterator = task.data

        self._pull(
            task.env, iterator,
            Task('contains_value', task.env, data=task.data),
            Task('contains_stop', task.env),
        )

    def _task_contains_value(self, task: Task) -> None:
        value = self._pop()

        if self._space.identical(task.data[0], value):
            self._push(True)
        else:
            self._add('contains_comparison', task.env, data=task.data)
            self._operation('compare:Eq', task.env, value, task.data[0])

    def _task_contains_comparison(self, task: Task) -> None:
        self._add('contains_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_contains_test(self, task: Task) -> None:
        if self._pop():
            self._push(True)
        else:
            self._add('contains_next', task.env, data=task.data)

    def _task_contains_stop(self, task: Task) -> None:
        self._pop()
        self._push(False)

    def _task_invoke(self, task: Task) -> None:
        function, args, kwargs = task.data
        space = self._space
        kind = space.kind(function)

        if kind == 'bound_method':
            info = space.data(function)
            self._invoke(task.env, info.function, (info.receiver, *args), kwargs)

        elif kind == 'function':
            self._enter_function(function, args, kwargs)

        elif kind == 'builtin':
            self._builtin(task.env, space.data(function), args, kwargs)

        elif kind == 'capability':
            if space.capabilities.guest_arguments(space.data(function)):
                exported_args = list(args)
                exported_kwargs = dict(kwargs)
            else:
                memo: dict[int, object] = {}
                exported_args = [space.export_value(v, memo=memo) for v in args]
                exported_kwargs = {k: space.export_value(v, memo=memo) for k, v in kwargs.items()}

            try:
                result = space.capabilities.invoke(space.data(function), exported_args, exported_kwargs)
            except CapabilityFailure as exc:
                imported = tuple(space.import_value(v) for v in exc.args)
                space.error(exc.name, *imported)

            self._push(space.import_value(result, capabilities=True))

        elif kind in ('class', 'type'):
            if space.subclass(function, space.types['BaseException']):
                value = space.new('exception', ExceptionData(function, args))
                init = space.special(value, '__init__')

                if init is not _MISSING:
                    self._add('instance_initialized', task.env, data=value)
                    self._invoke(task.env, init, args, kwargs)

                else:
                    if kwargs:
                        space.error('TypeError', 'exception constructor does not accept keywords')
                    self._push(value)

            elif kind == 'type' and function != space.types['object']:
                self._constructor(task.env, space.data(function).name, args, kwargs)

            else:
                value = space.new('instance', InstanceData(function, space.new('namespace', {})))
                init = space.special(value, '__init__')

                if init is not _MISSING:
                    self._add('instance_initialized', task.env, data=value)
                    self._invoke(task.env, init, args, kwargs)

                elif args or kwargs:
                    space.error('TypeError', 'class takes no arguments')

                else:
                    self._push(value)

        else:
            method = space.special(function, '__call__')
            if method is _MISSING:
                space.error('TypeError', 'object is not callable')
            self._invoke(task.env, method, args, kwargs)

    def _resume_generator(
            self,
            env: Environment,
            ref: ObjectRef,
            mode: str,
            value: Value,
    ) -> None:
        info = self._runtime.edit_generator(ref)

        if info.running:
            self._space.error('ValueError', 'generator already executing')

        if info.closed:
            if mode == 'close':
                self._push(None)
            elif mode == 'throw':
                self._raise(value)
            else:
                self._space.error('StopIteration')
            return

        if not info.started:
            if mode == 'send' and value is not None:
                self._space.error('TypeError', "can't send non-None value to a just-started generator")
            if mode in ('throw', 'close'):
                info.closed = True
                info.execution.tasks.clear()
                if mode == 'throw':
                    self._raise(value)
                else:
                    self._push(None)
                return

        if self._thread.call_depth >= self._budget.limits.call_depth:
            self._budget.fail('guest call depth limit')
        self._thread.call_depth += 1

        info.running = True
        info.execution.resume_mode = mode

        self._thread.executions.append(info.execution)

        if mode == 'close':
            value = self._space.exception('GeneratorExit', ())

        if not info.started:
            info.started = True
        elif info.waiting == 'delegate':
            info.packet = Outcome('raise' if mode in ('throw', 'close') else 'send', value)
        elif mode in ('throw', 'close'):
            self._raise(value)
        else:
            self._push(value)

        info.waiting = ''

    def _suspend(
            self,
            value: Value,
            *,
            waiting: str,
    ) -> None:
        execution = self._execution()

        if execution.generator is None:
            raise InterpreterError('yield without a generator execution')

        info = self._runtime.edit_generator(execution.generator)
        info.running = False
        info.waiting = waiting

        mode = execution.resume_mode

        self._thread.executions.pop()
        self._thread.call_depth -= 1

        if mode == 'close':
            self._space.error('RuntimeError', 'generator ignored GeneratorExit')

        self._push(value)

    def _finish_generator(self, outcome: Outcome) -> None:
        execution = self._execution()

        info = self._runtime.edit_generator(execution.generator)
        info.running = False
        info.closed = True
        info.waiting = ''

        mode = execution.resume_mode

        execution.tasks.clear()
        execution.values.clear()
        execution.exceptions.clear()

        self._thread.executions.pop()
        self._thread.call_depth -= 1

        if outcome.kind == 'raise':
            exception = outcome.value

            if self._space.exception_matches(exception, self._space.types['StopIteration']):
                replacement = self._space.exception('RuntimeError', ('generator raised StopIteration',))
                self._runtime.replace(replacement, dc.replace(
                    self._space.data(replacement), cause=exception, context=exception, suppress_context=True,
                ))
                self._raise(replacement)

            elif mode == 'close' and self._space.exception_matches(exception, self._space.types['GeneratorExit']):
                self._push(None)

            else:
                self._raise(exception)

        elif mode == 'close':
            self._push(outcome.value)

        else:
            args = () if outcome.value is None else (outcome.value,)
            self._raise(self._space.exception('StopIteration', args))

    def _task_generator_end(self, task: Task) -> None:
        self._finish_generator(Outcome('return'))

    def _task_yield_value(self, task: Task) -> None:
        self._suspend(self._pop(), waiting='yield')

    def _task_yieldfrom_iterable(self, task: Task) -> None:
        self._add('yieldfrom_iterator', task.env)
        self._operation('iter', task.env, self._pop())

    def _task_yieldfrom_iterator(self, task: Task) -> None:
        self._delegate(task.env, self._pop(), Outcome('send'))

    def _optional_attribute(self, value: Value, name: str) -> Value:
        try:
            return self._space.get_attribute(value, name)
        except _GuestRaise as exc:
            if self._space.exception_matches(exc.value, self._space.types['AttributeError']):
                return _MISSING
            raise

    def _delegate(
            self,
            env: Environment,
            iterator: Value,
            packet: Outcome,
    ) -> None:
        space = self._space

        if packet.kind == 'raise' and space.exception_matches(packet.value, space.types['GeneratorExit']):
            close = self._optional_attribute(iterator, 'close')
            if close is _MISSING:
                self._raise(packet.value)
            else:
                self._add('delegate_closed', env, data=packet.value)
                self._invoke(env, close, ())
            return

        on_value = Task('delegate_value', env, data=iterator)
        on_stop = Task('delegate_stop', env)

        if packet.kind == 'send' and packet.value is None:
            self._pull(env, iterator, on_value, on_stop)
            return

        if packet.kind == 'raise':
            method = self._optional_attribute(iterator, 'throw')
            if method is _MISSING:
                self._raise(packet.value)
                return

        else:
            method = space.get_attribute(iterator, 'send')

        self._add('next_guard', env, data=(on_value, on_stop))
        self._invoke(env, method, (packet.value,))

    def _task_delegate_value(self, task: Task) -> None:
        value = self._pop()

        self._add('delegate_resume', task.env, data=task.data)
        self._suspend(value, waiting='delegate')

    def _task_delegate_resume(self, task: Task) -> None:
        packet = self._runtime.edit_generator(self._execution().generator).packet

        self._delegate(task.env, task.data, packet)

    def _task_delegate_stop(self, task: Task) -> None:
        exception = self._pop()
        args = self._space.data(exception).args

        self._push(args[0] if args else None)

    def _task_delegate_closed(self, task: Task) -> None:
        self._pop()
        self._raise(task.data)

    def _generator_method(
            self,
            env: Environment,
            ref: ObjectRef,
            name: str,
            args: tuple[Value, ...],
    ) -> None:
        if name in ('__iter__', '__next__', 'close'):
            self._arity(name, args, {}, 0, 0)
            if name == '__iter__':
                self._push(ref)
            else:
                self._resume_generator(env, ref, 'close' if name == 'close' else 'next', None)

        elif name == 'send':
            self._arity(name, args, {}, 1, 1)
            self._resume_generator(env, ref, 'send', args[0])

        elif name == 'throw':
            self._arity(name, args, {}, 1, 3)

            if len(args) > 2 and args[2] is not None:
                self._space.error('TypeError', 'non-None throw traceback is not supported')

            kind = self._space.kind(args[0])

            if kind == 'exception':
                if len(args) > 1 and args[1] is not None:
                    self._space.error('TypeError', 'instance exception may not have a separate value')
                exception, values = args[0], ()

            elif (
                    kind in ('class', 'type') and
                    self._space.subclass(args[0], self._space.types['BaseException'])
            ):
                exception, values = args[0], ()
                if len(args) > 1 and args[1] is not None:
                    if (
                            self._space.kind(args[1]) == 'exception' and
                            self._space.subclass(self._space.data(args[1]).cls, args[0])
                    ):
                        exception = args[1]
                    else:
                        values = self._space.data(args[1]) if self._space.kind(args[1]) == 'tuple' else (args[1],)

            else:
                self._space.error('TypeError', 'exceptions must derive from BaseException')

            self._add('generator_throw_normalized', env, data=ref)
            self._normalize_exception(env, exception, tuple(values))

        else:
            raise InterpreterError('unknown generator method')

    def _task_generator_throw_normalized(self, task: Task) -> None:
        self._resume_generator(task.env, task.data, 'throw', self._pop())

    def _task_comprehension_outer(self, task: Task) -> None:
        self._add('comprehension_created', task.env, task.node)
        self._operation('iter', task.env, self._pop())

    def _task_comprehension_created(self, task: Task) -> None:
        iterator = self._pop()
        node = task.node

        env = Environment(
            task.env.program,
            task.env.program.scopes[node],
            self._space.new('namespace', {}),
            task.env.globals,
            task.env,
        )

        if isinstance(node, ast.GeneratorExp):
            state = ComprehensionState(node, None, iterator=iterator)
            execution = Execution(tasks=[Task('generator_end', env, node), Task('comprehension_next', env, data=state)])
            ref = self._space.new('generator', GeneratorData(execution))
            execution.generator = ref
            self._push(ref)

        else:
            kind = {ast.ListComp: 'list', ast.SetComp: 'set', ast.DictComp: 'dict'}[type(node)]
            result = self._space.new(kind, [] if kind == 'list' else {})
            self._add('comprehension_next', env, data=ComprehensionState(node, result, iterator=iterator))

    def _task_comprehension_next(self, task: Task) -> None:
        self._pull(
            task.env,
            task.data.iterator,
            Task('comprehension_item', task.env, data=task.data),
            Task('comprehension_stop', task.env, data=task.data),
        )

    def _task_comprehension_item(self, task: Task) -> None:
        state = task.data
        item = self._pop()

        self._add('comprehension_next', task.env, data=state)
        self._add('comprehension_condition', task.env, data=dc.replace(state, condition=0))
        self._add('assign', task.env, state.node.generators[state.level].target, (item, False))

    def _task_comprehension_condition(self, task: Task) -> None:
        state = task.data
        gen = state.node.generators[state.level]

        if state.condition < len(gen.ifs):
            self._add('comprehension_condition_value', task.env, data=state)
            self._evaluate(gen.ifs[state.condition], task.env)

        elif state.level + 1 < len(state.node.generators):
            self._add('comprehension_inner', task.env, data=state)
            self._evaluate(state.node.generators[state.level + 1].iter, task.env)

        else:
            self._add('comprehension_emit', task.env, data=state)
            if isinstance(state.node, ast.DictComp):
                self._many((state.node.key, state.node.value), task.env)
            else:
                self._evaluate(state.node.elt, task.env)

    def _task_comprehension_condition_value(self, task: Task) -> None:
        self._add('comprehension_condition_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_comprehension_condition_test(self, task: Task) -> None:
        if self._pop():
            state = dc.replace(task.data, condition=task.data.condition + 1)
            self._add('comprehension_condition', task.env, data=state)

    def _task_comprehension_inner(self, task: Task) -> None:
        self._add('comprehension_inner_iterator', task.env, data=task.data)
        self._operation('iter', task.env, self._pop())

    def _task_comprehension_inner_iterator(self, task: Task) -> None:
        state = dc.replace(task.data, level=task.data.level + 1, condition=0, iterator=self._pop())

        self._add('comprehension_next', task.env, data=state)

    def _task_comprehension_emit(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        if isinstance(state.node, ast.GeneratorExp):
            self._add('discard', task.env)
            self._suspend(value, waiting='yield')

        elif isinstance(state.node, ast.ListComp):
            self._space.append(state.result, value)

        elif isinstance(state.node, ast.DictComp):
            key, item = self._space.data(value)
            self._space.set_item(state.result, key, item)

        else:
            self._space.set_item(state.result, value, None)

    def _task_comprehension_stop(self, task: Task) -> None:
        self._pop()

        if task.data.level == 0:
            if isinstance(task.data.node, ast.GeneratorExp):
                self._unwind(Outcome('return'))
            else:
                self._push(task.data.result)

    def _task_import_next(self, task: Task) -> None:
        if task.data < len(task.node.names):
            self._add('import_bound', task.env, task.node, task.data)
            self._add('import_module', task.env, data=task.node.names[task.data].name)

    def _task_import_bound(self, task: Task) -> None:
        alias = task.node.names[task.data]

        self._write_name(task.env, alias.asname or alias.name, self._pop())
        self._add('import_next', task.env, task.node, task.data + 1)

    def _task_from_import(self, task: Task) -> None:
        module = self._pop()

        for alias in task.node.names:
            try:
                value = self._space.get_attribute(module, alias.name)

            except _GuestRaise as exc:
                if self._space.exception_matches(exc.value, self._space.types['AttributeError']):
                    self._space.error('ImportError', 'cannot import name ' + alias.name)
                raise

            self._write_name(task.env, alias.asname or alias.name, value)

    def _task_import_module(self, task: Task) -> None:
        name = task.data

        if name in self._runtime.modules():
            self._push(self._runtime.modules()[name])
            return

        if name not in self._modules:
            self._space.error('ModuleNotFoundError', 'module is not granted: ' + name)

        source = self._modules[name]
        namespace = self._space.new('namespace', {'__name__': name, '__package__': ''})
        module = self._space.new('module', namespace)

        if type(source) is SourceModule:
            program = self._frontend.prepare(source.source, filename=source.filename)
            self._programs.append(program)
            env = Environment(program, program.scopes[program.tree], namespace, namespace)
            self._runtime.set_module(name, module)
            self._add('module_end', env, data=(name, module))
            self._suite(program.tree.body, env)

        else:
            memo = {}
            for key, value in source.items():
                if type(key) is not str:
                    raise BoundaryError('intrinsic module names must be strings')
                self._runtime.write(namespace, key, self._space.import_value(value, capabilities=True, memo=memo))
            self._runtime.set_module(name, module)
            self._push(module)

    def _task_module_end(self, task: Task) -> None:
        self._push(task.data[1])

    def _arity(
            self,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
            minimum: int,
            maximum: int | None,
            allowed: ta.AbstractSet[str] = frozenset(),
    ) -> None:
        if len(args) < minimum or (maximum is not None and len(args) > maximum):
            self._space.error('TypeError', f'{name}: wrong number of arguments')

        if any(k not in allowed for k in kwargs):
            self._space.error('TypeError', f'{name}: unsupported keyword argument')

    def _constructor(
            self,
            env: Environment,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space

        if name in ('list', 'tuple', 'set', 'frozenset'):
            self._arity(name, args, kwargs, 0, 1)

            if not args:
                self._push(space.new(name, [] if name == 'list' else (() if name == 'tuple' else {})))
            elif name == 'tuple' and space.kind(args[0]) == 'tuple':
                self._push(args[0])
            else:
                self._add('construct_collection', env, data=name)
                self._collect(env, args[0])

        elif name == 'dict':
            self._arity(name, args, {}, 0, 1)
            result = space.new('dict', {})
            self._update_mapping(env, result, args[0] if args else None, kwargs, result)

        elif name == 'bool':
            self._arity(name, args, kwargs, 0, 1)

            if args:
                self._operation('truth', env, args[0])
            else:
                self._push(False)

        elif name == 'str':
            self._arity(name, args, kwargs, 0, 1)

            if args:
                self._operation('str', env, args[0])
            else:
                self._push('')

        elif name in ('int', 'float', 'complex'):
            allowed = frozenset({'base'}) if name == 'int' else frozenset()
            self._arity(name, args, kwargs, 0, 2 if name in ('int', 'complex') else 1, allowed)

            if args and space.kind(args[0]) == 'instance':
                method = space.special(args[0], '__' + name + '__')
                if method is not _MISSING and len(args) == 1 and not kwargs:
                    self._add('numeric_constructed', env, data=name)
                    self._invoke(env, method, ())
                    return

            if any(type(v) not in (*_NUMBERS, str, bytes) for v in args):
                space.error('TypeError', 'unsupported numeric conversion')
            if any(type(v) not in (int, bool) for v in kwargs.values()):
                space.error('TypeError', 'base must be an integer')

            if name == 'int':
                text = args[0] if args else None
                if type(text) in (str, bytes) and len(text) > space.budget.limits.integer_bits:
                    space.budget.fail('integer parsing size limit')

            function = {'int': int, 'float': float, 'complex': complex}[name]
            self._push(space.native(function, *args, **kwargs))

        elif name == 'bytes':
            self._arity(name, args, kwargs, 0, 1)

            if not args:
                self._push(b'')

            elif type(args[0]) is bytes:
                self._push(args[0])

            elif type(args[0]) in (int, bool):
                count = space.index(args[0])
                self._budget.size(count, string=True)
                self._budget.allocate(max(0, count))
                self._push(space.native(bytes, count))

            else:
                self._add('construct_bytes', env)
                self._collect(env, args[0])

        elif name == 'range':
            self._arity(name, args, kwargs, 1, 3)
            numbers = tuple(space.index(v) for v in args)

            if len(numbers) == 1:
                start, stop, step = 0, numbers[0], 1
            elif len(numbers) == 2:
                start, stop, step = *numbers, 1
            else:
                start, stop, step = numbers

            if step == 0:
                space.error('ValueError', 'range() arg 3 must not be zero')

            self._push(space.new('range', RangeData(start, stop, step)))

        elif name == 'slice':
            self._arity(name, args, kwargs, 1, 3)
            parts = (None, args[0], None) if len(args) == 1 else (*args, None) if len(args) == 2 else args
            self._push(space.new('slice', parts))

        elif name == 'type':
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.type_of(args[0]))

        else:
            space.error('TypeError', name + ' cannot be constructed directly')

    def _task_numeric_constructed(self, task: Task) -> None:
        value = self._pop()
        expected = {'int': int, 'float': float, 'complex': complex}[task.data]

        if type(value) is not expected:
            self._space.error('TypeError', 'numeric conversion returned the wrong type')

        self._push(value)

    def _task_construct_collection(self, task: Task) -> None:
        value = self._pop()

        if task.data == 'list':
            self._push(value)

        elif task.data == 'tuple':
            self._push(self._space.new('tuple', tuple(self._space.data(value))))

        else:
            result = {}
            for item in self._space.data(value):
                result[self._space.key(item)] = item
            self._push(self._space.new(task.data, result))

    def _task_construct_bytes(self, task: Task) -> None:
        values = self._space.data(self._pop())

        self._budget.size(len(values), string=True)
        self._push(self._space.native(bytes, [self._space.index(v) for v in values]))

    def _isinstance(
            self,
            value: Value,
            classes: Value,
            *,
            subclass: bool = False,
    ) -> bool:
        space = self._space
        cls = value if subclass else space.type_of(value)
        if subclass and space.kind(cls) not in ('type', 'class'):
            space.error('TypeError', 'issubclass first argument must be a class')

        todo = [classes]

        while todo:
            self._budget.tick()
            base = todo.pop()
            kind = space.kind(base)

            if kind == 'tuple':
                todo.extend(reversed(space.data(base)))

            elif kind not in ('type', 'class'):
                space.error('TypeError', 'class information must be a class or tuple of classes')

            elif space.subclass(cls, base):
                return True

        return False

    def _builtin(
            self,
            env: Environment,
            info: BuiltinData,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space
        name = info.name

        if name in ('exception_init', 'exception_init_bound'):
            self._arity(name, args, kwargs, 1 if name == 'exception_init' else 0, None)
            value = args[0] if name == 'exception_init' else info.receiver

            if space.kind(value) != 'exception':
                space.error('TypeError', 'exception initializer requires a guest exception')
            if name == 'exception_init' and not space.subclass(space.data(value).cls, info.receiver):
                space.error('TypeError', 'exception initializer received an unrelated exception')

            values = args[1:] if name == 'exception_init' else args
            self._runtime.replace(value, dc.replace(space.data(value), args=values))
            self._push(None)
            return

        if info.receiver is not _MISSING:
            self._method(env, info, args, kwargs)
            return

        if name in ('len', 'repr', 'ascii', 'iter', 'next', 'format'):
            self._arity(name, args, kwargs, 1, 2 if name in ('iter', 'next', 'format') else 1)

            if name == 'iter' and len(args) == 2:
                self._push(space.new('adapter', AdapterData('sentinel', (), args[0], extra=args[1])))

            elif name == 'next':
                if len(args) == 2:
                    self._add('default_next_guard', env, data=args[1])
                self._operation('next', env, args[0])

            elif name == 'format':
                self._operation('format', env, args[0], args[1] if len(args) == 2 else '')

            else:
                self._operation(name, env, args[0])

        elif name in ('getattr', 'hasattr'):
            self._arity(name, args, kwargs, 2, 3 if name == 'getattr' else 2)

            if name == 'hasattr' or len(args) == 3:
                self._add('hasattr_guard', env, data=(False if name == 'hasattr' else args[2], name == 'hasattr'))

            self._operation('getattr', env, args[0], args[1])

        elif name in ('setattr', 'delattr'):
            count = 3 if name == 'setattr' else 2
            self._arity(name, args, kwargs, count, count)
            space.set_attribute(args[0], args[1], args[2] if len(args) == 3 else None, delete=name == 'delattr')
            self._push(None)

        elif name in ('isinstance', 'issubclass'):
            self._arity(name, args, kwargs, 2, 2)
            self._push(self._isinstance(*args, subclass=name == 'issubclass'))

        elif name == 'callable':
            self._arity(name, args, kwargs, 1, 1)
            value = args[0]
            self._push(
                space.kind(value) in ('type', 'class', 'function', 'builtin', 'bound_method', 'capability') or
                space.special(value, '__call__') is not _MISSING
            )

        elif name in ('globals', 'locals', 'vars'):
            self._arity(name, args, kwargs, 0, 1 if name == 'vars' else 0)

            if args:
                self._operation('getattr', env, args[0], '__dict__')

            elif name == 'globals':
                self._push(env.globals)

            elif env.scope.kind in ('function', 'comprehension'):
                self._push(space.new('namespace', dict(space.data(env.namespace))))

            else:
                self._push(env.namespace)

        elif name == 'id':
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.identity_number(args[0]))

        elif name == 'hash':
            self._arity(name, args, kwargs, 1, 1)
            self._push(hash(space.key(args[0])))

        elif name in ('staticmethod', 'classmethod'):
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.new(name, args[0]))

        elif name in ('chr', 'ord', 'bin', 'oct', 'hex'):
            self._arity(name, args, kwargs, 1, 1)

            if name == 'ord':
                if type(args[0]) not in (str, bytes):
                    space.error('TypeError', 'ord expects a string or bytes')
                self._push(space.native(ord, args[0]))

            else:
                self._push(space.native({'chr': chr, 'bin': bin, 'oct': oct, 'hex': hex}[name], space.index(args[0])))

        elif name in ('abs', 'round'):
            self._arity(name, args, kwargs, 1, 2 if name == 'round' else 1)
            method = space.special(args[0], '__' + name + '__')

            if method is not _MISSING:
                self._invoke(env, method, args[1:])

            elif type(args[0]) in _NUMBERS:
                if len(args) == 2:
                    space.index(args[1])
                self._push(space.native(abs if name == 'abs' else round, *args))

            else:
                space.error('TypeError', 'invalid numeric operand')

        elif name == 'pow':
            self._arity(name, args, kwargs, 2, 3)

            if len(args) == 2 or args[2] is None:
                self._operation('binary:Pow', env, *args[:2])

            else:
                numbers = tuple(space.index(v) for v in args)
                work = max(1, abs(numbers[2]).bit_length()) ** 2 * max(1, abs(numbers[1]).bit_length())
                self._budget.tick(max(1, work // 1024))
                self._push(space.native(pow, *numbers))

        elif name == 'divmod':
            self._arity(name, args, kwargs, 2, 2)

            if any(type(v) not in _NUMBERS for v in args):
                space.error('TypeError', 'divmod requires intrinsic numeric values')

            self._push(space.import_value(space.native(divmod, *args)))

        elif name in ('enumerate', 'zip', 'map', 'filter', 'reversed'):
            if name == 'enumerate':
                self._arity(name, args, kwargs, 1, 2, frozenset({'start'}))

                if len(args) == 2 and 'start' in kwargs:
                    space.error('TypeError', 'multiple values for start')

                index = space.index(args[1] if len(args) == 2 else kwargs.get('start', 0))
                state, inputs = AdapterData(name, (), index=index), args[:1]

            elif name == 'zip':
                self._arity(name, args, kwargs, 0, None, frozenset({'strict'}))

                if type(kwargs.get('strict', False)) is not bool:
                    space.error('TypeError', 'this implementation requires a bool strict flag')

                state, inputs = AdapterData(name, (), strict=kwargs.get('strict', False)), args

            elif name in ('map', 'filter'):
                self._arity(name, args, kwargs, 2, 2 if name == 'filter' else None)
                state, inputs = AdapterData(name, (), args[0]), args[1:]

            else:
                self._arity(name, args, kwargs, 1, 1)

                method = space.special(args[0], '__reversed__')
                if method is not _MISSING:
                    self._invoke(env, method, ())
                    return

                if space.kind(args[0]) not in ('list', 'tuple', 'str', 'bytes', 'range'):
                    space.error('TypeError', 'reversed requires an intrinsic sequence or __reversed__')

                self._push(space.new('adapter', AdapterData(name, (), index=space.length(args[0]) - 1, extra=args[0])))
                return

            self._add('adapter_iterators', env, data=(state, inputs, 0))

        elif name in ('sum', 'all', 'any', 'min', 'max'):
            minimum = 1
            maximum = 2 if name == 'sum' else 1 if name in ('all', 'any') else None

            allowed = (
                frozenset({'start'}) if name == 'sum' else
                frozenset({'key', 'default'}) if name in ('min', 'max') else frozenset()
            )

            self._arity(name, args, kwargs, minimum, maximum, allowed)

            if name in ('min', 'max') and len(args) > 1:
                if 'default' in kwargs:
                    space.error('TypeError', 'default is only valid with a single iterable')
                iterable = space.new('tuple', args)

            else:
                iterable = args[0]

            if name == 'sum' and len(args) == 2 and 'start' in kwargs:
                space.error('TypeError', 'multiple values for start')

            initial = (args[1] if len(args) == 2 else kwargs.get('start', 0)) if name == 'sum' else _MISSING
            if name == 'sum' and type(initial) in (str, bytes):
                space.error('TypeError', 'sum cannot concatenate strings')

            state = ReductionState(
                name,
                None,
                initial,
                _MISSING,
                kwargs.get('key'),
                kwargs.get('default', _MISSING),
            )

            self._add('reduction_iterator', env, data=state)
            self._operation('iter', env, iterable)

        elif name == 'sorted':
            self._arity(name, args, kwargs, 1, 1, frozenset({'key', 'reverse'}))
            self._add('sort_reverse', env, data=(args[0], kwargs.get('key')))
            self._operation('truth', env, kwargs.get('reverse', False))

        else:
            raise InterpreterError('unimplemented registered builtin: ' + name)

    def _task_hasattr_guard(self, task: Task) -> None:
        if task.data[1]:
            self._pop()
            self._push(True)

    def _method(
            self,
            env: Environment,
            info: BuiltinData,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        kind, name = info.name.split('.', 1)
        value, space = info.receiver, self._space

        if kind == 'generator':
            if kwargs:
                space.error('TypeError', 'generator methods do not accept keywords')
            self._generator_method(env, value, name, args)
            return

        if kind in ('iterator', 'adapter'):
            self._arity(name, args, kwargs, 0, 0)
            if name == '__iter__':
                self._push(value)
            else:
                self._operation('next', env, value)
            return

        if kind in ('str', 'bytes'):
            self._string_method(env, value, name, args, kwargs)
            return

        if kind == 'range':
            self._arity(name, args, kwargs, 1, 1)

            if type(args[0]) not in _SCALARS:
                space.error('TypeError', 'range method requires intrinsic data')
            data = space.data(value)
            seq = range(data.start, data.stop, data.step)

            # Avoid native linear fallback for non-integral objects and enormous ranges.
            if type(args[0]) not in (int, bool):
                space.error('TypeError', 'range methods currently require an integer')

            self._push(space.native(range.count if name == 'count' else range.index, seq, args[0]))
            return

        if name in ('copy', 'clear', 'reverse'):
            self._arity(name, args, kwargs, 0, 0)
            data = space.data(value)

            if name == 'copy':
                if kind == 'frozenset':
                    self._push(value)
                else:
                    self._push(space.new(kind, data.copy()))

            elif name == 'clear':
                self._runtime.replace(value, [] if kind == 'list' else {})
                self._push(None)

            else:
                self._runtime.replace(value, list(reversed(data)))
                self._push(None)

            return

        if kind == 'list' and name == 'append':
            self._arity(name, args, kwargs, 1, 1)
            space.append(value, args[0])
            self._push(None)

        elif kind in ('list', 'set') and name in ('extend', 'update'):
            self._arity(name, args, kwargs, 1, 1)
            self._add('extend_iterator', env, data=value)
            source = args[0]
            if kind == 'list' and space.identical(value, source):
                source = space.new('tuple', tuple(space.data(value)))
            self._operation('iter', env, source)

        elif kind == 'list' and name == 'insert':
            self._arity(name, args, kwargs, 2, 2)
            index = space.index(args[0])
            length = space.length(value)
            index = max(0, length + index) if index < 0 else min(index, length)
            self._budget.size(length + 1)
            self._budget.allocate(1)
            self._runtime.write(value, slice(index, index), [args[1]])
            self._push(None)

        elif kind == 'list' and name == 'pop':
            self._arity(name, args, kwargs, 0, 1)
            index = space.index(args[0]) if args else -1
            item = space.get_item(value, index)
            space.set_item(value, index, None, delete=True)
            self._push(item)

        elif kind in ('list', 'tuple') and name in ('count', 'index', 'remove'):
            self._arity(name, args, kwargs, 1, 3 if name == 'index' else 1)
            length = space.length(value)
            start = space.index(args[1]) if len(args) > 1 else 0
            stop = space.index(args[2]) if len(args) > 2 else length
            start = max(0, start + length) if start < 0 else start
            stop = max(0, stop + length) if stop < 0 else stop
            self._add('sequence_search', env, data=(value, name, args[0], start, stop, 0))

        elif kind in ('dict', 'namespace'):
            self._mapping_method(env, value, name, args, kwargs)

        elif kind == 'set' and name in ('add', 'discard', 'remove'):
            self._arity(name, args, kwargs, 1, 1)
            token = space.key(args[0])
            if name == 'add':
                space.set_item(value, args[0], None)
            elif token in space.data(value):
                space.set_item(value, args[0], None, delete=True)
            elif name == 'remove':
                space.error('KeyError', args[0])
            self._push(None)

        elif kind == 'set' and name == 'pop':
            self._arity(name, args, kwargs, 0, 0)
            data = space.data(value)
            if not data:
                space.error('KeyError', 'pop from an empty set')
            key = next(iter(data))
            item = data[key]
            self._runtime.delete(value, key)
            self._push(item)

        else:
            raise InterpreterError('unimplemented registered method: ' + info.name)

    def _task_extend_iterator(self, task: Task) -> None:
        self._add('extend_next', task.env, data=(task.data, self._pop()))

    def _task_extend_next(self, task: Task) -> None:
        target, iterator = task.data
        self._pull(task.env, iterator, Task('extend_value', task.env, data=task.data), Task('extend_stop', task.env))

    def _task_extend_value(self, task: Task) -> None:
        target, iterator = task.data
        value = self._pop()
        if self._space.kind(target) == 'list':
            self._space.append(target, value)
        else:
            self._space.set_item(target, value, None)
        self._add('extend_next', task.env, data=task.data)

    def _task_extend_stop(self, task: Task) -> None:
        self._pop()
        self._push(None)

    def _task_sequence_search(self, task: Task) -> None:
        ref, name, sought, index, stop, count = task.data

        if index >= min(stop, self._space.length(ref)):
            if name == 'count':
                self._push(count)
            else:
                self._space.error('ValueError', 'value is not in sequence')

            return

        self._add('sequence_search_comparison', task.env, data=task.data)

        value = self._space.get_item(ref, index)
        if self._space.identical(value, sought):
            self._push(True)
        else:
            self._operation('compare:Eq', task.env, value, sought)

    def _task_sequence_search_comparison(self, task: Task) -> None:
        self._add('sequence_search_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_sequence_search_test(self, task: Task) -> None:
        ref, name, sought, index, stop, count = task.data
        matches = self._pop()

        if matches and name != 'count':
            if name == 'remove':
                self._space.set_item(ref, index, None, delete=True)
                self._push(None)

            else:
                self._push(index)

        else:
            self._add('sequence_search', task.env, data=(ref, name, sought, index + 1, stop, count + int(matches)))

    def _mapping_method(
            self,
            env: Environment,
            ref: ObjectRef,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space

        if name in ('get', 'pop', 'setdefault'):
            self._arity(name, args, kwargs, 1, 2)

            try:
                value = space.get_item(ref, args[0])

            except _GuestRaise as exc:
                if not space.exception_matches(exc.value, space.types['KeyError']):
                    raise

                if name == 'pop' and len(args) == 1:
                    raise

                value = args[1] if len(args) == 2 else None
                if name == 'setdefault':
                    space.set_item(ref, args[0], value)

            else:
                if name == 'pop':
                    space.set_item(ref, args[0], None, delete=True)

            self._push(value)

        elif name == 'popitem':
            self._arity(name, args, kwargs, 0, 0)

            pairs = space.mapping_pairs(ref)
            if not pairs:
                space.error('KeyError', 'popitem(): dictionary is empty')

            key, item = pairs[-1]
            space.set_item(ref, key, None, delete=True)
            self._push(space.new('tuple', (key, item)))

        elif name in ('keys', 'values', 'items'):
            self._arity(name, args, kwargs, 0, 0)
            self._push(space.new('dict_view', (ref, name)))

        elif name == 'update':
            self._arity(name, args, {}, 0, 1)
            self._update_mapping(env, ref, args[0] if args else None, kwargs, None)

        else:
            raise InterpreterError('unknown mapping method')

    def _update_mapping(
            self,
            env: Environment,
            target: ObjectRef,
            source: Value,
            keywords: ta.Mapping[str, Value],
            result: Value,
    ) -> None:
        self._add('mapping_update_keywords', env, data=(target, tuple(keywords.items()), result))

        if source is None:
            return

        if self._space.kind(source) in ('dict', 'namespace'):
            for key, value in self._space.mapping_pairs(source):
                self._budget.tick()
                self._space.set_item(target, key, value)

        else:
            self._add('mapping_update_iterator', env, data=target)
            self._operation('iter', env, source)

    def _task_mapping_update_keywords(self, task: Task) -> None:
        target, pairs, result = task.data

        for key, value in pairs:
            self._budget.tick()
            self._space.set_item(target, key, value)

        self._push(result)

    def _task_mapping_update_iterator(self, task: Task) -> None:
        self._add('mapping_update_next', task.env, data=(task.data, self._pop()))

    def _task_mapping_update_next(self, task: Task) -> None:
        target, iterator = task.data

        self._pull(
            task.env, iterator,
            Task('mapping_update_item', task.env, data=task.data),
            Task('mapping_update_stop', task.env),
        )

    def _task_mapping_update_item(self, task: Task) -> None:
        self._add('mapping_update_pair', task.env, data=task.data)
        self._collect(task.env, self._pop(), 3)

    def _task_mapping_update_pair(self, task: Task) -> None:
        pair = self._space.data(self._pop())
        if len(pair) != 2:
            self._space.error('ValueError', 'dictionary update element must have length 2')

        self._space.set_item(task.data[0], pair[0], pair[1])
        self._add('mapping_update_next', task.env, data=task.data)

    def _task_mapping_update_stop(self, task: Task) -> None:
        self._pop()

    def _string_method(
            self,
            env: Environment,
            value: Value,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space

        if name == 'join':
            self._arity(name, args, kwargs, 1, 1)
            self._add('string_join', env, data=value)
            self._collect(env, args[0])
            return

        if kwargs:
            space.error('TypeError', 'string method keyword arguments are not supported')

        exported = []

        for arg in args:
            if space.kind(arg) == 'tuple':
                parts = space.data(arg)
                if any(type(v) not in (str, bytes) for v in parts):
                    space.error('TypeError', 'string argument tuple must contain strings')
                exported.append(tuple(parts))

            elif type(arg) in (type(None), bool, int, str, bytes):
                exported.append(arg)

            else:
                space.error('TypeError', 'string methods accept only intrinsic data')

        self._budget.tick(len(value) // 64 + 1)
        if name in ('upper', 'lower', 'casefold', 'capitalize', 'title', 'swapcase'):
            self._budget.size(len(value) * 3, string=True)

        if name == 'replace' and len(exported) in (2, 3) and type(value) is str:
            old, new = exported[:2]
            if type(old) is str and type(new) is str:
                count = str.count(value, old)
                if len(exported) == 3:
                    count = min(count, exported[2]) if type(exported[2]) in (bool, int) and exported[2] >= 0 else count
                estimate = len(value) + max(0, len(new) - len(old)) * count
                self._budget.size(estimate, string=True)

        if name in ('split', 'rsplit', 'splitlines'):
            # Conservative preflight: avoids allocating an unbounded number of substrings in one host call.
            self._budget.size(len(value) + 1)

        primitive_type = str if type(value) is str else bytes

        # This lookup is constrained by the immutable method allowlist and an exact primitive receiver.
        if name not in space._METHODS[primitive_type.__name__]:
            raise InterpreterError('string method was not whitelisted')

        method = vars(primitive_type)[name]
        result = space.native(method, value, *exported)
        self._push(space.import_value(result))

    def _task_string_join(self, task: Task) -> None:
        values = self._space.data(self._pop())

        if any(type(v) is not str for v in values):
            self._space.error('TypeError', 'str.join requires strings')

        size = sum(map(len, values)) + max(0, len(values) - 1) * len(task.data)

        self._budget.size(size, string=True)
        self._budget.allocate(size)
        self._push(str.join(task.data, values))

    def _task_adapter_iterators(self, task: Task) -> None:
        state, inputs, index = task.data

        if index == len(inputs):
            self._push(self._space.new('adapter', state))
        else:
            self._add('adapter_iterator_value', task.env, data=task.data)
            self._operation('iter', task.env, inputs[index])

    def _task_adapter_iterator_value(self, task: Task) -> None:
        state, inputs, index = task.data
        state = dc.replace(state, iterators=(*state.iterators, self._pop()))

        self._add('adapter_iterators', task.env, data=(state, inputs, index + 1))

    def _adapter_stop(self, ref: ObjectRef) -> ta.NoReturn:
        self._runtime.replace(ref, dc.replace(self._space.data(ref), exhausted=True))
        self._space.error('StopIteration')

    def _adapter_next(self, env: Environment, ref: ObjectRef) -> None:
        info = self._space.data(ref)

        if info.exhausted:
            self._space.error('StopIteration')

        if info.kind == 'reversed':
            if info.index < 0 or info.index >= self._space.length(info.extra):
                self._adapter_stop(ref)
            value = self._space.get_item(info.extra, info.index)
            self._runtime.replace(ref, dc.replace(info, index=info.index - 1))
            self._push(value)

        elif info.kind == 'sentinel':
            self._add('sentinel_value', env, data=ref)
            self._invoke(env, info.function, ())

        else:
            if not info.iterators:
                self._adapter_stop(ref)
            self._add('adapter_pull', env, data=(ref, (), 0))

    def _task_adapter_pull(self, task: Task) -> None:
        ref, row, index = task.data
        info = self._space.data(ref)

        if index == len(info.iterators):
            if info.kind == 'enumerate':
                self._runtime.replace(ref, dc.replace(info, index=self._budget.scalar(info.index + 1)))
                self._push(self._space.new('tuple', (info.index, row[0])))

            elif info.kind == 'zip':
                self._push(self._space.new('tuple', row))

            elif info.kind == 'map':
                self._invoke(task.env, info.function, row)

            elif info.kind == 'filter':
                self._add('filter_value', task.env, data=(ref, row[0]))
                if info.function is None:
                    self._push(row[0])
                else:
                    self._invoke(task.env, info.function, (row[0],))

            return

        self._pull(
            task.env, info.iterators[index],
            Task('adapter_item', task.env, data=task.data),
            Task('adapter_exhausted', task.env, data=task.data),
        )

    def _task_adapter_item(self, task: Task) -> None:
        ref, row, index = task.data

        self._add('adapter_pull', task.env, data=(ref, (*row, self._pop()), index + 1))

    def _task_adapter_exhausted(self, task: Task) -> None:
        self._pop()

        ref, row, index = task.data
        info = self._space.data(ref)

        if info.strict:
            if index:
                self._space.error('ValueError', 'zip arguments have different lengths')
            self._add('zip_probe', task.env, data=(ref, 1))
        else:
            self._adapter_stop(ref)

    def _task_zip_probe(self, task: Task) -> None:
        ref, index = task.data
        info = self._space.data(ref)

        if index == len(info.iterators):
            self._adapter_stop(ref)

        self._pull(
            task.env, info.iterators[index],
            Task('zip_too_long', task.env),
            Task('zip_probe_stop', task.env, data=(ref, index + 1)),
        )

    def _task_zip_probe_stop(self, task: Task) -> None:
        self._pop()
        self._add('zip_probe', task.env, data=task.data)

    def _task_zip_too_long(self, task: Task) -> None:
        self._pop()
        self._space.error('ValueError', 'zip arguments have different lengths')

    def _task_filter_value(self, task: Task) -> None:
        self._add('filter_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_filter_test(self, task: Task) -> None:
        ref, value = task.data

        if self._pop():
            self._push(value)
        else:
            self._operation('next', task.env, ref)

    def _task_sentinel_value(self, task: Task) -> None:
        value = self._pop()

        self._add('sentinel_comparison', task.env, data=(task.data, value))
        self._operation('compare:Eq', task.env, self._space.data(task.data).extra, value)

    def _task_sentinel_comparison(self, task: Task) -> None:
        self._add('sentinel_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_sentinel_test(self, task: Task) -> None:
        ref, value = task.data

        if self._pop():
            self._adapter_stop(ref)
        self._push(value)

    def _task_reduction_iterator(self, task: Task) -> None:
        self._add('reduction_next', task.env, data=dc.replace(task.data, iterator=self._pop()))

    def _task_reduction_next(self, task: Task) -> None:
        self._pull(
            task.env, task.data.iterator,
            Task('reduction_item', task.env, data=task.data),
            Task('reduction_stop', task.env, data=task.data),
        )

    def _task_reduction_item(self, task: Task) -> None:
        value = self._pop()
        state = task.data

        if state.name in ('all', 'any'):
            self._add('reduction_truth', task.env, data=state)
            self._operation('truth', task.env, value)

        elif state.name == 'sum':
            self._add('reduction_sum', task.env, data=state)
            self._operation('binary:Add', task.env, state.value, value)

        else:
            self._add('reduction_key', task.env, data=(state, value))
            if state.key is None:
                self._push(value)
            else:
                self._invoke(task.env, state.key, (value,))

    def _task_reduction_truth(self, task: Task) -> None:
        value = self._pop()

        if value == (task.data.name == 'any'):
            self._push(value)
        else:
            self._add('reduction_next', task.env, data=task.data)

    def _task_reduction_sum(self, task: Task) -> None:
        self._add('reduction_next', task.env, data=dc.replace(task.data, value=self._pop()))

    def _task_reduction_key(self, task: Task) -> None:
        state, value = task.data
        key = self._pop()

        if state.value is _MISSING:
            self._add('reduction_next', task.env, data=dc.replace(state, value=value, value_key=key))

        else:
            self._add('reduction_comparison', task.env, data=(state, value, key))
            self._operation('compare:' + ('Lt' if state.name == 'min' else 'Gt'), task.env, key, state.value_key)

    def _task_reduction_comparison(self, task: Task) -> None:
        self._add('reduction_selected', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_reduction_selected(self, task: Task) -> None:
        state, value, key = task.data

        if self._pop():
            state = dc.replace(state, value=value, value_key=key)
        self._add('reduction_next', task.env, data=state)

    def _task_reduction_stop(self, task: Task) -> None:
        self._pop()

        state = task.data

        if state.name in ('all', 'any'):
            self._push(state.name == 'all')

        elif state.value is not _MISSING:
            self._push(state.value)

        elif state.default is not _MISSING:
            self._push(state.default)

        else:
            self._space.error('ValueError', state.name + '() iterable is empty')

    def _task_sort_reverse(self, task: Task) -> None:
        source, key = task.data

        self._add('sort_collected', task.env, data=(key, self._pop()))
        self._collect(task.env, source)

    def _task_sort_collected(self, task: Task) -> None:
        source = self._pop()
        key, reverse = task.data

        state = SortState(source, self._space.new('list', []), self._space.new('list', []), key, reverse)

        self._add('sort_key_next', task.env, data=state)

    def _task_sort_key_next(self, task: Task) -> None:
        state = task.data

        if state.index == self._space.length(state.source):
            self._add('sort_next', task.env, data=dc.replace(state, index=0))

        else:
            value = self._space.get_item(state.source, state.index)
            self._add('sort_key_value', task.env, data=(state, value))
            if state.key is None:
                self._push(value)
            else:
                self._invoke(task.env, state.key, (value,))

    def _task_sort_key_value(self, task: Task) -> None:
        state, value = task.data
        pair = self._space.new('tuple', (self._pop(), value))

        self._space.append(state.decorated, pair)
        self._add('sort_key_next', task.env, data=dc.replace(state, index=state.index + 1))

    def _task_sort_next(self, task: Task) -> None:
        state = task.data

        if state.index == self._space.length(state.decorated):
            self._push(self._space.new('list', [self._space.data(p)[1] for p in self._space.data(state.output)]))
        else:
            self._add('sort_search', task.env, data=(state, 0, self._space.length(state.output)))

    def _task_sort_search(self, task: Task) -> None:
        state, low, high = task.data
        pair = self._space.get_item(state.decorated, state.index)

        if low == high:
            self._budget.allocate(1)
            self._runtime.write(state.output, slice(low, low), [pair])
            self._add('sort_next', task.env, data=dc.replace(state, index=state.index + 1))

        else:
            middle = (low + high) // 2
            other = self._space.get_item(state.output, middle)
            self._add('sort_comparison', task.env, data=(state, low, high, middle))
            self._operation(
                'compare:Gt' if state.reverse else 'compare:Lt', task.env,
                self._space.data(pair)[0], self._space.data(other)[0],
            )

    def _task_sort_comparison(self, task: Task) -> None:
        self._add('sort_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_sort_test(self, task: Task) -> None:
        state, low, high, middle = task.data

        if self._pop():
            high = middle
        else:
            low = middle + 1

        self._add('sort_search', task.env, data=(state, low, high))

    def _task_host_resume(self, task: Task) -> None:
        ref, mode, value = task.data

        self._resume_generator(task.env, ref, mode, value)

    def start(self, tasks: ta.Sequence[Task]) -> None:
        thread = self._runtime.edit_thread()
        if not thread.done:
            raise InterpreterError('execution already in progress')
        thread.executions = [Execution(tasks=list(tasks))]
        thread.call_depth = 0
        thread.done = False
        thread.result = None
        thread.error = None

    def step(self) -> bool:
        thread = self._runtime.edit_thread()
        if thread.done:
            return True
        self._thread = thread

        try:
            self._budget.tick()

            execution = self._execution()

            if execution.generator is not None:
                # Explicit write barrier for mutable suspended/active execution records.
                execution = self._runtime.edit_generator(execution.generator).execution
                thread.executions[-1] = execution

            if not execution.tasks:
                if execution.generator is not None:
                    raise InterpreterError('generator lost its end continuation')

                if len(execution.values) > 1:
                    raise InterpreterError('value stack was not balanced')

                thread.result = execution.values.pop() if execution.values else None
                thread.done = True

            else:
                self._task = execution.tasks.pop()

                try:
                    self._handlers[self._task.kind](self._task)
                except _GuestRaise as exc:
                    self._raise(exc.value)

            return thread.done

        finally:
            self._task = None
            self._thread = None


## Intrinsic continuation payloads


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


@dc.dataclass(frozen=True, slots=True)
class SortState:
    source: ObjectRef
    decorated: ObjectRef
    output: ObjectRef
    key: Value
    reverse: bool
    index: int = 0


## Embedding API


class Interpreter:
    def __init__(
            self,
            *,
            runtime: Runtime | None = None,
            limits: Limits | None = None,
            modules: ta.Mapping[str, SourceModule | ta.Mapping[str, object]] | None = None,
    ) -> None:
        super().__init__()

        self._runtime = runtime if runtime is not None else DictRuntime()
        self._budget = Budget(limits)
        self._capabilities = Capabilities()
        self._space = ObjectSpace(self._runtime, self._budget, self._capabilities)
        self._frontend = Frontend(self._budget)
        self._programs: list[Program] = []
        self._machine = Machine(
            self._runtime,
            self._space,
            self._frontend,
            self._programs,
            dict(modules or {}),
        )
        self._globals = self._space.new('namespace', {'__name__': '__main__'})
        self._busy = False
        self._poisoned = False

    @property
    def done(self) -> bool:
        return self._runtime.read_thread().done

    @property
    def steps_used(self) -> int:
        return self._budget.steps

    def _check_host_entry(self) -> None:
        if self._busy:
            raise InterpreterError('interpreter is non-reentrant')
        if self._poisoned:
            raise InterpreterError('interpreter aborted; create a fresh instance')

    def _environment(self, program: Program) -> Environment:
        scope = program.scopes.get(program.tree, Scope('module', frozenset(), frozenset(), frozenset()))
        return Environment(program, scope, self._globals, self._globals)

    def _host_environment(self) -> Environment:
        if not self._programs:
            self.prepare('')
        return self._environment(self._programs[0])

    def _check_error(self) -> None:
        error = self._runtime.read_thread().error
        if error is not None:
            raise GuestError(
                self._space.exception_name(error),
                self._space.representation(error, string=True),
                error,
            )

    def _snapshot_memo(self) -> dict[int, object]:
        # AST identity indexes scope metadata. Programs are immutable trusted code, not mutable guest state.
        memo: dict[int, object] = {}
        for program in self._programs:
            memo[id(program)] = program
            for node in ast.walk(program.tree):
                memo[id(node)] = node
        return memo

    def prepare(
            self,
            source: str,
            *,
            filename: str = '<guest>',
            expression: bool = False,
    ) -> Program:
        self._check_host_entry()
        program = self._frontend.prepare(
            source,
            filename=filename,
            expression=expression,
        )
        self._programs.append(program)
        return program

    def start(
            self,
            source: str | Program,
            *,
            filename: str = '<guest>',
    ) -> None:
        self._check_host_entry()

        program = self.prepare(source, filename=filename) if type(source) is str else source
        if type(program) is not Program:
            raise TypeError('expected source text or a prepared Program')
        if not self._programs or self._programs[-1] is not program:
            if not any(existing is program for existing in self._programs):
                self._programs.append(program)

        env = self._environment(program)

        if isinstance(program.tree, ast.Expression):
            tasks = [Task('eval', env, program.tree.body)]
        else:
            tasks = [Task('exec', env, node) for node in reversed(program.tree.body)]

        self._machine.start(tasks)

    def step(self, count: int = 1) -> bool:
        self._check_host_entry()

        if type(count) is not int or count < 0:
            raise ValueError('step count must be a nonnegative integer')

        self._busy = True
        try:
            for _ in range(count):
                if self._machine.step():
                    break

        except Exception:
            self._poisoned = True
            raise

        finally:
            self._busy = False

        if self.done:
            self._check_error()

        return self.done

    def run(self) -> Value:
        self._check_host_entry()

        while not self.done:
            self.step()

        self._check_error()

        return self._runtime.read_thread().result

    def execute(
            self,
            source: str | Program,
            *,
            filename: str = '<guest>',
    ) -> None:
        self.start(source, filename=filename)
        self.run()

    def evaluate_value(
            self,
            source: str,
            *,
            filename: str = '<guest>',
    ) -> Value:
        program = self.prepare(
            source,
            filename=filename,
            expression=True,
        )
        self.start(program)
        return self.run()

    def evaluate(
            self,
            source: str,
            *,
            filename: str = '<guest>',
    ) -> object:
        return self.export(self.evaluate_value(source, filename=filename))

    def get_value(self, name: str) -> Value:
        self._check_host_entry()
        return self._space.data(self._globals)[name]

    def get(self, name: str) -> object:
        return self.export(self.get_value(name))

    def set(self, name: str, value: object) -> None:
        self._check_host_entry()

        if type(name) is not str:
            raise TypeError('name must be a string')

        self._runtime.write(self._globals, name, self._space.import_value(value))

    def export(self, value: Value) -> object:
        self._check_host_entry()

        return self._space.export_value(value)

    def grant(self, name: str, callback: ta.Callable[..., object] | HostCall) -> None:
        self._check_host_entry()

        if type(name) is not str:
            raise TypeError('name must be a string')

        value = self._space.new('capability', self._capabilities.register(callback))

        self._runtime.write(self._globals, name, value)

    def grant_object(self, name: str, obj: HostObject) -> None:
        self._check_host_entry()

        if type(name) is not str or type(obj) is not HostObject:
            raise TypeError('expected a name and an explicit HostObject method table')

        self._runtime.write(self._globals, name, self._space.import_value(obj, capabilities=True))

    def call_value(
            self,
            function: Value,
            args: ta.Sequence[Value] = (),
            kwargs: ta.Mapping[str, Value] | None = None,
    ) -> Value:
        self._check_host_entry()

        self._space.kind(function)
        for value in [*args, *(kwargs or {}).values()]:
            self._space.kind(value)

        task = Task(
            'invoke',
            self._host_environment(),
            data=(
                function,
                tuple(args),
                dict(kwargs or {}),
            ),
        )

        self._machine.start([task])

        return self.run()

    def call(
            self,
            function: Value,
            *args: object,
            **kwargs: object,
    ) -> object:
        self._check_host_entry()

        memo = {}

        imported_args = tuple(self._space.import_value(v, memo=memo) for v in args)
        imported_kwargs = {k: self._space.import_value(v, memo=memo) for k, v in kwargs.items()}

        return self.export(self.call_value(function, imported_args, imported_kwargs))

    def resume_value(
            self,
            generator: ObjectRef,
            *,
            mode: str = 'next',
            value: Value = None,
    ) -> Value:
        self._check_host_entry()

        if self._space.kind(generator) != 'generator' or mode not in ('next', 'send', 'throw', 'close'):
            raise ValueError('invalid generator resume request')
        self._space.kind(value)
        if mode == 'throw' and self._space.kind(value) != 'exception':
            raise ValueError('throw requires a guest exception instance')

        task = Task(
            'host_resume',
            self._host_environment(),
            data=(generator, mode, value),
        )

        self._machine.start([task])

        return self.run()

    def checkpoint(self) -> Checkpoint:
        self._check_host_entry()
        return self._runtime.checkpoint(self._snapshot_memo())

    def restore(self, checkpoint: Checkpoint) -> None:
        self._check_host_entry()
        self._runtime.restore(checkpoint, self._snapshot_memo())
