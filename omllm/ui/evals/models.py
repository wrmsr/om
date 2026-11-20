import hashlib
import json
import os
import re
import typing as ta

from omcore import dataclasses as dc

from .commands import CommandResult
from .commands import read_text


##


def hash_tree(path: str) -> str:
    digest = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', '__pycache__'})
        files.extend(d for d in dirs if os.path.islink(os.path.join(root, d)))
        for name in sorted(files):
            full_path = os.path.join(root, name)
            digest.update(os.path.relpath(full_path, path).encode() + b'\0')
            digest.update(str(os.stat(full_path, follow_symlinks=False).st_mode & 0o777).encode() + b'\0')
            if os.path.islink(full_path):
                digest.update(b'link\0' + os.readlink(full_path).encode())
            else:
                with open(full_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b''):
                        digest.update(chunk)
            digest.update(b'\0')
    return digest.hexdigest()


##


@dc.dataclass(frozen=True)
class Task:
    name: str
    path: str
    instruction: str


def load_tasks(root: str, names: ta.Sequence[str] = ()) -> list[Task]:
    root = os.path.abspath(root)
    selected = list(names) if names else sorted(os.listdir(root))
    tasks = []
    for name in selected:
        path = os.path.join(root, name)
        if not names and (name.startswith('.') or not os.path.isdir(path)):
            continue
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', name):
            raise ValueError(f'Invalid task name: {name!r}')
        for item in ('instruction.md', 'environment/Dockerfile', 'tests/test.sh'):
            if not os.path.isfile(os.path.join(path, item)):
                raise ValueError(f'Missing task file: {os.path.join(path, item)}')
        tasks.append(Task(name, path, read_text(os.path.join(path, 'instruction.md'))))
    if not tasks:
        raise ValueError('No tasks selected')
    if len({t.name for t in tasks}) != len(tasks):
        raise ValueError('Duplicate task selection')
    return tasks


@dc.dataclass(frozen=True)
class Agent:
    name: str
    kind: str
    command: tuple[str, ...] = ()
    directory: str = ''
    dockerfile: str = ''
    env: tuple[str, ...] = ()
    required_env: tuple[str, ...] = ()
    environment: ta.Mapping[str, str] = dc.field(default_factory=dict)
    user: str = 'agent'
    stdin: str = 'prompt'
    version_command: tuple[str, ...] = ()


def load_agent(name: str, root: str, command: ta.Sequence[str]) -> Agent:
    if name in {'oracle', 'nop', 'external', 'scripted', 'om'}:
        if (name == 'external') != bool(command):
            raise ValueError('Use --agent external -- COMMAND [ARGS...] for a host agent')
        return Agent(name, name, tuple(command))
    if command:
        raise ValueError('A trailing command is only valid with --agent external')
    path = name if name.endswith('.json') else os.path.join(root, name, 'agent.json')
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError('Agent configuration must be a JSON object')  # noqa
    raw['directory'] = os.path.dirname(os.path.abspath(path))
    for key in ('command', 'env', 'required_env', 'version_command'):
        values = raw.get(key, [])
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise ValueError(f'Agent {key} must be a list of strings')
        raw[key] = tuple(values)
    agent = Agent(**raw)
    if not isinstance(agent.name, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', agent.name):
        raise ValueError('Agent name must be a simple filename component')
    if agent.kind != 'container' or not agent.command:
        raise ValueError('A configured agent needs kind="container" and a command')
    if agent.stdin not in {'prompt', 'none'}:
        raise ValueError('Agent stdin must be "prompt" or "none"')
    if not isinstance(agent.environment, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in agent.environment.items()
    ):
        raise ValueError('Agent environment must map strings to strings')
    return agent


def classify_result(agent: CommandResult, verifier: CommandResult) -> str:
    if agent.timed_out:
        return 'agent_timeout'
    if agent.returncode:
        return 'agent_error'
    if verifier.timed_out:
        return 'test_timeout'
    if verifier.returncode == 0:
        return 'passed'
    if verifier.returncode == 1:
        return 'failed'
    return 'grader_error'


##
