import pytest

from ..semver import satisfies
from ..semver import sort_versions


##


@pytest.mark.parametrize(('version', 'expression', 'expected'), [
    ('1.2.3', '1.2.3', True),
    ('1.2.4', '1.2.3', False),
    ('1.9.0', '^1.2.3', True),
    ('2.0.0', '^1.2.3', False),
    ('0.2.9', '^0.2.3', True),
    ('0.3.0', '^0.2.3', False),
    ('0.0.4', '^0.0.3', False),
    ('1.2.9', '~1.2.3', True),
    ('1.3.0', '~1.2.3', False),
    ('6.9.1', '6.x.x', True),
    ('7.0.0', '6.x.x', False),
    ('1.2.9', '1.2', True),
    ('1.3.0', '1.2', False),
    ('1.2.8', '>=1.2.7 <1.3.0', True),
    ('1.3.0', '>=1.2.7 <1.3.0', False),
    ('2.2.0', '1.2.3 - 2.3', True),
    ('2.4.0', '1.2.3 - 2.3', False),
    ('1.2.8', '1.2.7 || >=1.2.9 <2.0.0', False),
    ('1.4.0', '1.2.7 || >=1.2.9 <2.0.0', True),
    ('1.2.3-beta.2', '>=1.2.3-beta.1 <1.2.3', True),
    ('1.2.4-beta.1', '>=1.2.3-beta.1', False),
    ('1.2.3-beta.1', '*', False),
])
def test_satisfies(version: str, expression: str, expected: bool) -> None:
    assert satisfies(version, expression) is expected


def test_sort_versions_uses_semantic_precedence() -> None:
    assert sort_versions(['1.0.0', '1.0.0-beta.2', '1.0.0-beta.11', '2.0.0'], reverse=True) == [
        '2.0.0',
        '1.0.0',
        '1.0.0-beta.11',
        '1.0.0-beta.2',
    ]
