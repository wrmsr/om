"""
A guided tutorial for the embedded WAM in :mod:`wam`.

The intended reader knows Python and has a rough idea that logic programming can answer questions from facts and rules,
but does not yet know Prolog or WAM vocabulary.

The most important mental shift is this:

* ordinary Python functions compute one result from their arguments;
* a logic *relation* describes combinations of values that may be true;
* a *query* asks the engine to enumerate every combination that makes its goals true.

This implementation uses a Warren Abstract Machine, or WAM.  "WAM" describes the execution machinery, not a different
logic language.  The public Python DSL has Prolog-like semantics: clauses and goals are tried in source order using
left-to-right, depth-first backtracking.

A small vocabulary ------------------

atom
    An indivisible ground value such as ``'alice'``, ``42``, or ``None``.  In this implementation an atom may be any
    hashable Python object.

term
    A value manipulated by the logic engine.  A term is an atom, a logic variable, a structure, or a logical list.

logic variable
    A placeholder that may be unified with a term.  It is not a mutable Python box.  Two occurrences of the *same*
    :class:`wam.Var` object mean the same unknown.

structure
    A named compound term such as ``point(10, 20)`` or ``employee('alice', 7)``. Construct one with :func:`wam.struct`.

relation
    A named family of true tuples, such as ``parent/2``.  The ``/2`` means that the relation has two arguments.

fact
    A clause with no body: ``parent('alice', 'bob')`` is unconditionally true.

rule
    A clause whose head is true when every goal in its body succeeds.

clause
    One fact or rule belonging to a relation.  Clauses are tried in insertion order.

goal
    One condition in a query or rule body: a relation call, unification, a host predicate, ``CUT``, ``TRUE``, or
    ``FAIL``.

unification
    Structural equality with variables.  Unifying ``pair(x, x)`` with ``pair(1, y)`` binds both ``x`` and ``y`` to
    ``1``.

backtracking
    When a later goal fails, the machine undoes bindings and tries the next available fact or rule.

choice point
    The saved machine state that makes backtracking possible.

query variable
    A variable occurring in the query.  Its final value appears in each :class:`wam.Solution`.

The examples contain assertions so that the tutorial also serves as a smoke test.
"""
import itertools
import pprint
import textwrap

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


##
## 1. Facts, relations, and queries


def facts_and_queries() -> None:
    _chapter(
        1,
        'Facts, relations, and queries',
        """
        A Program is a collection of relations and clauses.  Calling
        program.relation('color', 2) declares the *name and arity* of a relation;
        it does not yet say which color pairs are true.

        A relation object is callable.  color('apple', 'red') constructs a goal-
        shaped value, but it does not execute anything by itself and is not a Python
        Boolean.  program.fact(...) installs that call as an unconditional clause.

        A query may contain concrete values, logic variables, or both.  solve()
        returns a lazy iterator because a query can have zero, one, many, or even
        infinitely many answers.
        """,
    )

    program = wam.Program()
    color = program.relation('color', 2)

    program.fact(color('apple', 'red'))
    program.fact(color('sky', 'blue'))
    program.fact(color('leaf', 'green'))

    thing, value = wam.variables('thing value')
    solutions = list(program.solve(color(thing, value)))
    rows = [solution.as_dict(names=True) for solution in solutions]

    assert rows == [
        {'thing': 'apple', 'value': 'red'},
        {'thing': 'sky', 'value': 'blue'},
        {'thing': 'leaf', 'value': 'green'},
    ]
    _show('all color pairs', rows)

    red_things = [
        solution[thing]
        for solution in program.solve(color(thing, 'red'))
    ]
    assert red_things == ['apple']
    _show("things whose color is 'red'", red_things)

    # A fully ground query asks only whether a proof exists.  Its successful
    # Solution is empty because there are no query variables to report.
    assert [solution.as_dict() for solution in program.solve(color('sky', 'blue'))] == [{}]
    assert list(program.solve(color('sky', 'green'))) == []
    _show("is color('sky', 'blue') true?", True)

    # Variable identity matters.  Names exist for humans and result lookup; two
    # separately-created variables named "x" are still distinct variables.
    x1 = wam.var('x')
    x2 = wam.var('x')
    assert x1 is not x2


##
## 2. Terms and unification


def terms_and_unification() -> None:
    _chapter(
        2,
        'Terms and unification',
        """
        Unification is the engine's central operation.  It recursively makes two
        terms equal, binding variables where necessary.  Unlike assignment, it is
        symmetric: neither side is inherently the input or output.

        A Struct is a compound term with a functor name and arguments.  Functor
        name plus arity identifies its shape: point/2 cannot unify with point/3 or
        line/2.

        The same Var object repeated in a term imposes equality.  pair(x, x) only
        matches pairs whose two fields can be the same value.
        """,
    )

    x, y = wam.variables('x y')
    left = wam.struct('pair', x, x)
    right = wam.struct('pair', 1, y)

    solution = next(wam.Program().solve(wam.unify(left, right)))
    assert solution[x] == 1
    assert solution[y] == 1
    _show('unify pair(x, x) with pair(1, y)', solution.as_dict(names=True))

    impossible = list(wam.Program().solve(
        wam.unify(
            wam.struct('pair', x, x),
            wam.struct('pair', 1, 2),
        )
    ))
    assert impossible == []
    _show('unify pair(x, x) with pair(1, 2)', impossible)

    # Unification can be one of several query goals.  Goals are a conjunction:
    # every goal must succeed under one consistent set of bindings.
    out = wam.var('out')
    chained = list(wam.Program().solve(
        wam.unify(out, wam.struct('point', x, y)),
        wam.unify(x, 10),
        wam.unify(y, 20),
    ))
    assert chained[0][out] == wam.struct('point', 10, 20)
    _show('a three-goal unification query', chained[0].as_dict(names=True))

    # A variable that remains unconstrained is reified as wam.Unbound.  Reify is
    # logic-programming vocabulary for turning the internal variable graph into a
    # stable answer value that ordinary Python can inspect.
    free = wam.var('free')
    unconstrained = next(wam.Program().solve(wam.unify(free, free)))[free]
    assert isinstance(unconstrained, wam.Unbound)
    _show('an unconstrained query variable', unconstrained)


##
## 3. Rules and local variables


def rules_and_local_variables() -> None:
    _chapter(
        3,
        'Rules, conjunction, and clause-local variables',
        """
        A rule has a head and a body.  The head is true whenever all body goals are
        true.  Body goals are tried from left to right.

        Variables written into a rule are clause-local templates.  Each invocation
        receives fresh runtime variables, so recursive and concurrent uses do not
        accidentally share bindings.

        grandparent(x, z) below reads as:

            x is a grandparent of z
            if there exists some y such that
            parent(x, y) and parent(y, z).

        The "there exists y" is implicit because y occurs inside the clause but is
        not fixed by the caller.
        """,
    )

    program = wam.Program()
    parent = program.relation('parent', 2)
    grandparent = program.relation('grandparent', 2)

    program.fact(parent('alice', 'bob'))
    program.fact(parent('bob', 'carol'))
    program.fact(parent('alice', 'dana'))
    program.fact(parent('dana', 'erin'))

    x, y, z = wam.variables('x y z')
    program.rule(
        grandparent(x, z),
        parent(x, y),
        parent(y, z),
    )

    descendant = wam.var('descendant')
    answers = [
        solution[descendant]
        for solution in program.solve(grandparent('alice', descendant))
    ]
    assert answers == ['carol', 'erin']
    _show("alice's grandchildren", answers)

    grandparent_value = wam.var('grandparent')
    answers = [
        solution[grandparent_value]
        for solution in program.solve(grandparent(grandparent_value, 'carol'))
    ]
    assert answers == ['alice']
    _show("carol's grandparents", answers)


##
## 4. Backtracking, order, and laziness


def backtracking_order_and_laziness() -> None:
    _chapter(
        4,
        'Backtracking, source order, and lazy answers',
        """
        The WAM explores one branch to completion.  If a later goal fails, it
        restores the most recent choice point and tries the next alternative.

        Both kinds of order matter:

        * clauses are tried in the order they were added;
        * goals inside a rule are tried left to right.

        This is operational behavior, not merely an optimization detail.  Put
        selective or grounding goals early when practical, and do not put an
        infinite recursive branch before a productive alternative.
        """,
    )

    program = wam.Program()
    candidate = program.relation('candidate', 1)
    accepted = program.relation('accepted', 1)

    for value in range(1, 7):
        program.fact(candidate(value))

    x = wam.var('x')
    program.rule(
        accepted(x),
        candidate(x),
        wam.guard(lambda value: value % 2 == 0, x, name='is_even'),
        wam.guard(lambda value: value > 2, x, name='greater_than_two'),
    )

    out = wam.var('out')
    answers = [solution[out] for solution in program.solve(accepted(out))]
    assert answers == [4, 6]
    _show('accepted candidates', answers)

    # The binding x=1 is undone when is_even fails, then candidate/1 is retried
    # with x=2, and so on.  That undo operation is what the WAM trail records.

    # Solutions are produced lazily.  We can stop after a prefix without asking
    # the machine to explore the remaining alternatives.
    first_two = [
        solution[out]
        for solution in itertools.islice(program.solve(candidate(out)), 2)
    ]
    assert first_two == [1, 2]
    _show('first two answers only', first_two)

    # First-argument indexing is automatic.  A call with a known first argument
    # can skip clauses whose first argument clearly has another atom or structure.
    lookup = program.relation('lookup', 2)
    program.fact(lookup('alpha', 1))
    program.fact(lookup('beta', 2))
    program.fact(lookup('gamma', 3))
    result = [solution[out] for solution in program.solve(lookup('beta', out))]
    assert result == [2]
    _show("indexed lookup('beta', out)", result)


##
## 5. Recursion and reachability


def recursion_and_reachability() -> None:
    _chapter(
        5,
        'Recursion and reachability',
        """
        Recursive relations usually need a base clause and a recursive clause.
        path(x, y) below says that y is reachable from x either by one edge, or by
        taking one edge to an intermediate node and recursively finding a path from
        there.

        This WAM uses depth-first search and has no tabling.  The graph below is
        acyclic on purpose.  A naive recursive path relation over a cycle can loop
        forever or repeatedly produce the same proof.  Production code should keep
        such input acyclic, carry an explicit visited set, bound the depth, or add a
        tabled relation facility.
        """,
    )

    program = wam.Program()
    edge = program.relation('edge', 2)
    path = program.relation('path', 2)

    for left, right in (
            ('frontend', 'api'),
            ('api', 'auth'),
            ('api', 'orders'),
            ('auth', 'database'),
            ('orders', 'database'),
    ):
        program.fact(edge(left, right))

    x, y, middle = wam.variables('x y middle')
    program.rule(path(x, y), edge(x, y))
    program.rule(
        path(x, y),
        edge(x, middle),
        path(middle, y),
    )

    target = wam.var('target')
    reachable = [
        solution[target]
        for solution in program.solve(path('frontend', target))
    ]
    assert reachable == ['api', 'auth', 'orders', 'database', 'database']
    _show('reachable nodes, including distinct proof paths', reachable)

    # Logic engines enumerate proofs, not automatically distinct values.  Database
    # is reached through auth and through orders, so it appears twice.
    distinct_reachable = list(dict.fromkeys(reachable))
    assert distinct_reachable == ['api', 'auth', 'orders', 'database']
    _show('deduplicated in ordinary Python', distinct_reachable)


##
## 6. Logical lists and multi-directional relations


def logical_lists() -> None:
    _chapter(
        6,
        'Logical lists and multi-directional relations',
        """
        A logical list is either NIL or cons(head, tail).  Python lists passed into
        the DSL are normalized to that representation and proper logical lists are
        reified back to Python lists.

        Because append/3 is a relation rather than a one-way function, the same two
        clauses can concatenate known lists, solve for a missing suffix, or enumerate
        every split of a known output.
        """,
    )

    program = wam.Program()
    append = program.relation('append', 3)
    head, tail, right, rest = wam.variables('head tail right rest')

    # append([], right, right).
    program.fact(append(wam.NIL, right, right))

    # append([head | tail], right, [head | rest]) :- append(tail, right, rest).
    program.rule(
        append(
            wam.cons(head, tail),
            right,
            wam.cons(head, rest),
        ),
        append(tail, right, rest),
    )

    out = wam.var('out')
    joined = [
        solution[out]
        for solution in program.solve(append([1, 2], [3, 4], out))
    ]
    assert joined == [[1, 2, 3, 4]]
    _show('append([1, 2], [3, 4], out)', joined)

    left, suffix = wam.variables('left suffix')
    splits = [
        (solution[left], solution[suffix])
        for solution in program.solve(append(left, suffix, [1, 2, 3]))
    ]
    assert splits == [
        ([], [1, 2, 3]),
        ([1], [2, 3]),
        ([1, 2], [3]),
        ([1, 2, 3], []),
    ]
    _show('every split of [1, 2, 3]', splits)

    # An improper list has a final tail other than NIL.  Python's list type cannot
    # represent that shape, so the answer uses wam.ListValue.
    improper = wam.var('improper')
    value = next(wam.Program().solve(
        wam.unify(improper, wam.cons(1, 2))
    ))[improper]
    assert value == wam.ListValue((1,), 2)
    _show('the improper list [1 | 2]', value)


##
## 7. Calling ordinary Python


def host_language_goals() -> None:
    _chapter(
        7,
        'Calling ordinary Python: guard, project, and foreign',
        """
        Pure relations are flexible because unification can run in several
        directions.  Real programs also need arithmetic, parsing, API adapters, and
        other ordinary Python operations.

        guard(fn, *terms)
            Read ground term values, call fn, and succeed when its result is truthy.

        project(out, fn, *inputs)
            Read ground inputs, compute fn(*inputs), and unify the result with out.

        foreign(fn, *terms)
            The lower-level interface.  fn receives a ForeignContext and opaque
            TermRef objects.  It may inspect ground values and unify outputs.

        These operations are deliberately directional: values read by ctx.value(),
        guard(), or project() must already be ground.  Put grounding relation goals
        before them.  An unground read raises InstantiationError rather than silently
        guessing an execution direction.  Host callbacks may run again during
        backtracking, so they should normally be deterministic and free of external
        side effects.
        """,
    )

    program = wam.Program()
    number = program.relation('number', 1)
    interesting_square = program.relation('interesting_square', 2)
    x, square = wam.variables('x square')

    for value in range(6):
        program.fact(number(value))

    program.rule(
        interesting_square(x, square),
        number(x),
        wam.project(square, lambda value: value * value, x, name='square'),
        wam.guard(lambda value: value >= 9, square, name='at_least_nine'),
    )

    out_x, out_square = wam.variables('out_x out_square')
    answers = [
        (solution[out_x], solution[out_square])
        for solution in program.solve(interesting_square(out_x, out_square))
    ]
    assert answers == [(3, 9), (4, 16), (5, 25)]
    _show('interesting squares', answers)

    parse_int = program.relation('parse_int', 2)
    text, integer = wam.variables('text integer')

    def parse_int_foreign(
            ctx: wam.ForeignContext,
            text_ref: wam.TermRef,
            integer_ref: wam.TermRef,
    ) -> bool:
        text_value = ctx.value(text_ref)
        if not isinstance(text_value, str):
            return False
        try:
            parsed = int(text_value)
        except ValueError:
            return False
        return ctx.unify(integer_ref, parsed)

    program.rule(
        parse_int(text, integer),
        wam.foreign(
            parse_int_foreign,
            text,
            integer,
            name='parse_int_python',
        ),
    )

    out = wam.var('out')
    assert [solution[out] for solution in program.solve(parse_int('42', out))] == [42]
    assert list(program.solve(parse_int('not-an-int', out))) == []
    _show("parse_int('42', out)", [42])

    # A failed foreign goal has its own heap and binding changes rolled back before
    # normal WAM backtracking continues.  An exceptional callback is rolled back too,
    # after which the original exception is propagated to Python.


##
## 8. Cut and explicit success or failure


def cut_and_control() -> None:
    _chapter(
        8,
        'Cut, TRUE, and FAIL',
        """
        CUT commits to choices made since entry into the current predicate.  Once
        reached, alternatives created inside that predicate are discarded.  It is
        written ! in Prolog and is called "cut" because it cuts branches from the
        search tree.

        Cut is useful for "take the first match" behavior and procedural
        if/then/else patterns, but it makes clause order part of a relation's meaning
        and can destroy useful reverse modes.  Prefer ordinary logical constraints
        unless commitment is intentional.

        TRUE is a goal that succeeds once.  FAIL is a goal that never succeeds.
        """,
    )

    program = wam.Program()
    candidate = program.relation('candidate', 1)
    first_candidate = program.relation('first_candidate', 1)
    x = wam.var('x')

    program.fact(candidate('alpha'))
    program.fact(candidate('beta'))
    program.fact(candidate('gamma'))
    program.rule(first_candidate(x), candidate(x), wam.CUT)

    out = wam.var('out')
    answers = [
        solution[out]
        for solution in program.solve(first_candidate(out))
    ]
    assert answers == ['alpha']
    _show('first_candidate(out)', answers)

    assert len(list(program.solve(wam.TRUE))) == 1
    assert list(program.solve(wam.FAIL)) == []

    # Cut is scoped to the predicate containing it.  It does not normally erase a
    # caller's older choices.  This distinction is why it is called a *deep* cut
    # with a saved predicate-entry choice-point boundary.


##
## 9. Rational trees


def rational_trees() -> None:
    _chapter(
        9,
        'Rational trees and the missing occurs check',
        """
        An occurs check would reject unifying x with f(x), because x occurs inside
        the term it would be bound to.  Traditional WAM implementations often omit
        that check for speed and thereby support *rational trees*: finite cyclic
        graphs that denote infinitely unfolding terms.

        This implementation intentionally follows that model.  Reification detects
        the cycle and inserts a wam.Cycle marker so Python printing terminates.
        Accidental self-reference can therefore succeed; applications expecting only
        ordinary finite trees must guard against it.
        """,
    )

    x = wam.var('x')
    value = next(wam.Program().solve(
        wam.unify(x, wam.struct('f', x))
    ))[x]

    assert isinstance(value, wam.Struct)
    assert value.functor == 'f'
    assert isinstance(value.args[0], wam.Cycle)
    _show('x unified with f(x)', value)


##
## 10. Compilation, disassembly, tracing, and limits


def compilation_and_observability() -> None:
    _chapter(
        10,
        'Compilation, disassembly, tracing, and step limits',
        """
        Program is a mutable builder.  compile() freezes its current clauses into an
        immutable Executable containing WAM-like instructions and predicate indexes.
        Compile once and reuse the executable for repeated queries.

        disassemble() is educational and useful when inspecting compiler behavior.
        A trace callback observes each executed instruction.  max_steps turns an
        accidental infinite computation into a controlled exception.
        """,
    )

    program = wam.Program()
    edge = program.relation('edge', 2)
    path = program.relation('path', 2)
    x, y, middle = wam.variables('x y middle')

    program.fact(edge('a', 'b'))
    program.fact(edge('b', 'c'))
    program.rule(path(x, y), edge(x, y))
    program.rule(path(x, y), edge(x, middle), path(middle, y))

    executable = program.compile()

    # Mutating the builder later does not mutate the already-compiled image.
    program.fact(edge('a', 'd'))
    out = wam.var('out')
    assert [solution[out] for solution in executable.solve(path('a', out))] == ['b', 'c']
    assert [solution[out] for solution in program.solve(path('a', out))] == ['b', 'd', 'c']

    disassembly = executable.disassemble().splitlines()
    _show('first lines of the compiled image', disassembly[:18])

    events: list[wam.TraceEvent] = []
    answers = [
        solution[out]
        for solution in executable.solve(
            path('a', out),
            config=wam.MachineConfig(trace=events.append),
        )
    ]
    assert answers == ['b', 'c']
    _show(
        'first trace events',
        [
            {
                'step': event.step,
                'pc': event.pc,
                'operation': event.operation,
                'heap': event.heap_size,
                'trail': event.trail_size,
                'choices': event.choice_depth,
            }
            for event in events[:10]
        ],
    )

    looping = wam.Program()
    loop = looping.relation('loop', 0)
    looping.rule(loop(), loop())
    try:
        list(looping.solve(loop(), config=wam.MachineConfig(max_steps=100)))
    except wam.StepLimitExceeded:
        stopped = True
    else:
        stopped = False
    assert stopped
    _show('a recursive loop stopped by max_steps', stopped)


##
## 11. A small application-shaped rule set


def application_shaped_example() -> None:
    _chapter(
        11,
        'Putting it together: explainable authorization',
        """
        Logic programming is especially useful when a decision is a join across
        several relations and there may be several proofs.  Here an authorization
        query returns not just whether access is allowed, but the role that explains
        it.

        Ordinary Python remains responsible for loading facts, deduplicating or
        ranking proofs, logging decisions, and performing side effects.
        """,
    )

    program = wam.Program()
    user_role = program.relation('user_role', 2)
    role_parent = program.relation('role_parent', 2)
    effective_role = program.relation('effective_role', 2)
    permission = program.relation('permission', 3)
    authorized = program.relation('authorized', 4)

    program.fact(user_role('alice', 'editor'))
    program.fact(user_role('bob', 'reader'))
    program.fact(role_parent('editor', 'reader'))
    program.fact(permission('reader', 'read', 'document'))
    program.fact(permission('editor', 'edit', 'document'))

    user, role, parent, action, kind, reason = wam.variables(
        'user role parent action kind reason'
    )
    program.rule(effective_role(user, role), user_role(user, role))
    program.rule(
        effective_role(user, parent),
        user_role(user, role),
        role_parent(role, parent),
    )
    program.rule(
        authorized(user, action, kind, reason),
        effective_role(user, role),
        permission(role, action, kind),
        wam.unify(reason, wam.struct('via_role', role)),
    )

    reason_out = wam.var('reason')
    alice_read = [
        solution[reason_out]
        for solution in program.solve(
            authorized('alice', 'read', 'document', reason_out)
        )
    ]
    assert alice_read == [wam.struct('via_role', 'reader')]
    _show("why alice may read a document", alice_read)

    bob_edit = list(program.solve(
        authorized('bob', 'edit', 'document', reason_out)
    ))
    assert bob_edit == []
    _show("why bob may edit a document", bob_edit)


##


def run_tutorial() -> None:
    facts_and_queries()
    terms_and_unification()
    rules_and_local_variables()
    backtracking_order_and_laziness()
    recursion_and_reachability()
    logical_lists()
    host_language_goals()
    cut_and_control()
    rational_trees()
    compilation_and_observability()
    application_shaped_example()

    print()
    print('=' * 78)
    print('Tutorial complete')
    print('=' * 78)
    print(
        'The central habits are: model truth as relations, let unification carry '
        'values, remember that search is ordered and depth-first, and cross into '
        'ordinary Python only when the required inputs are ground.'
    )


def _main() -> None:
    run_tutorial()


if __name__ == '__main__':
    _main()
