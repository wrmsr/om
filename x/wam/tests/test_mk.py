import pytest

from .. import mk


##


def test_basic_unification_reifies_shared_variables():
    x, y = mk.variables('x y')

    assert mk.run_star(
        (x, y),
        mk.eq(mk.struct('pair', x, x), mk.struct('pair', 1, y)),
    ) == [(1, 1)]


def test_atom_equality_distinguishes_bool_and_int():
    x = mk.var('x')

    assert mk.run_star(x, mk.eq(True, 1), mk.eq(x, 'bad')) == []
    assert mk.run_star(x, mk.conde((mk.eq(x, True),), (mk.eq(x, 1),))) == [True, 1]


def test_python_tuples_and_mappings_unify_structurally():
    x, y = mk.variables('x y')

    assert mk.run_star(
        (x, y),
        mk.eq(
            {'kind': 'event', 'payload': (x, 2)},
            {'kind': 'event', 'payload': (1, y)},
        ),
    ) == [(1, 2)]


def test_occurs_check_rejects_cycles_by_default_and_nocheck_reifies_them():
    x = mk.var('x')
    recursive = mk.struct('f', x)

    assert mk.run_star(x, mk.eq(x, recursive)) == []

    result = mk.run_nocheck(None, x, mk.eq(x, recursive))

    assert len(result) == 1
    assert result[0].functor == 'f'
    assert isinstance(result[0].args[0], mk.Cycle)


def test_fair_disjunction_reaches_a_sibling_of_an_infinite_branch():
    @mk.relation
    def loopo(value):
        return loopo(value)

    out = mk.var('out')

    assert mk.run(
        1,
        out,
        mk.conde(
            (loopo(out),),
            (mk.eq(out, 'reachable'),),
        ),
        max_steps=100,
    ) == ['reachable']


def test_run_limit_does_not_force_the_tail_after_enough_answers():
    @mk.relation
    def loopo(value):
        return loopo(value)

    out = mk.var('out')

    assert mk.run(
        1,
        out,
        mk.conde(
            (mk.eq(out, 'first'),),
            (loopo(out),),
        ),
        max_steps=20,
    ) == ['first']


def test_recursive_appendo_runs_forward_and_backward():
    out = mk.var('out')

    assert mk.run_star(out, mk.appendo([1, 2], [3, 4], out)) == [[1, 2, 3, 4]]

    left, right = mk.variables('left right')
    assert mk.run_star((left, right), mk.appendo(left, right, [1, 2])) == [
        ([], [1, 2]),
        ([1], [2]),
        ([1, 2], []),
    ]


def test_improper_logical_list_preserves_its_tail():
    out = mk.var('out')

    assert mk.run_star(out, mk.eq(out, mk.cons(1, 2))) == [
        mk.ListValue((1,), 2),
    ]


def test_member1o_uses_disequality_to_remove_duplicate_proofs():
    out = mk.var('out')

    assert mk.run_star(out, mk.membero(out, [1, 1, 2])) == [1, 1, 2]
    assert mk.run_star(out, mk.member1o(out, [1, 1, 2])) == [1, 2]


def test_disequality_delays_and_is_reported_as_a_residual_constraint():
    out = mk.var('out')

    result = mk.run_star(out, mk.neq(out, 5))

    assert len(result) == 1
    assert isinstance(result[0], mk.Constrained)
    assert result[0].value == mk.ReifiedVar('_0')
    assert result[0].constraints == (
        mk.Residual('=/=', (mk.ReifiedVar('_0'), 5)),
    )

    assert mk.run_star(out, mk.neq(out, 5), mk.eq(out, 6)) == [6]
    assert mk.run_star(out, mk.neq(out, 5), mk.eq(out, 5)) == []


def test_structural_disequality_waits_for_the_deciding_binding():
    x = mk.var('x')
    pair = mk.struct('pair', x, 2)

    assert mk.run_star(x, mk.neq(pair, mk.struct('pair', 1, 2)), mk.eq(x, 1)) == []
    assert mk.run_star(x, mk.neq(pair, mk.struct('pair', 1, 2)), mk.eq(x, 3)) == [3]


def test_type_constraints_delay_and_then_validate():
    out = mk.var('out')

    residual = mk.run_star(out, mk.symbolo(out))[0]
    assert isinstance(residual, mk.Constrained)
    assert residual.constraints == (
        mk.Residual('symbolo', (mk.ReifiedVar('_0'),)),
    )

    assert mk.run_star(out, mk.symbolo(out), mk.eq(out, mk.symbol('ready'))) == [mk.symbol('ready')]
    assert mk.run_star(out, mk.symbolo(out), mk.eq(out, 'ready')) == []
    assert mk.run_star(out, mk.stringo(out), mk.eq(out, 'ready')) == ['ready']
    assert mk.run_star(out, mk.numbero(out), mk.eq(out, True)) == []


def test_absento_constrains_all_present_and_future_subterms():
    x = mk.var('x')

    assert mk.run_star(x, mk.absento('secret', mk.struct('msg', x)), mk.eq(x, 'public')) == ['public']
    assert mk.run_star(x, mk.absento('secret', mk.struct('msg', x)), mk.eq(x, 'secret')) == []
    assert mk.run_star(x, mk.absento(x, ['public', 'secret']), mk.eq(x, 'secret')) == []


def test_featureo_matches_a_partial_mapping_and_can_bind_values():
    kind = mk.var('kind')
    event = mk.var('event')

    assert mk.run_star(
        kind,
        mk.featureo({'kind': kind}, event),
        mk.eq(event, {'kind': 'deploy', 'region': 'west'}),
    ) == ['deploy']

    assert mk.run_star(
        event,
        mk.featureo({'missing': 1}, event),
        mk.eq(event, {'kind': 'deploy'}),
    ) == []


def test_onceo_returns_only_the_first_answer():
    out = mk.var('out')

    assert mk.run_star(
        out,
        mk.onceo(mk.conde((mk.eq(out, 1),), (mk.eq(out, 2),))),
    ) == [1]


def test_conda_soft_cut_commits_after_the_first_clause_head_succeeds():
    out = mk.var('out')

    assert mk.run_star(
        out,
        mk.conda(
            (
                mk.conde((mk.eq(out, 1),), (mk.eq(out, 2),)),
                mk.eq(out, 2),
            ),
            (mk.eq(out, 3),),
        ),
    ) == [2]


def test_condu_committed_choice_uses_only_the_first_head_answer():
    out = mk.var('out')

    assert mk.run_star(
        out,
        mk.condu(
            (
                mk.conde((mk.eq(out, 1),), (mk.eq(out, 2),)),
                mk.eq(out, 2),
            ),
            (mk.eq(out, 3),),
        ),
    ) == []


def test_project_predicate_and_is_are_explicitly_directional():
    x, y = mk.variables('x y')

    assert mk.run_star(
        y,
        mk.eq(x, 41),
        mk.is_(y, lambda value: value + 1, x),
        mk.pred(y, lambda value: value % 2 == 0),
    ) == [42]

    with pytest.raises(mk.InstantiationError):
        mk.run_star(y, mk.is_(y, lambda value: value + 1, x))


def test_lvaro_and_nonlvaro_observe_the_current_substitution():
    out = mk.var('out')

    assert len(mk.run_star(out, mk.lvaro(out))) == 1
    assert mk.run_star(out, mk.nonlvaro(out)) == []
    assert mk.run_star(out, mk.eq(out, 1), mk.nonlvaro(out)) == [1]


def test_fd_arithmetic_ordering_and_labelling():
    left, right = mk.variables('left right')

    assert mk.run_star(
        (left, right),
        mk.in_(left, mk.interval(0, 5)),
        mk.in_(right, mk.interval(0, 5)),
        mk.fd_add(left, right, 5),
        mk.fd_lt(left, right),
        mk.label(left, right),
    ) == [
        (0, 5),
        (1, 4),
        (2, 3),
    ]


def test_fd_constraints_leave_useful_residual_domains_without_labelling():
    left, right = mk.variables('left right')

    result = mk.run_star(
        (left, right),
        mk.in_(left, mk.interval(0, 5)),
        mk.in_(right, mk.interval(0, 5)),
        mk.fd_add(left, right, 5),
        mk.fd_lt(left, right),
    )[0]

    assert isinstance(result, mk.Constrained)
    assert result.value == (mk.ReifiedVar('_0'), mk.ReifiedVar('_1'))
    assert mk.Residual('fd_add', (mk.ReifiedVar('_0'), mk.ReifiedVar('_1'), 5)) in result.constraints
    assert mk.Residual('fd_lt', (mk.ReifiedVar('_0'), mk.ReifiedVar('_1'))) in result.constraints


def test_all_different_solves_a_small_assignment_problem():
    alice, bob, carol = mk.variables('alice bob carol')

    assert set(mk.run_star(
        (alice, bob, carol),
        mk.in_(alice, mk.domain(1, 2)),
        mk.in_(bob, mk.domain(1, 2, 3)),
        mk.in_(carol, mk.domain(2, 3)),
        mk.all_different(alice, bob, carol),
        mk.fd_lt(alice, carol),
        mk.label(alice, bob, carol),
    )) == {
        (1, 2, 3),
        (1, 3, 2),
        (2, 1, 3),
    }


def test_fd_multiplication_modulus_and_quotient():
    x, y = mk.variables('x y')

    assert mk.run_star(
        (x, y),
        mk.in_(x, mk.interval(1, 10)),
        mk.in_(y, mk.interval(0, 10)),
        mk.fd_mul(x, 3, 18),
        mk.fd_mod(x, 4, y),
        mk.label(x, y),
    ) == [(6, 2)]

    quotient = mk.var('quotient')
    assert mk.run_star(
        quotient,
        mk.in_(quotient, mk.interval(0, 10)),
        mk.fd_quot(17, 5, quotient),
        mk.label(quotient),
    ) == [3]


def test_tabling_terminates_on_a_cyclic_graph_and_deduplicates_answers():
    @mk.relation
    def edge(left, right):
        return mk.conde(
            (mk.eq((left, right), ('a', 'b')),),
            (mk.eq((left, right), ('b', 'c')),),
            (mk.eq((left, right), ('c', 'a')),),
            (mk.eq((left, right), ('c', 'd')),),
        )

    @mk.tabled
    def path(left, right):
        return mk.conde(
            (edge(left, right),),
            (mk.fresh(lambda middle: mk.all(
                edge(left, middle),
                path(middle, right),
            )),),
        )

    out = mk.var('out')

    assert mk.run_star(out, path('a', out), max_steps=10_000) == ['b', 'c', 'a', 'd']


def test_tabling_supports_direct_left_recursion():
    @mk.relation
    def edge(left, right):
        return mk.conde(
            (mk.eq((left, right), ('a', 'b')),),
            (mk.eq((left, right), ('b', 'c')),),
        )

    @mk.tabled
    def path(left, right):
        return mk.conde(
            (mk.fresh(lambda middle: mk.all(
                path(left, middle),
                edge(middle, right),
            )),),
            (edge(left, right),),
        )

    out = mk.var('out')

    assert mk.run_star(out, path('a', out), max_steps=10_000) == ['b', 'c']


def test_tabled_answers_freshen_their_internal_variables_on_reuse():
    @mk.tabled
    def repeated_pair(value):
        return mk.fresh(lambda item: mk.eq(value, mk.struct('pair', item, item)))

    left, right = mk.variables('left right')

    results = mk.run_star(
        (left, right),
        repeated_pair(left),
        repeated_pair(right),
    )

    assert len(results) == 1
    left_pair, right_pair = results[0]
    assert left_pair.args[0] == left_pair.args[1]
    assert right_pair.args[0] == right_pair.args[1]
    assert left_pair.args[0] != right_pair.args[0]


def test_tables_are_scoped_to_each_run():
    calls = []

    @mk.tabled
    def observed(value):
        calls.append('call')
        return mk.eq(value, 1)

    out = mk.var('out')

    assert mk.run_star(out, observed(out)) == [1]
    assert mk.run_star(out, observed(out)) == [1]
    assert calls == ['call', 'call']


def test_tabled_finite_domain_answer_preserves_its_residual_domain():
    @mk.tabled
    def small(value):
        return mk.in_(value, mk.interval(1, 3))

    out = mk.var('out')
    result = mk.run_star(out, small(out))[0]

    assert isinstance(result, mk.Constrained)
    assert mk.Residual('in_', (mk.ReifiedVar('_0'), mk.interval(1, 3))) in result.constraints


def test_trace_reports_goal_execution_without_exposing_mutable_state():
    events = []
    out = mk.var('out')

    assert mk.run_star(out, mk.eq(out, 1), trace=events.append) == [1]
    assert events
    assert events[0].step == 1
    assert events[-1].goal.startswith('eq(')


def test_step_limit_breaks_a_nonproductive_computation():
    @mk.relation
    def loopo(value):
        return loopo(value)

    out = mk.var('out')

    with pytest.raises(mk.StepLimitExceeded):
        mk.run_star(out, loopo(out), max_steps=20)


def test_tabled_general_query_remains_complete_across_cycles_and_predecessors():
    edges = (
        ('api', 'auth'),
        ('auth', 'common'),
        ('common', 'api'),
        ('common', 'target'),
        ('orders', 'common'),
        ('worker', 'orders'),
    )

    @mk.relation
    def edge(left, right):
        return mk.any(*(
            mk.eq((left, right), pair)
            for pair in edges
        ))

    @mk.tabled
    def path(left, right):
        return mk.conde(
            (edge(left, right),),
            (mk.fresh(lambda middle: mk.all(
                edge(left, middle),
                path(middle, right),
            )),),
        )

    out = mk.var('out')

    assert set(mk.run_star(
        out,
        path(out, 'target'),
        max_steps=50_000,
    )) == {
        'common',
        'auth',
        'api',
        'orders',
        'worker',
    }


def test_application_examples_execute_and_return_expected_results():
    from . import mk_examples

    results = mk_examples.run_examples()

    assert results['incident_staffing']['solution_count'] == 3
    assert set(results['vulnerability_blast_radius']['affected_components']) == {
        'common',
        'payments',
        'auth',
        'orders',
        'api',
        'worker',
        'frontend',
    }
    assert [
        'strip',
        'lower',
        'spaces_to_underscore',
    ] in results['pipeline_synthesis']['valid_three_step_pipelines']

    templates = results['deployment_template']['templates']
    assert len(templates) == 1
    assert isinstance(templates[0], mk.Constrained)


def test_wam_side_by_side_comparisons_execute():
    from . import compare

    results = compare.run_comparisons()

    assert results['append']['wam'] == results['append']['minikanren']
    assert results['reachability']['same_answer_set']
    assert (
        results['arithmetic']['wam_generate_then_test'] ==
        results['arithmetic']['minikanren_constraint_propagation']
    )
    assert results['projection']['wam_project'] == [42]
    assert results['fair_search']['minikanren_interleaving'] == ['ok']


@pytest.mark.parametrize(
    ('goal_factory', 'predicate'),
    [
        (mk.fd_eq, lambda left, right: left == right),
        (mk.fd_ne, lambda left, right: left != right),
        (mk.fd_lt, lambda left, right: left < right),
        (mk.fd_le, lambda left, right: left <= right),
        (mk.fd_gt, lambda left, right: left > right),
        (mk.fd_ge, lambda left, right: left >= right),
    ],
)
def test_fd_binary_relations_match_brute_force(goal_factory, predicate):
    left, right = mk.variables('left right')
    values = range(-2, 3)

    actual = set(mk.run_star(
        (left, right),
        mk.in_(left, values),
        mk.in_(right, values),
        goal_factory(left, right),
        mk.label(left, right),
    ))
    expected = {
        (left_value, right_value)
        for left_value in values
        for right_value in values
        if predicate(left_value, right_value)
    }

    assert actual == expected


@pytest.mark.parametrize(
    ('goal_factory', 'function'),
    [
        (mk.fd_add, lambda left, right: left + right),
        (mk.fd_sub, lambda left, right: left - right),
        (mk.fd_mul, lambda left, right: left * right),
    ],
)
def test_fd_arithmetic_relations_match_brute_force(goal_factory, function):
    left, right, out = mk.variables('left right out')
    inputs = range(-2, 3)
    outputs = range(-4, 5)

    actual = set(mk.run_star(
        (left, right, out),
        mk.in_(left, inputs),
        mk.in_(right, inputs),
        mk.in_(out, outputs),
        goal_factory(left, right, out),
        mk.label(left, right, out),
    ))
    expected = {
        (left_value, right_value, function(left_value, right_value))
        for left_value in inputs
        for right_value in inputs
        if function(left_value, right_value) in outputs
    }

    assert actual == expected


@pytest.mark.parametrize(
    ('goal_factory', 'function'),
    [
        (mk.fd_quot, lambda left, right: left // right),
        (mk.fd_mod, lambda left, right: left % right),
    ],
)
def test_fd_division_relations_match_python_integer_semantics(
        goal_factory,
        function,
):
    left, right, out = mk.variables('left right out')
    inputs = range(-3, 4)
    outputs = range(-4, 5)

    actual = set(mk.run_star(
        (left, right, out),
        mk.in_(left, inputs),
        mk.in_(right, inputs),
        mk.in_(out, outputs),
        goal_factory(left, right, out),
        mk.label(left, right, out),
    ))
    expected = {
        (left_value, right_value, function(left_value, right_value))
        for left_value in inputs
        for right_value in inputs
        if right_value and function(left_value, right_value) in outputs
    }

    assert actual == expected
