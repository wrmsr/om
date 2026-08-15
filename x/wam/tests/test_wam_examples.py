from . import wam_examples as examples


##


def test_authorization_example():
    result = examples.authorization_example()

    assert result['bob_is_denied_roadmap'] is True
    assert ('delete', 'roadmap', examples.wam.struct('role', 'admin')) not in result['alice_grants']
    assert ('edit', 'roadmap', 'owner') in result['alice_grants']
    assert ('read', 'roadmap', examples.wam.struct('role', 'reader')) in result['alice_grants']


def test_scheduler_example():
    result = examples.scheduler_example()

    assert result['least_waste_placement'] == {
        'arm-builder': 'west-a',
        'inference': 'west-b',
        'api': 'west-b',
        'docs': 'east-a',
    }
    assert result['unscheduled'] == ['oversized']


def test_test_selection_example():
    result = examples.test_selection_example()

    assert result['suites'] == [
        'unit-schema',
        'unit-model',
        'unit-api',
        'unit-billing',
        'e2e-web',
        'integration',
        'smoke-release',
    ]
    assert ('smoke-release', ['release', 'web', 'api', 'model', 'schema']) in result['proofs']
    assert ('smoke-release', ['release', 'integration', 'billing', 'model', 'schema']) in result['proofs']


def test_incident_correlation_example():
    result = examples.incident_correlation_example()
    top = result['ranked_suspects'][0]

    assert top['suspect'] == 'postgres'
    assert top['coverage'] == 3
    assert set(top['paths']) == {'frontend', 'worker', 'payments'}
