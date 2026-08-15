"""
A guided tutorial for the portable relational DSL in :mod:`dsl`.

The intended reader knows Python and broadly understands why logic programming is
useful, but has not used Prolog, a WAM, miniKanren, or their terminology.

The central idea is not that the two engines are secretly identical. They are not.
The shared DSL captures a useful declarative center and compiles it in two ways:

* the WAM backend installs ordinary clauses into an existing ``wam.Program``;
* the miniKanren backend generates ordinary ``mk.Goal``-returning relations.

The portable center contains:

* atoms, variables, explicit structures, and logical lists;
* facts and definite Horn-clause rules;
* structural unification;
* conjunction through rule bodies;
* disjunction through multiple clauses;
* true and failure;
* pure Python guards and projections whose inputs must be ground;
* imported relations and imported backend primitives.

The portable center intentionally does not pretend that these are equivalent:

* WAM cut and miniKanren committed choice;
* depth-first WAM search and fair miniKanren search;
* miniKanren constraints and WAM ground tests;
* miniKanren tabling and untabled WAM recursion;
* WAM rational trees and miniKanren's default occurs check.

A small vocabulary
------------------

portable module
    An inspectable collection of relation declarations and clauses. It is source
    data, not a third logic engine.

relation
    A named family of tuples that can be true. ``path/2`` means a relation named
    ``path`` with two arguments.

local relation
    A relation used internally by one portable module.

exported relation
    A relation intended for callers of the linked module.

imported relation
    A relation used by portable clauses but supplied by the surrounding backend
    application.

clause
    One fact or rule. Multiple clauses for one relation are alternatives.

term
    An atom, logic variable, explicit structure, or logical list.

unification
    Structural equality that can bind variables on either side.

linking
    Translating one portable module into backend-native relations and goals.

namespace
    The result of linking. ``namespace[portable_relation]`` returns the actual
    backend-native relation.

native overlay
    Backend-specific rules or goals composed with portable relations after, or
    while, linking.

query facade
    ``namespace.solve(..., select=...)``. It lowers portable query goals and
    normalizes backend answers into common ``dsl`` answer values.

The examples contain assertions, so this tutorial also serves as an integration
smoke test.
"""
import pprint
import textwrap

from .. import dsl
from .. import mk
from .. import wam


##
## Presentation helpers


def _chapter(number: int, title: str, explanation: str) -> None:
    print()
    print('=' * 78)
    print(f'{number}. {title}')
    print('=' * 78)
    print(textwrap.dedent(explanation).strip())


def _show(label: str, value: object) -> None:
    print(f'\n{label}:')
    pprint.pp(value, sort_dicts=False)


def _sets(values: list[object]) -> set[str]:
    return {repr(value) for value in values}


##
## 1. One definition, two backends


def one_definition_two_backends() -> None:
    _chapter(
        1,
        'One portable definition, two native backends',
        """
        A Module is a builder for portable relation declarations and clauses.
        export_relation('color', 2) declares color/2. Calling that relation creates
        a portable Call value; it does not execute anything and is not a Boolean.

        fact() adds a clause with no body. Linking takes a snapshot of the module.
        The returned WamNamespace and MkNamespace both understand the same portable
        query expression and normalize their answers to ordinary common values.
        """,
    )

    colors = dsl.Module('colors')
    color = colors.export_relation('color', 2)

    colors.fact(color('apple', 'red'))
    colors.fact(color('sky', 'blue'))
    colors.fact(color('leaf', 'green'))

    colors_w = colors.link_wam(wam.Program())
    colors_k = colors.link_mk()

    thing, value = dsl.variables('thing value')
    query = color(thing, value)

    expected = [
        ('apple', 'red'),
        ('sky', 'blue'),
        ('leaf', 'green'),
    ]
    assert colors_w.solve(query, select=(thing, value)) == expected
    assert colors_k.solve(query, select=(thing, value)) == expected

    _show('WAM answers', colors_w.solve(query, select=(thing, value)))
    _show('miniKanren answers', colors_k.solve(query, select=(thing, value)))

    # select= is a host-side projection shape. A tuple here asks for a Python
    # tuple in each answer; portable logical products use dsl.struct instead.
    shaped = colors_w.solve(
        query,
        select={'thing': thing, 'color': value},
    )
    assert shaped[0] == {'thing': 'apple', 'color': 'red'}
    _show('dictionary-shaped query projection', shaped)


##
## 2. Terms and unification


def terms_and_unification() -> None:
    _chapter(
        2,
        'Terms, variables, structures, lists, and unification',
        """
        The same dsl.Var object denotes the same unknown wherever it appears in a
        clause or query. Names are for humans; identity carries the meaning.

        dsl.struct('pair', a, b) makes an explicit compound term. Explicitness is
        important because Python tuples and dictionaries have different native
        meanings in the two engines and are therefore not portable logic terms.

        Python lists in portable terms become logical lists. dsl.llist(...,
        tail=...) constructs an improper list when the tail is not NIL.
        """,
    )

    module = dsl.Module('terms')
    repeated = module.export_relation('repeated', 1)
    split = module.export_relation('split', 3)
    x, head, tail = dsl.variables('x head tail')

    module.rule(
        repeated(dsl.struct('pair', x, x)),
    )
    module.rule(
        split(dsl.cons(head, tail), head, tail),
    )

    module_w = module.link_wam(wam.Program())
    module_k = module.link_mk()
    out = dsl.var('out')

    assert module_w.solve(repeated(dsl.struct('pair', 7, out)), select=out) == [7]
    assert module_k.solve(repeated(dsl.struct('pair', 7, out)), select=out) == [7]

    expected = [(1, [2, 3])]
    assert module_w.solve(split([1, 2, 3], head, tail), select=(head, tail)) == expected
    assert module_k.solve(split([1, 2, 3], head, tail), select=(head, tail)) == expected

    improper = dsl.llist(1, 2, tail='rest')
    expected_improper = [(1, dsl.ListValue((2,), 'rest'))]
    assert module_w.solve(split(improper, head, tail), select=(head, tail)) == expected_improper
    assert module_k.solve(split(improper, head, tail), select=(head, tail)) == expected_improper

    _show('repeated-field unification', module_k.solve(
        repeated(dsl.struct('pair', 7, out)),
        select=out,
    ))
    _show('splitting an improper list', expected_improper)


##
## 3. Rules, conjunction, alternatives, and recursion


def rules_and_recursion() -> None:
    _chapter(
        3,
        'Rules, conjunction, alternative clauses, and recursion',
        """
        rule(head, goal1, goal2, ...) means that the head is true when every body
        goal succeeds under one consistent set of bindings. The body is logical
        AND, also called conjunction.

        Multiple clauses with the same head relation are alternatives, or logical
        OR. This replaces miniKanren's conde in the portable source language.

        Source variables are automatically fresh for every clause invocation in
        both backends. No explicit miniKanren fresh(...) is needed in this static
        clause representation.
        """,
    )

    graph = dsl.Module('graph')
    edge = graph.relation('edge', 2)
    path = graph.export_relation('path', 2)
    left, right, middle = dsl.variables('left right middle')

    graph.fact(edge('a', 'b'))
    graph.fact(edge('b', 'c'))
    graph.fact(edge('a', 'd'))

    graph.rule(path(left, right), edge(left, right))
    graph.rule(path(left, right), edge(left, middle), path(middle, right))

    graph_w = graph.link_wam(wam.Program())
    graph_k = graph.link_mk()
    out = dsl.var('out')

    expected = ['b', 'd', 'c']
    assert graph_w.solve(path('a', out), select=out) == expected
    assert graph_k.solve(path('a', out), select=out) == expected
    _show("path('a', out)", expected)


##
## 4. Relational lists


def relational_lists() -> None:
    _chapter(
        4,
        'A reusable relational list operation',
        """
        append/3 relates a left list, a right list, and their concatenation. It is
        not written as a one-way function, so the same clauses can concatenate two
        known lists or enumerate every split of a known result.

        This is well beyond Datalog: portable terms may be recursively structured,
        and recursive clauses may deconstruct and construct those structures.
        """,
    )

    lists = dsl.Module('lists')
    append = lists.export_relation('append', 3)
    head, tail, right, rest = dsl.variables('head tail right rest')

    lists.rule(append(dsl.NIL, right, right))
    lists.rule(
        append(dsl.cons(head, tail), right, dsl.cons(head, rest)),
        append(tail, right, rest),
    )

    lists_w = lists.link_wam(wam.Program())
    lists_k = lists.link_mk()
    left_query, right_query = dsl.variables('left_query right_query')

    expected = [
        ([], [1, 2, 3]),
        ([1], [2, 3]),
        ([1, 2], [3]),
        ([1, 2, 3], []),
    ]
    goal = append(left_query, right_query, [1, 2, 3])

    assert lists_w.solve(goal, select=(left_query, right_query)) == expected
    assert lists_k.solve(goal, select=(left_query, right_query)) == expected
    _show('all splits of [1, 2, 3]', expected)


##
## 5. Imports and module composition


def imports_and_composition() -> None:
    _chapter(
        5,
        'Imported relations and composition between portable modules',
        """
        An imported relation declares a dependency without defining it. Each linker
        receives a backend-native binding for that dependency.

        Imports also let portable modules depend on one another without sharing
        Relation objects across module boundaries. Link the providing module first,
        then bind the consumer's import to the provider namespace's native handle.
        """,
    )

    lists = dsl.Module('lists')
    member = lists.export_relation('member', 2)
    item, head, tail = dsl.variables('item head tail')
    lists.rule(member(head, dsl.cons(head, tail)))
    lists.rule(member(item, dsl.cons(head, tail)), member(item, tail))

    app = dsl.Module('app')
    member_import = app.import_relation('member', 2)
    contains = app.export_relation('contains', 2)
    collection, value = dsl.variables('collection value')
    app.rule(contains(collection, value), member_import(value, collection))

    program = wam.Program()
    lists_w = lists.link_wam(program)
    app_w = app.link_wam(
        program,
        imports={
            member_import: lists_w[member],
        },
    )

    lists_k = lists.link_mk()
    app_k = app.link_mk(
        imports={
            member_import: lists_k[member],
        },
    )

    out = dsl.var('out')
    expected = [1, 2, 3]
    assert app_w.solve(contains([1, 2, 3], out), select=out) == expected
    assert app_k.solve(contains([1, 2, 3], out), select=out) == expected
    _show('portable module composition', expected)


##
## 6. Ground Python operations


def guards_and_projections() -> None:
    _chapter(
        6,
        'Pure ground Python guards and projections',
        """
        dsl.guard(fn, *terms) succeeds when every input term is ground and fn
        returns a truthy value. dsl.project(out, fn, *inputs) computes a ground
        Python result and unifies it with out.

        These operations are directional escape hatches. They are portable because
        both engines support the same weakest contract, not because they become
        magically relational. Put goals that ground their inputs before them.

        The adapter converts backend structures, logical lists, symbols, and answer
        markers to neutral dsl values before invoking your function, and converts a
        neutral ground result back to the selected backend.
        """,
    )

    numbers = dsl.Module('numbers')
    value = numbers.relation('value', 1)
    even_successor = numbers.export_relation('even_successor', 2)
    current, following = dsl.variables('current following')

    for number in range(6):
        numbers.fact(value(number))

    numbers.rule(
        even_successor(current, following),
        value(current),
        dsl.project(following, lambda number: number + 1, current),
        dsl.guard(lambda number: number % 2 == 0, following),
    )

    numbers_w = numbers.link_wam(wam.Program())
    numbers_k = numbers.link_mk()
    x, y = dsl.variables('x y')
    expected = [(1, 2), (3, 4), (5, 6)]

    assert numbers_w.solve(even_successor(x, y), select=(x, y)) == expected
    assert numbers_k.solve(even_successor(x, y), select=(x, y)) == expected
    _show('ground host computation and filtering', expected)


##
## 7. Imported backend primitives


def imported_primitives() -> None:
    _chapter(
        7,
        'One portable primitive contract, two backend implementations',
        """
        import_goal() declares a body-only operation supplied at link time. The
        ground_inputs metadata documents the weakest portable calling mode.

        Here the WAM implementation is a ground foreign guard. The miniKanren
        implementation is fd_lt, which is stronger and can propagate finite-domain
        constraints before its arguments are ground. Portable clauses rely only on
        the declared ground mode; native MK code may use the stronger behavior.
        """,
    )

    ordering = dsl.Module('ordering')
    less = ordering.import_goal('less', 2, ground_inputs=(0, 1))
    value = ordering.relation('value', 1)
    ordered = ordering.export_relation('ordered', 2)
    left, right = dsl.variables('left right')

    for number in (1, 2, 3):
        ordering.fact(value(number))
    ordering.rule(ordered(left, right), value(left), value(right), less(left, right))

    ordering_w = ordering.link_wam(
        wam.Program(),
        primitives={
            less: lambda a, b: wam.guard(lambda x, y: x < y, a, b),
        },
    )
    ordering_k = ordering.link_mk(
        primitives={
            less: mk.fd_lt,
        },
    )

    expected = [(1, 2), (1, 3), (2, 3)]
    assert ordering_w.solve(ordered(left, right), select=(left, right)) == expected
    assert ordering_k.solve(ordered(left, right), select=(left, right)) == expected
    _show('ordered pairs', expected)


##
## 8. Native WAM overlays


def native_wam_overlays() -> None:
    _chapter(
        8,
        'Portable clauses become ordinary WAM clauses',
        """
        WamNamespace[relation] returns the actual wam.Relation installed into the
        supplied Program. Handwritten WAM facts and rules can call it, and clauses
        added to that same native relation are visible to recursive calls made by
        portable clauses.

        This is where WAM-only operations such as CUT and the full ForeignContext
        interface belong. They do not contaminate the portable source module.
        """,
    )

    choices = dsl.Module('choices')
    choice = choices.export_relation('choice', 1)
    choices.fact(choice(1))
    choices.fact(choice(2))

    program = wam.Program()
    choices_w = choices.link_wam(program)
    first = program.relation('first', 1)
    native_x = wam.var('native_x')

    program.rule(
        first(native_x),
        choices_w[choice](native_x),
        wam.CUT,
    )

    result = [solution[native_x] for solution in program.solve(first(native_x))]
    assert result == [1]
    _show('a native WAM rule using a portable relation and CUT', result)

    graph = dsl.Module('graph')
    edge = graph.import_relation('edge', 2)
    path = graph.export_relation('path', 2)
    left, right, middle = dsl.variables('left right middle')
    graph.rule(path(left, right), edge(left, right))
    graph.rule(path(left, right), edge(left, middle), path(middle, right))

    graph_program = wam.Program()
    edge_w = graph_program.relation('edge', 2)
    graph_program.fact(edge_w('a', 'b'))
    graph_program.fact(edge_w('b', 'c'))
    graph_w = graph.link_wam(graph_program, imports={edge: edge_w})

    # Add a backend-only clause after linking. Portable recursive path calls target
    # this exact native relation, so the added c -> d case is visible from a.
    graph_program.fact(graph_w[path]('c', 'd'))
    out = dsl.var('out')
    assert graph_w.solve(path('a', out), select=out) == ['b', 'c', 'd']
    _show('a WAM-native extension seen through portable recursion', ['b', 'c', 'd'])


##
## 9. Native miniKanren overlays and open recursion


def native_mk_overlays() -> None:
    _chapter(
        9,
        'Native miniKanren goals and open-recursive extension clauses',
        """
        MkNamespace[relation] returns an ordinary callable producing mk.Goal.
        Native code can compose it with disequality, type, finite-domain, or other
        miniKanren constraints.

        MkBuilder.extend(relation, function) adds a native alternative to the final
        generated dispatcher. Portable recursive calls resolve through that same
        dispatcher, so extensions are open-recursive rather than merely wrapping
        calls from the outside. The builder freezes after build().
        """,
    )

    values = dsl.Module('values')
    value = values.export_relation('value', 1)
    for number in (1, 2, 3):
        values.fact(value(number))
    values_k = values.link_mk()
    native_x = mk.var('native_x')

    constrained = mk.run_star(
        native_x,
        mk.all(
            values_k[value](native_x),
            mk.neq(native_x, 2),
        ),
    )
    assert constrained == [1, 3]
    _show('native disequality composed with a portable relation', constrained)

    graph = dsl.Module('graph')
    edge = graph.import_relation('edge', 2)
    path = graph.export_relation('path', 2)
    left, right, middle = dsl.variables('left right middle')
    graph.rule(path(left, right), edge(left, right))
    graph.rule(path(left, right), edge(left, middle), path(middle, right))

    @mk.relation
    def edgeo(a, b):
        return mk.conde(
            (mk.eq((a, b), ('a', 'b')),),
            (mk.eq((a, b), ('b', 'c')),),
        )

    builder = graph.mk_builder(imports={edge: edgeo})

    def extra_path(namespace: dsl.MkNamespace, a: object, b: object) -> mk.Goal:
        return mk.eq((a, b), ('c', 'd'))

    builder.extend(path, extra_path)
    graph_k = builder.build()
    out = dsl.var('out')

    assert graph_k.solve(path('a', out), select=out) == ['b', 'c', 'd']
    _show('an MK-native extension seen through portable recursion', ['b', 'c', 'd'])


##
## 10. Tabling as an MK assembly choice


def tabling() -> None:
    _chapter(
        10,
        'Tabling a portable relation only in the miniKanren assembly',
        """
        Tabling is not a portable goal. It is an execution policy selected while
        assembling the miniKanren backend. A tabled relation caches calls and
        answers, deduplicates table answers, and can terminate on many cyclic
        recursive graphs.

        The same portable source linked to the WAM remains ordinary depth-first,
        untabled recursion. On a cycle it may enumerate some answers and then loop;
        a step limit can detect that operational failure.
        """,
    )

    graph = dsl.Module('cyclic_graph')
    edge = graph.import_relation('edge', 2)
    path = graph.export_relation('path', 2)
    left, right, middle = dsl.variables('left right middle')
    graph.rule(path(left, right), edge(left, right))
    graph.rule(path(left, right), edge(left, middle), path(middle, right))

    edges = (
        ('a', 'b'),
        ('b', 'c'),
        ('c', 'a'),
        ('c', 'd'),
    )

    @mk.relation
    def edgeo(a, b):
        return mk.any(*(mk.eq((a, b), item) for item in edges))

    graph_k = graph.link_mk(
        imports={edge: edgeo},
        tabled={path},
    )
    out = dsl.var('out')
    result = graph_k.solve(path('a', out), select=out)

    assert result == ['b', 'c', 'a', 'd']
    assert graph_k.tabled == {path}
    _show('tabled reachability across a cycle', result)

    program = wam.Program()
    edge_w = program.relation('edge', 2)
    for a, b in edges:
        program.fact(edge_w(a, b))
    graph_w = graph.link_wam(program, imports={edge: edge_w})

    try:
        graph_w.solve(path('a', out), select=out, max_steps=500)
    except wam.StepLimitExceeded:
        wam_detected_cycle = True
    else:
        wam_detected_cycle = False

    assert wam_detected_cycle
    _show('WAM step limit detected nonterminating cyclic search', wam_detected_cycle)


##
## 11. Residual constraints through the common answer facade


def residual_constraints() -> None:
    _chapter(
        11,
        'Backend-specific residual constraints can cross the answer facade',
        """
        The portable source can call an imported primitive whose MK binding is a
        delayed constraint. If the query leaves that constraint unresolved, the MK
        namespace normalizes mk.Constrained, mk.Residual, and reified variables to
        their dsl equivalents.

        This does not make delayed disequality portable to the WAM. A WAM binding
        would need a weaker ground-only contract, or the module should be linked
        only for MK when its meaning fundamentally requires residual constraints.
        """,
    )

    constraints = dsl.Module('constraints')
    different = constraints.import_goal('different', 2)
    not_five = constraints.export_relation('not_five', 1)
    x = dsl.var('x')
    constraints.rule(not_five(x), different(x, 5))

    constraints_k = constraints.link_mk(
        primitives={
            different: mk.neq,
        },
    )
    result = constraints_k.solve(not_five(x), select=x)
    expected = [
        dsl.Constrained(
            dsl.Unbound('_0'),
            (
                dsl.Residual('=/=', (dsl.Unbound('_0'), 5)),
            ),
        ),
    ]

    assert result == expected
    _show('a normalized residual disequality', result)


##
## 12. The shared contract is answer-set oriented


def semantic_boundaries() -> None:
    _chapter(
        12,
        'Answer sets are portable; search behavior is not',
        """
        For a finite proof tree, pure portable clauses should describe the same set
        of substitutions on both backends. Do not require identical answer order,
        termination on infinite trees, or duplicate-proof counts:

        * WAM search is ordered, left-to-right, and depth-first;
        * miniKanren interleaves alternatives fairly;
        * tabled MK relations deduplicate table answers;
        * the WAM omits the occurs check and supports rational trees;
        * miniKanren rejects cyclic bindings by default.

        The default portable profile is therefore finite-tree logic. Cyclic terms
        are outside the cross-backend contract even though both engines can expose
        them under different settings.
        """,
    )

    empty = dsl.Module('empty')
    empty_w = empty.link_wam(wam.Program())
    empty_k = empty.link_mk()
    x = dsl.var('x')
    cyclic = dsl.unify(x, dsl.struct('f', x))

    wam_result = empty_w.solve(cyclic, select=x)
    mk_checked_result = empty_k.solve(cyclic, select=x)
    mk_nocheck_result = empty_k.solve(cyclic, select=x, occurs_check=False)

    assert len(wam_result) == 1
    assert isinstance(wam_result[0].args[0], dsl.Cycle)
    assert mk_checked_result == []
    assert len(mk_nocheck_result) == 1
    assert isinstance(mk_nocheck_result[0].args[0], dsl.Cycle)

    _show('WAM rational-tree answer', wam_result)
    _show('default occurs-checked MK answer', mk_checked_result)
    _show('MK no-check rational-tree answer', mk_nocheck_result)


##
## 13. Differential testing and practical use


def differential_testing() -> None:
    _chapter(
        13,
        'Differential testing and the intended application shape',
        """
        A useful production arrangement is:

            portable rule libraries
                    |
               backend linking
               /             \\
          WAM service      MK exploration/tests

        The WAM side can add indexing-friendly facts, foreign predicates, and cut.
        The MK side can table selected relations and add constraints for symbolic
        queries or test generation.

        For bounded finite cases, running the same portable query through both
        facades and comparing normalized answer sets is a strong differential test.
        It catches mistakes in a linker, variable freshening, backtracking, table
        reuse, and assumptions accidentally dependent on answer order.
        """,
    )

    policy = dsl.Module('policy')
    role = policy.relation('role', 2)
    permits = policy.relation('permits', 3)
    authorized = policy.export_relation('authorized', 3)
    user, action, resource, role_name = dsl.variables(
        'user action resource role_name'
    )

    policy.fact(role('alice', 'editor'))
    policy.fact(role('bob', 'reader'))
    policy.fact(permits('editor', 'read', 'document'))
    policy.fact(permits('editor', 'edit', 'document'))
    policy.fact(permits('reader', 'read', 'document'))
    policy.rule(
        authorized(user, action, resource),
        role(user, role_name),
        permits(role_name, action, resource),
    )

    policy_w = policy.link_wam(wam.Program())
    policy_k = policy.link_mk()
    u, a, r = dsl.variables('u a r')
    goal = authorized(u, a, r)

    wam_answers = policy_w.solve(goal, select=(u, a, r))
    mk_answers = policy_k.solve(goal, select=(u, a, r))

    assert _sets(wam_answers) == _sets(mk_answers)
    assert _sets(wam_answers) == {
        repr(('alice', 'read', 'document')),
        repr(('alice', 'edit', 'document')),
        repr(('bob', 'read', 'document')),
    }
    _show('normalized authorization answers', wam_answers)


##
## Entrypoint


def _main() -> None:
    one_definition_two_backends()
    terms_and_unification()
    rules_and_recursion()
    relational_lists()
    imports_and_composition()
    guards_and_projections()
    imported_primitives()
    native_wam_overlays()
    native_mk_overlays()
    tabling()
    residual_constraints()
    semantic_boundaries()
    differential_testing()

    print()
    print('=' * 78)
    print('All dsl tutorial assertions passed.')
    print('=' * 78)


if __name__ == '__main__':
    _main()
