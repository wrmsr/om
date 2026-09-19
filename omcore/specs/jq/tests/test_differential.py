import json
import shutil
import subprocess

import pytest

from ..program import compile_jq


##


def _jq_18_executable():
    executable = shutil.which('jq')
    if executable is None:
        pytest.skip('jq executable is not installed')
    version = subprocess.run(
        [executable, '--version'],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not version.startswith('jq-1.8'):
        pytest.skip(f'differential tests require jq 1.8.x, found {version}')
    return executable


@pytest.mark.parametrize(('source', 'value'), [
    ('(1, 2) | (., . + 10)', None),
    ('(1, 2) + (10, 20)', None),
    ('[if (true, false) then 1 else 2 end]', None),
    ('def twice(f): f, f; twice(.name)', {'name': 'value'}),
    ('reduce .[] as $x (0; . + $x)', [1, 2, 3]),
    ('foreach .[] as $x (0; . + $x)', [1, 2, 3]),
    ('(.a, .b) = range(3)', None),
    ('(.[] | select(. % 2 == 0)) |= empty', [0, 1, 2, 3]),
    ('sort_by(.key) | group_by(.key)', [{'key': 2}, {'key': 1}, {'key': 2}]),
    ('[limit(4; repeat(7))]', None),
])
def test_against_jq_18(source, value):
    executable = _jq_18_executable()
    completed = subprocess.run(
        [executable, '--compact-output', source],
        input=json.dumps(value),
        check=True,
        capture_output=True,
        text=True,
    )
    expected = [json.loads(line) for line in completed.stdout.splitlines()]
    assert list(compile_jq(source).evaluate(value)) == expected
