"""
A guided tutorial for the embedded miniKanren in :mod:`mk`.

The intended reader knows Python and understands the broad promise of logic programming, but has not used miniKanren and
may find its vocabulary unfamiliar.

miniKanren is deliberately small.  Instead of presenting a database and a special query language, it gives the host
language a few values and combinators from which relations and searches are assembled.

The central mental model is:

    Goal: logical State -> lazy fair Stream[logical State]

You normally do not manipulate State or Stream directly.  It is still useful to know what the words mean:

state
    One possible world of the search.  It contains a substitution (variable bindings), delayed constraints, finite
    domains, and run-local table data.

substitution
    The mapping from logic variables to terms.  Applying it recursively is often called "walking" a term.

goal
    A constraint-producing computation.  Given one state, a goal may produce no states (failure), one state, or many
    alternative states.

conjunction
    Logical AND.  In this API use ``mk.all(g1, g2, ...)``.  Later goals run on every state produced by earlier goals.

disjunction
    Logical OR.  Use ``mk.any(...)`` or, more commonly, ``mk.conde(...)``.  The engine interleaves alternatives instead
    of exhausting one branch first.

fresh variable
    A new logic variable local to part of a relation.  Construct local variables with ``mk.fresh(lambda x, y: ...)``.

reification
    Turning internal logic variables and constraints into stable Python answer values such as ``ReifiedVar('_0')`` and
    ``Constrained(...)``.

residual constraint
    A condition that is valid but not yet decided because the answer remains partially unknown.  miniKanren can return
    that condition as part of the answer.

relation
    A Python function that returns a Goal.  By convention relation names end in ``o``: ``parento``, ``appendo``,
    ``membero``.  The suffix is read loosely as "relation" and warns that the function does not compute an ordinary
    Python return value.

conde
    miniKanren's relational conditional.  Each argument is a clause; goals inside a clause are ANDed, while clauses are
    fairly ORed.

tabling
    Caching calls and answers by their logical shape.  Tabled recursive relations can terminate on many cyclic graphs
    and can support direct left recursion.

The examples contain assertions so that the tutorial doubles as a smoke test.
"""
import itertools
import pprint
import textwrap

from .. import mk


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
## 1. Variables, goals, run, and reification


def variables_goals_and_run() -> None:
    _chapter(
        1,
        'Variables, goals, run, and reification',
        """
        mk.var() creates a logic variable.  mk.eq(a, b) creates an equality goal;
        it does not immediately compare a and b.  run_star(query, *goals) creates an
        initial state, searches for every state satisfying all goals, then reifies
        the query term in each state.

        "star" means "all answers", following the traditional miniKanren run* form.
        run(n, ...) asks for at most n answers and is safer for an infinite result
        stream.
        """,
    )

    x = mk.var('x')
    assert mk.run_star(x, mk.eq(x, 42)) == [42]
    _show('run_star(x, eq(x, 42))', [42])

    # A tuple can itself be the query.  Reification walks every variable inside it.
    x, y = mk.variables('x y')
    result = mk.run_star(
        (x, y),
        mk.eq(mk.struct('pair', x, x), mk.struct('pair', 1, y)),
    )
    assert result == [(1, 1)]
    _show('structural unification', result)

    # An unconstrained variable is returned as a stable ReifiedVar.  _0 is an
    # answer-local name, not the original Python Var.name.
    free = mk.var('free')
    result = mk.run_star(free, mk.succeed)
    assert result == [mk.ReifiedVar('_0')]
    _show('an unconstrained answer', result)

    # run(2, ...) consumes only a prefix of the fair answer stream.
    choice = mk.var('choice')
    result = mk.run(
        2,
        choice,
        mk.conde(
            (mk.eq(choice, 'a'),),
            (mk.eq(choice, 'b'),),
            (mk.eq(choice, 'c'),),
        ),
    )
    assert result == ['a', 'b']
    _show('the first two answers', result)


##
## 2. Terms and unification


def terms_and_unification() -> None:
    _chapter(
        2,
        'Terms and unification',
        """
        Unification recursively makes two terms equal, extending the substitution
        when variables are encountered.  It is symmetric: eq(x, 1) and eq(1, x)
        have the same logical meaning.

        This implementation understands:

        * hashable Python atoms;
        * logic variables;
        * mk.Struct values;
        * proper and improper logical lists;
        * Python tuples;
        * Python dictionaries with fixed, hashable keys.

        mk.Symbol is deliberately distinct from a Python string.  This matters for
        type constraints: symbolo(x) accepts symbol('ready'), while stringo(x)
        accepts 'ready'.
        """,
    )

    x, y = mk.variables('x y')
    result = mk.run_star(
        (x, y),
        mk.eq(
            {'kind': 'event', 'payload': (x, 2)},
            {'kind': 'event', 'payload': (1, y)},
        ),
    )
    assert result == [(1, 2)]
    _show('tuple and mapping unification', result)

    result = mk.run_star(
        x,
        mk.conde(
            (mk.eq(x, mk.symbol('ready')),),
            (mk.eq(x, 'ready'),),
        ),
    )
    assert result == [mk.symbol('ready'), 'ready']
    _show('a Symbol atom and a string atom', result)

    # Repeating the same variable imposes equality.
    result = mk.run_star(
        x,
        mk.eq(mk.struct('pair', x, x), mk.struct('pair', 3, 4)),
    )
    assert result == []
    _show('pair(x, x) cannot match pair(3, 4)', result)


##
## 3. AND, OR, and conde


def conjunction_disjunction_and_conde() -> None:
    _chapter(
        3,
        'Conjunction, disjunction, and conde',
        """
        mk.all(g1, g2, ...) is conjunction: each later goal sees every state from
        the previous goal.  A failing goal removes that branch.

        mk.any(g1, g2, ...) is disjunction: each goal starts from the same incoming
        state, and their output streams are fairly interleaved.

        conde is the usual relational spelling.  Each tuple is one alternative
        clause.  Goals inside a tuple are ANDed; the tuples are ORed.  A one-goal
        clause must be written ``(goal,)``: the trailing comma is ordinary Python's
        one-element-tuple syntax.

        Do not substitute Python ``and`` and ``or``.  Those operators perform eager
        Boolean short-circuiting and do not compose Goal streams.
        """,
    )

    x, label = mk.variables('x label')
    result = mk.run_star(
        (x, label),
        mk.conde(
            (
                mk.eq(x, 1),
                mk.eq(label, 'one'),
            ),
            (
                mk.eq(x, 2),
                mk.eq(label, 'two'),
            ),
        ),
    )
    assert result == [(1, 'one'), (2, 'two')]
    _show('two conde clauses', result)

    # The same goal can be written with the Goal operators, although explicit all
    # and any are often clearer in tutorial and generated code.
    result = mk.run_star(x, mk.eq(x, 1) | mk.eq(x, 2))
    assert result == [1, 2]
    _show('Goal.__or__ as disjunction', result)

    result = mk.run_star(x, (mk.eq(x, 2) | mk.eq(x, 3)) & mk.neq(x, 3))
    assert result == [2]
    _show('disjunction followed by conjunction', result)


##
## 4. Relations and fresh variables


def relations_and_fresh_variables() -> None:
    _chapter(
        4,
        'Relations, the o suffix, and fresh variables',
        """
        A relation is a Python function that builds a Goal.  @mk.relation wraps the
        body in a suspension, which is important for recursive definitions and fair
        search.

        miniKanren code conventionally appends "o" to relation names.  parento is
        not a Boolean Python predicate; parento(a, b) constructs a goal describing
        the relationship between a and b.

        fresh(lambda middle: ...) creates a new variable each time that goal runs.
        It expresses an existential variable: "there exists some middle such that
        ...".  The variable helps prove the result but does not need to appear in
        the query answer.
        """,
    )

    parent_pairs = (
        ('alice', 'bob'),
        ('bob', 'carol'),
        ('alice', 'dana'),
        ('dana', 'erin'),
    )

    @mk.relation
    def parento(parent, child):
        return mk.any(*(
            mk.eq((parent, child), pair)
            for pair in parent_pairs
        ))

    @mk.relation
    def grandparento(grandparent, grandchild):
        return mk.fresh(lambda middle: mk.all(
            parento(grandparent, middle),
            parento(middle, grandchild),
        ))

    out = mk.var('out')
    result = mk.run_star(out, grandparento('alice', out))
    assert result == ['carol', 'erin']
    _show("alice's grandchildren", result)

    result = mk.run_star(out, grandparento(out, 'carol'))
    assert result == ['alice']
    _show("carol's grandparents", result)

    # The relation is multi-directional because it consists only of unification and
    # other relations.  It is not declared with input and output parameters.


##
## 5. Logical lists and running relations backward


def logical_lists_and_reverse_modes() -> None:
    _chapter(
        5,
        'Logical lists and running relations in several directions',
        """
        A logical list is NIL or cons(head, tail).  Python lists entering the DSL
        are normalized to that form, and proper answers are reified as Python lists.

        appendo(left, right, out) is included in mk.py.  It does not merely call
        Python's + operator.  Its relational definition can solve for whichever
        pieces are unknown, subject to search order and a finite answer request.
        """,
    )

    out = mk.var('out')
    result = mk.run_star(out, mk.appendo([1, 2], [3, 4], out))
    assert result == [[1, 2, 3, 4]]
    _show('concatenation', result)

    left, right = mk.variables('left right')
    result = mk.run_star((left, right), mk.appendo(left, right, [1, 2, 3]))
    assert result == [
        ([], [1, 2, 3]),
        ([1], [2, 3]),
        ([1, 2], [3]),
        ([1, 2, 3], []),
    ]
    _show('every split of [1, 2, 3]', result)

    # Asking for all three arguments to be unknown has infinitely many answers.
    # run(5, ...) requests a safe prefix.
    left, right, whole = mk.variables('left right whole')
    result = mk.run(5, (left, right, whole), mk.appendo(left, right, whole))
    assert len(result) == 5
    _show('five increasingly general append answers', result)

    improper = mk.var('improper')
    result = mk.run_star(improper, mk.eq(improper, mk.cons(1, 2)))
    assert result == [mk.ListValue((1,), 2)]
    _show('the improper list [1 | 2]', result)

    # Answers correspond to proofs.  The ordinary membero relation therefore
    # reports 1 twice when it occurs twice.  member1o adds disequality while
    # recursing and reports each first occurrence only once.
    item = mk.var('item')
    assert mk.run_star(item, mk.membero(item, [1, 1, 2])) == [1, 1, 2]
    assert mk.run_star(item, mk.member1o(item, [1, 1, 2])) == [1, 2]
    _show('membero preserves duplicate proofs', [1, 1, 2])
    _show('member1o suppresses later equal proofs', [1, 2])


##
## 6. Fair search and delayed recursion


def fair_search() -> None:
    _chapter(
        6,
        'Fair search and delayed recursion',
        """
        Traditional Prolog search completely explores the first branch before its
        sibling.  miniKanren interleaves suspended branches.  A productive sibling
        can therefore be reached even when an earlier branch describes an infinite
        computation.

        @relation automatically delays expanding its body.  mk.delay(fn) is the
        lower-level tool when an arbitrary recursive goal must be suspended.

        Fairness prevents one *suspended logical branch* from monopolizing search;
        it cannot preempt an ordinary Python function that itself loops forever.
        Goal order still affects performance.
        """,
    )

    @mk.relation
    def forevero(value):
        return forevero(value)

    out = mk.var('out')
    result = mk.run(
        1,
        out,
        mk.conde(
            (forevero(out),),
            (mk.eq(out, 'reachable'),),
        ),
        max_steps=100,
    )
    assert result == ['reachable']
    _show('answer beside an infinite branch', result)

    # run(1, ...) stops after the first answer; it does not force an infinite tail.
    result = mk.run(
        1,
        out,
        mk.conde(
            (mk.eq(out, 'first'),),
            (forevero(out),),
        ),
        max_steps=20,
    )
    assert result == ['first']
    _show('a finite prefix does not force the tail', result)


##
## 7. Disequality and residual constraints


def disequality_and_residuals() -> None:
    _chapter(
        7,
        'Disequality and residual constraints',
        """
        eq(x, 5) can bind x immediately.  neq(x, 5) cannot choose what x *is*; it
        records what x must not become.  The constraint sleeps until later bindings
        either prove it satisfied or violate it.

        If a query finishes while such a condition is still undecided, reification
        returns Constrained(value, residuals).  A residual is useful information,
        not an error: it describes a whole family of still-valid answers.
        """,
    )

    x = mk.var('x')
    result = mk.run_star(x, mk.neq(x, 5))
    assert result == [
        mk.Constrained(
            mk.ReifiedVar('_0'),
            (mk.Residual('=/=', (mk.ReifiedVar('_0'), 5)),),
        ),
    ]
    _show('x is anything except 5', result)

    assert mk.run_star(x, mk.neq(x, 5), mk.eq(x, 6)) == [6]
    assert mk.run_star(x, mk.neq(x, 5), mk.eq(x, 5)) == []
    _show('later binding x to 6', [6])
    _show('later binding x to 5', [])

    # Disequality is structural and may remain undecided until one nested field is
    # known.
    result = mk.run_star(
        x,
        mk.neq(
            mk.struct('pair', x, 2),
            mk.struct('pair', 1, 2),
        ),
        mk.eq(x, 3),
    )
    assert result == [3]
    _show('a structural disequality decided later', result)


##
## 8. Type, absence, and partial-mapping constraints


def general_constraints() -> None:
    _chapter(
        8,
        'Type, absence, and partial-mapping constraints',
        """
        core.logic-style constraints let a relation say more than equality:

        symbolo, stringo, numbero, integero, booleano
            Require a term to have a logical type, now or after future binding.

        absento(needle, haystack)
            Require needle to be absent recursively from all present and future
            subterms of haystack.

        featureo(required, mapping)
            Require a mapping to contain at least the specified key/value features.
            Extra keys are allowed.

        These constraints also survive as residuals when their variables remain
        unknown.  lvaro(term) and nonlvaro(term) are lower-level tests of whether a
        term is currently an unbound logic variable; unlike the constraints above,
        they inspect the present substitution rather than delaying a future test.
        """,
    )

    environment, ticket = mk.variables('environment ticket')
    template = {
        'service': 'billing',
        'environment': environment,
        'ticket': ticket,
    }
    result = mk.run_star(
        template,
        mk.symbolo(environment),
        mk.neq(environment, mk.symbol('prod')),
        mk.stringo(ticket),
        mk.absento('secret', template),
    )
    assert len(result) == 1
    assert isinstance(result[0], mk.Constrained)
    _show('a partially specified deployment template', result)

    event, kind = mk.variables('event kind')
    result = mk.run_star(
        kind,
        mk.featureo({'kind': kind}, event),
        mk.eq(event, {'kind': 'deploy', 'region': 'west'}),
    )
    assert result == ['deploy']
    _show('featureo ignores unrelated mapping fields', result)

    assert mk.run_star(
        environment,
        mk.symbolo(environment),
        mk.eq(environment, 'prod'),
    ) == []
    assert mk.run_star(
        environment,
        mk.symbolo(environment),
        mk.eq(environment, mk.symbol('prod')),
    ) == [mk.symbol('prod')]


##
## 9. Finite-domain constraint logic programming


def finite_domains() -> None:
    _chapter(
        9,
        'Finite-domain constraints and labeling',
        """
        A finite-domain variable ranges over a finite set of integers.  in_(x,
        domain) attaches that domain.  fd_add, fd_lt, and the other fd_* relations
        propagate restrictions among variables without immediately enumerating every
        complete assignment.

        label(...) is the search phase: it chooses concrete values from the remaining
        domains.  Before labeling, a partially solved domain system is itself a valid
        residual answer.  Keeping propagation separate from labeling is standard
        constraint-logic-programming vocabulary.
        """,
    )

    x, y = mk.variables('x y')
    residual = mk.run_star(
        (x, y),
        mk.in_(x, mk.interval(0, 10)),
        mk.in_(y, mk.interval(0, 10)),
        mk.fd_add(x, y, 10),
        mk.fd_lt(x, y),
    )
    assert len(residual) == 1
    assert isinstance(residual[0], mk.Constrained)
    _show('propagated but not labeled', residual)

    solutions = mk.run_star(
        (x, y),
        mk.in_(x, mk.interval(0, 10)),
        mk.in_(y, mk.interval(0, 10)),
        mk.fd_add(x, y, 10),
        mk.fd_lt(x, y),
        mk.label(x, y),
    )
    assert solutions == [
        (0, 10),
        (1, 9),
        (2, 8),
        (3, 7),
        (4, 6),
    ]
    _show('labeled integer solutions', solutions)

    # all_different is useful for assignment and scheduling models.
    primary, secondary, database = mk.variables('primary secondary database')
    assignments = mk.run_star(
        (primary, secondary, database),
        mk.in_(primary, mk.domain(0, 1)),
        mk.in_(secondary, mk.domain(1, 2)),
        mk.in_(database, mk.domain(0, 2)),
        mk.all_different(primary, secondary, database),
        mk.label(primary, secondary, database),
    )
    assert assignments == [(0, 1, 2), (1, 2, 0)]
    _show('three distinct role assignments', assignments)


##
## 10. Tabling and cyclic recursion


def tabling() -> None:
    _chapter(
        10,
        'Variant tabling and cyclic recursion',
        """
        Fair interleaving alone does not remember that a recursive call has already
        been explored.  On a cyclic graph, a path relation can revisit the same
        logical call forever.

        @mk.tabled caches calls by variant: calls with the same logical shape share
        an answer table.  Recursive consumers wait for newly discovered answers,
        and duplicate table answers are discarded.  Tables live only for one run.

        Tabling enables many cyclic reachability queries and even direct left
        recursion.  It is closer to memoized fixed-point evaluation than ordinary
        function memoization because answers can wake suspended recursive consumers.
        Use @mk.tabled in place of @mk.relation on the tabled definition; the tabled
        decorator supplies its own relation-like suspension.
        """,
    )

    edges = (
        ('a', 'b'),
        ('b', 'c'),
        ('c', 'a'),
        ('c', 'd'),
    )

    @mk.relation
    def edgeo(left, right):
        return mk.any(*(
            mk.eq((left, right), edge)
            for edge in edges
        ))

    @mk.tabled
    def patho(left, right):
        return mk.conde(
            (edgeo(left, right),),
            (mk.fresh(lambda middle: mk.all(
                edgeo(left, middle),
                patho(middle, right),
            )),),
        )

    out = mk.var('out')
    result = mk.run_star(out, patho('a', out), max_steps=10_000)
    assert result == ['b', 'c', 'a', 'd']
    _show('nodes reachable from a through a cycle', result)

    # A table records distinct answers, so d is not repeated merely because another
    # proof later rediscovers the same call/result pair.

    @mk.tabled
    def left_recursive_patho(left, right):
        return mk.conde(
            (mk.fresh(lambda middle: mk.all(
                left_recursive_patho(left, middle),
                edgeo(middle, right),
            )),),
            (edgeo(left, right),),
        )

    result = mk.run_star(
        out,
        left_recursive_patho('a', out),
        max_steps=10_000,
    )
    assert result == ['b', 'c', 'a', 'd']
    _show('the same closure with direct left recursion', result)


##
## 11. Directional host-language escape hatches


def host_language_escape_hatches() -> None:
    _chapter(
        11,
        'Directional host-language escape hatches',
        """
        Some work is clearer in ordinary Python.  miniKanren provides explicit
        escape hatches:

        pred(term, fn)
            Require a ground term to satisfy a Boolean Python predicate.

        is_(out, fn, *inputs)
            Read ground inputs, compute a Python value, and unify it with out.

        project(fn, *terms)
            Read ground terms and let fn return an arbitrary Goal.

        They are not relational in every direction.  Their input terms must already
        be ground, or InstantiationError is raised.  The name "project" refers to
        projecting logical terms into ordinary host-language values.  Host callbacks
        may be evaluated more than once as search explores branches, so external side
        effects should generally remain outside the logic program.
        """,
    )

    x, y = mk.variables('x y')
    result = mk.run_star(
        y,
        mk.eq(x, 41),
        mk.is_(y, lambda value: value + 1, x, name='successor'),
        mk.pred(y, lambda value: value % 2 == 0, name='even'),
    )
    assert result == [42]
    _show('ground Python computation', result)

    try:
        mk.run_star(y, mk.is_(y, lambda value: value + 1, x))
    except mk.InstantiationError:
        raised = True
    else:
        raised = False
    assert raised
    _show('using is_ before its input is ground raises', raised)

    # project is more general because the callback returns a Goal.
    category = mk.var('category')
    result = mk.run_star(
        category,
        mk.project(
            lambda value: mk.eq(
                category,
                'large' if value >= 10 else 'small',
            ),
            12,
            name='classify',
        ),
    )
    assert result == ['large']
    _show('project returns another goal', result)


##
## 12. onceo, conda, and condu


def committed_control() -> None:
    _chapter(
        12,
        'onceo, conda, and condu',
        """
        Pure conde explores every viable clause.  core.logic also supplies committed
        control forms for procedural cases:

        onceo(goal)
            Keep only the first state produced by goal.

        conda((question, body...), ...)
            Try clause questions in order.  Commit to the first clause whose question
            has at least one answer, then run its body for the question's answers.
            Later clauses are not considered even if the selected body fails.

        condu(...)
            Stronger committed choice: use only the first answer of the selected
            question and at most the first answer of its body.

        These forms are intentionally non-relational.  They make ordering semantically
        significant and should be used as an explicit optimization or policy choice.
        """,
    )

    out = mk.var('out')
    result = mk.run_star(
        out,
        mk.onceo(mk.conde(
            (mk.eq(out, 1),),
            (mk.eq(out, 2),),
        )),
    )
    assert result == [1]
    _show('onceo', result)

    result = mk.run_star(
        out,
        mk.conda(
            (
                mk.conde((mk.eq(out, 1),), (mk.eq(out, 2),)),
                mk.eq(out, 2),
            ),
            (mk.eq(out, 3),),
        ),
    )
    assert result == [2]
    _show('conda preserves later answers of the selected question', result)

    result = mk.run_star(
        out,
        mk.condu(
            (
                mk.conde((mk.eq(out, 1),), (mk.eq(out, 2),)),
                mk.eq(out, 2),
            ),
            (mk.eq(out, 3),),
        ),
    )
    assert result == []
    _show('condu commits to the first question answer, which then fails', result)


##
## 13. Occurs check and rational-tree mode


def occurs_check() -> None:
    _chapter(
        13,
        'The occurs check and explicit rational-tree mode',
        """
        By default, unification performs an occurs check.  Binding x to f(x) would
        make x contain itself, so ordinary run/run_star reject that branch.

        run_nocheck disables the test and permits a rational tree: a finite cyclic
        graph representing an infinitely unfolding term.  Reification marks the
        cycle explicitly.  Use no-check mode only when cyclic terms are deliberate.
        """,
    )

    x = mk.var('x')
    recursive = mk.struct('f', x)

    assert mk.run_star(x, mk.eq(x, recursive)) == []
    result = mk.run_nocheck(None, x, mk.eq(x, recursive))
    assert len(result) == 1
    assert isinstance(result[0], mk.Struct)
    assert isinstance(result[0].args[0], mk.Cycle)
    _show('default occurs-checked result', [])
    _show('no-check rational-tree result', result)


##
## 14. Tracing, laziness, and step limits


def observability_and_limits() -> None:
    _chapter(
        14,
        'Tracing, lazy iteration, and step limits',
        """
        iter_run() exposes the lazy answer iterator directly.  A trace callback sees
        immutable summaries of goal execution: step number, goal name, substitution
        size, delayed-constraint count, and finite-domain count.

        max_steps is a safety boundary for nonproductive or unexpectedly expensive
        searches.  Fairness improves completeness among suspended branches; it does
        not guarantee that every relation terminates.
        """,
    )

    out = mk.var('out')
    iterator = mk.iter_run(
        out,
        mk.conde(*(
            (mk.eq(out, value),)
            for value in range(100)
        )),
    )
    first_three = list(itertools.islice(iterator, 3))
    assert first_three == [0, 1, 2]
    _show('three lazily consumed answers', first_three)

    events: list[mk.TraceEvent] = []
    assert mk.run_star(out, mk.eq(out, 1), trace=events.append) == [1]
    _show(
        'trace events',
        [
            {
                'step': event.step,
                'goal': event.goal,
                'bindings': event.substitution_size,
                'constraints': event.constraint_count,
                'domains': event.domain_count,
            }
            for event in events
        ],
    )

    @mk.relation
    def loopo(value):
        return loopo(value)

    try:
        mk.run_star(out, loopo(out), max_steps=20)
    except mk.StepLimitExceeded:
        stopped = True
    else:
        stopped = False
    assert stopped
    _show('a nonproductive relation stopped by max_steps', stopped)


##
## 15. A mini synthesis example


def synthesis_example() -> None:
    _chapter(
        15,
        'Putting it together: synthesizing a tiny transformation pipeline',
        """
        Relational search is useful when the unknown is itself a small program or
        plan.  Here three logic variables choose operations.  The same chosen
        pipeline must satisfy two input/output examples.

        The operation application uses is_, so execution of a selected operation is
        directional.  The *choice of operations* remains logical and is searched by
        conde.  This hybrid style is often practical in embedded miniKanren systems.
        """,
    )

    @mk.relation
    def operationo(operation, before, after):
        return mk.conde(
            (
                mk.eq(operation, 'strip'),
                mk.is_(after, str.strip, before, name='strip'),
            ),
            (
                mk.eq(operation, 'lower'),
                mk.is_(after, str.lower, before, name='lower'),
            ),
            (
                mk.eq(operation, 'underscores'),
                mk.is_(
                    after,
                    lambda value: value.replace(' ', '_'),
                    before,
                    name='underscores',
                ),
            ),
        )

    @mk.relation
    def pipelineo(operations, before, after):
        return mk.conde(
            (
                mk.eq(operations, mk.NIL),
                mk.eq(before, after),
            ),
            (mk.fresh(lambda operation, rest, middle: mk.all(
                mk.eq(operations, mk.cons(operation, rest)),
                operationo(operation, before, middle),
                pipelineo(rest, middle, after),
            )),),
        )

    first, second, third = mk.variables('first second third')
    pipeline = mk.llist(first, second, third)
    result = mk.run_star(
        pipeline,
        pipelineo(pipeline, '  Alice Smith  ', 'alice_smith'),
        pipelineo(pipeline, ' BOB Brown ', 'bob_brown'),
    )
    assert result == [
        ['strip', 'lower', 'underscores'],
        ['strip', 'underscores', 'lower'],
        ['lower', 'strip', 'underscores'],
    ]
    _show('three-operation pipelines fitting both examples', result)


##


def run_tutorial() -> None:
    variables_goals_and_run()
    terms_and_unification()
    conjunction_disjunction_and_conde()
    relations_and_fresh_variables()
    logical_lists_and_reverse_modes()
    fair_search()
    disequality_and_residuals()
    general_constraints()
    finite_domains()
    tabling()
    host_language_escape_hatches()
    committed_control()
    occurs_check()
    observability_and_limits()
    synthesis_example()

    print()
    print('=' * 78)
    print('Tutorial complete')
    print('=' * 78)
    print(
        'The central habits are: build Goals instead of computing Booleans, use '
        'fresh variables for local unknowns, read conde as fair OR-of-AND clauses, '
        'treat residual constraints as meaningful answers, and reserve project/is_ '
        'for points where their inputs are already ground.'
    )


def _main() -> None:
    run_tutorial()


if __name__ == '__main__':
    _main()
