"""
Apply known fixes through the external-agent contract to check the runner's wiring.

Run from the project directory:
    python3 -m minieval run --agent external -- python3 -m examples.externaloracle --solutions tasks

This reads solution files on the host and copies them into the provided container.
Its success measures the smoke test, not a coding agent's performance.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import typing as ta


##


def run_oracle(request: ta.Mapping[str, ta.Any], *, solutions: str) -> None:
    task_id = request.get('task_id')
    if not isinstance(task_id, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', task_id):
        raise ValueError('task_id must be a simple directory name')

    solution = os.path.abspath(os.path.join(solutions, task_id, 'solution'))
    if not os.path.isfile(os.path.join(solution, 'solve.sh')):
        raise ValueError(f'Missing reference fix: {os.path.join(solution, "solve.sh")}')

    docker = request.get('docker_executable', 'docker')
    container_id = request.get('container_id')
    user = request.get('user')
    workdir = request.get('workdir')
    if not all(isinstance(value, str) and value for value in (docker, container_id, user, workdir)):
        raise ValueError('The request needs docker_executable, container_id, user, and workdir strings')

    timeout = float(request.get('timeout_seconds', 600))
    if not (0 < timeout < float('inf')):
        raise ValueError('timeout_seconds must be a finite positive number')
    deadline = time.monotonic() + timeout

    commands = [
        [docker, 'cp', solution, ta.cast(str, container_id) + ':/solution'],
        [docker, 'exec', '-i', '--user', user, '--workdir', workdir, container_id, 'sh', '/solution/solve.sh'],
    ]
    for command in commands:
        subprocess.run(
            command,
            check=True,
            stdin=subprocess.DEVNULL,
            timeout=max(0.0, deadline - time.monotonic()),
        )


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solutions', default='tasks', help='Task root containing TASK_ID/solution/solve.sh')
    args = parser.parse_args()

    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError('Expected one JSON request object on stdin')  # noqa
        run_oracle(request, solutions=args.solutions)
    except (OSError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    _main()
