import collections
import pprint
import typing as ta

from .. import wam


##


def _unique(items: ta.Iterable[ta.Any]) -> list[ta.Any]:
    return list(dict.fromkeys(items))


## Authorization policy evaluation


def build_authorization_program() -> tuple[wam.Executable, dict[str, wam.Relation]]:
    program = wam.Program()

    user_role = program.relation('user_role', 2)
    role_parent = program.relation('role_parent', 2)
    role_permission = program.relation('role_permission', 3)
    resource = program.relation('resource', 4)
    clearance = program.relation('clearance', 2)
    owner_action = program.relation('owner_action', 1)

    inherits = program.relation('inherits', 2)
    effective_role = program.relation('effective_role', 2)
    authorized = program.relation('authorized', 4)

    child, parent, ancestor = wam.variables('child parent ancestor')
    user, role, direct_role = wam.variables('user role direct_role')
    action, resource_id, kind, owner = wam.variables('action resource_id kind owner')
    actual_clearance, required_clearance = wam.variables('actual_clearance required_clearance')

    program.rule(inherits(child, parent), role_parent(child, parent))
    program.rule(
        inherits(child, ancestor),
        role_parent(child, parent),
        inherits(parent, ancestor),
    )

    program.rule(effective_role(user, role), user_role(user, role))
    program.rule(
        effective_role(user, role),
        user_role(user, direct_role),
        inherits(direct_role, role),
    )

    program.rule(
        authorized(user, action, resource_id, wam.struct('role', role)),
        resource(resource_id, kind, owner, required_clearance),
        effective_role(user, role),
        role_permission(role, action, kind),
        clearance(user, actual_clearance),
        wam.guard(
            lambda actual, required: actual >= required,
            actual_clearance,
            required_clearance,
            name='clearance_allows',
        ),
    )
    program.rule(
        authorized(user, action, resource_id, 'owner'),
        resource(resource_id, kind, user, required_clearance),
        owner_action(action),
        clearance(user, actual_clearance),
        wam.guard(
            lambda actual, required: actual >= required,
            actual_clearance,
            required_clearance,
            name='clearance_allows',
        ),
    )

    for fact in [
        user_role('alice', 'editor'),
        user_role('bob', 'reader'),
        user_role('carol', 'admin'),
        role_parent('admin', 'editor'),
        role_parent('editor', 'reader'),
        role_permission('reader', 'read', 'document'),
        role_permission('editor', 'edit', 'document'),
        role_permission('admin', 'delete', 'document'),
        resource('handbook', 'document', 'bob', 1),
        resource('roadmap', 'document', 'alice', 2),
        resource('incident-2026-08-04', 'document', 'carol', 3),
        clearance('alice', 2),
        clearance('bob', 1),
        clearance('carol', 3),
        owner_action('read'),
        owner_action('edit'),
    ]:
        program.fact(fact)

    return program.compile(), {
        'authorized': authorized,
    }


def authorization_example() -> dict[str, object]:
    executable, relations = build_authorization_program()
    authorized = relations['authorized']
    action, resource_id, reason = wam.variables('action resource_id reason')

    grants = [
        (solution[action], solution[resource_id], solution[reason])
        for solution in executable.solve(authorized('alice', action, resource_id, reason))
    ]

    denied = next(
        executable.solve(authorized('bob', 'read', 'roadmap', reason)),
        None,
    ) is None

    return {
        'alice_grants': grants,
        'bob_is_denied_roadmap': denied,
    }


## Workload placement


def build_scheduler_program() -> tuple[wam.Executable, dict[str, wam.Relation]]:
    program = wam.Program()

    workload = program.relation('workload', 4)
    node = program.relation('node', 4)
    node_capability = program.relation('node_capability', 2)
    has_capabilities = program.relation('has_capabilities', 2)
    placement = program.relation('placement', 3)

    node_name, capability, capabilities, rest = wam.variables(
        'node_name capability capabilities rest'
    )
    workload_name, region = wam.variables('workload_name region')
    required_cpu, free_cpu, headroom = wam.variables('required_cpu free_cpu headroom')

    program.fact(has_capabilities(node_name, wam.NIL))
    program.rule(
        has_capabilities(node_name, wam.cons(capability, rest)),
        node_capability(node_name, capability),
        has_capabilities(node_name, rest),
    )

    program.rule(
        placement(workload_name, node_name, headroom),
        workload(workload_name, region, required_cpu, capabilities),
        node(node_name, region, free_cpu, 'ready'),
        wam.guard(
            lambda free, required: free >= required,
            free_cpu,
            required_cpu,
            name='enough_cpu',
        ),
        has_capabilities(node_name, capabilities),
        wam.project(
            headroom,
            lambda free, required: free - required,
            free_cpu,
            required_cpu,
            name='cpu_headroom',
        ),
    )

    workloads = [
        ('arm-builder', 'us-west', 4, ['docker', 'arm64']),
        ('inference', 'us-west', 12, ['docker', 'x86_64', 'gpu']),
        ('api', 'us-west', 2, ['docker', 'x86_64']),
        ('docs', 'us-east', 4, ['docker']),
        ('oversized', 'us-west', 32, ['docker', 'x86_64']),
    ]
    nodes = [
        ('west-a', 'us-west', 8, 'ready'),
        ('west-b', 'us-west', 20, 'ready'),
        ('west-c', 'us-west', 64, 'draining'),
        ('east-a', 'us-east', 16, 'ready'),
    ]
    capabilities_by_node = {
        'west-a': ['docker', 'arm64'],
        'west-b': ['docker', 'x86_64', 'gpu'],
        'west-c': ['docker', 'x86_64', 'gpu'],
        'east-a': ['docker', 'x86_64'],
    }

    for row in workloads:
        program.fact(workload(*row))
    for row in nodes:
        program.fact(node(*row))
    for name, capabilities in capabilities_by_node.items():
        for item in capabilities:
            program.fact(node_capability(name, item))

    return program.compile(), {
        'placement': placement,
    }


def scheduler_example() -> dict[str, object]:
    executable, relations = build_scheduler_program()
    placement = relations['placement']
    workload_name, node_name, headroom = wam.variables('workload_name node_name headroom')

    candidates = [
        (solution[workload_name], solution[node_name], solution[headroom])
        for solution in executable.solve(placement(workload_name, node_name, headroom))
    ]

    by_workload: dict[str, list[tuple[str, int]]] = collections.defaultdict(list)
    for name, node, free in candidates:
        by_workload[ta.cast(str, name)].append((ta.cast(str, node), ta.cast(int, free)))

    chosen = {
        name: min(nodes, key=lambda item: item[1])[0]
        for name, nodes in by_workload.items()
    }

    return {
        'candidates': candidates,
        'least_waste_placement': chosen,
        'unscheduled': sorted({'arm-builder', 'inference', 'api', 'docs', 'oversized'} - chosen.keys()),
    }


## Incremental test selection


def build_test_selection_program() -> tuple[wam.Executable, dict[str, wam.Relation]]:
    program = wam.Program()

    depends_on = program.relation('depends_on', 2)
    test_suite = program.relation('test_suite', 2)
    impact = program.relation('impact', 3)
    rerun = program.relation('rerun', 3)

    changed, target, dependency, path, suite = wam.variables(
        'changed target dependency path suite'
    )

    program.rule(
        impact(changed, target, [target, changed]),
        depends_on(target, changed),
    )
    program.rule(
        impact(changed, target, wam.cons(target, path)),
        depends_on(target, dependency),
        impact(changed, dependency, path),
    )

    program.rule(rerun(changed, suite, [changed]), test_suite(changed, suite))
    program.rule(
        rerun(changed, suite, path),
        impact(changed, target, path),
        test_suite(target, suite),
    )

    for target_name, dependency_name in [
        ('model', 'schema'),
        ('api', 'model'),
        ('billing', 'model'),
        ('web', 'api'),
        ('integration', 'api'),
        ('integration', 'billing'),
        ('release', 'web'),
        ('release', 'integration'),
    ]:
        program.fact(depends_on(target_name, dependency_name))

    for component, name in [
        ('schema', 'unit-schema'),
        ('model', 'unit-model'),
        ('api', 'unit-api'),
        ('billing', 'unit-billing'),
        ('web', 'e2e-web'),
        ('integration', 'integration'),
        ('release', 'smoke-release'),
    ]:
        program.fact(test_suite(component, name))

    return program.compile(), {
        'rerun': rerun,
    }


def test_selection_example() -> dict[str, object]:
    executable, relations = build_test_selection_program()
    rerun = relations['rerun']
    suite, path = wam.variables('suite path')

    proofs = [
        (solution[suite], solution[path])
        for solution in executable.solve(rerun('schema', suite, path))
    ]

    return {
        'proofs': proofs,
        'suites': _unique(suite_name for suite_name, _ in proofs),
    }


## Incident correlation


def build_incident_program() -> tuple[wam.Executable, dict[str, wam.Relation]]:
    program = wam.Program()

    depends_on = program.relation('depends_on', 2)
    uses = program.relation('uses', 3)

    service, dependency, direct, path = wam.variables('service dependency direct path')

    program.rule(
        uses(service, dependency, [service, dependency]),
        depends_on(service, dependency),
    )
    program.rule(
        uses(service, dependency, wam.cons(service, path)),
        depends_on(service, direct),
        uses(direct, dependency, path),
    )

    for consumer, provider in [
        ('frontend', 'api'),
        ('api', 'auth'),
        ('api', 'orders'),
        ('auth', 'postgres'),
        ('orders', 'postgres'),
        ('worker', 'orders'),
        ('payments', 'postgres'),
        ('metrics', 'prometheus'),
    ]:
        program.fact(depends_on(consumer, provider))

    return program.compile(), {
        'uses': uses,
    }


def incident_correlation_example() -> dict[str, object]:
    executable, relations = build_incident_program()
    uses = relations['uses']
    dependency, path = wam.variables('dependency path')
    failed_services = ['frontend', 'worker', 'payments']

    evidence: dict[object, dict[str, object]] = collections.defaultdict(dict)
    for service in failed_services:
        for solution in executable.solve(uses(service, dependency, path)):
            evidence[solution[dependency]].setdefault(service, solution[path])

    ranked = sorted(
        (
            {
                'suspect': suspect,
                'coverage': len(paths),
                'paths': paths,
            }
            for suspect, paths in evidence.items()
        ),
        key=lambda item: (-ta.cast(int, item['coverage']), str(item['suspect'])),
    )

    return {
        'failed_services': failed_services,
        'ranked_suspects': ranked,
    }


##


def main() -> None:
    examples = {
        'authorization': authorization_example(),
        'scheduler': scheduler_example(),
        'test_selection': test_selection_example(),
        'incident_correlation': incident_correlation_example(),
    }
    pprint.pp(examples, sort_dicts=False, width=120)


if __name__ == '__main__':
    main()
