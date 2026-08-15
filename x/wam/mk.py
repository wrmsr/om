"""
A compact, embedded miniKanren with useful core.logic-style extensions.

The public surface is a Python DSL::

    x = var('x')

    @relation
    def appendo(left, right, out):
        return conde(
            (eq(left, NIL), eq(right, out)),
            (fresh(lambda head, tail, rest: all(
                eq(left, cons(head, tail)),
                eq(out, cons(head, rest)),
                appendo(tail, right, rest),
            )),),
        )

    assert run_star(x, appendo([1, 2], [3], x)) == [[1, 2, 3]]

The implementation follows the modern miniKanren operational model rather than Prolog's depth-first model. Goals map
immutable logical states to fair, suspended streams of states. Disjunction interleaves alternatives; conjunction binds a
goal over a stream. Branches share no mutable substitution or constraint state.

Included extensions are deliberately substantial but still compact:

* occurs-checked unification, plus an explicit rational-tree mode;
* delayed structural disequality and residual constrained answers;
* type, absence, partial-mapping, and finite-domain constraints;
* exact finite-domain propagation, arithmetic, ordering, all-different, and first-fail labelling;
* soft cut, committed choice, once, projection, and host predicates;
* variant tabling with answer deduplication and wakeable suspended consumers;
* recursive relations, logical lists, Python tuples and mappings, tracing, and step limits.

The implementation intentionally uses copied standard-library dictionaries. That is not the fastest persistent-state
representation, but it keeps this single file standalone and makes the state transitions unusually easy to inspect and
modify.
"""
import builtins
import dataclasses as dc
import functools
import inspect
import itertools
import typing as ta


type GoalFn = ta.Callable[[State], _Stream]
type TraceFn = ta.Callable[[TraceEvent], None]


##
## Errors


class MkError(Exception):
    pass


class InstantiationError(MkError):
    pass


class StepLimitExceeded(MkError):
    pass


class TableError(MkError):
    pass


##
## Terms and answers


@dc.dataclass(frozen=True, slots=True)
class _Nil:
    def __repr__(self) -> str:
        return 'NIL'


NIL = _Nil()


@dc.dataclass(frozen=True, slots=True)
class Symbol:
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise TypeError(self.name)

    def __repr__(self) -> str:
        return self.name


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
class Cons:
    head: object
    tail: object

    def __repr__(self) -> str:
        return f'cons({self.head!r}, {self.tail!r})'


@dc.dataclass(frozen=True, slots=True)
class ListValue:
    items: tuple[object, ...]
    tail: object

    def __repr__(self) -> str:
        body = ', '.join(map(repr, self.items))
        return f'[{body} | {self.tail!r}]'


@dc.dataclass(frozen=True, slots=True)
class ReifiedVar:
    name: str

    def __repr__(self) -> str:
        return self.name


@dc.dataclass(frozen=True, slots=True)
class Cycle:
    name: str

    def __repr__(self) -> str:
        return f'<cycle {self.name}>'


@dc.dataclass(frozen=True, slots=True)
class Residual:
    operator: str
    args: tuple[object, ...]

    def __repr__(self) -> str:
        return f'{self.operator}({", ".join(map(repr, self.args))})'


@dc.dataclass(frozen=True, slots=True)
class Constrained:
    value: object
    constraints: tuple[Residual, ...]

    def __repr__(self) -> str:
        return f'{self.value!r} :- {", ".join(map(repr, self.constraints))}'


@dc.dataclass(frozen=True, slots=True)
class TraceEvent:
    step: int
    goal: str
    substitution_size: int
    constraint_count: int
    domain_count: int


##
## Finite domains


def _is_fd_int(value: object) -> ta.TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


@dc.dataclass(frozen=True, slots=True)
class FdDomain:
    intervals: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        normalized: list[tuple[int, int]] = []
        for lower, upper in sorted(self.intervals):
            if not _is_fd_int(lower) or not _is_fd_int(upper):
                raise TypeError((lower, upper))
            if lower > upper:
                raise ValueError((lower, upper))
            if normalized and lower <= normalized[-1][1] + 1:
                normalized[-1] = normalized[-1][0], max(normalized[-1][1], upper)
            else:
                normalized.append((lower, upper))
        object.__setattr__(self, 'intervals', tuple(normalized))

    def __bool__(self) -> bool:
        return bool(self.intervals)

    def __contains__(self, value: object) -> bool:
        if not _is_fd_int(value):
            return False
        return builtins.any(lower <= value <= upper for lower, upper in self.intervals)

    def __iter__(self) -> ta.Iterator[int]:
        for lower, upper in self.intervals:
            yield from range(lower, upper + 1)

    def __len__(self) -> int:
        return sum(upper - lower + 1 for lower, upper in self.intervals)

    @property
    def lower(self) -> int:
        if not self.intervals:
            raise ValueError('empty domain')
        return self.intervals[0][0]

    @property
    def upper(self) -> int:
        if not self.intervals:
            raise ValueError('empty domain')
        return self.intervals[-1][1]

    @property
    def singleton(self) -> int | None:
        if len(self.intervals) == 1 and self.intervals[0][0] == self.intervals[0][1]:
            return self.intervals[0][0]
        return None

    def intersect(self, other: 'FdDomain') -> 'FdDomain':
        out: list[tuple[int, int]] = []
        left = 0
        right = 0
        while left < len(self.intervals) and right < len(other.intervals):
            ll, lu = self.intervals[left]
            rl, ru = other.intervals[right]
            lower = max(ll, rl)
            upper = min(lu, ru)
            if lower <= upper:
                out.append((lower, upper))
            if lu < ru:
                left += 1
            else:
                right += 1
        return FdDomain(tuple(out))

    def without(self, value: int) -> 'FdDomain':
        if value not in self:
            return self
        out: list[tuple[int, int]] = []
        for lower, upper in self.intervals:
            if not lower <= value <= upper:
                out.append((lower, upper))
                continue
            if lower < value:
                out.append((lower, value - 1))
            if value < upper:
                out.append((value + 1, upper))
        return FdDomain(tuple(out))

    @classmethod
    def values(cls, values: ta.Iterable[int]) -> 'FdDomain':
        ordered = sorted(set(values))
        if not builtins.all(_is_fd_int(value) for value in ordered):
            raise TypeError(ordered)
        return cls(tuple((value, value) for value in ordered))

    def __repr__(self) -> str:
        parts = [str(lower) if lower == upper else f'{lower}..{upper}' for lower, upper in self.intervals]
        return f'domain({", ".join(parts)})'


def interval(lower: int, upper: int | None = None, /) -> FdDomain:
    if upper is None:
        lower, upper = 0, lower
    return FdDomain(((lower, upper),))


def domain(*values: object) -> FdDomain:
    intervals: list[tuple[int, int]] = []
    for value in values:
        if isinstance(value, FdDomain):
            intervals.extend(value.intervals)
        elif isinstance(value, range):
            if value.step != 1:
                intervals.extend((item, item) for item in value)
            elif value:
                intervals.append((value.start, value.stop - 1))
        elif _is_fd_int(value):
            intervals.append((value, value))
        elif isinstance(value, ta.Iterable) and not isinstance(value, (str, bytes, bytearray)):
            intervals.extend((item, item) for item in value)
        else:
            raise TypeError(value)
    return FdDomain(tuple(intervals))


##
## Term construction


def var(name: str = '_') -> Var:
    return Var(name)


def variables(names: str, /) -> tuple[Var, ...]:
    return tuple(Var(name) for name in names.replace(',', ' ').split())


def symbol(name: str, /) -> Symbol:
    return Symbol(name)


def struct(functor: str, *args: object) -> Struct:
    return Struct(functor, tuple(_normalize_term(arg) for arg in args))


def cons(head: object, tail: object) -> Cons:
    return Cons(_normalize_term(head), _normalize_term(tail))


def llist(*items: object, tail: object = NIL) -> object:
    out = _normalize_term(tail)
    for item in reversed(items):
        out = Cons(_normalize_term(item), out)
    return out


def _normalize_term(value: object) -> object:
    if isinstance(value, (Var, Symbol, Struct, Cons, _Nil, ReifiedVar, Cycle)):
        return value
    if isinstance(value, list):
        return llist(*value)
    if isinstance(value, tuple):
        return tuple(_normalize_term(item) for item in value)
    if isinstance(value, dict):
        out: dict[object, object] = {}
        for key, item in value.items():
            try:
                hash(key)
            except TypeError as exc:
                raise TypeError(f'logic mapping keys must be hashable: {key!r}') from exc
            out[key] = _normalize_term(item)
        return out
    try:
        hash(value)
    except TypeError as exc:
        raise TypeError(f'unsupported logic term: {value!r}') from exc
    return value


def _term_children(value: object) -> tuple[object, ...]:
    if isinstance(value, Struct):
        return value.args
    if isinstance(value, Cons):
        return value.head, value.tail
    if isinstance(value, tuple):
        return value
    if isinstance(value, dict):
        return tuple(value.values())
    return ()


##
## Constraints and logical state


@dc.dataclass(frozen=True, slots=True)
class _DiseqConstraint:
    left: object
    right: object


@dc.dataclass(frozen=True, slots=True)
class _TypeConstraint:
    term: object
    kind: str


@dc.dataclass(frozen=True, slots=True)
class _AbsentoConstraint:
    needle: object
    haystack: object


@dc.dataclass(frozen=True, slots=True)
class _FeatureConstraint:
    term: object
    items: tuple[tuple[object, object], ...]


@dc.dataclass(frozen=True, slots=True)
class _FdConstraint:
    operator: str
    terms: tuple[object, ...]


type _Constraint = ta.Union[
    _DiseqConstraint,
    _TypeConstraint,
    _AbsentoConstraint,
    _FeatureConstraint,
    _FdConstraint,
]


@dc.dataclass(slots=True)
class _Runtime:
    max_steps: int | None
    trace: TraceFn | None
    steps: int = 0
    tables: dict[tuple[object, object], '_TableEntry'] = dc.field(default_factory=dict)

    def tick(self, goal: str, state: 'State') -> None:
        self.steps += 1
        if self.max_steps is not None and self.steps > self.max_steps:
            raise StepLimitExceeded(self.max_steps)
        if self.trace is not None:
            self.trace(TraceEvent(
                self.steps,
                goal,
                len(state.substitution),
                len(state.constraints),
                len(state.domains),
            ))


@dc.dataclass(frozen=True, slots=True)
class State:
    substitution: ta.Mapping[Var, object]
    constraints: tuple[_Constraint, ...]
    domains: ta.Mapping[Var, FdDomain]
    occurs_check: bool
    runtime: _Runtime

    @classmethod
    def empty(
            cls,
            *,
            occurs_check: bool = True,
            max_steps: int | None = None,
            trace: TraceFn | None = None,
    ) -> 'State':
        return cls({}, (), {}, occurs_check, _Runtime(max_steps, trace))


def walk(term: object, state: State, /) -> object:
    value = term
    seen: set[Var] = set()
    while isinstance(value, Var) and value in state.substitution:
        if value in seen:
            break
        seen.add(value)
        value = state.substitution[value]
    return value


def _walk_path(term: object, state: State) -> tuple[object, tuple[Var, ...]]:
    value = term
    path: list[Var] = []
    seen: set[Var] = set()
    while isinstance(value, Var) and value in state.substitution:
        if value in seen:
            return value, tuple(path)
        seen.add(value)
        path.append(value)
        value = state.substitution[value]
    return value, tuple(path)


def _is_ground(term: object, state: State, active: set[Var] | None = None) -> bool:
    if active is None:
        active = set()
    value, path = _walk_path(term, state)
    if isinstance(value, Var):
        return False
    if builtins.any(item in active for item in path):
        return False
    active.update(path)
    try:
        return builtins.all(_is_ground(child, state, active) for child in _term_children(value))
    finally:
        active.difference_update(path)


def _occurs(variable: Var, term: object, state: State, active: set[int] | None = None) -> bool:
    value = walk(term, state)
    if value is variable:
        return True
    if isinstance(value, Var):
        return False
    if active is None:
        active = set()
    marker = id(value)
    if marker in active:
        return False
    active.add(marker)
    try:
        return builtins.any(_occurs(variable, child, state, active) for child in _term_children(value))
    finally:
        active.remove(marker)


def _same_atom(left: object, right: object) -> bool:
    return type(left) is type(right) and left == right


def _state_with(
        state: State,
        *,
        substitution: ta.Mapping[Var, object] | None = None,
        constraints: tuple[_Constraint, ...] | None = None,
        domains: ta.Mapping[Var, FdDomain] | None = None,
) -> State:
    return State(
        state.substitution if substitution is None else substitution,
        state.constraints if constraints is None else constraints,
        state.domains if domains is None else domains,
        state.occurs_check,
        state.runtime,
    )


def _bind_raw(state: State, variable: Var, value: object) -> State | None:
    value = walk(value, state)
    if value is variable:
        return state
    if state.occurs_check and _occurs(variable, value, state):
        return None

    substitution = dict(state.substitution)
    domains = dict(state.domains)
    variable_domain = domains.pop(variable, None)

    if isinstance(value, Var):
        value_domain = domains.get(value)
        if variable_domain is not None and value_domain is not None:
            merged = variable_domain.intersect(value_domain)
            if not merged:
                return None
            domains[value] = merged
        elif variable_domain is not None:
            domains[value] = variable_domain
        substitution[variable] = value
        next_state = _state_with(state, substitution=substitution, domains=domains)
        merged_domain = domains.get(value)
        if merged_domain is not None and merged_domain.singleton is not None:
            return _bind_raw(next_state, value, merged_domain.singleton)
        return next_state

    if variable_domain is not None:
        if not _is_fd_int(value) or value not in variable_domain:
            return None
    substitution[variable] = value
    return _state_with(state, substitution=substitution, domains=domains)


def _unify_raw(state: State, left: object, right: object) -> State | None:
    pending: list[tuple[object, object]] = [(left, right)]
    out = state
    while pending:
        left, right = pending.pop()
        left = walk(left, out)
        right = walk(right, out)
        if left is right:
            continue
        if isinstance(left, Var):
            out = _bind_raw(out, left, right)
            if out is None:
                return None
            continue
        if isinstance(right, Var):
            out = _bind_raw(out, right, left)
            if out is None:
                return None
            continue
        if isinstance(left, Struct) and isinstance(right, Struct):
            if left.functor != right.functor or left.arity != right.arity:
                return None
            pending.extend(zip(left.args, right.args))
            continue
        if isinstance(left, Cons) and isinstance(right, Cons):
            pending.append((left.tail, right.tail))
            pending.append((left.head, right.head))
            continue
        if isinstance(left, tuple) and isinstance(right, tuple):
            if len(left) != len(right):
                return None
            pending.extend(zip(left, right))
            continue
        if isinstance(left, dict) and isinstance(right, dict):
            if left.keys() != right.keys():
                return None
            pending.extend((left[key], right[key]) for key in left)
            continue
        if not _same_atom(left, right):
            return None
    return out


def _set_domain_raw(state: State, term: object, new_domain: FdDomain) -> State | None:
    value = walk(term, state)
    if _is_fd_int(value):
        return state if value in new_domain else None
    if not isinstance(value, Var):
        return None
    old_domain = state.domains.get(value)
    merged = new_domain if old_domain is None else old_domain.intersect(new_domain)
    if not merged:
        return None
    if old_domain == merged:
        return state
    domains = dict(state.domains)
    domains[value] = merged
    out = _state_with(state, domains=domains)
    if merged.singleton is not None:
        return _bind_raw(out, value, merged.singleton)
    return out


def _constraint_terms(constraint: _Constraint) -> tuple[object, ...]:
    if isinstance(constraint, _DiseqConstraint):
        return constraint.left, constraint.right
    if isinstance(constraint, _TypeConstraint):
        return constraint.term,
    if isinstance(constraint, _AbsentoConstraint):
        return constraint.needle, constraint.haystack
    if isinstance(constraint, _FeatureConstraint):
        return (constraint.term,) + tuple(value for _, value in constraint.items)
    if isinstance(constraint, _FdConstraint):
        return constraint.terms
    raise TypeError(constraint)


def _map_constraint(constraint: _Constraint, function: ta.Callable[[object], object]) -> _Constraint:
    if isinstance(constraint, _DiseqConstraint):
        return _DiseqConstraint(function(constraint.left), function(constraint.right))
    if isinstance(constraint, _TypeConstraint):
        return _TypeConstraint(function(constraint.term), constraint.kind)
    if isinstance(constraint, _AbsentoConstraint):
        return _AbsentoConstraint(function(constraint.needle), function(constraint.haystack))
    if isinstance(constraint, _FeatureConstraint):
        return _FeatureConstraint(
            function(constraint.term),
            tuple((key, function(value)) for key, value in constraint.items),
        )
    if isinstance(constraint, _FdConstraint):
        return _FdConstraint(constraint.operator, tuple(function(term) for term in constraint.terms))
    raise TypeError(constraint)


def _probe_disequality(state: State, left: object, right: object) -> int:
    probe = _unify_raw(state, left, right)
    if probe is None:
        return 1
    if probe.substitution == state.substitution and probe.domains == state.domains:
        return -1
    return 0


def _type_matches(kind: str, value: object) -> bool:
    if kind == 'symbol':
        return isinstance(value, Symbol)
    if kind == 'string':
        return isinstance(value, str)
    if kind == 'number':
        return isinstance(value, (int, float, complex)) and not isinstance(value, bool)
    if kind == 'integer':
        return _is_fd_int(value)
    if kind == 'boolean':
        return isinstance(value, bool)
    raise ValueError(kind)


def _step_absento(state: State, needle: object, haystack: object) -> int:
    pending = False
    stack = [haystack]
    seen: set[int] = set()
    while stack:
        value = walk(stack.pop(), state)
        status = _probe_disequality(state, needle, value)
        if status < 0:
            return -1
        if status == 0:
            pending = True
        if isinstance(value, Var):
            continue
        marker = id(value)
        if marker in seen:
            continue
        seen.add(marker)
        stack.extend(_term_children(value))
    return 0 if pending else 1


def _fd_predicate(operator: str, values: tuple[int, ...]) -> bool:
    if operator == 'eq':
        return values[0] == values[1]
    if operator == 'ne':
        return values[0] != values[1]
    if operator == 'lt':
        return values[0] < values[1]
    if operator == 'le':
        return values[0] <= values[1]
    if operator == 'gt':
        return values[0] > values[1]
    if operator == 'ge':
        return values[0] >= values[1]
    if operator == 'add':
        return values[0] + values[1] == values[2]
    if operator == 'sub':
        return values[0] - values[1] == values[2]
    if operator == 'mul':
        return values[0] * values[1] == values[2]
    if operator == 'quot':
        return values[1] != 0 and values[0] // values[1] == values[2]
    if operator == 'mod':
        return values[1] != 0 and values[0] % values[1] == values[2]
    raise ValueError(operator)


def _step_fd_constraint(state: State, constraint: _FdConstraint) -> tuple[State | None, int]:
    values: list[object] = [walk(term, state) for term in constraint.terms]
    if builtins.all(_is_fd_int(value) for value in values):
        fd_values = tuple(ta.cast(int, value) for value in values)
        return (state, 1) if _fd_predicate(constraint.operator, fd_values) else (None, -1)

    choices: list[tuple[int, ...]] = []
    for value in values:
        if _is_fd_int(value):
            choices.append((value,))
        elif isinstance(value, Var):
            value_domain = state.domains.get(value)
            if value_domain is None:
                return state, 0
            choices.append(tuple(value_domain))
        else:
            return None, -1

    supported: list[set[int]] = [set() for _ in values]
    found = False
    for candidate in itertools.product(*choices):
        assignments: dict[Var, int] = {}
        consistent = True
        for value, item in zip(values, candidate):
            if isinstance(value, Var):
                previous = assignments.get(value)
                if previous is not None and previous != item:
                    consistent = False
                    break
                assignments[value] = item
        if not consistent or not _fd_predicate(constraint.operator, candidate):
            continue
        found = True
        for index, item in enumerate(candidate):
            supported[index].add(item)
    if not found:
        return None, -1

    out = state
    per_variable: dict[Var, set[int]] = {}
    for value, items in zip(values, supported):
        if not isinstance(value, Var):
            continue
        previous = per_variable.get(value)
        per_variable[value] = set(items) if previous is None else previous.intersection(items)
    for variable, items in per_variable.items():
        out = _set_domain_raw(out, variable, FdDomain.values(items))
        if out is None:
            return None, -1
    return out, 0


def _step_constraint(state: State, constraint: _Constraint) -> tuple[State | None, int]:
    if isinstance(constraint, _DiseqConstraint):
        status = _probe_disequality(state, constraint.left, constraint.right)
        return (None, -1) if status < 0 else (state, status)

    if isinstance(constraint, _TypeConstraint):
        value = walk(constraint.term, state)
        if isinstance(value, Var):
            return state, 0
        return (state, 1) if _type_matches(constraint.kind, value) else (None, -1)

    if isinstance(constraint, _AbsentoConstraint):
        status = _step_absento(state, constraint.needle, constraint.haystack)
        return (None, -1) if status < 0 else (state, status)

    if isinstance(constraint, _FeatureConstraint):
        value = walk(constraint.term, state)
        if isinstance(value, Var):
            return state, 0
        if not isinstance(value, dict):
            return None, -1
        out = state
        for key, required in constraint.items:
            if key not in value:
                return None, -1
            out = _unify_raw(out, required, value[key])
            if out is None:
                return None, -1
        return out, 1

    if isinstance(constraint, _FdConstraint):
        return _step_fd_constraint(state, constraint)

    raise TypeError(constraint)


def _propagate(state: State) -> State | None:
    out = state
    while True:
        before_substitution = out.substitution
        before_domains = out.domains
        before_constraints = out.constraints
        pending: list[_Constraint] = []
        for constraint in before_constraints:
            stepped, status = _step_constraint(out, constraint)
            if stepped is None or status < 0:
                return None
            out = stepped
            if status == 0:
                pending.append(constraint)
        out = _state_with(out, constraints=tuple(pending))
        if (
                out.substitution == before_substitution and
                out.domains == before_domains and
                out.constraints == before_constraints
        ):
            return out


def _add_constraint(state: State, constraint: _Constraint) -> State | None:
    return _propagate(_state_with(state, constraints=state.constraints + (constraint,)))


##
## Fair streams


class _Stream:
    pass


@dc.dataclass(frozen=True, slots=True)
class _Empty(_Stream):
    pass


@dc.dataclass(frozen=True, slots=True)
class _Unit(_Stream):
    state: State


@dc.dataclass(frozen=True, slots=True)
class _Choice(_Stream):
    head: State
    tail: ta.Callable[[], _Stream]


@dc.dataclass(frozen=True, slots=True)
class _Suspend(_Stream):
    thunk: ta.Callable[[], _Stream]


@dc.dataclass(frozen=True, slots=True)
class _TableWait:
    entry: '_TableEntry'
    seen: int
    resume: ta.Callable[[], _Stream]

    @property
    def ready(self) -> bool:
        return len(self.entry.answers) > self.seen

    def bind(self, goal: 'Goal') -> '_TableWait':
        return _TableWait(self.entry, self.seen, lambda: _bind(self.resume(), goal))


@dc.dataclass(frozen=True, slots=True)
class _Waiting(_Stream):
    waits: tuple[_TableWait, ...]


_EMPTY = _Empty()


def _ready_waiting_stream(waiting: _Waiting) -> _Stream | None:
    for index, wait in enumerate(waiting.waits):
        if not wait.ready:
            continue
        rest_waits = waiting.waits[:index] + waiting.waits[index + 1:]

        def resume(
                wait: _TableWait = wait,
                rest_waits: tuple[_TableWait, ...] = rest_waits,
        ) -> _Stream:
            stream = wait.resume()
            if not rest_waits:
                return stream
            return _mplus(stream, lambda: _Waiting(rest_waits))

        return _Suspend(resume)
    return None


def _mplus(left: _Stream, right: ta.Callable[[], _Stream]) -> _Stream:
    if isinstance(left, _Empty):
        return right()
    if isinstance(left, _Suspend):
        return _Suspend(lambda: _mplus(right(), left.thunk))
    if isinstance(left, _Waiting):
        ready = _ready_waiting_stream(left)
        if ready is not None:
            return _mplus(ready, right)
        right_stream = right()
        if isinstance(right_stream, _Waiting):
            return _Waiting(right_stream.waits + left.waits)
        return _mplus(right_stream, lambda: left)
    if isinstance(left, _Unit):
        return _Choice(left.state, right)
    if isinstance(left, _Choice):
        return _Choice(left.head, lambda: _mplus(right(), left.tail))
    raise TypeError(left)


def _bind(stream: _Stream, goal: 'Goal') -> _Stream:
    if isinstance(stream, _Empty):
        return stream
    if isinstance(stream, _Suspend):
        return _Suspend(lambda: _bind(stream.thunk(), goal))
    if isinstance(stream, _Waiting):
        ready = _ready_waiting_stream(stream)
        if ready is not None:
            return _bind(ready, goal)
        return _Waiting(tuple(wait.bind(goal) for wait in stream.waits))
    if isinstance(stream, _Unit):
        return goal(stream.state)
    if isinstance(stream, _Choice):
        return _mplus(goal(stream.head), lambda: _bind(stream.tail(), goal))
    raise TypeError(stream)


def _first(stream: _Stream) -> State | None:
    current = stream
    while True:
        if isinstance(current, _Empty):
            return None
        if isinstance(current, _Suspend):
            current = current.thunk()
            continue
        if isinstance(current, _Waiting):
            ready = _ready_waiting_stream(current)
            if ready is None:
                return None
            current = ready
            continue
        if isinstance(current, _Unit):
            return current.state
        if isinstance(current, _Choice):
            return current.head
        raise TypeError(current)


def _take(stream: _Stream) -> ta.Iterator[State]:
    current = stream
    while True:
        if isinstance(current, _Empty):
            return
        if isinstance(current, _Suspend):
            current = current.thunk()
            continue
        if isinstance(current, _Waiting):
            ready = _ready_waiting_stream(current)
            if ready is None:
                return
            current = ready
            continue
        if isinstance(current, _Unit):
            yield current.state
            return
        if isinstance(current, _Choice):
            yield current.head
            current = current.tail()
            continue
        raise TypeError(current)


##
## Goals and combinators


@dc.dataclass(frozen=True, slots=True)
class Goal:
    function: GoalFn
    name: str = '<goal>'

    def __call__(self, state: State) -> _Stream:
        state.runtime.tick(self.name, state)
        return self.function(state)

    def __and__(self, other: 'Goal') -> 'Goal':
        return all(self, other)

    def __or__(self, other: 'Goal') -> 'Goal':
        return any(self, other)

    def __repr__(self) -> str:
        return self.name


def _coerce_goal(value: object) -> Goal:
    if not isinstance(value, Goal):
        raise TypeError(f'expected Goal, got {value!r}')
    return value


def _succeed(state: State) -> _Stream:
    return _Unit(state)


def _fail(state: State) -> _Stream:
    return _EMPTY


succeed = Goal(_succeed, 'succeed')
fail = Goal(_fail, 'fail')


def eq(left: object, right: object, /) -> Goal:
    left = _normalize_term(left)
    right = _normalize_term(right)

    def invoke(state: State) -> _Stream:
        unified = _unify_raw(state, left, right)
        if unified is None:
            return _EMPTY
        propagated = _propagate(unified)
        return _EMPTY if propagated is None else _Unit(propagated)

    return Goal(invoke, f'eq({left!r}, {right!r})')


def neq(left: object, right: object, /) -> Goal:
    left = _normalize_term(left)
    right = _normalize_term(right)

    def invoke(state: State) -> _Stream:
        out = _add_constraint(state, _DiseqConstraint(left, right))
        return _EMPTY if out is None else _Unit(out)

    return Goal(invoke, f'neq({left!r}, {right!r})')


def all(*goals: Goal) -> Goal:
    goals = tuple(_coerce_goal(goal) for goal in goals)
    if not goals:
        return succeed

    def invoke(state: State) -> _Stream:
        stream: _Stream = _Unit(state)
        for goal in goals:
            stream = _bind(stream, goal)
        return stream

    return Goal(invoke, f'all({", ".join(goal.name for goal in goals)})')


def any(*goals: Goal) -> Goal:
    goals = tuple(_coerce_goal(goal) for goal in goals)
    if not goals:
        return fail

    def invoke(state: State) -> _Stream:
        def build(index: int) -> _Stream:
            if index >= len(goals):
                return _EMPTY
            return _mplus(goals[index](state), lambda: build(index + 1))

        return _Suspend(lambda: build(0))

    return Goal(invoke, f'any({", ".join(goal.name for goal in goals)})')


def conde(*clauses: ta.Sequence[Goal]) -> Goal:
    return any(*(all(*clause) for clause in clauses))


def delay(function: ta.Callable[[], Goal], /, *, name: str | None = None) -> Goal:
    if not callable(function):
        raise TypeError(function)

    def invoke(state: State) -> _Stream:
        return _Suspend(lambda: _coerce_goal(function())(state))

    return Goal(invoke, name or getattr(function, '__name__', '<delay>'))


def fresh(function: ta.Callable[..., Goal], /) -> Goal:
    if not callable(function):
        raise TypeError(function)
    signature = inspect.signature(function)
    parameters = tuple(signature.parameters.values())
    if not builtins.all(
            parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
            for parameter in parameters
    ):
        raise TypeError('fresh functions must have only positional parameters')
    names = tuple(parameter.name for parameter in parameters)

    def invoke(state: State) -> _Stream:
        variables_ = tuple(Var(name) for name in names)
        return _coerce_goal(function(*variables_))(state)

    return Goal(invoke, f'fresh({", ".join(names)})')


def relation(function: ta.Callable[..., Goal], /) -> ta.Callable[..., Goal]:
    if not callable(function):
        raise TypeError(function)

    @functools.wraps(function)
    def wrapped(*args: object) -> Goal:
        args = tuple(_normalize_term(arg) for arg in args)

        def invoke(state: State) -> _Stream:
            return _Suspend(lambda: _coerce_goal(function(*args))(state))

        return Goal(invoke, f'{function.__name__}({", ".join(map(repr, args))})')

    return wrapped


def onceo(goal: Goal, /) -> Goal:
    goal = _coerce_goal(goal)

    def invoke(state: State) -> _Stream:
        first = _first(goal(state))
        return _EMPTY if first is None else _Unit(first)

    return Goal(invoke, f'onceo({goal.name})')


def _committed_clauses(clauses: tuple[tuple[Goal, ...], ...], *, once: bool) -> Goal:
    def invoke(state: State) -> _Stream:
        for clause in clauses:
            if not clause:
                return _Unit(state)
            head_stream = clause[0](state)
            first = _first(head_stream)
            if first is None:
                continue
            rest = all(*clause[1:])
            if once:
                return onceo(rest)(first)
            return _bind(head_stream, rest)
        return _EMPTY

    operator = 'condu' if once else 'conda'
    return Goal(invoke, operator)


def conda(*clauses: ta.Sequence[Goal]) -> Goal:
    normalized = tuple(tuple(_coerce_goal(goal) for goal in clause) for clause in clauses)
    return _committed_clauses(normalized, once=False)


def condu(*clauses: ta.Sequence[Goal]) -> Goal:
    normalized = tuple(tuple(_coerce_goal(goal) for goal in clause) for clause in clauses)
    return _committed_clauses(normalized, once=True)


def project(function: ta.Callable[..., Goal], *terms: object, name: str | None = None) -> Goal:
    if not callable(function):
        raise TypeError(function)
    terms = tuple(_normalize_term(term) for term in terms)

    def invoke(state: State) -> _Stream:
        values = []
        for term in terms:
            if not _is_ground(term, state):
                raise InstantiationError(term)
            values.append(_reify_plain(term, state))
        return _coerce_goal(function(*values))(state)

    return Goal(invoke, name or getattr(function, '__name__', '<project>'))


def pred(term: object, function: ta.Callable[[object], object], /, *, name: str | None = None) -> Goal:
    if not callable(function):
        raise TypeError(function)
    return project(
        lambda value: succeed if function(value) else fail,
        term,
        name=name or getattr(function, '__name__', '<pred>'),
    )


def is_(out: object, function: ta.Callable[..., object], *terms: object, name: str | None = None) -> Goal:
    if not callable(function):
        raise TypeError(function)
    return project(
        lambda *values: eq(out, function(*values)),
        *terms,
        name=name or getattr(function, '__name__', '<is>'),
    )


def lvaro(term: object, /) -> Goal:
    term = _normalize_term(term)

    def invoke(state: State) -> _Stream:
        return _Unit(state) if isinstance(walk(term, state), Var) else _EMPTY

    return Goal(invoke, f'lvaro({term!r})')


def nonlvaro(term: object, /) -> Goal:
    term = _normalize_term(term)

    def invoke(state: State) -> _Stream:
        return _EMPTY if isinstance(walk(term, state), Var) else _Unit(state)

    return Goal(invoke, f'nonlvaro({term!r})')


##
## General constraints


def _unary_constraint(term: object, kind: str) -> Goal:
    term = _normalize_term(term)

    def invoke(state: State) -> _Stream:
        out = _add_constraint(state, _TypeConstraint(term, kind))
        return _EMPTY if out is None else _Unit(out)

    return Goal(invoke, f'{kind}o({term!r})')


def symbolo(term: object, /) -> Goal:
    return _unary_constraint(term, 'symbol')


def stringo(term: object, /) -> Goal:
    return _unary_constraint(term, 'string')


def numbero(term: object, /) -> Goal:
    return _unary_constraint(term, 'number')


def integero(term: object, /) -> Goal:
    return _unary_constraint(term, 'integer')


def booleano(term: object, /) -> Goal:
    return _unary_constraint(term, 'boolean')


def absento(needle: object, haystack: object, /) -> Goal:
    needle = _normalize_term(needle)
    haystack = _normalize_term(haystack)

    def invoke(state: State) -> _Stream:
        out = _add_constraint(state, _AbsentoConstraint(needle, haystack))
        return _EMPTY if out is None else _Unit(out)

    return Goal(invoke, f'absento({needle!r}, {haystack!r})')


def featureo(required: ta.Mapping[object, object], term: object, /) -> Goal:
    if not isinstance(required, ta.Mapping):
        raise TypeError(required)
    term = _normalize_term(term)
    items = tuple((key, _normalize_term(value)) for key, value in required.items())

    def invoke(state: State) -> _Stream:
        out = _add_constraint(state, _FeatureConstraint(term, items))
        return _EMPTY if out is None else _Unit(out)

    return Goal(invoke, f'featureo({required!r}, {term!r})')


def distincto(*terms: object) -> Goal:
    return all(*(neq(left, right) for left, right in itertools.combinations(terms, 2)))


##
## Finite-domain goals


def in_(term: object, fd_domain: FdDomain | range | ta.Iterable[int], /) -> Goal:
    term = _normalize_term(term)
    if not isinstance(fd_domain, FdDomain):
        fd_domain = domain(fd_domain)

    def invoke(state: State) -> _Stream:
        out = _set_domain_raw(state, term, fd_domain)
        if out is None:
            return _EMPTY
        out = _propagate(out)
        return _EMPTY if out is None else _Unit(out)

    return Goal(invoke, f'in_({term!r}, {fd_domain!r})')


def _fd(operator: str, *terms: object) -> Goal:
    terms = tuple(_normalize_term(term) for term in terms)

    def invoke(state: State) -> _Stream:
        out = _add_constraint(state, _FdConstraint(operator, terms))
        return _EMPTY if out is None else _Unit(out)

    return Goal(invoke, f'fd_{operator}({", ".join(map(repr, terms))})')


def fd_eq(left: object, right: object, /) -> Goal:
    return _fd('eq', left, right)


def fd_ne(left: object, right: object, /) -> Goal:
    return _fd('ne', left, right)


def fd_lt(left: object, right: object, /) -> Goal:
    return _fd('lt', left, right)


def fd_le(left: object, right: object, /) -> Goal:
    return _fd('le', left, right)


def fd_gt(left: object, right: object, /) -> Goal:
    return _fd('gt', left, right)


def fd_ge(left: object, right: object, /) -> Goal:
    return _fd('ge', left, right)


def fd_add(left: object, right: object, out: object, /) -> Goal:
    return _fd('add', left, right, out)


def fd_sub(left: object, right: object, out: object, /) -> Goal:
    return _fd('sub', left, right, out)


def fd_mul(left: object, right: object, out: object, /) -> Goal:
    return _fd('mul', left, right, out)


def fd_quot(left: object, right: object, out: object, /) -> Goal:
    return _fd('quot', left, right, out)


def fd_mod(left: object, right: object, out: object, /) -> Goal:
    return _fd('mod', left, right, out)


def all_different(*terms: object) -> Goal:
    return all(*(fd_ne(left, right) for left, right in itertools.combinations(terms, 2)))


def label(*terms: object, strategy: str = 'first_fail') -> Goal:
    terms = tuple(_normalize_term(term) for term in terms)
    if strategy not in ('first_fail', 'leftmost'):
        raise ValueError(strategy)

    def invoke(state: State) -> _Stream:
        candidates: list[tuple[Var, FdDomain, int]] = []
        for index, term in enumerate(terms):
            value = walk(term, state)
            if _is_fd_int(value):
                continue
            if not isinstance(value, Var):
                return _EMPTY
            value_domain = state.domains.get(value)
            if value_domain is None:
                raise InstantiationError(f'finite-domain variable has no domain: {value!r}')
            candidates.append((value, value_domain, index))
        if not candidates:
            return _Unit(state)
        if strategy == 'first_fail':
            variable, value_domain, _ = min(candidates, key=lambda item: (len(item[1]), item[2]))
        else:
            variable, value_domain, _ = candidates[0]

        values = tuple(value_domain)

        def build(index: int) -> _Stream:
            if index >= len(values):
                return _EMPTY
            branch = all(eq(variable, values[index]), Goal(invoke, 'label'))
            return _mplus(branch(state), lambda: build(index + 1))

        return _Suspend(lambda: build(0))

    return Goal(invoke, f'label({", ".join(map(repr, terms))})')


##
## Useful relations


@relation
def membero(item: object, values: object) -> Goal:
    return fresh(lambda head, tail: all(
        eq(values, cons(head, tail)),
        conde(
            (eq(item, head),),
            (membero(item, tail),),
        ),
    ))


@relation
def member1o(item: object, values: object) -> Goal:
    return fresh(lambda head, tail: all(
        eq(values, cons(head, tail)),
        conde(
            (eq(item, head),),
            (neq(item, head), member1o(item, tail)),
        ),
    ))


@relation
def appendo(left: object, right: object, out: object) -> Goal:
    return conde(
        (eq(left, NIL), eq(right, out)),
        (fresh(lambda head, tail, rest: all(
            eq(left, cons(head, tail)),
            eq(out, cons(head, rest)),
            appendo(tail, right, rest),
        )),),
    )


##
## Variant tabling


@dc.dataclass(frozen=True, slots=True)
class _CanonicalVar:
    index: int


@dc.dataclass(frozen=True, slots=True)
class _CanonicalAtom:
    type_: type
    value: object


@dc.dataclass(frozen=True, slots=True)
class _CanonicalTerm:
    tag: str
    value: object


@dc.dataclass(frozen=True, slots=True)
class _TablePayload:
    term: object
    constraints: tuple[_Constraint, ...]
    domains: tuple[tuple[_CanonicalVar, FdDomain], ...]


@dc.dataclass(slots=True)
class _TableEntry:
    answers: list[_TablePayload] = dc.field(default_factory=list)
    keys: set[_TablePayload] = dc.field(default_factory=set)

    def add(self, answer: _TablePayload) -> bool:
        if answer in self.keys:
            return False
        self.keys.add(answer)
        self.answers.append(answer)
        return True


class _Canonicalizer:
    def __init__(self, state: State) -> None:
        super().__init__()

        self._state = state
        self._variables: dict[Var, _CanonicalVar] = {}
        self._active: set[Var] = set()

    @property
    def variables(self) -> ta.Mapping[Var, _CanonicalVar]:
        return self._variables

    def term(self, term: object) -> object:
        value, path = _walk_path(term, self._state)
        if builtins.any(variable in self._active for variable in path):
            raise TableError('cyclic terms cannot currently be tabled')
        if isinstance(value, Var):
            canonical = self._variables.get(value)
            if canonical is None:
                canonical = _CanonicalVar(len(self._variables))
                self._variables[value] = canonical
            return canonical
        self._active.update(path)
        try:
            if isinstance(value, Struct):
                return _CanonicalTerm('struct', (value.functor, tuple(self.term(arg) for arg in value.args)))
            if isinstance(value, Cons):
                return _CanonicalTerm('cons', (self.term(value.head), self.term(value.tail)))
            if isinstance(value, tuple):
                return _CanonicalTerm('tuple', tuple(self.term(item) for item in value))
            if isinstance(value, dict):
                return _CanonicalTerm('dict', tuple((self.term(key), self.term(item)) for key, item in value.items()))
            if value is NIL:
                return _CanonicalTerm('nil', None)
            return _CanonicalAtom(type(value), value)
        finally:
            self._active.difference_update(path)


class _Freshener:
    def __init__(self) -> None:
        super().__init__()

        self._variables: dict[_CanonicalVar, Var] = {}

    def term(self, term: object) -> object:
        if isinstance(term, _CanonicalVar):
            variable = self._variables.get(term)
            if variable is None:
                variable = Var(f't{term.index}')
                self._variables[term] = variable
            return variable
        if isinstance(term, _CanonicalAtom):
            return term.value
        if isinstance(term, _CanonicalTerm):
            if term.tag == 'struct':
                functor, args = term.value
                return Struct(functor, tuple(self.term(arg) for arg in args))
            if term.tag == 'cons':
                head, tail = term.value
                return Cons(self.term(head), self.term(tail))
            if term.tag == 'tuple':
                return tuple(self.term(item) for item in term.value)
            if term.tag == 'dict':
                return {self.term(key): self.term(value) for key, value in term.value}
            if term.tag == 'nil':
                return NIL
        raise TypeError(term)


def _collect_vars(
        term: object,
        state: State,
        out: set[Var],
        active: set[Var] | None = None,
) -> None:
    if active is None:
        active = set()
    value, path = _walk_path(term, state)
    if builtins.any(variable in active for variable in path):
        return
    if isinstance(value, Var):
        out.add(value)
        return
    active.update(path)
    try:
        for child in _term_children(value):
            _collect_vars(child, state, out, active)
    finally:
        active.difference_update(path)


def _relevant_constraints(state: State, term: object) -> tuple[tuple[_Constraint, ...], set[Var]]:
    relevant_vars: set[Var] = set()
    _collect_vars(term, state, relevant_vars)
    selected: list[_Constraint] = []
    remaining = list(state.constraints)
    changed = True
    while changed:
        changed = False
        next_remaining: list[_Constraint] = []
        for constraint in remaining:
            constraint_vars: set[Var] = set()
            for constraint_term in _constraint_terms(constraint):
                _collect_vars(constraint_term, state, constraint_vars)
            if relevant_vars.intersection(constraint_vars):
                selected.append(constraint)
                old_size = len(relevant_vars)
                relevant_vars.update(constraint_vars)
                changed = changed or len(relevant_vars) != old_size
            else:
                next_remaining.append(constraint)
        remaining = next_remaining
    return tuple(selected), relevant_vars


def _table_payload(state: State, term: object) -> _TablePayload:
    constraints, relevant_vars = _relevant_constraints(state, term)
    canonicalizer = _Canonicalizer(state)
    canonical_term = canonicalizer.term(term)
    canonical_constraints = tuple(_map_constraint(constraint, canonicalizer.term) for constraint in constraints)
    canonical_domains: list[tuple[_CanonicalVar, FdDomain]] = []
    for variable in relevant_vars:
        root = walk(variable, state)
        if not isinstance(root, Var):
            continue
        value_domain = state.domains.get(root)
        if value_domain is None:
            continue
        canonical = canonicalizer.term(root)
        if not isinstance(canonical, _CanonicalVar):
            raise TableError(canonical)
        canonical_domains.append((canonical, value_domain))
    canonical_domains.sort(key=lambda item: item[0].index)
    return _TablePayload(canonical_term, canonical_constraints, tuple(canonical_domains))


def _reuse_answer(state: State, args: tuple[object, ...], answer: _TablePayload) -> State | None:
    freshener = _Freshener()
    answer_term = freshener.term(answer.term)
    out = _unify_raw(state, args, answer_term)
    if out is None:
        return None
    for variable, value_domain in answer.domains:
        out = _set_domain_raw(out, freshener.term(variable), value_domain)
        if out is None:
            return None
    constraints = tuple(_map_constraint(constraint, freshener.term) for constraint in answer.constraints)
    out = _state_with(out, constraints=out.constraints + constraints)
    return _propagate(out)


def _reuse_table(entry: _TableEntry, state: State, args: tuple[object, ...], start: int) -> _Stream:
    end = len(entry.answers)

    def build(index: int) -> _Stream:
        while index < end:
            answer = entry.answers[index]
            index += 1
            reused = _reuse_answer(state, args, answer)
            if reused is not None:
                return _Choice(reused, lambda index=index: build(index))
        wait = _TableWait(entry, end, lambda: _reuse_table(entry, state, args, end))
        return _Waiting((wait,))

    return build(start)


def tabled(function: ta.Callable[..., Goal], /) -> ta.Callable[..., Goal]:
    if not callable(function):
        raise TypeError(function)
    token = object()

    @functools.wraps(function)
    def wrapped(*args: object) -> Goal:
        args = tuple(_normalize_term(arg) for arg in args)

        def invoke(state: State) -> _Stream:
            key_payload = _table_payload(state, args)
            key = token, key_payload
            entry = state.runtime.tables.get(key)
            if entry is not None:
                return _reuse_table(entry, state, args, 0)

            entry = _TableEntry()
            state.runtime.tables[key] = entry

            def cache(answer_state: State) -> _Stream:
                if not entry.add(_table_payload(answer_state, args)):
                    return _EMPTY
                return _Unit(answer_state)

            body = _coerce_goal(function(*args))
            return _bind(body(state), Goal(cache, f'cache {function.__name__}{args!r}'))

        return Goal(invoke, f'{function.__name__}({", ".join(map(repr, args))})')

    return wrapped


##
## Reification and query execution


class _Reifier:
    def __init__(self, state: State) -> None:
        super().__init__()

        self._state = state
        self._variables: dict[Var, ReifiedVar] = {}
        self._active: set[Var] = set()

    @property
    def variables(self) -> ta.Mapping[Var, ReifiedVar]:
        return self._variables

    def variable(self, variable: Var) -> ReifiedVar:
        out = self._variables.get(variable)
        if out is None:
            out = ReifiedVar(f'_{len(self._variables)}')
            self._variables[variable] = out
        return out

    def term(self, term: object) -> object:
        value, path = _walk_path(term, self._state)
        cycle_variable = next((variable for variable in path if variable in self._active), None)
        if cycle_variable is not None:
            return Cycle(self.variable(cycle_variable).name)
        if isinstance(value, Var):
            return self.variable(value)
        self._active.update(path)
        try:
            if isinstance(value, Struct):
                return Struct(value.functor, tuple(self.term(arg) for arg in value.args))
            if isinstance(value, Cons):
                return Cons(self.term(value.head), self.term(value.tail))
            if isinstance(value, tuple):
                return tuple(self.term(item) for item in value)
            if isinstance(value, dict):
                return {self.term(key): self.term(item) for key, item in value.items()}
            return value
        finally:
            self._active.difference_update(path)


def _finish_lists(term: object) -> object:
    if term is NIL:
        return []
    if isinstance(term, Cons):
        items: list[object] = []
        value: object = term
        seen: set[int] = set()
        while isinstance(value, Cons):
            marker = id(value)
            if marker in seen:
                return ListValue(tuple(items), Cycle('list'))
            seen.add(marker)
            items.append(_finish_lists(value.head))
            value = value.tail
        if value is NIL:
            return items
        value = _finish_lists(value)
        return ListValue(tuple(items), value)
    if isinstance(term, Struct):
        return Struct(term.functor, tuple(_finish_lists(arg) for arg in term.args))
    if isinstance(term, tuple):
        return tuple(_finish_lists(item) for item in term)
    if isinstance(term, dict):
        return {_finish_lists(key): _finish_lists(value) for key, value in term.items()}
    return term


def _reify_plain(term: object, state: State) -> object:
    return _finish_lists(_Reifier(state).term(term))


def _constraint_residual(constraint: _Constraint, reifier: _Reifier) -> Residual:
    if isinstance(constraint, _DiseqConstraint):
        return Residual('=/=', (reifier.term(constraint.left), reifier.term(constraint.right)))
    if isinstance(constraint, _TypeConstraint):
        return Residual(f'{constraint.kind}o', (reifier.term(constraint.term),))
    if isinstance(constraint, _AbsentoConstraint):
        return Residual('absento', (reifier.term(constraint.needle), reifier.term(constraint.haystack)))
    if isinstance(constraint, _FeatureConstraint):
        required = {key: reifier.term(value) for key, value in constraint.items}
        return Residual('featureo', (required, reifier.term(constraint.term)))
    if isinstance(constraint, _FdConstraint):
        return Residual(f'fd_{constraint.operator}', tuple(reifier.term(term) for term in constraint.terms))
    raise TypeError(constraint)


def _reify_answer(term: object, state: State, *, with_constraints: bool) -> object:
    reifier = _Reifier(state)
    value = _finish_lists(reifier.term(term))
    if not with_constraints:
        return value

    constraints, relevant_vars = _relevant_constraints(state, term)
    residuals = [_constraint_residual(constraint, reifier) for constraint in constraints]
    seen_domains: set[Var] = set()
    for variable in relevant_vars:
        root = walk(variable, state)
        if not isinstance(root, Var) or root in seen_domains:
            continue
        seen_domains.add(root)
        value_domain = state.domains.get(root)
        if value_domain is not None:
            residuals.append(Residual('in_', (reifier.term(root), value_domain)))
    residuals = [
        Residual(residual.operator, tuple(_finish_lists(arg) for arg in residual.args))
        for residual in residuals
    ]
    return value if not residuals else Constrained(value, tuple(residuals))


def iter_states(
        *goals: Goal,
        occurs_check: bool = True,
        max_steps: int | None = None,
        trace: TraceFn | None = None,
) -> ta.Iterator[State]:
    state = State.empty(occurs_check=occurs_check, max_steps=max_steps, trace=trace)
    yield from _take(all(*goals)(state))


def iter_run(
        query: object,
        *goals: Goal,
        limit: int | None = None,
        occurs_check: bool = True,
        with_constraints: bool = True,
        max_steps: int | None = None,
        trace: TraceFn | None = None,
) -> ta.Iterator[object]:
    query = _normalize_term(query)
    states: ta.Iterable[State] = iter_states(
        *goals,
        occurs_check=occurs_check,
        max_steps=max_steps,
        trace=trace,
    )
    if limit is not None:
        states = itertools.islice(states, limit)
    for state in states:
        yield _reify_answer(query, state, with_constraints=with_constraints)


def run(
        count: int | None,
        query: object,
        *goals: Goal,
        occurs_check: bool = True,
        with_constraints: bool = True,
        max_steps: int | None = None,
        trace: TraceFn | None = None,
) -> list[object]:
    if count is not None and (not isinstance(count, int) or count < 0):
        raise TypeError(count)
    return list(iter_run(
        query,
        *goals,
        limit=count,
        occurs_check=occurs_check,
        with_constraints=with_constraints,
        max_steps=max_steps,
        trace=trace,
    ))


def run_star(
        query: object,
        *goals: Goal,
        occurs_check: bool = True,
        with_constraints: bool = True,
        max_steps: int | None = None,
        trace: TraceFn | None = None,
) -> list[object]:
    return run(
        None,
        query,
        *goals,
        occurs_check=occurs_check,
        with_constraints=with_constraints,
        max_steps=max_steps,
        trace=trace,
    )


def run_nocheck(
        count: int | None,
        query: object,
        *goals: Goal,
        with_constraints: bool = True,
        max_steps: int | None = None,
        trace: TraceFn | None = None,
) -> list[object]:
    return run(
        count,
        query,
        *goals,
        occurs_check=False,
        with_constraints=with_constraints,
        max_steps=max_steps,
        trace=trace,
    )
