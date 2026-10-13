import os.path
import re
import subprocess
import sys


def test_async_outcomes_are_reported():
    # Each outcome has to be observed from outside the run which produces it, so the cases run under a child pytest.
    # Skips and xfails raised inside async tests were once swallowed, reporting those tests as passed.
    cases_path = os.path.join(os.path.dirname(__file__), 'outcomes.py')

    proc = subprocess.run(  # noqa
        [
            sys.executable,
            '-m', 'pytest',
            cases_path,
            '-p', 'no:cacheprovider',
            '-q',
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    summary = re.search(r'^=+ (.+) in [\d.]+s', proc.stdout, re.MULTILINE)
    assert summary is not None, proc.stdout + proc.stderr

    counts = {
        kind: int(num)
        for num, kind in re.findall(r'(\d+) (\w+)', summary.group(1))
    }
    assert counts == {
        'passed': 1,
        'failed': 1,
        'skipped': 2,
        'xfailed': 1,
    }, proc.stdout
