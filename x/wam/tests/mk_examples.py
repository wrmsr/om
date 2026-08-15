"""
Application-oriented examples for ``mk.py``.

These examples emphasize work that benefits specifically from miniKanren-style search: finite-domain solving, cyclic
recursive relations with tabling, bounded program synthesis, and useful residual constraints.
"""
import pprint
import typing as ta

from .. import mk


##
## Finite-domain incident staffing


_ENGINEERS = ('alice', 'bob', 'carol', 'dave')


def _engineer_domain(*names: str) -> mk.FdDomain:
    return mk.domain(*(_ENGINEERS.index(name) for name in names))


def incident_staffing_example() -> dict[str, object]:
    """Assign four incident roles while enforcing availability and separation."""

    primary, secondary, database, communications = mk.variables('primary secondary database communications')

    assignments = mk.run_star(
        (primary, secondary, database, communications),
        mk.in_(primary, _engineer_domain('alice', 'bob')),
        mk.in_(secondary, _engineer_domain('bob', 'carol')),
        mk.in_(database, _engineer_domain('alice', 'carol', 'dave')),
        mk.in_(communications, _engineer_domain('bob', 'dave')),
        mk.all_different(primary, secondary, database, communications),
        mk.label(primary, secondary, database, communications),
    )

    named = [
        {
            'primary': _ENGINEERS[primary_id],
            'secondary': _ENGINEERS[secondary_id],
            'database': _ENGINEERS[database_id],
            'communications': _ENGINEERS[communications_id],
        }
        for primary_id, secondary_id, database_id, communications_id in assignments
    ]

    return {
        'solution_count': len(named),
        'assignments': named,
    }


##
## Tabled vulnerability blast radius through a cyclic graph


def _dependency_relations():
    edges = (
        ('frontend', 'api'),
        ('api', 'auth'),
        ('api', 'orders'),
        ('auth', 'common'),
        ('orders', 'common'),
        ('common', 'api'),
        ('common', 'openssl-wrapper'),
        ('worker', 'orders'),
        ('payments', 'openssl-wrapper'),
        ('metrics', 'prometheus'),
    )

    @mk.relation
    def depends_on(component, dependency):
        return mk.any(*(
            mk.eq((component, dependency), edge)
            for edge in edges
        ))

    @mk.tabled
    def transitively_depends_on(component, dependency):
        return mk.conde(
            (depends_on(component, dependency),),
            (mk.fresh(lambda direct: mk.all(
                depends_on(component, direct),
                transitively_depends_on(direct, dependency),
            )),),
        )

    return depends_on, transitively_depends_on


def vulnerability_blast_radius_example() -> dict[str, object]:
    """Find every component affected by a vulnerable dependency despite cycles."""

    _, transitively_depends_on = _dependency_relations()
    component = mk.var('component')

    affected = mk.run_star(
        component,
        transitively_depends_on(component, 'openssl-wrapper'),
        max_steps=50_000,
    )

    return {
        'vulnerable_dependency': 'openssl-wrapper',
        'affected_components': affected,
    }


##
## Bounded data-cleaning pipeline synthesis


def _apply_operation(name: str, value: str) -> str:
    operations: dict[str, ta.Callable[[str], str]] = {
        'strip': str.strip,
        'lower': str.lower,
        'spaces_to_underscore': lambda item: item.replace(' ', '_'),
        'upper': str.upper,
    }
    return operations[name](value)


@mk.relation
def _operationo(operation, before, after):
    return mk.conde(
        (
            mk.eq(operation, 'strip'),
            mk.is_(after, lambda value: _apply_operation('strip', value), before),
        ),
        (
            mk.eq(operation, 'lower'),
            mk.is_(after, lambda value: _apply_operation('lower', value), before),
        ),
        (
            mk.eq(operation, 'spaces_to_underscore'),
            mk.is_(after, lambda value: _apply_operation('spaces_to_underscore', value), before),
        ),
        (
            mk.eq(operation, 'upper'),
            mk.is_(after, lambda value: _apply_operation('upper', value), before),
        ),
    )


@mk.relation
def _pipelineo(operations, before, after):
    return mk.conde(
        (mk.eq(operations, mk.NIL), mk.eq(before, after)),
        (mk.fresh(lambda operation, rest, middle: mk.all(
            mk.eq(operations, mk.cons(operation, rest)),
            _operationo(operation, before, middle),
            _pipelineo(rest, middle, after),
        )),),
    )


def pipeline_synthesis_example() -> dict[str, object]:
    """Synthesize a shared normalization pipeline from input/output examples."""

    first, second, third = mk.variables('first second third')
    operations = mk.llist(first, second, third)

    pipelines = mk.run_star(
        operations,
        _pipelineo(operations, '  Alice Smith  ', 'alice_smith'),
        _pipelineo(operations, ' BOB Brown ', 'bob_brown'),
    )

    return {
        'training_examples': [
            ('  Alice Smith  ', 'alice_smith'),
            (' BOB Brown ', 'bob_brown'),
        ],
        'valid_three_step_pipelines': pipelines,
    }


##
## Residual deployment-template constraints


def deployment_template_example() -> dict[str, object]:
    """Return a partially specified request together with enforceable residuals."""

    environment, change_ticket = mk.variables('environment change_ticket')
    request = {
        'service': 'billing',
        'environment': environment,
        'change_ticket': change_ticket,
        'metadata': {'source': 'release-bot'},
    }

    templates = mk.run_star(
        request,
        mk.featureo({'service': 'billing'}, request),
        mk.symbolo(environment),
        mk.neq(environment, mk.symbol('prod')),
        mk.stringo(change_ticket),
        mk.absento('secret', request),
    )

    return {
        'templates': templates,
        'note': 'The answer remains executable: later equality either satisfies or rejects each residual.',
    }


##


def run_examples() -> dict[str, object]:
    return {
        'incident_staffing': incident_staffing_example(),
        'vulnerability_blast_radius': vulnerability_blast_radius_example(),
        'pipeline_synthesis': pipeline_synthesis_example(),
        'deployment_template': deployment_template_example(),
    }


def _main() -> None:
    pprint.pp(run_examples(), sort_dicts=False)


if __name__ == '__main__':
    _main()
