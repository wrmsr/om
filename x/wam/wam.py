"""
A compact, programmable Warren Abstract Machine.

The public surface is a Python DSL rather than a Prolog parser::

    program = Program() edge = program.relation('edge', 2) path = program.relation('path', 2) x, y, z = variables('x y
    z')

    program.fact(edge('a', 'b')) program.fact(edge('b', 'c')) program.rule(path(x, y), edge(x, y)) program.rule(path(x,
    y), edge(x, z), path(z, y))

    assert [solution[y] for solution in program.solve(path('a', y))] == ['b', 'c']

The implementation uses a recognizable WAM core: tagged heap cells, X registers, environment frames, a trail, choice
points, read/write structure unification, first-argument indexing, last-call execution, and deep cut. Source variables
are heap-resident and every clause gets an environment; those two simplifications avoid unsafe-variable and
environment-trimming machinery without changing the search semantics. Textbook switch/try/retry/trust instructions are
fused into immutable predicate indexes and choice-point operations. Unification deliberately omits the occurs check and
therefore supports rational trees.

A deterministic host goal is written ``foreign(fn, *terms)``. The callback receives a ``ForeignContext`` and opaque
``TermRef`` values, reads ground values with ``ctx.value(ref)``, binds with ``ctx.unify(ref, value)``, and returns
success as a boolean. Failed or exceptional callbacks are rolled back transactionally.

The DSL/compiler and the mutable ``_Machine`` core are deliberately separated. The compiled image is immutable, opcodes
and locations are integers, and hot state lives in flat lists, making ``_Machine`` the natural seam for a future C
implementation.
"""
import dataclasses as dc
import enum
import typing as ta


type ForeignFn = ta.Callable[..., bool]
type TraceFn = ta.Callable[[TraceEvent], None]


##


class WamError(Exception):
    pass


class CompileError(WamError):
    pass


class InstantiationError(WamError):
    pass


class StepLimitExceeded(WamError):
    pass


## Terms and goals


@dc.dataclass(frozen=True, slots=True)
class _Nil:
    def __repr__(self) -> str:
        return 'NIL'


NIL = _Nil()


@dc.dataclass(frozen=True, slots=True, eq=False)
class Var:
    name: str = '_'

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise TypeError(self.name)

    def __repr__(self) -> str:
        return self.name


@dc.dataclass(frozen=True, slots=True)
class Struct:
    functor: str
    args: tuple[object, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.functor, str) or not self.functor:
            raise TypeError(self.functor)
        if not isinstance(self.args, tuple):
            raise TypeError(self.args)

    @property
    def arity(self) -> int:
        return len(self.args)

    def __repr__(self) -> str:
        if not self.args:
            return self.functor
        return f'{self.functor}({", ".join(map(repr, self.args))})'


@dc.dataclass(frozen=True, slots=True)
class Relation:
    name: str
    arity: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise TypeError(self.name)
        if not isinstance(self.arity, int) or self.arity < 0:
            raise TypeError(self.arity)

    @property
    def key(self) -> tuple[str, int]:
        return self.name, self.arity

    def __call__(self, *args: object) -> 'Call':
        if len(args) != self.arity:
            raise TypeError(f'{self.name}/{self.arity} got {len(args)} arguments')
        return Call(self, tuple(_normalize_term(arg) for arg in args))

    def __repr__(self) -> str:
        return f'{self.name}/{self.arity}'


@dc.dataclass(frozen=True, slots=True)
class Call:
    relation: Relation
    args: tuple[object, ...]

    def __post_init__(self) -> None:
        if len(self.args) != self.relation.arity:
            raise TypeError(self)

    def __repr__(self) -> str:
        return f'{self.relation.name}({", ".join(map(repr, self.args))})'


@dc.dataclass(frozen=True, slots=True)
class Unify:
    left: object
    right: object


@dc.dataclass(frozen=True, slots=True)
class Foreign:
    function: ForeignFn
    args: tuple[object, ...]
    name: str


@dc.dataclass(frozen=True, slots=True)
class _Cut:
    def __repr__(self) -> str:
        return 'CUT'


@dc.dataclass(frozen=True, slots=True)
class _True:
    def __repr__(self) -> str:
        return 'TRUE'


@dc.dataclass(frozen=True, slots=True)
class _Fail:
    def __repr__(self) -> str:
        return 'FAIL'


CUT = _Cut()
TRUE = _True()
FAIL = _Fail()


@dc.dataclass(frozen=True, slots=True)
class Clause:
    head: Call
    body: tuple[object, ...] = ()


def var(name: str = '_') -> Var:
    return Var(name)


def variables(names: str, /) -> tuple[Var, ...]:
    return tuple(Var(name) for name in names.replace(',', ' ').split())


def struct(functor: str, *args: object) -> Struct:
    return Struct(functor, tuple(_normalize_term(arg) for arg in args))


def cons(head: object, tail: object) -> Struct:
    return struct('.', head, tail)


def llist(*items: object, tail: object = NIL) -> object:
    out = _normalize_term(tail)
    for item in reversed(items):
        out = cons(item, out)
    return out


def unify(left: object, right: object) -> Unify:
    return Unify(_normalize_term(left), _normalize_term(right))


def foreign(function: ForeignFn, *args: object, name: str | None = None) -> Foreign:
    if not callable(function):
        raise TypeError(function)
    return Foreign(
        function,
        tuple(_normalize_term(arg) for arg in args),
        name or getattr(function, '__name__', '<foreign>'),
    )


def guard(function: ta.Callable[..., object], *args: object, name: str | None = None) -> Foreign:
    if not callable(function):
        raise TypeError(function)

    def invoke(ctx: 'ForeignContext', *refs: 'TermRef') -> bool:
        return bool(function(*(ctx.value(ref) for ref in refs)))

    return foreign(invoke, *args, name=name or getattr(function, '__name__', '<guard>'))


def project(result: object, function: ta.Callable[..., object], *args: object, name: str | None = None) -> Foreign:
    if not callable(function):
        raise TypeError(function)

    def invoke(ctx: 'ForeignContext', out: 'TermRef', *refs: 'TermRef') -> bool:
        value = function(*(ctx.value(ref) for ref in refs))
        return ctx.unify(out, value)

    return foreign(invoke, result, *args, name=name or getattr(function, '__name__', '<project>'))


def _normalize_term(value: object) -> object:
    if isinstance(value, Var):
        return value
    if isinstance(value, Struct):
        return Struct(value.functor, tuple(_normalize_term(arg) for arg in value.args))
    if isinstance(value, Call):
        raise TypeError('a relation call is a goal, not a term')
    if isinstance(value, list):
        return llist(*value)
    try:
        hash(value)
    except TypeError as exc:
        raise TypeError(f'logic atoms must be hashable: {value!r}') from exc
    return value


def _normalize_goal(value: object) -> object:
    if isinstance(value, Call):
        return Call(value.relation, tuple(_normalize_term(arg) for arg in value.args))
    if isinstance(value, Unify):
        return unify(value.left, value.right)
    if isinstance(value, Foreign):
        return Foreign(value.function, tuple(_normalize_term(arg) for arg in value.args), value.name)
    if value is CUT or value is TRUE or value is FAIL:
        return value
    raise TypeError(f'not a logic goal: {value!r}')


## Results and foreign calls


@dc.dataclass(frozen=True, slots=True)
class Unbound:
    index: int

    def __repr__(self) -> str:
        return f'_{self.index}'


@dc.dataclass(frozen=True, slots=True)
class Cycle:
    index: int

    def __repr__(self) -> str:
        return f'<cycle {self.index}>'


@dc.dataclass(frozen=True, slots=True)
class ListValue:
    items: tuple[object, ...]
    tail: object


class Solution:
    def __init__(self, items: ta.Iterable[tuple[Var, object]]) -> None:
        super().__init__()

        self._items = tuple(items)
        self._values = dict(self._items)

    def __getitem__(self, key: Var | str) -> object:
        if isinstance(key, Var):
            return self._values[key]
        if isinstance(key, str):
            found = [value for variable, value in self._items if variable.name == key]
            if len(found) != 1:
                raise KeyError(key)
            return found[0]
        raise TypeError(key)

    def __iter__(self) -> ta.Iterator[Var]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def items(self) -> ta.Iterator[tuple[Var, object]]:
        return iter(self._items)

    def as_dict(self, *, names: bool = False) -> dict[object, object]:
        if not names:
            return dict(self._items)
        out: dict[object, object] = {}
        for variable, value in self._items:
            if variable.name in out:
                raise KeyError(f'duplicate query variable name: {variable.name!r}')
            out[variable.name] = value
        return out

    def __repr__(self) -> str:
        return repr({variable.name: value for variable, value in self._items})


@dc.dataclass(frozen=True, slots=True)
class TermRef:
    _address: int


class ForeignContext:
    def __init__(self, machine: '_Machine', captures: list[int]) -> None:
        super().__init__()

        self._machine = machine
        self._captures = captures

    def is_ground(self, ref: TermRef, /) -> bool:
        return self._machine._is_ground(ref._address)

    def value(self, ref: TermRef, /) -> object:
        if not self.is_ground(ref):
            raise InstantiationError(ref)
        return _Reifier(self._machine).reify(ref._address)

    def unify(self, left: TermRef, right: TermRef | object, /) -> bool:
        capture_top = len(self._captures)
        trail_top = len(self._machine._trail)
        heap_top = len(self._machine._heap_tags)

        if isinstance(right, TermRef):
            ok = self._machine._unify(left._address, right._address, self._captures)
        else:
            right_address = self._machine._append_term(_normalize_term(right))
            ok = self._machine._unify(left._address, right_address, self._captures)

        if not ok:
            self._machine._rollback(self._captures, capture_top, trail_top, heap_top)
        return ok


## Bytecode image


class _Tag(enum.IntEnum):
    REF = 0
    STR = 1
    FUN = 2
    CON = 3


class _Mode(enum.IntEnum):
    READ = 0
    WRITE = 1


class _Op(enum.IntEnum):
    ALLOCATE = 0
    GET_CONSTANT = 1
    GET_STRUCTURE = 2
    GET_VALUE = 3
    UNIFY_CONSTANT = 4
    UNIFY_VALUE = 5
    UNIFY_VARIABLE = 6
    PUT_CONSTANT = 7
    PUT_STRUCTURE = 8
    PUT_VALUE = 9
    SET_CONSTANT = 10
    SET_VALUE = 11
    CALL = 12
    EXECUTE = 13
    UNIFY = 14
    FOREIGN = 15
    CUT = 16
    FAIL = 17
    DEALLOCATE = 18
    PROCEED = 19
    YIELD = 20


@dc.dataclass(frozen=True, slots=True)
class _Instruction:
    op: int
    a: object = None
    b: object = None


@dc.dataclass(frozen=True, slots=True)
class _Functor:
    name: str
    arity: int


@dc.dataclass(frozen=True, slots=True)
class _ForeignCode:
    function: ForeignFn
    name: str


@dc.dataclass(frozen=True, slots=True)
class _ClauseCode:
    entry: int
    end: int
    variable_count: int


@dc.dataclass(frozen=True, slots=True)
class _PredicateCode:
    relation: Relation
    clauses: tuple[_ClauseCode, ...]
    all_candidates: tuple[int, ...]
    wildcard_candidates: tuple[int, ...]
    atom_candidates: ta.Mapping[tuple[type, object], tuple[int, ...]]
    structure_candidates: ta.Mapping[int, tuple[int, ...]]


@dc.dataclass(frozen=True, slots=True)
class _Image:
    code: tuple[_Instruction, ...]
    predicates: tuple[_PredicateCode, ...]
    functors: tuple[_Functor, ...]
    foreigns: tuple[_ForeignCode, ...]
    list_functor: int


@dc.dataclass(frozen=True, slots=True)
class _Query:
    image: _Image
    entry: int
    variables: tuple[tuple[Var, int], ...]


## Compilation


def _y(index: int) -> int:
    return ~index


def _is_y(location: int) -> bool:
    return location < 0


def _location_index(location: int) -> int:
    return ~location if location < 0 else location


class _CodeBuilder:
    def __init__(self, image: _Image | None = None) -> None:
        super().__init__()

        if image is None:
            self.code: list[_Instruction] = []
            self.functors: list[_Functor] = []
            self.foreigns: list[_ForeignCode] = []
        else:
            self.code = list(image.code)
            self.functors = list(image.functors)
            self.foreigns = list(image.foreigns)

        self.functor_ids = {(functor.name, functor.arity): i for i, functor in enumerate(self.functors)}
        self.list_functor = self.functor('.', 2)

    def emit(self, op: _Op, a: object = None, b: object = None) -> int:
        address = len(self.code)
        self.code.append(_Instruction(int(op), a, b))
        return address

    def functor(self, name: str, arity: int) -> int:
        key = name, arity
        try:
            return self.functor_ids[key]
        except KeyError:
            out = len(self.functors)
            self.functor_ids[key] = out
            self.functors.append(_Functor(name, arity))
            return out

    def add_foreign(self, goal: Foreign) -> int:
        out = len(self.foreigns)
        self.foreigns.append(_ForeignCode(goal.function, goal.name))
        return out


class _VariableCollector:
    def __init__(self) -> None:
        super().__init__()

        self.variables: list[Var] = []
        self.slots: dict[Var, int] = {}

    def add_term(self, term: object) -> None:
        if isinstance(term, Var):
            if term not in self.slots:
                self.slots[term] = len(self.variables)
                self.variables.append(term)
        elif isinstance(term, Struct):
            for arg in term.args:
                self.add_term(arg)

    def add_goal(self, goal: object) -> None:
        if isinstance(goal, Call):
            for arg in goal.args:
                self.add_term(arg)
        elif isinstance(goal, Unify):
            self.add_term(goal.left)
            self.add_term(goal.right)
        elif isinstance(goal, Foreign):
            for arg in goal.args:
                self.add_term(arg)


class _ClauseCompiler:
    def __init__(
            self,
            builder: _CodeBuilder,
            predicate_ids: ta.Mapping[tuple[str, int], int],
            variable_slots: ta.Mapping[Var, int],
    ) -> None:
        super().__init__()

        self._builder = builder
        self._predicate_ids = predicate_ids
        self._variable_slots = variable_slots
        self._next_temporary = 0

    def _new_temporary(self) -> int:
        out = self._next_temporary
        self._next_temporary += 1
        return out

    def _variable_location(self, variable: Var) -> int:
        return _y(self._variable_slots[variable])

    def _emit_match(self, head: Call) -> None:
        self._next_temporary = head.relation.arity
        pending: list[tuple[Struct, int]] = []

        for register, term in enumerate(head.args):
            if isinstance(term, Var):
                self._builder.emit(_Op.GET_VALUE, self._variable_location(term), register)
            elif isinstance(term, Struct):
                self._builder.emit(_Op.GET_STRUCTURE, self._builder.functor(term.functor, term.arity), register)
                self._emit_unify_args(term, pending)
            else:
                self._builder.emit(_Op.GET_CONSTANT, term, register)

        pending_index = 0
        while pending_index < len(pending):
            term, register = pending[pending_index]
            pending_index += 1
            self._builder.emit(_Op.GET_STRUCTURE, self._builder.functor(term.functor, term.arity), register)
            self._emit_unify_args(term, pending)

    def _emit_unify_args(self, term: Struct, pending: list[tuple[Struct, int]]) -> None:
        for arg in term.args:
            if isinstance(arg, Var):
                self._builder.emit(_Op.UNIFY_VALUE, self._variable_location(arg))
            elif isinstance(arg, Struct):
                temporary = self._new_temporary()
                self._builder.emit(_Op.UNIFY_VARIABLE, temporary)
                pending.append((arg, temporary))
            else:
                self._builder.emit(_Op.UNIFY_CONSTANT, arg)

    def _emit_build(self, term: object, target: int) -> None:
        if isinstance(term, Var):
            self._builder.emit(_Op.PUT_VALUE, self._variable_location(term), target)
            return
        if not isinstance(term, Struct):
            self._builder.emit(_Op.PUT_CONSTANT, term, target)
            return

        arguments: list[tuple[str, object]] = []
        for arg in term.args:
            if isinstance(arg, Struct):
                temporary = self._new_temporary()
                self._emit_build(arg, temporary)
                arguments.append(('value', temporary))
            elif isinstance(arg, Var):
                arguments.append(('value', self._variable_location(arg)))
            else:
                arguments.append(('constant', arg))

        self._builder.emit(_Op.PUT_STRUCTURE, self._builder.functor(term.functor, term.arity), target)
        for kind, value in arguments:
            if kind == 'value':
                self._builder.emit(_Op.SET_VALUE, value)
            else:
                self._builder.emit(_Op.SET_CONSTANT, value)

    def _emit_build_many(self, terms: ta.Sequence[object]) -> None:
        self._next_temporary = len(terms)
        for register, term in enumerate(terms):
            self._emit_build(term, register)

    def _predicate_id(self, relation: Relation) -> int:
        try:
            return self._predicate_ids[relation.key]
        except KeyError as exc:
            raise CompileError(f'unknown relation: {relation!r}') from exc

    def emit_goal(self, goal: object) -> None:
        if goal is TRUE:
            return
        if goal is CUT:
            self._builder.emit(_Op.CUT)
            return
        if goal is FAIL:
            self._builder.emit(_Op.FAIL)
            return
        if isinstance(goal, Call):
            self._emit_build_many(goal.args)
            self._builder.emit(_Op.CALL, self._predicate_id(goal.relation))
            return
        if isinstance(goal, Unify):
            self._emit_build_many((goal.left, goal.right))
            self._builder.emit(_Op.UNIFY, 0, 1)
            return
        if isinstance(goal, Foreign):
            self._emit_build_many(goal.args)
            self._builder.emit(_Op.FOREIGN, self._builder.add_foreign(goal), len(goal.args))
            return
        raise TypeError(goal)

    def emit_clause(self, clause: Clause, variable_count: int) -> _ClauseCode:
        entry = len(self._builder.code)
        self._builder.emit(_Op.ALLOCATE, variable_count)
        self._emit_match(clause.head)

        if clause.body and isinstance(clause.body[-1], Call):
            for goal in clause.body[:-1]:
                self.emit_goal(goal)
            tail = ta.cast(Call, clause.body[-1])
            self._emit_build_many(tail.args)
            self._builder.emit(_Op.DEALLOCATE)
            self._builder.emit(_Op.EXECUTE, self._predicate_id(tail.relation))
        else:
            for goal in clause.body:
                self.emit_goal(goal)
            self._builder.emit(_Op.DEALLOCATE)
            self._builder.emit(_Op.PROCEED)

        return _ClauseCode(entry, len(self._builder.code), variable_count)

    def emit_query(self, goals: ta.Sequence[object], variable_count: int) -> int:
        entry = len(self._builder.code)
        self._builder.emit(_Op.ALLOCATE, variable_count)
        for goal in goals:
            self.emit_goal(goal)
        self._builder.emit(_Op.YIELD)
        return entry


class _ProgramCompiler:
    def __init__(self, program: 'Program') -> None:
        super().__init__()

        self._program = program

    @staticmethod
    def _atom_key(value: object) -> tuple[type, object]:
        return type(value), value

    def _index_key(self, term: object, builder: _CodeBuilder) -> tuple[str, object]:
        if isinstance(term, Var):
            return 'variable', None
        if isinstance(term, Struct):
            return 'structure', builder.functor(term.functor, term.arity)
        return 'atom', self._atom_key(term)

    def compile(self) -> 'Executable':
        relations = tuple(self._program._relations.values())
        predicate_ids = {relation.key: i for i, relation in enumerate(relations)}
        grouped: dict[tuple[str, int], list[Clause]] = {relation.key: [] for relation in relations}
        for clause in self._program._clauses:
            grouped[clause.head.relation.key].append(clause)

        builder = _CodeBuilder()
        predicates: list[_PredicateCode] = []

        for relation in relations:
            clauses = grouped[relation.key]
            clause_codes: list[_ClauseCode] = []
            keys: list[tuple[str, object]] = []

            for clause in clauses:
                collector = _VariableCollector()
                for arg in clause.head.args:
                    collector.add_term(arg)
                for goal in clause.body:
                    collector.add_goal(goal)

                compiler = _ClauseCompiler(builder, predicate_ids, collector.slots)
                clause_codes.append(compiler.emit_clause(clause, len(collector.variables)))
                if relation.arity:
                    keys.append(self._index_key(clause.head.args[0], builder))
                else:
                    keys.append(('variable', None))

            all_candidates = tuple(range(len(clauses)))
            wildcard_candidates = tuple(i for i, key in enumerate(keys) if key[0] == 'variable')
            atom_values = {ta.cast(tuple[type, object], key[1]) for key in keys if key[0] == 'atom'}
            structure_values = {ta.cast(int, key[1]) for key in keys if key[0] == 'structure'}

            atom_candidates = {
                value: tuple(
                    i
                    for i, key in enumerate(keys)
                    if key[0] == 'variable' or (key[0] == 'atom' and key[1] == value)
                )
                for value in atom_values
            }
            structure_candidates = {
                value: tuple(
                    i
                    for i, key in enumerate(keys)
                    if key[0] == 'variable' or (key[0] == 'structure' and key[1] == value)
                )
                for value in structure_values
            }

            predicates.append(_PredicateCode(
                relation,
                tuple(clause_codes),
                all_candidates,
                wildcard_candidates,
                atom_candidates,
                structure_candidates,
            ))

        image = _Image(
            tuple(builder.code),
            tuple(predicates),
            tuple(builder.functors),
            tuple(builder.foreigns),
            builder.list_functor,
        )
        return Executable(image, predicate_ids, builder.functor_ids)


class _QueryCompiler:
    def __init__(self, executable: 'Executable') -> None:
        super().__init__()

        self._executable = executable

    def compile(self, goals: ta.Sequence[object]) -> _Query:
        collector = _VariableCollector()
        for goal in goals:
            collector.add_goal(goal)

        builder = _CodeBuilder(self._executable._image)
        compiler = _ClauseCompiler(builder, self._executable._predicate_ids, collector.slots)
        entry = compiler.emit_query(goals, len(collector.variables))
        image = _Image(
            tuple(builder.code),
            self._executable._image.predicates,
            tuple(builder.functors),
            tuple(builder.foreigns),
            builder.list_functor,
        )
        return _Query(image, entry, tuple((variable, collector.slots[variable]) for variable in collector.variables))


## Machine


@dc.dataclass(frozen=True, slots=True)
class MachineConfig:
    max_steps: int | None = None
    trace: TraceFn | None = None

    def __post_init__(self) -> None:
        if self.max_steps is not None and self.max_steps < 1:
            raise ValueError(self.max_steps)


@dc.dataclass(frozen=True, slots=True)
class TraceEvent:
    step: int
    pc: int
    operation: str
    heap_size: int
    trail_size: int
    choice_depth: int


@dc.dataclass(frozen=True, slots=True)
class _Frame:
    previous: int
    continuation: int
    cut_base: int
    slots: tuple[int, ...]


@dc.dataclass(slots=True)
class _Choice:
    predicate: int
    candidates: tuple[int, ...]
    next_candidate: int
    arguments: tuple[int, ...]
    environment: int
    continuation: int
    heap_top: int
    trail_top: int
    frame_top: int
    base_depth: int


class _Machine:
    def __init__(self, query: _Query, config: MachineConfig) -> None:
        super().__init__()

        self._image = query.image
        self._query = query
        self._config = config

        self._heap_tags: list[int] = []
        self._heap_values: list[object] = []
        self._functors = list(query.image.functors)
        self._functor_ids = {(functor.name, functor.arity): i for i, functor in enumerate(self._functors)}
        self._x: list[int] = []
        self._frames: list[_Frame] = []
        self._trail: list[int] = []
        self._choices: list[_Choice] = []

        self._p = query.entry
        self._cp = -1
        self._e = -1
        self._s = -1
        self._mode = _Mode.READ
        self._pending_cut_base = 0
        self._query_frame = -1
        self._steps = 0

    def _ensure_x(self, index: int) -> None:
        if index >= len(self._x):
            self._x.extend([-1] * (index + 1 - len(self._x)))

    def _set_x(self, index: int, address: int) -> None:
        self._ensure_x(index)
        self._x[index] = address

    def _get_x(self, index: int) -> int:
        self._ensure_x(index)
        address = self._x[index]
        if address < 0:
            raise WamError(f'uninitialized X register: {index}')
        return address

    def _get_location(self, location: int) -> int:
        if not _is_y(location):
            return self._get_x(location)
        if self._e < 0:
            raise WamError('no current environment')
        return self._frames[self._e].slots[_location_index(location)]

    def _alloc(self, tag: _Tag, value: object) -> int:
        address = len(self._heap_tags)
        self._heap_tags.append(int(tag))
        self._heap_values.append(value)
        return address

    def _alloc_ref(self) -> int:
        address = len(self._heap_tags)
        self._heap_tags.append(int(_Tag.REF))
        self._heap_values.append(address)
        return address

    def _alloc_constant(self, value: object) -> int:
        return self._alloc(_Tag.CON, value)

    def _alloc_structure(self, functor: int) -> int:
        structure = self._alloc(_Tag.STR, len(self._heap_tags) + 1)
        self._alloc(_Tag.FUN, functor)
        return structure

    def _copy_cell(self, address: int) -> int:
        return self._alloc(_Tag(self._heap_tags[address]), self._heap_values[address])

    def _deref(self, address: int) -> int:
        while self._heap_tags[address] == _Tag.REF:
            next_address = ta.cast(int, self._heap_values[address])
            if next_address == address:
                break
            address = next_address
        return address

    def _trail_binding(self, address: int) -> None:
        if self._choices and address < self._choices[-1].heap_top:
            self._trail.append(address)

    def _bind_ref(self, address: int, target: int, captures: list[int] | None) -> None:
        if captures is not None:
            captures.append(address)
        self._trail_binding(address)
        self._heap_values[address] = target

    def _unify(self, left: int, right: int, captures: list[int] | None = None) -> bool:
        pending = [(left, right)]
        seen: set[tuple[int, int]] = set()

        while pending:
            left, right = pending.pop()
            left = self._deref(left)
            right = self._deref(right)
            if left == right:
                continue

            left_tag = _Tag(self._heap_tags[left])
            right_tag = _Tag(self._heap_tags[right])
            if left_tag is _Tag.REF:
                if right_tag is _Tag.REF and left < right:
                    self._bind_ref(right, left, captures)
                else:
                    self._bind_ref(left, right, captures)
                continue
            if right_tag is _Tag.REF:
                self._bind_ref(right, left, captures)
                continue
            if left_tag is not right_tag:
                return False

            if left_tag is _Tag.CON:
                if not _atoms_equal(self._heap_values[left], self._heap_values[right]):
                    return False
                continue
            if left_tag is not _Tag.STR:
                raise WamError(f'invalid term cell: {left_tag!r}')

            left_functor = ta.cast(int, self._heap_values[left])
            right_functor = ta.cast(int, self._heap_values[right])
            if left_functor == right_functor:
                continue
            key = (left_functor, right_functor) if left_functor < right_functor else (right_functor, left_functor)
            if key in seen:
                continue
            seen.add(key)

            left_id = ta.cast(int, self._heap_values[left_functor])
            right_id = ta.cast(int, self._heap_values[right_functor])
            if left_id != right_id:
                return False
            arity = self._functors[left_id].arity
            for i in range(arity):
                pending.append((left_functor + 1 + i, right_functor + 1 + i))

        return True

    def _match_constant(self, address: int, value: object) -> bool:
        address = self._deref(address)
        tag = _Tag(self._heap_tags[address])
        if tag is _Tag.REF:
            self._bind_ref(address, self._alloc_constant(value), None)
            return True
        return tag is _Tag.CON and _atoms_equal(self._heap_values[address], value)

    def _get_structure(self, functor: int, register: int) -> bool:
        address = self._deref(self._get_x(register))
        tag = _Tag(self._heap_tags[address])
        if tag is _Tag.REF:
            structure = self._alloc_structure(functor)
            self._bind_ref(address, structure, None)
            self._mode = _Mode.WRITE
            self._s = len(self._heap_tags)
            return True
        if tag is not _Tag.STR:
            return False

        functor_address = ta.cast(int, self._heap_values[address])
        if self._heap_values[functor_address] != functor:
            return False
        self._mode = _Mode.READ
        self._s = functor_address + 1
        return True

    def _unify_constant(self, value: object) -> bool:
        if self._mode is _Mode.WRITE:
            self._alloc_constant(value)
            self._s += 1
            return True
        address = self._s
        self._s += 1
        return self._match_constant(address, value)

    def _unify_value(self, location: int) -> bool:
        if self._mode is _Mode.WRITE:
            self._copy_cell(self._get_location(location))
            self._s += 1
            return True
        address = self._s
        self._s += 1
        return self._unify(self._get_location(location), address)

    def _unify_variable(self, location: int) -> None:
        if _is_y(location):
            raise WamError('UNIFY_VARIABLE requires an X register')
        if self._mode is _Mode.WRITE:
            self._set_x(location, self._alloc_ref())
        else:
            self._set_x(location, self._s)
        self._s += 1

    def _append_term(self, term: object) -> int:
        if isinstance(term, Var):
            raise TypeError('foreign values cannot introduce scoped logic variables')
        if not isinstance(term, Struct):
            return self._alloc_constant(term)

        arguments = [self._append_term(arg) for arg in term.args]
        structure = self._alloc_structure(self._functor_id(term.functor, term.arity))
        for argument in arguments:
            self._copy_cell(argument)
        return structure

    def _functor_id(self, name: str, arity: int) -> int:
        key = name, arity
        try:
            return self._functor_ids[key]
        except KeyError:
            out = len(self._functors)
            self._functor_ids[key] = out
            self._functors.append(_Functor(name, arity))
            return out

    def _rollback(
            self,
            captures: list[int],
            capture_top: int,
            trail_top: int,
            heap_top: int,
    ) -> None:
        for address in reversed(captures[capture_top:]):
            if address < len(self._heap_tags):
                self._heap_tags[address] = int(_Tag.REF)
                self._heap_values[address] = address
        del captures[capture_top:]
        del self._trail[trail_top:]
        del self._heap_tags[heap_top:]
        del self._heap_values[heap_top:]

    def _run_foreign(self, foreign_id: int, arity: int) -> bool:
        code = self._image.foreigns[foreign_id]
        captures: list[int] = []
        trail_top = len(self._trail)
        heap_top = len(self._heap_tags)
        context = ForeignContext(self, captures)
        refs = tuple(TermRef(self._get_x(i)) for i in range(arity))

        try:
            ok = bool(code.function(context, *refs))
        except Exception:
            self._rollback(captures, 0, trail_top, heap_top)
            raise
        if not ok:
            self._rollback(captures, 0, trail_top, heap_top)
        return ok

    def _is_ground(self, address: int) -> bool:
        pending = [address]
        seen: set[int] = set()
        while pending:
            address = self._deref(pending.pop())
            tag = _Tag(self._heap_tags[address])
            if tag is _Tag.REF:
                return False
            if tag is _Tag.STR:
                functor_address = ta.cast(int, self._heap_values[address])
                if functor_address in seen:
                    continue
                seen.add(functor_address)
                functor_id = ta.cast(int, self._heap_values[functor_address])
                for i in range(self._functors[functor_id].arity):
                    pending.append(functor_address + 1 + i)
        return True

    def _trim_frames(self) -> None:
        keep = self._e + 1
        for choice in self._choices:
            keep = max(keep, choice.frame_top)
        if keep < len(self._frames):
            del self._frames[keep:]

    def _allocate(self, variable_count: int) -> None:
        self._trim_frames()
        slots = tuple(self._alloc_ref() for _ in range(variable_count))
        frame = _Frame(self._e, self._cp, self._pending_cut_base, slots)
        self._frames.append(frame)
        self._e = len(self._frames) - 1
        if self._query_frame < 0:
            self._query_frame = self._e
        self._pending_cut_base = len(self._choices)

    def _deallocate(self) -> None:
        if self._e < 0:
            raise WamError('environment underflow')
        frame = self._frames[self._e]
        self._e = frame.previous
        self._cp = frame.continuation
        self._trim_frames()

    @staticmethod
    def _atom_key(value: object) -> tuple[type, object]:
        return type(value), value

    def _select_candidates(self, predicate: _PredicateCode) -> tuple[int, ...]:
        if not predicate.relation.arity:
            return predicate.all_candidates
        address = self._deref(self._get_x(0))
        tag = _Tag(self._heap_tags[address])
        if tag is _Tag.REF:
            return predicate.all_candidates
        if tag is _Tag.CON:
            return predicate.atom_candidates.get(
                self._atom_key(self._heap_values[address]),
                predicate.wildcard_candidates,
            )
        if tag is _Tag.STR:
            functor_address = ta.cast(int, self._heap_values[address])
            functor = ta.cast(int, self._heap_values[functor_address])
            return predicate.structure_candidates.get(functor, predicate.wildcard_candidates)
        raise WamError(tag)

    def _enter_clause(self, predicate: int, candidate: int, cut_base: int) -> None:
        self._pending_cut_base = cut_base
        self._p = self._image.predicates[predicate].clauses[candidate].entry

    def _invoke(self, predicate_id: int) -> bool:
        predicate = self._image.predicates[predicate_id]
        candidates = self._select_candidates(predicate)
        if not candidates:
            return False

        self._trim_frames()
        base_depth = len(self._choices)
        arguments = tuple(self._get_x(i) for i in range(predicate.relation.arity))
        if len(candidates) > 1:
            self._choices.append(_Choice(
                predicate_id,
                candidates,
                1,
                arguments,
                self._e,
                self._cp,
                len(self._heap_tags),
                len(self._trail),
                len(self._frames),
                base_depth,
            ))
        self._enter_clause(predicate_id, candidates[0], base_depth)
        return True

    def _unwind_trail(self, top: int) -> None:
        for address in reversed(self._trail[top:]):
            self._heap_tags[address] = int(_Tag.REF)
            self._heap_values[address] = address
        del self._trail[top:]

    def _restore_choice(self, choice: _Choice) -> None:
        self._unwind_trail(choice.trail_top)
        del self._heap_tags[choice.heap_top:]
        del self._heap_values[choice.heap_top:]
        del self._frames[choice.frame_top:]
        self._e = choice.environment
        self._cp = choice.continuation
        for i, address in enumerate(choice.arguments):
            self._set_x(i, address)

    def _backtrack(self) -> bool:
        while self._choices:
            choice = self._choices[-1]
            self._restore_choice(choice)
            candidate = choice.candidates[choice.next_candidate]
            choice.next_candidate += 1
            if choice.next_candidate == len(choice.candidates):
                self._choices.pop()
                self._trim_frames()
            self._enter_clause(choice.predicate, candidate, choice.base_depth)
            return True
        return False

    def _cut(self) -> None:
        if self._e < 0:
            raise WamError('cut outside an environment')
        base = self._frames[self._e].cut_base
        if base < len(self._choices):
            del self._choices[base:]
            self._trim_frames()

    def _trace(self, pc: int, instruction: _Instruction) -> None:
        trace = self._config.trace
        if trace is not None:
            trace(TraceEvent(
                self._steps,
                pc,
                _Op(instruction.op).name.lower(),
                len(self._heap_tags),
                len(self._trail),
                len(self._choices),
            ))

    def _tick(self, pc: int, instruction: _Instruction) -> None:
        self._steps += 1
        if self._config.max_steps is not None and self._steps > self._config.max_steps:
            raise StepLimitExceeded(self._config.max_steps)
        self._trace(pc, instruction)

    def _fail(self) -> bool:
        return self._backtrack()

    def _run_until_yield(self) -> bool:
        code = self._image.code
        while self._p >= 0:
            pc = self._p
            instruction = code[pc]
            self._p += 1
            self._tick(pc, instruction)
            op = _Op(instruction.op)

            if op is _Op.ALLOCATE:
                self._allocate(ta.cast(int, instruction.a))
            elif op is _Op.GET_CONSTANT:
                if not self._match_constant(
                        self._get_x(ta.cast(int, instruction.b)),
                        instruction.a,
                ) and not self._fail():
                    return False
            elif op is _Op.GET_STRUCTURE:
                if not self._get_structure(
                        ta.cast(int, instruction.a),
                        ta.cast(int, instruction.b),
                ) and not self._fail():
                    return False
            elif op is _Op.GET_VALUE:
                if not self._unify(
                        self._get_location(ta.cast(int, instruction.a)),
                        self._get_x(ta.cast(int, instruction.b)),
                ) and not self._fail():
                    return False
            elif op is _Op.UNIFY_CONSTANT:
                if not self._unify_constant(instruction.a) and not self._fail():
                    return False
            elif op is _Op.UNIFY_VALUE:
                if not self._unify_value(ta.cast(int, instruction.a)) and not self._fail():
                    return False
            elif op is _Op.UNIFY_VARIABLE:
                self._unify_variable(ta.cast(int, instruction.a))
            elif op is _Op.PUT_CONSTANT:
                self._set_x(ta.cast(int, instruction.b), self._alloc_constant(instruction.a))
            elif op is _Op.PUT_STRUCTURE:
                self._set_x(ta.cast(int, instruction.b), self._alloc_structure(ta.cast(int, instruction.a)))
                self._mode = _Mode.WRITE
                self._s = len(self._heap_tags)
            elif op is _Op.PUT_VALUE:
                self._set_x(ta.cast(int, instruction.b), self._get_location(ta.cast(int, instruction.a)))
            elif op is _Op.SET_CONSTANT:
                self._alloc_constant(instruction.a)
                self._s += 1
            elif op is _Op.SET_VALUE:
                self._copy_cell(self._get_location(ta.cast(int, instruction.a)))
                self._s += 1
            elif op is _Op.CALL:
                self._cp = self._p
                if not self._invoke(ta.cast(int, instruction.a)) and not self._fail():
                    return False
            elif op is _Op.EXECUTE:
                if not self._invoke(ta.cast(int, instruction.a)) and not self._fail():
                    return False
            elif op is _Op.UNIFY:
                if not self._unify(
                        self._get_x(ta.cast(int, instruction.a)),
                        self._get_x(ta.cast(int, instruction.b)),
                ) and not self._fail():
                    return False
            elif op is _Op.FOREIGN:
                if not self._run_foreign(ta.cast(int, instruction.a), ta.cast(int, instruction.b)) and not self._fail():
                    return False
            elif op is _Op.CUT:
                self._cut()
            elif op is _Op.FAIL:
                if not self._fail():
                    return False
            elif op is _Op.DEALLOCATE:
                self._deallocate()
            elif op is _Op.PROCEED:
                self._p = self._cp
            elif op is _Op.YIELD:
                return True
            else:
                raise WamError(op)
        return False

    def _solution(self) -> Solution:
        if self._query_frame < 0:
            raise WamError('query frame was not allocated')
        frame = self._frames[self._query_frame]
        reifier = _Reifier(self)
        return Solution((variable, reifier.reify(frame.slots[slot])) for variable, slot in self._query.variables)

    def solutions(self) -> ta.Iterator[Solution]:
        while self._run_until_yield():
            yield self._solution()
            if not self._backtrack():
                return


class _Reifier:
    def __init__(self, machine: _Machine) -> None:
        super().__init__()

        self._machine = machine
        self._unbound: dict[int, Unbound] = {}
        self._active: dict[int, int] = {}
        self._next_cycle = 0

    def _cycle_id(self) -> int:
        out = self._next_cycle
        self._next_cycle += 1
        return out

    def _reify_list(self, address: int) -> object:
        items: list[object] = []
        active: list[int] = []
        tail: object = NIL

        try:
            while True:
                address = self._machine._deref(address)
                tag = _Tag(self._machine._heap_tags[address])
                if tag is _Tag.REF:
                    tail = self._reify_ref(address)
                    break
                if tag is _Tag.CON:
                    value = self._machine._heap_values[address]
                    if value is NIL:
                        tail = NIL
                    else:
                        tail = value
                    break
                if tag is not _Tag.STR:
                    raise WamError(tag)

                functor_address = ta.cast(int, self._machine._heap_values[address])
                functor_id = ta.cast(int, self._machine._heap_values[functor_address])
                if functor_id != self._machine._image.list_functor:
                    tail = self.reify(address)
                    break
                if functor_address in self._active:
                    tail = Cycle(self._active[functor_address])
                    break

                cycle = self._cycle_id()
                self._active[functor_address] = cycle
                active.append(functor_address)
                items.append(self.reify(functor_address + 1))
                address = functor_address + 2
        finally:
            for functor_address in reversed(active):
                del self._active[functor_address]

        if tail is NIL:
            return items
        return ListValue(tuple(items), tail)

    def _reify_ref(self, address: int) -> Unbound:
        try:
            return self._unbound[address]
        except KeyError:
            out = Unbound(len(self._unbound))
            self._unbound[address] = out
            return out

    def reify(self, address: int) -> object:
        address = self._machine._deref(address)
        tag = _Tag(self._machine._heap_tags[address])
        if tag is _Tag.REF:
            return self._reify_ref(address)
        if tag is _Tag.CON:
            value = self._machine._heap_values[address]
            return [] if value is NIL else value
        if tag is not _Tag.STR:
            raise WamError(tag)

        functor_address = ta.cast(int, self._machine._heap_values[address])
        functor_id = ta.cast(int, self._machine._heap_values[functor_address])
        if functor_id == self._machine._image.list_functor:
            return self._reify_list(address)
        if functor_address in self._active:
            return Cycle(self._active[functor_address])

        cycle = self._cycle_id()
        self._active[functor_address] = cycle
        try:
            functor = self._machine._functors[functor_id]
            args = tuple(self.reify(functor_address + 1 + i) for i in range(functor.arity))
            return Struct(functor.name, args)
        finally:
            del self._active[functor_address]


## Public program objects


def _atoms_equal(left: object, right: object) -> bool:
    return type(left) is type(right) and bool(left == right)


def _format_location(location: int) -> str:
    if _is_y(location):
        return f'Y{_location_index(location)}'
    return f'X{location}'


def _format_instruction(instruction: _Instruction, image: _Image) -> str:
    op = _Op(instruction.op)
    if op in {_Op.GET_STRUCTURE, _Op.PUT_STRUCTURE}:
        functor = image.functors[ta.cast(int, instruction.a)]
        return f'{op.name.lower()} {functor.name}/{functor.arity}, X{instruction.b}'
    if op in {_Op.GET_VALUE, _Op.PUT_VALUE}:
        return f'{op.name.lower()} {_format_location(ta.cast(int, instruction.a))}, X{instruction.b}'
    if op in {_Op.UNIFY_VALUE, _Op.SET_VALUE}:
        return f'{op.name.lower()} {_format_location(ta.cast(int, instruction.a))}'
    if op is _Op.UNIFY_VARIABLE:
        return f'{op.name.lower()} X{instruction.a}'
    if op in {_Op.CALL, _Op.EXECUTE}:
        relation = image.predicates[ta.cast(int, instruction.a)].relation
        return f'{op.name.lower()} {relation.name}/{relation.arity}'
    if op is _Op.FOREIGN:
        foreign_code = image.foreigns[ta.cast(int, instruction.a)]
        return f'foreign {foreign_code.name}/{instruction.b}'
    if op is _Op.UNIFY:
        return f'unify X{instruction.a}, X{instruction.b}'
    if instruction.b is not None:
        return f'{op.name.lower()} {instruction.a!r}, {instruction.b!r}'
    if instruction.a is not None:
        return f'{op.name.lower()} {instruction.a!r}'
    return op.name.lower()


class Executable:
    def __init__(
            self,
            image: _Image,
            predicate_ids: ta.Mapping[tuple[str, int], int],
            functor_ids: ta.Mapping[tuple[str, int], int],
    ) -> None:
        super().__init__()

        self._image = image
        self._predicate_ids = dict(predicate_ids)
        self._functor_ids = dict(functor_ids)

    def disassemble(self) -> str:
        lines: list[str] = []
        for predicate in self._image.predicates:
            lines.append(f'{predicate.relation.name}/{predicate.relation.arity}:')
            for i, clause in enumerate(predicate.clauses):
                lines.append(f'  clause {i}:')
                for pc in range(clause.entry, clause.end):
                    lines.append(f'    {pc:04d}  {_format_instruction(self._image.code[pc], self._image)}')
        return '\n'.join(lines)

    def solve(self, *goals: object, config: MachineConfig | None = None) -> ta.Iterator[Solution]:
        normalized = tuple(_normalize_goal(goal) for goal in goals)
        query = _QueryCompiler(self).compile(normalized)
        return _Machine(query, config or MachineConfig()).solutions()


class Program:
    def __init__(self) -> None:
        super().__init__()

        self._relations: dict[tuple[str, int], Relation] = {}
        self._clauses: list[Clause] = []

    @property
    def clauses(self) -> ta.Sequence[Clause]:
        return tuple(self._clauses)

    def relation(self, name: str, arity: int) -> Relation:
        key = name, arity
        try:
            return self._relations[key]
        except KeyError:
            relation = Relation(name, arity)
            self._relations[key] = relation
            return relation

    def _register_relation(self, relation: Relation) -> Relation:
        return self._relations.setdefault(relation.key, relation)

    def _register_goal(self, goal: object) -> object:
        if isinstance(goal, Call):
            relation = self._register_relation(goal.relation)
            return Call(relation, goal.args)
        return goal

    def rule(self, head: Call, *body: object) -> Clause:
        if not isinstance(head, Call):
            raise TypeError(head)
        relation = self._register_relation(head.relation)
        normalized_head = Call(relation, tuple(_normalize_term(arg) for arg in head.args))
        normalized_body = tuple(self._register_goal(_normalize_goal(goal)) for goal in body)
        clause = Clause(normalized_head, normalized_body)
        self._clauses.append(clause)
        return clause

    def fact(self, head: Call) -> Clause:
        return self.rule(head)

    def compile(self) -> Executable:
        return _ProgramCompiler(self).compile()

    def solve(self, *goals: object, config: MachineConfig | None = None) -> ta.Iterator[Solution]:
        return self.compile().solve(*goals, config=config)
