"""
Side-by-side examples for ``wam.py`` and ``mk.py``.

The examples intentionally solve the same small problems with both engines. They show where the surface syntax is merely
different and where the operational models lead to materially different programs.
"""
import pprint

from .. import mk
from .. import wam


##
## Logical append and relational splitting


def append_comparison() -> dict[str, object]:
    """Split a known list at every position with each engine."""

    wam_program = wam.Program()
    wam_append = wam_program.relation('append', 3)
    item, left_tail, right, out_tail = wam.variables(
        'item left_tail right out_tail'
    )

    wam_program.fact(wam_append(wam.NIL, right, right))
    wam_program.rule(
        wam_append(
            wam.cons(item, left_tail),
            right,
            wam.cons(item, out_tail),
        ),
        wam_append(left_tail, right, out_tail),
    )

    wam_left, wam_right = wam.variables('left right')
    wam_results = [
        (solution[wam_left], solution[wam_right])
        for solution in wam_program.solve(
            wam_append(wam_left, wam_right, [1, 2, 3])
        )
    ]

    mk_left, mk_right = mk.variables('left right')
    mk_results = mk.run_star(
        (mk_left, mk_right),
        mk.appendo(mk_left, mk_right, [1, 2, 3]),
    )

    assert wam_results == mk_results
    return {
        'wam': wam_results,
        'minikanren': mk_results,
    }


##
## Recursive reachability


def reachability_comparison() -> dict[str, object]:
    """Compute the same acyclic dependency closure in both engines."""

    edges = (
        ('frontend', 'api'),
        ('api', 'auth'),
        ('api', 'orders'),
        ('auth', 'database'),
        ('orders', 'database'),
    )

    wam_program = wam.Program()
    wam_edge = wam_program.relation('edge', 2)
    wam_path = wam_program.relation('path', 2)
    for left, right in edges:
        wam_program.fact(wam_edge(left, right))

    wam_left, wam_right, wam_middle = wam.variables('left right middle')
    wam_program.rule(
        wam_path(wam_left, wam_right),
        wam_edge(wam_left, wam_right),
    )
    wam_program.rule(
        wam_path(wam_left, wam_right),
        wam_edge(wam_left, wam_middle),
        wam_path(wam_middle, wam_right),
    )

    wam_out = wam.var('out')
    wam_results = [
        solution[wam_out]
        for solution in wam_program.solve(wam_path('frontend', wam_out))
    ]

    @mk.relation
    def mk_edge(left, right):
        return mk.any(*(
            mk.eq((left, right), edge)
            for edge in edges
        ))

    @mk.tabled
    def mk_path(left, right):
        return mk.conde(
            (mk_edge(left, right),),
            (mk.fresh(lambda middle: mk.all(
                mk_edge(left, middle),
                mk_path(middle, right),
            )),),
        )

    mk_out = mk.var('out')
    mk_results = mk.run_star(mk_out, mk_path('frontend', mk_out))

    assert set(wam_results) == set(mk_results)
    return {
        'wam': wam_results,
        'minikanren': mk_results,
        'same_answer_set': True,
        'note': (
            'The miniKanren relation is tabled, so the same definition also '
            'terminates when cycles are added to the graph.'
        ),
    }


##
## Finite-domain arithmetic


def arithmetic_comparison() -> dict[str, object]:
    """Find 0 <= x,y <= 10 with x + y == 10 and x < y."""

    wam_program = wam.Program()
    wam_value = wam_program.relation('value', 1)
    wam_pair = wam_program.relation('pair', 2)
    for value in range(11):
        wam_program.fact(wam_value(value))

    wam_x, wam_y = wam.variables('x y')
    wam_program.rule(
        wam_pair(wam_x, wam_y),
        wam_value(wam_x),
        wam_value(wam_y),
        wam.guard(
            lambda left, right: left + right == 10 and left < right,
            wam_x,
            wam_y,
            name='sum_and_order',
        ),
    )

    wam_results = [
        (solution[wam_x], solution[wam_y])
        for solution in wam_program.solve(wam_pair(wam_x, wam_y))
    ]

    mk_x, mk_y = mk.variables('x y')
    mk_results = mk.run_star(
        (mk_x, mk_y),
        mk.in_(mk_x, mk.interval(0, 10)),
        mk.in_(mk_y, mk.interval(0, 10)),
        mk.fd_add(mk_x, mk_y, 10),
        mk.fd_lt(mk_x, mk_y),
        mk.label(mk_x, mk_y),
    )

    assert wam_results == mk_results
    return {
        'wam_generate_then_test': wam_results,
        'minikanren_constraint_propagation': mk_results,
    }


##
## Ground host-language computation


def projection_comparison() -> dict[str, object]:
    """Use an ordinary Python function inside each logic program."""

    wam_program = wam.Program()
    wam_successor = wam_program.relation('successor', 2)
    wam_before, wam_after = wam.variables('before after')
    wam_program.rule(
        wam_successor(wam_before, wam_after),
        wam.project(wam_after, lambda value: value + 1, wam_before),
    )

    wam_out = wam.var('out')
    wam_results = [
        solution[wam_out]
        for solution in wam_program.solve(wam_successor(41, wam_out))
    ]

    mk_out = mk.var('out')
    mk_results = mk.run_star(
        mk_out,
        mk.is_(mk_out, lambda value: value + 1, 41),
    )

    assert wam_results == mk_results == [42]
    return {
        'wam_project': wam_results,
        'minikanren_is': mk_results,
        'note': 'Both forms require their Python-function inputs to be ground.',
    }


##
## Deliberate search-semantics contrast


def fair_search_contrast() -> dict[str, object]:
    """Put an infinite branch before a productive branch."""

    wam_program = wam.Program()
    wam_answer = wam_program.relation('answer', 1)
    wam_value = wam.var('value')
    wam_program.rule(wam_answer(wam_value), wam_answer(wam_value))
    wam_program.fact(wam_answer('ok'))

    wam_result: object
    try:
        wam_result = [
            solution[wam_value]
            for solution in wam_program.solve(
                wam_answer(wam_value),
                config=wam.MachineConfig(max_steps=100),
            )
        ]
    except wam.StepLimitExceeded:
        wam_result = 'step limit reached before the second clause'

    @mk.relation
    def mk_answer(value):
        return mk.conde(
            (mk.delay(lambda: mk_answer(value)),),
            (mk.eq(value, 'ok'),),
        )

    mk_value = mk.var('value')
    mk_result = mk.run(1, mk_value, mk_answer(mk_value), max_steps=1_000)

    assert mk_result == ['ok']
    return {
        'wam_depth_first': wam_result,
        'minikanren_interleaving': mk_result,
    }


##


def run_comparisons() -> dict[str, object]:
    return {
        'append': append_comparison(),
        'reachability': reachability_comparison(),
        'arithmetic': arithmetic_comparison(),
        'projection': projection_comparison(),
        'fair_search': fair_search_contrast(),
    }


def _main() -> None:
    pprint.pp(run_comparisons(), sort_dicts=False)


if __name__ == '__main__':
    _main()
