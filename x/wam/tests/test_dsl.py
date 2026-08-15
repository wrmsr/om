import pytest

from .. import dsl
from .. import mk
from .. import wam


##
## Helpers


def make_edge_backends(edges):
    program = wam.Program()
    edge_w = program.relation('edge', 2)
    for left, right in edges:
        program.fact(edge_w(left, right))

    @mk.relation
    def edgeo(left, right):
        return mk.any(*(
            mk.eq((left, right), edge)
            for edge in edges
        ))

    return program, edge_w, edgeo


def make_path_module():
    module = dsl.Module('graph')
    edge = module.import_relation('edge', 2)
    path = module.export_relation('path', 2)
    left, right, middle = dsl.variables('left right middle')
    module.rule(path(left, right), edge(left, right))
    module.rule(path(left, right), edge(left, middle), path(middle, right))
    return module, edge, path


def solve_both(module, relation, query_args, select):
    program = wam.Program()
    wam_namespace = module.link_wam(program)
    mk_namespace = module.link_mk()
    query = relation(*query_args)
    return (
        wam_namespace.solve(query, select=select),
        mk_namespace.solve(query, select=select),
    )


##
## Portable language


def test_term_construction():
    x = dsl.var('x')

    assert dsl.struct('pair', 1, x) == dsl.Struct('pair', (1, x))
    assert dsl.llist(1, 2, tail=x) == dsl.cons(1, dsl.cons(2, x))
    assert dsl.symbol('hello') == dsl.Symbol('hello')

    with pytest.raises(TypeError, match='tuples'):
        dsl.struct('box', (1, 2))

    with pytest.raises(TypeError, match='mappings'):
        dsl.struct('box', {'x': 1})


def test_relation_declarations_are_stable_and_typed():
    module = dsl.Module('m')

    relation = module.export_relation('value', 1)

    assert module.export_relation('value', 1) is relation
    assert relation.exported
    assert not relation.imported

    with pytest.raises(dsl.DefinitionError, match='already declared'):
        module.import_relation('value', 1)

    with pytest.raises(TypeError):
        relation(1, 2)


def test_imported_relations_cannot_be_defined():
    module = dsl.Module('m')
    external = module.import_relation('external', 1)

    with pytest.raises(dsl.DefinitionError, match='cannot define imported'):
        module.fact(external(1))


def test_cross_module_calls_require_an_explicit_import():
    left = dsl.Module('left')
    right = dsl.Module('right')
    source = left.export_relation('source', 1)
    target = right.export_relation('target', 1)
    x = dsl.var('x')

    with pytest.raises(dsl.DefinitionError, match='belongs to another module'):
        right.rule(target(x), source(x))


def test_import_goal_contract():
    module = dsl.Module('m')

    less = module.import_goal('less', 2, ground_inputs=(0, 1))

    assert less.ground_inputs == (0, 1)
    assert module.import_goal('less', 2, ground_inputs=(0, 1)) is less

    with pytest.raises(dsl.DefinitionError, match='different contract'):
        module.import_goal('less', 2, ground_inputs=(0,))

    with pytest.raises(ValueError):
        module.import_goal('bad', 2, ground_inputs=(2,))


##
## Shared execution


def test_facts_run_on_both_backends():
    module = dsl.Module('colors')
    color = module.export_relation('color', 1)
    module.fact(color('red'))
    module.fact(color('green'))
    module.fact(color('blue'))
    out = dsl.var('out')

    wam_answers, mk_answers = solve_both(module, color, (out,), out)

    assert wam_answers == ['red', 'green', 'blue']
    assert mk_answers == wam_answers


def test_query_projection_shapes_are_host_values():
    module = dsl.Module('pairs')
    pair = module.export_relation('pair', 2)
    module.fact(pair('a', 1))
    module.fact(pair('b', 2))
    left, right = dsl.variables('left right')

    for namespace in (
            module.link_wam(wam.Program()),
            module.link_mk(),
    ):
        assert namespace.solve(
            pair(left, right),
            select=(left, right),
        ) == [('a', 1), ('b', 2)]
        assert namespace.solve(
            pair(left, right),
            select={'name': left, 'number': right},
        ) == [
            {'name': 'a', 'number': 1},
            {'name': 'b', 'number': 2},
        ]


def test_unification_true_and_fail():
    module = dsl.Module('unification')
    chosen = module.export_relation('chosen', 1)
    x = dsl.var('x')
    module.rule(chosen(x), dsl.unify(x, dsl.struct('box', 3)), dsl.TRUE)
    module.rule(chosen('never'), dsl.FAIL)
    out = dsl.var('out')

    wam_answers, mk_answers = solve_both(module, chosen, (out,), out)

    assert wam_answers == [dsl.struct('box', 3)]
    assert mk_answers == wam_answers


def test_recursive_imported_relation():
    module, edge, path = make_path_module()
    program, edge_w, edgeo = make_edge_backends((
        ('a', 'b'),
        ('b', 'c'),
        ('a', 'd'),
    ))
    wam_namespace = module.link_wam(program, imports={edge: edge_w})
    mk_namespace = module.link_mk(imports={edge: edgeo})
    out = dsl.var('out')

    assert wam_namespace.solve(path('a', out), select=out) == ['b', 'd', 'c']
    assert mk_namespace.solve(path('a', out), select=out) == ['b', 'd', 'c']


def test_relational_append_runs_in_multiple_directions():
    module = dsl.Module('lists')
    append = module.export_relation('append', 3)
    head, tail, right, rest = dsl.variables('head tail right rest')
    module.rule(append(dsl.NIL, right, right))
    module.rule(
        append(dsl.cons(head, tail), right, dsl.cons(head, rest)),
        append(tail, right, rest),
    )
    left, right_query = dsl.variables('left right_query')

    expected = [
        ([], [1, 2, 3]),
        ([1], [2, 3]),
        ([1, 2], [3]),
        ([1, 2, 3], []),
    ]

    for namespace in (
            module.link_wam(wam.Program()),
            module.link_mk(),
    ):
        assert namespace.solve(
            append(left, right_query, [1, 2, 3]),
            select=(left, right_query),
        ) == expected
        assert namespace.solve(
            append([1, 2], [3, 4], left),
            select=left,
        ) == [[1, 2, 3, 4]]


def test_guards_and_projections():
    module = dsl.Module('numbers')
    value = module.relation('value', 1)
    successor = module.export_relation('successor', 2)
    even_successor = module.export_relation('even_successor', 2)
    x, y = dsl.variables('x y')
    for item in range(5):
        module.fact(value(item))
    module.rule(
        successor(x, y),
        value(x),
        dsl.project(y, lambda item: item + 1, x),
    )
    module.rule(
        even_successor(x, y),
        successor(x, y),
        dsl.guard(lambda item: item % 2 == 0, y),
    )
    out_x, out_y = dsl.variables('out_x out_y')

    for namespace in (
            module.link_wam(wam.Program()),
            module.link_mk(),
    ):
        assert namespace.solve(
            even_successor(out_x, out_y),
            select=(out_x, out_y),
        ) == [(1, 2), (3, 4)]


def test_host_operations_receive_and_return_neutral_values():
    module = dsl.Module('host')
    copy = module.export_relation('copy', 2)
    left, right = dsl.variables('left right')

    expected_source = dsl.Struct('payload', ([1, 2], dsl.symbol('tag')))

    def inspect_and_copy(value):
        assert isinstance(value, dsl.Struct)
        assert value == expected_source
        return dsl.struct('copied', value)

    module.rule(copy(left, right), dsl.project(right, inspect_and_copy, left))
    source = dsl.struct('payload', [1, 2], dsl.symbol('tag'))
    expected = dsl.Struct('copied', (expected_source,))

    for namespace in (
            module.link_wam(wam.Program()),
            module.link_mk(),
    ):
        assert namespace.solve(copy(source, right), select=right) == [expected]


def test_improper_lists_are_normalized():
    module = dsl.Module('lists')
    identity = module.export_relation('identity', 2)
    x = dsl.var('x')
    module.rule(identity(x, x))
    out = dsl.var('out')
    value = dsl.llist(1, 2, tail='tail')
    expected = dsl.ListValue((1, 2), 'tail')

    for namespace in (
            module.link_wam(wam.Program()),
            module.link_mk(),
    ):
        assert namespace.solve(identity(value, out), select=out) == [expected]


def test_symbols_are_distinct_from_strings():
    module = dsl.Module('symbols')
    value = module.export_relation('value', 1)
    module.fact(value('name'))
    module.fact(value(dsl.symbol('name')))
    out = dsl.var('out')

    for namespace in (
            module.link_wam(wam.Program()),
            module.link_mk(),
    ):
        assert namespace.solve(value(out), select=out) == [
            'name',
            dsl.symbol('name'),
        ]


##
## Imports and native composition


def test_missing_relation_imports_are_rejected():
    module, edge, _ = make_path_module()

    with pytest.raises(dsl.LinkError, match='missing WAM import'):
        module.link_wam(wam.Program())

    with pytest.raises(dsl.LinkError, match='missing miniKanren import'):
        module.link_mk()

    unrelated = dsl.Module('other').import_relation('edge', 2)

    with pytest.raises(dsl.LinkError, match='not an imported relation'):
        module.link_wam(wam.Program(), imports={unrelated: wam.Relation('edge', 2)})

    assert edge.imported


def test_imported_backend_primitives():
    module = dsl.Module('ordering')
    less = module.import_goal('less', 2, ground_inputs=(0, 1))
    value = module.relation('value', 1)
    ordered = module.export_relation('ordered', 2)
    left, right = dsl.variables('left right')
    for item in (1, 2, 3):
        module.fact(value(item))
    module.rule(ordered(left, right), value(left), value(right), less(left, right))

    wam_namespace = module.link_wam(
        wam.Program(),
        primitives={
            less: lambda a, b: wam.guard(lambda x, y: x < y, a, b),
        },
    )
    mk_namespace = module.link_mk(
        primitives={
            less: mk.fd_lt,
        },
    )

    expected = [(1, 2), (1, 3), (2, 3)]
    assert wam_namespace.solve(ordered(left, right), select=(left, right)) == expected
    assert mk_namespace.solve(ordered(left, right), select=(left, right)) == expected


def test_missing_primitive_bindings_are_rejected():
    module = dsl.Module('primitive')
    predicate = module.import_goal('predicate', 1)
    accepted = module.export_relation('accepted', 1)
    x = dsl.var('x')
    module.rule(accepted(x), predicate(x))

    with pytest.raises(dsl.LinkError, match='missing WAM primitive'):
        module.link_wam(wam.Program())

    with pytest.raises(dsl.LinkError, match='missing miniKanren primitive'):
        module.link_mk()


def test_wam_common_relations_are_ordinary_extendable_relations():
    module, edge, path = make_path_module()
    program, edge_w, _ = make_edge_backends((
        ('a', 'b'),
        ('b', 'c'),
    ))
    namespace = module.link_wam(program, imports={edge: edge_w})
    path_w = namespace[path]
    program.fact(path_w('c', 'd'))
    out = dsl.var('out')

    assert namespace.solve(path('a', out), select=out) == ['b', 'c', 'd']


def test_wam_native_rules_can_call_portable_relations_and_cut():
    module = dsl.Module('choices')
    choice = module.export_relation('choice', 1)
    module.fact(choice(1))
    module.fact(choice(2))
    program = wam.Program()
    namespace = module.link_wam(program)
    first = program.relation('first', 1)
    native_x = wam.var('native_x')
    program.rule(first(native_x), namespace[choice](native_x), wam.CUT)

    assert [solution[native_x] for solution in program.solve(first(native_x))] == [1]


def test_mk_native_goals_can_constrain_portable_relations():
    module = dsl.Module('values')
    value = module.export_relation('value', 1)
    for item in (1, 2, 3):
        module.fact(value(item))
    namespace = module.link_mk()
    x = mk.var('x')

    assert mk.run_star(
        x,
        mk.all(namespace[value](x), mk.neq(x, 2)),
    ) == [1, 3]


def test_mk_extensions_are_open_recursive():
    module, edge, path = make_path_module()
    _, _, edgeo = make_edge_backends((
        ('a', 'b'),
        ('b', 'c'),
    ))
    builder = module.mk_builder(imports={edge: edgeo})

    def extra_clause(namespace, left, right):
        return mk.eq((left, right), ('c', 'd'))

    builder.extend(path, extra_clause)
    namespace = builder.build()
    out = dsl.var('out')

    assert namespace.solve(path('a', out), select=out) == ['b', 'c', 'd']


def test_mk_builder_freezes_after_build():
    module = dsl.Module('m')
    value = module.export_relation('value', 1)
    module.fact(value(1))
    builder = module.mk_builder()
    namespace = builder.build()

    assert namespace[value]

    with pytest.raises(dsl.FrozenError):
        builder.table(value)

    with pytest.raises(dsl.FrozenError):
        builder.extend(value, lambda namespace, item: mk.fail)

    with pytest.raises(dsl.FrozenError):
        builder.build()


def test_mk_tabling_handles_a_cyclic_graph():
    module, edge, path = make_path_module()
    _, _, edgeo = make_edge_backends((
        ('a', 'b'),
        ('b', 'c'),
        ('c', 'a'),
        ('c', 'd'),
    ))
    namespace = module.link_mk(imports={edge: edgeo}, tabled={path})
    out = dsl.var('out')

    assert namespace.tabled == {path}
    assert namespace.solve(path('a', out), select=out) == ['b', 'c', 'a', 'd']


def test_mk_residual_constraints_cross_the_facade():
    module = dsl.Module('constraints')
    different = module.import_goal('different', 2)
    not_five = module.export_relation('not_five', 1)
    x = dsl.var('x')
    module.rule(not_five(x), different(x, 5))
    namespace = module.link_mk(primitives={different: mk.neq})

    assert namespace.solve(not_five(x), select=x) == [
        dsl.Constrained(
            dsl.Unbound('_0'),
            (
                dsl.Residual('=/=', (dsl.Unbound('_0'), 5)),
            ),
        ),
    ]


def test_modules_compose_through_backend_import_bindings():
    lists = dsl.Module('lists')
    member = lists.export_relation('member', 2)
    head, tail, item = dsl.variables('head tail item')
    lists.rule(member(head, dsl.cons(head, tail)))
    lists.rule(member(item, dsl.cons(head, tail)), member(item, tail))

    app = dsl.Module('app')
    imported_member = app.import_relation('member', 2)
    contains = app.export_relation('contains', 2)
    value, collection = dsl.variables('value collection')
    app.rule(contains(collection, value), imported_member(value, collection))

    program = wam.Program()
    lists_w = lists.link_wam(program)
    app_w = app.link_wam(program, imports={imported_member: lists_w[member]})
    lists_k = lists.link_mk()
    app_k = app.link_mk(imports={imported_member: lists_k[member]})
    out = dsl.var('out')

    assert app_w.solve(contains([1, 2, 3], out), select=out) == [1, 2, 3]
    assert app_k.solve(contains([1, 2, 3], out), select=out) == [1, 2, 3]


##
## Backend semantics and linker controls


def test_wam_prefix_and_relation_override():
    module = dsl.Module('m')
    value = module.export_relation('value', 1)
    module.fact(value(1))

    prefixed_program = wam.Program()
    prefixed = module.link_wam(prefixed_program, prefix='portable_')

    assert prefixed[value].name == 'portable_value'
    assert prefixed.solve(value(1), select=1) == [1]

    overridden_program = wam.Program()
    custom = overridden_program.relation('custom', 1)
    overridden = module.link_wam(overridden_program, relations={value: custom})

    assert overridden[value] is custom
    assert overridden.solve(value(1), select=1) == [1]


def test_export_lookup():
    module = dsl.Module('m')
    value = module.export_relation('value', 1)
    module.fact(value(1))
    wam_namespace = module.link_wam(wam.Program())
    mk_namespace = module.link_mk()

    assert wam_namespace.export('value') is wam_namespace[value]
    assert mk_namespace.export('value', 1) is mk_namespace[value]

    with pytest.raises(KeyError):
        wam_namespace.export('missing')


def test_unbound_answers_are_normalized():
    module = dsl.Module('empty')
    wam_namespace = module.link_wam(wam.Program())
    mk_namespace = module.link_mk()
    x = dsl.var('x')

    assert wam_namespace.solve(select=x) == [dsl.Unbound('_0')]
    assert mk_namespace.solve(select=x) == [dsl.Unbound('_0')]


def test_occurs_check_is_intentionally_not_portable():
    module = dsl.Module('cycles')
    wam_namespace = module.link_wam(wam.Program())
    mk_namespace = module.link_mk()
    x = dsl.var('x')
    goal = dsl.unify(x, dsl.struct('f', x))

    wam_answers = wam_namespace.solve(goal, select=x)
    mk_answers = mk_namespace.solve(goal, select=x)
    mk_nocheck_answers = mk_namespace.solve(goal, select=x, occurs_check=False)

    assert len(wam_answers) == 1
    assert isinstance(wam_answers[0], dsl.Struct)
    assert isinstance(wam_answers[0].args[0], dsl.Cycle)
    assert mk_answers == []
    assert len(mk_nocheck_answers) == 1
    assert isinstance(mk_nocheck_answers[0].args[0], dsl.Cycle)


def test_query_limits_are_forwarded():
    module = dsl.Module('values')
    value = module.export_relation('value', 1)
    for item in range(10):
        module.fact(value(item))
    out = dsl.var('out')

    for namespace in (
            module.link_wam(wam.Program()),
            module.link_mk(),
    ):
        assert namespace.solve(value(out), select=out, limit=3) == [0, 1, 2]
        assert namespace.solve(value(out), select=out, limit=0) == []


def test_linking_uses_a_module_snapshot():
    module = dsl.Module('snapshot')
    value = module.export_relation('value', 1)
    module.fact(value(1))
    wam_namespace = module.link_wam(wam.Program())
    mk_namespace = module.link_mk()
    module.fact(value(2))
    out = dsl.var('out')

    assert wam_namespace.solve(value(out), select=out) == [1]
    assert mk_namespace.solve(value(out), select=out) == [1]

    assert module.link_wam(wam.Program()).solve(value(out), select=out) == [1, 2]
    assert module.link_mk().solve(value(out), select=out) == [1, 2]


def test_project_results_must_be_ground():
    module = dsl.Module('bad_project')
    broken = module.export_relation('broken', 1)
    x = dsl.var('x')
    module.rule(broken(x), dsl.project(x, lambda: dsl.var('fresh')))

    with pytest.raises(TypeError, match='ground'):
        module.link_wam(wam.Program()).solve(broken(x), select=x)

    with pytest.raises(TypeError, match='ground'):
        module.link_mk().solve(broken(x), select=x)


def test_search_strategy_remains_backend_specific():
    module = dsl.Module('search')
    answer = module.export_relation('answer', 1)
    x = dsl.var('x')
    module.rule(answer(x), answer(x))
    module.fact(answer('ok'))

    mk_namespace = module.link_mk()
    assert mk_namespace.solve(
        answer(x),
        select=x,
        limit=1,
        max_steps=100,
    ) == ['ok']

    wam_namespace = module.link_wam(wam.Program())
    with pytest.raises(wam.StepLimitExceeded):
        wam_namespace.solve(
            answer(x),
            select=x,
            limit=1,
            max_steps=100,
        )
