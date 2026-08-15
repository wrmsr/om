import itertools

import pytest

from .. import wam


##


def test_facts_and_query_variable_lookup():
    program = wam.Program()
    color = program.relation('color', 2)
    thing = wam.var('thing')
    value = wam.var('value')

    program.fact(color('apple', 'red'))
    program.fact(color('sky', 'blue'))
    program.fact(color('leaf', 'green'))

    solutions = list(program.solve(color(thing, value)))

    assert [(solution[thing], solution['value']) for solution in solutions] == [
        ('apple', 'red'),
        ('sky', 'blue'),
        ('leaf', 'green'),
    ]
    assert solutions[0].as_dict(names=True) == {'thing': 'apple', 'value': 'red'}


def test_first_argument_indexing_keeps_wildcards_in_source_order():
    program = wam.Program()
    p = program.relation('p', 2)
    x = wam.var('x')
    out = wam.var('out')

    program.fact(p(x, 'wild-before'))
    program.fact(p('a', 'specific'))
    program.fact(p(x, 'wild-after'))
    program.fact(p('b', 'other'))

    assert [solution[out] for solution in program.solve(p('a', out))] == [
        'wild-before',
        'specific',
        'wild-after',
    ]
    assert [solution[out] for solution in program.solve(p('z', out))] == [
        'wild-before',
        'wild-after',
    ]


def test_atom_index_distinguishes_bool_and_int():
    program = wam.Program()
    p = program.relation('p', 2)
    out = wam.var('out')

    program.fact(p(True, 'bool'))
    program.fact(p(1, 'int'))

    assert [solution[out] for solution in program.solve(p(True, out))] == ['bool']
    assert [solution[out] for solution in program.solve(p(1, out))] == ['int']


def test_recursive_relation_and_last_call_execution():
    program = wam.Program()
    edge = program.relation('edge', 2)
    path = program.relation('path', 2)
    x, y, z = wam.variables('x y z')

    program.fact(edge('a', 'b'))
    program.fact(edge('b', 'c'))
    program.fact(edge('a', 'd'))
    program.rule(path(x, y), edge(x, y))
    program.rule(path(x, y), edge(x, z), path(z, y))

    assert [solution[y] for solution in program.solve(path('a', y))] == ['b', 'd', 'c']
    assert 'execute path/2' in program.compile().disassemble()


def test_structure_construction_matching_and_repeated_variables():
    program = wam.Program()
    same_pair = program.relation('same_pair', 1)
    x = wam.var('x')
    value = wam.var('value')

    program.fact(same_pair(wam.struct('pair', x, x)))

    assert list(program.solve(same_pair(wam.struct('pair', 1, 2)))) == []
    solutions = list(program.solve(same_pair(wam.struct('pair', value, value))))
    assert len(solutions) == 1
    assert isinstance(solutions[0][value], wam.Unbound)


def test_trail_undoes_bindings_between_clause_alternatives():
    program = wam.Program()
    pick = program.relation('pick', 1)
    only_two = program.relation('only_two', 1)
    x = wam.var('x')
    out = wam.var('out')

    program.fact(pick(1))
    program.fact(pick(2))
    program.rule(only_two(x), pick(x), wam.unify(x, 2))

    assert [solution[out] for solution in program.solve(only_two(out))] == [2]


def test_deep_cut_discards_local_choices_but_not_callers_choices():
    program = wam.Program()
    outer = program.relation('outer', 1)
    inner = program.relation('inner', 1)
    combined = program.relation('combined', 2)
    x, y = wam.variables('x y')

    program.fact(outer('left'))
    program.fact(outer('right'))
    program.fact(inner(1))
    program.fact(inner(2))
    program.rule(combined(x, y), outer(x), inner(y), wam.CUT)

    assert [(solution[x], solution[y]) for solution in program.solve(combined(x, y))] == [('left', 1)]

    first = program.relation('first', 1)
    wrapped = program.relation('wrapped', 2)
    program.rule(first(y), inner(y), wam.CUT)
    program.rule(wrapped(x, y), outer(x), first(y))

    assert [(solution[x], solution[y]) for solution in program.solve(wrapped(x, y))] == [
        ('left', 1),
        ('right', 1),
    ]


def test_logic_lists_append_and_split():
    program = wam.Program()
    append = program.relation('append', 3)
    x, xs, ys, zs = wam.variables('x xs ys zs')
    out = wam.var('out')

    program.fact(append(wam.NIL, ys, ys))
    program.rule(
        append(wam.cons(x, xs), ys, wam.cons(x, zs)),
        append(xs, ys, zs),
    )

    assert [solution[out] for solution in program.solve(append([1, 2], [3, 4], out))] == [[1, 2, 3, 4]]

    left = wam.var('left')
    right = wam.var('right')
    assert [(solution[left], solution[right]) for solution in program.solve(append(left, right, [1, 2]))] == [
        ([], [1, 2]),
        ([1], [2]),
        ([1, 2], []),
    ]


def test_improper_list_reifies_without_losing_tail():
    program = wam.Program()
    p = program.relation('p', 1)
    x = wam.var('x')

    program.fact(p(wam.cons(1, 2)))

    value = list(program.solve(p(x)))[0][x]
    assert value == wam.ListValue((1,), 2)


def test_unification_supports_rational_trees_and_reifier_breaks_cycles():
    program = wam.Program()
    x = wam.var('x')

    solution = list(program.solve(wam.unify(x, wam.struct('f', x))))[0]
    value = solution[x]

    assert isinstance(value, wam.Struct)
    assert value.functor == 'f'
    assert len(value.args) == 1
    assert isinstance(value.args[0], wam.Cycle)


def test_deterministic_foreign_predicate_can_read_and_bind_terms():
    program = wam.Program()
    successor = program.relation('successor', 2)
    even = program.relation('even', 1)
    x, y = wam.variables('x y')
    out = wam.var('out')

    program.rule(successor(x, y), wam.project(y, lambda value: value + 1, x, name='increment'))
    program.rule(even(x), wam.guard(lambda value: value % 2 == 0, x, name='is_even'))

    assert [solution[out] for solution in program.solve(successor(41, out))] == [42]
    assert len(list(program.solve(even(4)))) == 1
    assert list(program.solve(even(5))) == []


def test_failed_foreign_call_rolls_back_its_own_bindings():
    program = wam.Program()
    p = program.relation('p', 1)
    x = wam.var('x')
    out = wam.var('out')

    def bind_then_fail(ctx, ref):
        assert ctx.unify(ref, 1)
        return False

    program.rule(p(x), wam.foreign(bind_then_fail, x))
    program.fact(p(2))

    assert [solution[out] for solution in program.solve(p(out))] == [2]


def test_foreign_value_requires_ground_input():
    program = wam.Program()
    p = program.relation('p', 1)
    x = wam.var('x')
    out = wam.var('out')

    program.rule(p(x), wam.guard(bool, x))

    with pytest.raises(wam.InstantiationError):
        list(program.solve(p(out)))


def test_compiled_program_is_immutable_with_respect_to_builder_changes():
    program = wam.Program()
    p = program.relation('p', 1)
    x = wam.var('x')

    program.fact(p(1))
    executable = program.compile()
    program.fact(p(2))

    assert [solution[x] for solution in executable.solve(p(x))] == [1]
    assert [solution[x] for solution in program.solve(p(x))] == [1, 2]


def test_empty_query_succeeds_once():
    assert [solution.as_dict() for solution in wam.Program().solve()] == [{}]


def test_failure_and_unknown_index_key():
    program = wam.Program()
    p = program.relation('p', 1)

    program.fact(p('known'))

    assert list(program.solve(p('unknown'))) == []
    assert list(program.solve(wam.FAIL)) == []


def test_step_limit_stops_nonterminating_search():
    program = wam.Program()
    loop = program.relation('loop', 0)
    program.rule(loop(), loop())

    with pytest.raises(wam.StepLimitExceeded):
        list(program.solve(loop(), config=wam.MachineConfig(max_steps=100)))


def test_trace_hook_observes_bytecode_without_affecting_execution():
    program = wam.Program()
    p = program.relation('p', 1)
    x = wam.var('x')
    events = []

    program.fact(p('ok'))

    assert [solution[x] for solution in program.solve(p(x), config=wam.MachineConfig(trace=events.append))] == ['ok']
    assert events
    assert events[0].operation == 'allocate'
    assert any(event.operation == 'call' for event in events)


def test_solution_name_lookup_rejects_ambiguous_names():
    program = wam.Program()
    p = program.relation('p', 2)
    x1 = wam.var('x')
    x2 = wam.var('x')

    program.fact(p(1, 2))
    solution = list(program.solve(p(x1, x2)))[0]

    assert solution[x1] == 1
    assert solution[x2] == 2
    with pytest.raises(KeyError):
        _ = solution['x']
    with pytest.raises(KeyError):
        solution.as_dict(names=True)


def test_solutions_are_lazy():
    program = wam.Program()
    p = program.relation('p', 1)
    x = wam.var('x')
    for value in range(100):
        program.fact(p(value))

    first_three = list(itertools.islice(program.solve(p(x)), 3))
    assert [solution[x] for solution in first_three] == [0, 1, 2]


def test_choice_point_protects_a_deallocated_caller_environment():
    program = wam.Program()
    a = program.relation('a', 0)
    b = program.relation('b', 1)
    c = program.relation('c', 1)
    e = program.relation('e', 1)
    f = program.relation('f', 1)
    g = program.relation('g', 1)
    x = wam.var('x')

    program.rule(a(), b(x), c(x))
    program.rule(b(x), e(x))
    program.fact(c(1))
    program.rule(e(x), f(x))
    program.rule(e(x), g(x))
    program.fact(f(2))
    program.fact(g(1))

    assert len(list(program.solve(a()))) == 1


def test_foreign_result_can_introduce_a_new_functor():
    program = wam.Program()
    make = program.relation('make', 1)
    x = wam.var('x')
    out = wam.var('out')

    program.rule(make(x), wam.project(x, lambda: wam.struct('made_at_runtime', 1)))

    assert list(program.solve(make(out)))[0][out] == wam.struct('made_at_runtime', 1)


def test_last_call_execution_does_not_use_the_python_call_stack():
    program = wam.Program()
    count = program.relation('count', 1)
    n, previous = wam.variables('n previous')

    program.fact(count(0))
    program.rule(
        count(n),
        wam.guard(lambda value: value > 0, n),
        wam.project(previous, lambda value: value - 1, n),
        count(previous),
    )

    assert len(list(program.solve(count(2_000), config=wam.MachineConfig(max_steps=100_000)))) == 1
