"""
A portable relational DSL targeting the sibling WAM and miniKanren engines.

The portable language is intentionally smaller than either backend. It contains
first-order terms, definite Horn clauses, structural unification, logical lists,
true/fail, and pure ground Python guards and projections. Backend-specific search
control, constraints, tabling, and foreign interfaces remain available through the
native handles returned by the linkers.

A module is inspectable data rather than executable host-language control flow::

    graph = Module('graph')
    edge = graph.import_relation('edge', 2)
    path = graph.export_relation('path', 2)
    x, y, z = variables('x y z')

    graph.rule(path(x, y), edge(x, y))
    graph.rule(path(x, y), edge(x, z), path(z, y))

The same module can be installed into an existing ``wam.Program`` or assembled
into miniKanren relation callables. The WAM linker appends ordinary clauses to
ordinary WAM relations. The miniKanren builder creates open-recursive dispatchers,
so native extension clauses participate in recursive calls made by portable rules.
"""

import dataclasses as dc
import enum
import itertools
import typing as ta

from . import mk
from . import wam


GoalBinding: ta.TypeAlias = ta.Callable[..., object]
MkExtension: ta.TypeAlias = ta.Callable[..., mk.Goal]


##
## Errors


class DslError(Exception):
    pass


class DefinitionError(DslError):
    pass


class LinkError(DslError):
    pass


class FrozenError(DslError):
    pass


##
## Terms and normalized answers


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
class ListValue:
    items: tuple[object, ...]
    tail: object

    def __repr__(self) -> str:
        body = ', '.join(map(repr, self.items))
        return f'[{body} | {self.tail!r}]'


@dc.dataclass(frozen=True, slots=True)
class Unbound:
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


def var(name: str = '_') -> Var:
    return Var(name)


def variables(names: str, /) -> tuple[Var, ...]:
    return tuple(Var(name) for name in names.replace(',', ' ').split())


def symbol(name: str, /) -> Symbol:
    return Symbol(name)


def struct(functor: str, *args: object) -> Struct:
    return Struct(functor, tuple(_normalize_term(arg) for arg in args))


def cons(head: object, tail: object) -> Struct:
    return struct('.', head, tail)


def llist(*items: object, tail: object = NIL) -> object:
    out = _normalize_term(tail)
    for item in reversed(items):
        out = cons(item, out)
    return out


def _is_backend_term(value: object) -> bool:
    return isinstance(value, (
        mk.Cons,
        mk.Cycle,
        mk.ReifiedVar,
        mk.Struct,
        mk.Symbol,
        mk.Var,
        wam.Cycle,
        wam.Struct,
        wam.Unbound,
        wam.Var,
    )) or value is mk.NIL or value is wam.NIL


def _normalize_term(value: object) -> object:
    if value is NIL:
        return value
    if isinstance(value, Var):
        return value
    if isinstance(value, Symbol):
        return value
    if isinstance(value, Struct):
        return Struct(value.functor, tuple(_normalize_term(arg) for arg in value.args))
    if isinstance(value, ListValue):
        return llist(*value.items, tail=value.tail)
    if isinstance(value, (Call, PrimitiveCall)):
        raise TypeError('a relation or primitive call is a goal, not a term')
    if _is_backend_term(value):
        raise TypeError('backend-native terms cannot appear in portable clauses')
    if isinstance(value, list):
        return llist(*value)
    if isinstance(value, tuple):
        raise TypeError('portable tuples must be represented with struct()')
    if isinstance(value, dict):
        raise TypeError('portable mappings must be represented with struct() or logical lists')
    try:
        hash(value)
    except TypeError as exc:
        raise TypeError(f'portable logic atoms must be hashable: {value!r}') from exc
    return value


##
## Relations, goals, and clauses


class RelationKind(enum.Enum):
    IMPORT = 'import'
    LOCAL = 'local'
    EXPORT = 'export'


@dc.dataclass(frozen=True, slots=True, eq=False)
class Relation:
    module_name: str
    name: str
    arity: int
    kind: RelationKind
    _owner: object = dc.field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.module_name, str) or not self.module_name:
            raise TypeError(self.module_name)
        if not isinstance(self.name, str) or not self.name:
            raise TypeError(self.name)
        if not isinstance(self.arity, int) or self.arity < 0:
            raise TypeError(self.arity)
        if not isinstance(self.kind, RelationKind):
            raise TypeError(self.kind)

    @property
    def imported(self) -> bool:
        return self.kind is RelationKind.IMPORT

    @property
    def exported(self) -> bool:
        return self.kind is RelationKind.EXPORT

    def __call__(self, *args: object) -> 'Call':
        if len(args) != self.arity:
            raise TypeError(f'{self.name}/{self.arity} got {len(args)} arguments')
        return Call(self, tuple(_normalize_term(arg) for arg in args))

    def __repr__(self) -> str:
        return f'{self.module_name}.{self.name}/{self.arity}'


@dc.dataclass(frozen=True, slots=True, eq=False)
class Primitive:
    module_name: str
    name: str
    arity: int
    ground_inputs: tuple[int, ...]
    _owner: object = dc.field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.module_name, str) or not self.module_name:
            raise TypeError(self.module_name)
        if not isinstance(self.name, str) or not self.name:
            raise TypeError(self.name)
        if not isinstance(self.arity, int) or self.arity < 0:
            raise TypeError(self.arity)
        if not isinstance(self.ground_inputs, tuple):
            raise TypeError(self.ground_inputs)
        if len(set(self.ground_inputs)) != len(self.ground_inputs):
            raise ValueError(self.ground_inputs)
        if any(not isinstance(index, int) or not 0 <= index < self.arity for index in self.ground_inputs):
            raise ValueError(self.ground_inputs)

    def __call__(self, *args: object) -> 'PrimitiveCall':
        if len(args) != self.arity:
            raise TypeError(f'{self.name}/{self.arity} got {len(args)} arguments')
        return PrimitiveCall(self, tuple(_normalize_term(arg) for arg in args))

    def __repr__(self) -> str:
        return f'{self.module_name}.{self.name}/{self.arity}'


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
class PrimitiveCall:
    primitive: Primitive
    args: tuple[object, ...]

    def __post_init__(self) -> None:
        if len(self.args) != self.primitive.arity:
            raise TypeError(self)

    def __repr__(self) -> str:
        return f'{self.primitive.name}({", ".join(map(repr, self.args))})'


@dc.dataclass(frozen=True, slots=True)
class Unify:
    left: object
    right: object


@dc.dataclass(frozen=True, slots=True)
class Guard:
    function: ta.Callable[..., object]
    args: tuple[object, ...]
    name: str


@dc.dataclass(frozen=True, slots=True)
class Project:
    result: object
    function: ta.Callable[..., object]
    args: tuple[object, ...]
    name: str


@dc.dataclass(frozen=True, slots=True)
class _True:
    def __repr__(self) -> str:
        return 'TRUE'


@dc.dataclass(frozen=True, slots=True)
class _Fail:
    def __repr__(self) -> str:
        return 'FAIL'


TRUE = _True()
FAIL = _Fail()


@dc.dataclass(frozen=True, slots=True)
class Clause:
    head: Call
    body: tuple[object, ...] = ()


def unify(left: object, right: object) -> Unify:
    return Unify(_normalize_term(left), _normalize_term(right))


def guard(
        function: ta.Callable[..., object],
        *args: object,
        name: str | None = None,
) -> Guard:
    if not callable(function):
        raise TypeError(function)
    return Guard(
        function,
        tuple(_normalize_term(arg) for arg in args),
        name or getattr(function, '__name__', '<guard>'),
    )


def project(
        result: object,
        function: ta.Callable[..., object],
        *args: object,
        name: str | None = None,
) -> Project:
    if not callable(function):
        raise TypeError(function)
    return Project(
        _normalize_term(result),
        function,
        tuple(_normalize_term(arg) for arg in args),
        name or getattr(function, '__name__', '<project>'),
    )


def _normalize_goal(value: object) -> object:
    if isinstance(value, Call):
        return Call(value.relation, tuple(_normalize_term(arg) for arg in value.args))
    if isinstance(value, PrimitiveCall):
        return PrimitiveCall(value.primitive, tuple(_normalize_term(arg) for arg in value.args))
    if isinstance(value, Unify):
        return unify(value.left, value.right)
    if isinstance(value, Guard):
        return Guard(value.function, tuple(_normalize_term(arg) for arg in value.args), value.name)
    if isinstance(value, Project):
        return Project(
            _normalize_term(value.result),
            value.function,
            tuple(_normalize_term(arg) for arg in value.args),
            value.name,
        )
    if value is TRUE or value is FAIL:
        return value
    raise TypeError(f'not a portable logic goal: {value!r}')


##
## Portable modules


@dc.dataclass(frozen=True, slots=True)
class _ModuleImage:
    name: str
    owner: object
    relations: tuple[Relation, ...]
    primitives: tuple[Primitive, ...]
    clauses: tuple[Clause, ...]


class Module:
    def __init__(self, name: str) -> None:
        super().__init__()

        if not isinstance(name, str) or not name:
            raise TypeError(name)
        self._name = name
        self._owner = object()
        self._relations: dict[tuple[str, int], Relation] = {}
        self._primitives: dict[tuple[str, int], Primitive] = {}
        self._clauses: list[Clause] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def relations(self) -> ta.Sequence[Relation]:
        return tuple(self._relations.values())

    @property
    def primitives(self) -> ta.Sequence[Primitive]:
        return tuple(self._primitives.values())

    @property
    def clauses(self) -> ta.Sequence[Clause]:
        return tuple(self._clauses)

    @property
    def exports(self) -> ta.Sequence[Relation]:
        return tuple(relation for relation in self._relations.values() if relation.exported)

    @property
    def imports(self) -> ta.Sequence[Relation]:
        return tuple(relation for relation in self._relations.values() if relation.imported)

    def _declare_relation(self, name: str, arity: int, kind: RelationKind) -> Relation:
        key = name, arity
        relation = self._relations.get(key)
        if relation is not None:
            if relation.kind is not kind:
                raise DefinitionError(
                    f'{self._name}.{name}/{arity} was already declared as {relation.kind.value}'
                )
            return relation
        relation = Relation(self._name, name, arity, kind, self._owner)
        self._relations[key] = relation
        return relation

    def relation(self, name: str, arity: int) -> Relation:
        return self._declare_relation(name, arity, RelationKind.LOCAL)

    def export_relation(self, name: str, arity: int) -> Relation:
        return self._declare_relation(name, arity, RelationKind.EXPORT)

    def import_relation(self, name: str, arity: int) -> Relation:
        return self._declare_relation(name, arity, RelationKind.IMPORT)

    def import_goal(
            self,
            name: str,
            arity: int,
            *,
            ground_inputs: ta.Iterable[int] = (),
    ) -> Primitive:
        key = name, arity
        primitive = self._primitives.get(key)
        normalized_ground_inputs = tuple(ground_inputs)
        if primitive is not None:
            if primitive.ground_inputs != normalized_ground_inputs:
                raise DefinitionError(
                    f'{self._name}.{name}/{arity} was already declared with a different contract'
                )
            return primitive
        primitive = Primitive(
            self._name,
            name,
            arity,
            normalized_ground_inputs,
            self._owner,
        )
        self._primitives[key] = primitive
        return primitive

    def _validate_relation(self, relation: Relation) -> None:
        if relation._owner is not self._owner:
            raise DefinitionError(
                f'{relation!r} belongs to another module; declare an import in {self._name!r}'
            )

    def _validate_goal(self, goal: object) -> None:
        if isinstance(goal, Call):
            self._validate_relation(goal.relation)
        elif isinstance(goal, PrimitiveCall):
            if goal.primitive._owner is not self._owner:
                raise DefinitionError(
                    f'{goal.primitive!r} belongs to another module; declare an imported goal'
                )

    def rule(self, head: Call, *body: object) -> Clause:
        if not isinstance(head, Call):
            raise TypeError(head)
        self._validate_relation(head.relation)
        if head.relation.imported:
            raise DefinitionError(f'cannot define imported relation {head.relation!r}')

        normalized_head = ta.cast(Call, _normalize_goal(head))
        normalized_body = tuple(_normalize_goal(goal) for goal in body)
        for goal in normalized_body:
            self._validate_goal(goal)

        clause = Clause(normalized_head, normalized_body)
        self._clauses.append(clause)
        return clause

    def fact(self, head: Call) -> Clause:
        return self.rule(head)

    def _image(self) -> _ModuleImage:
        return _ModuleImage(
            self._name,
            self._owner,
            tuple(self._relations.values()),
            tuple(self._primitives.values()),
            tuple(self._clauses),
        )

    def link_wam(
            self,
            program: wam.Program,
            *,
            imports: ta.Mapping[Relation, wam.Relation] | None = None,
            relations: ta.Mapping[Relation, wam.Relation] | None = None,
            primitives: ta.Mapping[Primitive, GoalBinding] | None = None,
            prefix: str = '',
    ) -> 'WamNamespace':
        return _WamLinker(
            self._image(),
            program,
            imports=imports,
            relations=relations,
            primitives=primitives,
            prefix=prefix,
        ).link()

    def mk_builder(
            self,
            *,
            imports: ta.Mapping[Relation, ta.Callable[..., mk.Goal]] | None = None,
            primitives: ta.Mapping[Primitive, GoalBinding] | None = None,
            tabled: ta.Iterable[Relation] = (),
    ) -> 'MkBuilder':
        return MkBuilder(
            self._image(),
            imports=imports,
            primitives=primitives,
            tabled=tabled,
        )

    def link_mk(
            self,
            *,
            imports: ta.Mapping[Relation, ta.Callable[..., mk.Goal]] | None = None,
            primitives: ta.Mapping[Primitive, GoalBinding] | None = None,
            tabled: ta.Iterable[Relation] = (),
    ) -> 'MkNamespace':
        return self.mk_builder(
            imports=imports,
            primitives=primitives,
            tabled=tabled,
        ).build()


##
## Value conversion


def _neutralize(value: object) -> object:
    if value is NIL:
        return []
    if isinstance(value, (Symbol, Var, Struct, ListValue, Unbound, Cycle, Residual, Constrained)):
        return value
    if value is wam.NIL or value is mk.NIL:
        return []
    if isinstance(value, wam.Struct):
        return Struct(value.functor, tuple(_neutralize(arg) for arg in value.args))
    if isinstance(value, mk.Struct):
        return Struct(value.functor, tuple(_neutralize(arg) for arg in value.args))
    if isinstance(value, wam.ListValue):
        return ListValue(tuple(_neutralize(item) for item in value.items), _neutralize(value.tail))
    if isinstance(value, mk.ListValue):
        return ListValue(tuple(_neutralize(item) for item in value.items), _neutralize(value.tail))
    if isinstance(value, wam.Unbound):
        return Unbound(f'_{value.index}')
    if isinstance(value, mk.ReifiedVar):
        return Unbound(value.name)
    if isinstance(value, wam.Cycle):
        return Cycle(str(value.index))
    if isinstance(value, mk.Cycle):
        return Cycle(value.name)
    if isinstance(value, mk.Symbol):
        return Symbol(value.name)
    if isinstance(value, mk.Residual):
        return Residual(value.operator, tuple(_neutralize(arg) for arg in value.args))
    if isinstance(value, mk.Constrained):
        return Constrained(
            _neutralize(value.value),
            tuple(ta.cast(Residual, _neutralize(item)) for item in value.constraints),
        )
    if isinstance(value, list):
        return [_neutralize(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_neutralize(item) for item in value)
    if isinstance(value, dict):
        return {_neutralize(key): _neutralize(item) for key, item in value.items()}
    return value


##
## WAM lowering and linking


class _WamLowerer:
    def __init__(
            self,
            relations: ta.Mapping[Relation, wam.Relation],
            primitives: ta.Mapping[Primitive, GoalBinding],
            *,
            variables_: dict[Var, wam.Var] | None = None,
            no_new_variables: bool = False,
    ) -> None:
        super().__init__()

        self._relations = relations
        self._primitives = primitives
        self._variables = {} if variables_ is None else variables_
        self._no_new_variables = no_new_variables

    @property
    def variables(self) -> ta.Mapping[Var, wam.Var]:
        return self._variables

    def term(self, value: object) -> object:
        value = _normalize_term(value)
        if value is NIL:
            return wam.NIL
        if isinstance(value, Var):
            native = self._variables.get(value)
            if native is None:
                if self._no_new_variables:
                    raise TypeError('portable projections must return ground values')
                native = wam.var(value.name)
                self._variables[value] = native
            return native
        if isinstance(value, Symbol):
            return value
        if isinstance(value, Struct):
            return wam.struct(value.functor, *(self.term(arg) for arg in value.args))
        return value

    def _guard(self, goal: Guard) -> object:
        def invoke(*values: object) -> bool:
            return bool(goal.function(*(_neutralize(value) for value in values)))

        return wam.guard(
            invoke,
            *(self.term(arg) for arg in goal.args),
            name=goal.name,
        )

    def _project(self, goal: Project) -> object:
        def invoke(*values: object) -> object:
            result = goal.function(*(_neutralize(value) for value in values))
            return _WamLowerer(
                self._relations,
                self._primitives,
                no_new_variables=True,
            ).term(result)

        return wam.project(
            self.term(goal.result),
            invoke,
            *(self.term(arg) for arg in goal.args),
            name=goal.name,
        )

    def goal(self, value: object) -> object:
        goal = _normalize_goal(value)
        if isinstance(goal, Call):
            try:
                relation = self._relations[goal.relation]
            except KeyError as exc:
                raise LinkError(f'unlinked relation: {goal.relation!r}') from exc
            return relation(*(self.term(arg) for arg in goal.args))
        if isinstance(goal, PrimitiveCall):
            try:
                binding = self._primitives[goal.primitive]
            except KeyError as exc:
                raise LinkError(f'unlinked primitive: {goal.primitive!r}') from exc
            return binding(*(self.term(arg) for arg in goal.args))
        if isinstance(goal, Unify):
            return wam.unify(self.term(goal.left), self.term(goal.right))
        if isinstance(goal, Guard):
            return self._guard(goal)
        if isinstance(goal, Project):
            return self._project(goal)
        if goal is TRUE:
            return wam.TRUE
        if goal is FAIL:
            return wam.FAIL
        raise TypeError(goal)


class _WamLinker:
    def __init__(
            self,
            image: _ModuleImage,
            program: wam.Program,
            *,
            imports: ta.Mapping[Relation, wam.Relation] | None,
            relations: ta.Mapping[Relation, wam.Relation] | None,
            primitives: ta.Mapping[Primitive, GoalBinding] | None,
            prefix: str,
    ) -> None:
        super().__init__()

        if not isinstance(program, wam.Program):
            raise TypeError(program)
        if not isinstance(prefix, str):
            raise TypeError(prefix)
        self._image = image
        self._program = program
        self._imports = {} if imports is None else dict(imports)
        self._overrides = {} if relations is None else dict(relations)
        self._primitives = {} if primitives is None else dict(primitives)
        self._prefix = prefix

    def _resolve_relations(self) -> dict[Relation, wam.Relation]:
        known = set(self._image.relations)
        for relation in self._imports:
            if relation not in known or not relation.imported:
                raise LinkError(f'not an imported relation of {self._image.name!r}: {relation!r}')
        for relation in self._overrides:
            if relation not in known or relation.imported:
                raise LinkError(f'not a defined relation of {self._image.name!r}: {relation!r}')

        out: dict[Relation, wam.Relation] = {}
        for relation in self._image.relations:
            if relation.imported:
                native = self._imports.get(relation)
                if native is None:
                    raise LinkError(f'missing WAM import binding for {relation!r}')
            else:
                native = self._overrides.get(relation)
                if native is None:
                    native = self._program.relation(f'{self._prefix}{relation.name}', relation.arity)
            if not isinstance(native, wam.Relation) or native.arity != relation.arity:
                raise LinkError(f'invalid WAM relation binding for {relation!r}: {native!r}')
            out[relation] = native
        return out

    def _resolve_primitives(self) -> dict[Primitive, GoalBinding]:
        known = set(self._image.primitives)
        for primitive, binding in self._primitives.items():
            if primitive not in known:
                raise LinkError(f'not an imported primitive of {self._image.name!r}: {primitive!r}')
            if not callable(binding):
                raise LinkError(f'invalid WAM primitive binding for {primitive!r}: {binding!r}')
        for primitive in self._image.primitives:
            if primitive not in self._primitives:
                raise LinkError(f'missing WAM primitive binding for {primitive!r}')
        return dict(self._primitives)

    def link(self) -> 'WamNamespace':
        relations = self._resolve_relations()
        primitives = self._resolve_primitives()
        for clause in self._image.clauses:
            lowerer = _WamLowerer(relations, primitives)
            head = ta.cast(wam.Call, lowerer.goal(clause.head))
            body = tuple(lowerer.goal(goal) for goal in clause.body)
            self._program.rule(head, *body)
        return WamNamespace(self._image, self._program, relations, primitives)


class WamNamespace:
    def __init__(
            self,
            image: _ModuleImage,
            program: wam.Program,
            relations: ta.Mapping[Relation, wam.Relation],
            primitives: ta.Mapping[Primitive, GoalBinding],
    ) -> None:
        super().__init__()

        self._image = image
        self._program = program
        self._relations = dict(relations)
        self._primitives = dict(primitives)

    @property
    def program(self) -> wam.Program:
        return self._program

    @property
    def relations(self) -> ta.Mapping[Relation, wam.Relation]:
        return dict(self._relations)

    def __getitem__(self, relation: Relation) -> wam.Relation:
        try:
            return self._relations[relation]
        except KeyError as exc:
            raise KeyError(relation) from exc

    def export(self, name: str, arity: int | None = None) -> wam.Relation:
        matches = [
            relation
            for relation in self._image.relations
            if relation.exported and relation.name == name and (arity is None or relation.arity == arity)
        ]
        if len(matches) != 1:
            raise KeyError((name, arity))
        return self._relations[matches[0]]

    def _selection(
            self,
            value: object,
            lowerer: _WamLowerer,
    ) -> tuple[object, list[object]]:
        if isinstance(value, tuple):
            items = [self._selection(item, lowerer) for item in value]
            return tuple(item[0] for item in items), list(itertools.chain.from_iterable(item[1] for item in items))
        if isinstance(value, dict):
            items = {key: self._selection(item, lowerer) for key, item in value.items()}
            return (
                {key: item[0] for key, item in items.items()},
                list(itertools.chain.from_iterable(item[1] for item in items.values())),
            )
        native = wam.var('$select')
        return native, [wam.unify(native, lowerer.term(value))]

    def _read_selection(self, value: object, solution: wam.Solution) -> object:
        if isinstance(value, tuple):
            return tuple(self._read_selection(item, solution) for item in value)
        if isinstance(value, dict):
            return {key: self._read_selection(item, solution) for key, item in value.items()}
        return _neutralize(solution[ta.cast(wam.Var, value)])

    def iter_solve(
            self,
            *goals: object,
            select: object,
            limit: int | None = None,
            config: wam.MachineConfig | None = None,
            max_steps: int | None = None,
            trace: wam.TraceFn | None = None,
    ) -> ta.Iterator[object]:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise TypeError(limit)
        if config is not None and (max_steps is not None or trace is not None):
            raise ValueError('config cannot be combined with max_steps or trace')
        if config is None:
            config = wam.MachineConfig(max_steps=max_steps, trace=trace)

        lowerer = _WamLowerer(self._relations, self._primitives)
        native_goals = [lowerer.goal(goal) for goal in goals]
        native_selection, selection_goals = self._selection(select, lowerer)
        solutions: ta.Iterable[wam.Solution] = self._program.solve(
            *native_goals,
            *selection_goals,
            config=config,
        )
        if limit is not None:
            solutions = itertools.islice(solutions, limit)
        for solution in solutions:
            yield self._read_selection(native_selection, solution)

    def solve(
            self,
            *goals: object,
            select: object,
            limit: int | None = None,
            config: wam.MachineConfig | None = None,
            max_steps: int | None = None,
            trace: wam.TraceFn | None = None,
    ) -> list[object]:
        return list(self.iter_solve(
            *goals,
            select=select,
            limit=limit,
            config=config,
            max_steps=max_steps,
            trace=trace,
        ))


##
## miniKanren lowering and linking


class _MkLowerer:
    def __init__(
            self,
            relations: ta.Mapping[Relation, ta.Callable[..., mk.Goal]],
            primitives: ta.Mapping[Primitive, GoalBinding],
            *,
            variables_: dict[Var, mk.Var] | None = None,
            no_new_variables: bool = False,
    ) -> None:
        super().__init__()

        self._relations = relations
        self._primitives = primitives
        self._variables = {} if variables_ is None else variables_
        self._no_new_variables = no_new_variables

    def term(self, value: object) -> object:
        value = _normalize_term(value)
        if value is NIL:
            return mk.NIL
        if isinstance(value, Var):
            native = self._variables.get(value)
            if native is None:
                if self._no_new_variables:
                    raise TypeError('portable projections must return ground values')
                native = mk.var(value.name)
                self._variables[value] = native
            return native
        if isinstance(value, Symbol):
            return mk.symbol(value.name)
        if isinstance(value, Struct):
            if value.functor == '.' and value.arity == 2:
                return mk.cons(self.term(value.args[0]), self.term(value.args[1]))
            return mk.struct(value.functor, *(self.term(arg) for arg in value.args))
        return value

    def _guard(self, goal: Guard) -> mk.Goal:
        def invoke(*values: object) -> mk.Goal:
            return mk.succeed if goal.function(*(_neutralize(value) for value in values)) else mk.fail

        return mk.project(
            invoke,
            *(self.term(arg) for arg in goal.args),
            name=goal.name,
        )

    def _project(self, goal: Project) -> mk.Goal:
        def invoke(*values: object) -> object:
            result = goal.function(*(_neutralize(value) for value in values))
            return _MkLowerer(
                self._relations,
                self._primitives,
                no_new_variables=True,
            ).term(result)

        return mk.is_(
            self.term(goal.result),
            invoke,
            *(self.term(arg) for arg in goal.args),
            name=goal.name,
        )

    def goal(self, value: object) -> mk.Goal:
        goal = _normalize_goal(value)
        if isinstance(goal, Call):
            try:
                relation = self._relations[goal.relation]
            except KeyError as exc:
                raise LinkError(f'unlinked relation: {goal.relation!r}') from exc
            native = relation(*(self.term(arg) for arg in goal.args))
            if not isinstance(native, mk.Goal):
                raise LinkError(f'miniKanren relation returned a non-goal: {native!r}')
            return native
        if isinstance(goal, PrimitiveCall):
            try:
                binding = self._primitives[goal.primitive]
            except KeyError as exc:
                raise LinkError(f'unlinked primitive: {goal.primitive!r}') from exc
            native = binding(*(self.term(arg) for arg in goal.args))
            if not isinstance(native, mk.Goal):
                raise LinkError(f'miniKanren primitive returned a non-goal: {native!r}')
            return native
        if isinstance(goal, Unify):
            return mk.eq(self.term(goal.left), self.term(goal.right))
        if isinstance(goal, Guard):
            return self._guard(goal)
        if isinstance(goal, Project):
            return self._project(goal)
        if goal is TRUE:
            return mk.succeed
        if goal is FAIL:
            return mk.fail
        raise TypeError(goal)


class MkBuilder:
    def __init__(
            self,
            image: _ModuleImage,
            *,
            imports: ta.Mapping[Relation, ta.Callable[..., mk.Goal]] | None,
            primitives: ta.Mapping[Primitive, GoalBinding] | None,
            tabled: ta.Iterable[Relation],
    ) -> None:
        super().__init__()

        self._image = image
        self._imports = {} if imports is None else dict(imports)
        self._primitives = {} if primitives is None else dict(primitives)
        self._tabled = set(tabled)
        self._extensions: dict[Relation, list[MkExtension]] = {}
        self._built = False

    def _check_mutable(self) -> None:
        if self._built:
            raise FrozenError('miniKanren assembly has already been built')

    def _check_defined_relation(self, relation: Relation) -> None:
        if relation not in self._image.relations or relation.imported:
            raise LinkError(f'not a defined relation of {self._image.name!r}: {relation!r}')

    def table(self, *relations: Relation) -> 'MkBuilder':
        self._check_mutable()
        for relation in relations:
            self._check_defined_relation(relation)
            self._tabled.add(relation)
        return self

    def extend(self, relation: Relation, function: MkExtension) -> 'MkBuilder':
        self._check_mutable()
        self._check_defined_relation(relation)
        if not callable(function):
            raise TypeError(function)
        self._extensions.setdefault(relation, []).append(function)
        return self

    def build(self) -> 'MkNamespace':
        self._check_mutable()
        namespace = _MkLinker(
            self._image,
            imports=self._imports,
            primitives=self._primitives,
            tabled=self._tabled,
            extensions={relation: tuple(items) for relation, items in self._extensions.items()},
        ).link()
        self._built = True
        return namespace


class _MkAssembly:
    def __init__(
            self,
            image: _ModuleImage,
            primitives: ta.Mapping[Primitive, GoalBinding],
            extensions: ta.Mapping[Relation, tuple[MkExtension, ...]],
    ) -> None:
        super().__init__()

        self._image = image
        self._primitives = primitives
        self._extensions = extensions
        self._relations: dict[Relation, ta.Callable[..., mk.Goal]] = {}
        self._namespace: MkNamespace | None = None
        self._clauses: dict[Relation, tuple[Clause, ...]] = {
            relation: tuple(clause for clause in image.clauses if clause.head.relation is relation)
            for relation in image.relations
            if not relation.imported
        }

    @property
    def relations(self) -> ta.Mapping[Relation, ta.Callable[..., mk.Goal]]:
        return self._relations

    def set_namespace(self, namespace: 'MkNamespace') -> None:
        if self._namespace is not None:
            raise RuntimeError('namespace already assigned')
        self._namespace = namespace

    def body(self, relation: Relation, args: tuple[object, ...]) -> mk.Goal:
        branches: list[mk.Goal] = []
        for clause in self._clauses.get(relation, ()):
            lowerer = _MkLowerer(self._relations, self._primitives)
            goals = [
                mk.eq(actual, lowerer.term(expected))
                for actual, expected in zip(args, clause.head.args)
            ]
            goals.extend(lowerer.goal(goal) for goal in clause.body)
            branches.append(mk.all(*goals))

        if self._namespace is None:
            raise RuntimeError('miniKanren namespace is not initialized')
        for extension in self._extensions.get(relation, ()):
            goal = extension(self._namespace, *args)
            if not isinstance(goal, mk.Goal):
                raise LinkError(f'miniKanren extension returned a non-goal: {goal!r}')
            branches.append(goal)

        return mk.any(*branches)


class _MkLinker:
    def __init__(
            self,
            image: _ModuleImage,
            *,
            imports: ta.Mapping[Relation, ta.Callable[..., mk.Goal]],
            primitives: ta.Mapping[Primitive, GoalBinding],
            tabled: ta.AbstractSet[Relation],
            extensions: ta.Mapping[Relation, tuple[MkExtension, ...]],
    ) -> None:
        super().__init__()

        self._image = image
        self._imports = dict(imports)
        self._primitives = dict(primitives)
        self._tabled = set(tabled)
        self._extensions = dict(extensions)

    def _validate(self) -> None:
        known_relations = set(self._image.relations)
        for relation, binding in self._imports.items():
            if relation not in known_relations or not relation.imported:
                raise LinkError(f'not an imported relation of {self._image.name!r}: {relation!r}')
            if not callable(binding):
                raise LinkError(f'invalid miniKanren relation binding for {relation!r}: {binding!r}')
        for relation in self._image.relations:
            if relation.imported and relation not in self._imports:
                raise LinkError(f'missing miniKanren import binding for {relation!r}')
        for relation in self._tabled:
            if relation not in known_relations or relation.imported:
                raise LinkError(f'cannot table relation {relation!r}')

        known_primitives = set(self._image.primitives)
        for primitive, binding in self._primitives.items():
            if primitive not in known_primitives:
                raise LinkError(f'not an imported primitive of {self._image.name!r}: {primitive!r}')
            if not callable(binding):
                raise LinkError(f'invalid miniKanren primitive binding for {primitive!r}: {binding!r}')
        for primitive in self._image.primitives:
            if primitive not in self._primitives:
                raise LinkError(f'missing miniKanren primitive binding for {primitive!r}')

    @staticmethod
    def _name(function: ta.Callable[..., object], relation: Relation) -> ta.Callable[..., object]:
        function.__name__ = relation.name
        function.__qualname__ = f'{relation.module_name}.{relation.name}'
        return function

    def link(self) -> 'MkNamespace':
        self._validate()
        assembly = _MkAssembly(self._image, self._primitives, self._extensions)
        assembly._relations.update(self._imports)

        for relation in self._image.relations:
            if relation.imported:
                continue

            def implementation(*args: object, _relation: Relation = relation) -> mk.Goal:
                return assembly.body(_relation, args)

            named = self._name(implementation, relation)
            native = mk.tabled(named) if relation in self._tabled else mk.relation(named)
            assembly._relations[relation] = native

        namespace = MkNamespace(
            self._image,
            assembly.relations,
            self._primitives,
            frozenset(self._tabled),
        )
        assembly.set_namespace(namespace)
        return namespace


class MkNamespace:
    def __init__(
            self,
            image: _ModuleImage,
            relations: ta.Mapping[Relation, ta.Callable[..., mk.Goal]],
            primitives: ta.Mapping[Primitive, GoalBinding],
            tabled: ta.AbstractSet[Relation],
    ) -> None:
        super().__init__()

        self._image = image
        self._relations = dict(relations)
        self._primitives = dict(primitives)
        self._tabled = frozenset(tabled)

    @property
    def relations(self) -> ta.Mapping[Relation, ta.Callable[..., mk.Goal]]:
        return dict(self._relations)

    @property
    def tabled(self) -> ta.AbstractSet[Relation]:
        return self._tabled

    def __getitem__(self, relation: Relation) -> ta.Callable[..., mk.Goal]:
        try:
            return self._relations[relation]
        except KeyError as exc:
            raise KeyError(relation) from exc

    def export(self, name: str, arity: int | None = None) -> ta.Callable[..., mk.Goal]:
        matches = [
            relation
            for relation in self._image.relations
            if relation.exported and relation.name == name and (arity is None or relation.arity == arity)
        ]
        if len(matches) != 1:
            raise KeyError((name, arity))
        return self._relations[matches[0]]

    def _selection(self, value: object, lowerer: _MkLowerer) -> object:
        if isinstance(value, tuple):
            return tuple(self._selection(item, lowerer) for item in value)
        if isinstance(value, dict):
            return {key: self._selection(item, lowerer) for key, item in value.items()}
        return lowerer.term(value)

    def iter_solve(
            self,
            *goals: object,
            select: object,
            limit: int | None = None,
            occurs_check: bool = True,
            with_constraints: bool = True,
            max_steps: int | None = None,
            trace: mk.TraceFn | None = None,
    ) -> ta.Iterator[object]:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise TypeError(limit)
        lowerer = _MkLowerer(self._relations, self._primitives)
        native_goals = tuple(lowerer.goal(goal) for goal in goals)
        native_selection = self._selection(select, lowerer)
        for answer in mk.iter_run(
                native_selection,
                *native_goals,
                limit=limit,
                occurs_check=occurs_check,
                with_constraints=with_constraints,
                max_steps=max_steps,
                trace=trace,
        ):
            yield _neutralize(answer)

    def solve(
            self,
            *goals: object,
            select: object,
            limit: int | None = None,
            occurs_check: bool = True,
            with_constraints: bool = True,
            max_steps: int | None = None,
            trace: mk.TraceFn | None = None,
    ) -> list[object]:
        return list(self.iter_solve(
            *goals,
            select=select,
            limit=limit,
            occurs_check=occurs_check,
            with_constraints=with_constraints,
            max_steps=max_steps,
            trace=trace,
        ))
