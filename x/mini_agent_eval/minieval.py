"""A small, standard-library-only coding-agent evaluator using the Docker CLI."""
import argparse
import dataclasses as dc
import datetime
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import time
import typing as ta


##


WORKDIR = '/work'
CONTAINER_PROMPT = '/tmp/mini-eval-instruction.md'  # noqa


class CommandError(Exception):
    pass


@dc.dataclass(frozen=True)
class CommandResult:
    returncode: int
    seconds: float
    timed_out: bool = False
    stdout: bytes = b''


def write_json(path: str, value: ta.Any) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def read_text(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def stop_process(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    # A child can outlive its process-group leader.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def run_command(
        command: ta.Sequence[str],
        *,
        log_path: str,
        timeout: float,
        input_data: bytes | None = None,
        capture: bool = False,
) -> CommandResult:
    started = time.monotonic()
    timed_out = False
    with open(log_path, 'ab') as log:
        log.write(f'\n$ {shlex.join(command)}\n'.encode())
        log.flush()
        with subprocess.Popen(
                list(command),
                stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE if capture else log,
                stderr=log,
                start_new_session=True,
        ) as process:
            try:
                stdout, _ = process.communicate(input=input_data, timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                stop_process(process)
                stdout, _ = process.communicate(timeout=5)
            except BaseException:
                stop_process(process)
                raise
        if capture and stdout:
            log.write(stdout)
    return CommandResult(process.returncode, time.monotonic() - started, timed_out, stdout or b'')


def checked(result: CommandResult, log_path: str) -> CommandResult:
    if result.timed_out:
        raise CommandError(f'Command timed out; see {log_path}')
    if result.returncode:
        raise CommandError(f'Command exited {result.returncode}; see {log_path}')
    return result


def replace_tokens(value: str, tokens: ta.Mapping[str, str]) -> str:
    return re.sub(r'\{([a-z_]+)\}', lambda match: tokens.get(match[1], match[0]), value)


def remove_path(path: str) -> None:
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


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
    if name in {'oracle', 'nop', 'external'}:
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


class Docker:
    def __init__(
            self,
            *,
            executable: str,
            platform: str | None,
            timeout: float,
            log_path: str,
    ) -> None:
        super().__init__()

        self._executable = executable
        self._platform = platform
        self._timeout = timeout
        self._log_path = log_path

    @property
    def executable(self) -> str:
        return self._executable

    def call(
            self,
            args: ta.Sequence[str],
            *,
            log_path: str | None = None,
            timeout: float | None = None,
            input_data: bytes | None = None,
            capture: bool = False,
            no_check: bool = False,
    ) -> CommandResult:
        log_path = log_path or self._log_path
        result = run_command(
            [self._executable, *args],
            log_path=log_path,
            timeout=self._timeout if timeout is None else timeout,
            input_data=input_data,
            capture=capture,
        )
        return result if no_check else checked(result, log_path)

    def build(
            self,
            context: str,
            *,
            tag: str,
            dockerfile: str = 'Dockerfile',
            build_args: ta.Sequence[str] = (),
    ) -> str:
        args = ['build', '-t', tag, '-f', os.path.join(context, dockerfile)]
        if self._platform:
            args.extend(['--platform', self._platform])
        for arg in build_args:
            args.extend(['--build-arg', arg])
        self.call([*args, context])
        return self.call(['image', 'inspect', '--format', '{{.Id}}', tag], capture=True).stdout.decode().strip()

    def create(self, image: str, *, name: str, grading: bool = False) -> str:
        args = ['create', '--init', '--name', name, '--label', 'minieval=true', '--workdir', WORKDIR]
        if self._platform:
            args.extend(['--platform', self._platform])
        if grading:
            args.extend(['--network', 'none'])
        result = self.call([*args, '--entrypoint', 'sleep', image, 'infinity'], capture=True)
        container_id = result.stdout.decode().strip()
        if not re.fullmatch(r'[0-9a-f]{64}', container_id):
            raise CommandError('Docker did not return a container ID')
        return container_id

    def execute(
            self,
            container_id: str,
            command: ta.Sequence[str],
            *,
            user: str = 'agent',
            env: ta.Sequence[str] = (),
            **kwargs: ta.Any,
    ) -> CommandResult:
        args = ['exec', '-i', '--user', user, '--workdir', WORKDIR, '--env', 'HOME=/home/agent']
        for item in env:
            args.extend(['--env', item])
        return self.call([*args, container_id, *command], **kwargs)


def initialize_workspace(docker: Docker, container_id: str) -> None:
    docker.execute(
        container_id,
        ['sh', '-c', 'mkdir -p /work; chown -R agent:agent /work'],
        user='root',
    )
    docker.execute(container_id, ['git', 'init', '-q'])
    docker.execute(container_id, ['git', 'config', 'user.name', 'Mini Eval'])
    docker.execute(container_id, ['git', 'config', 'user.email', 'minieval@localhost'])
    docker.execute(container_id, ['git', 'add', '-f', '-A', '--', '.'])
    docker.execute(
        container_id,
        ['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Initial task', '--allow-empty'],
    )


def restore_workspace(docker: Docker, container_id: str, workspace: str) -> None:
    # Keep only the fresh grader's Git metadata, including when the agent deleted files.
    docker.execute(
        container_id,
        ['sh', '-c', 'find /work -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf -- {} +'],
        user='root',
    )
    docker.call(['cp', os.path.join(workspace, '.'), container_id + ':/work'])
    docker.execute(container_id, ['chown', '-hR', 'agent:agent', WORKDIR], user='root')


def run_agent(
        docker: Docker,
        agent: Agent,
        task: Task,
        request: ta.Mapping[str, ta.Any],
        *,
        timeout: float,
        extra_args: ta.Sequence[str],
        extra_env: ta.Sequence[str],
) -> CommandResult:
    container_id = request['container_id']
    log_path = os.path.join(request['output_dir'], 'agent.log')
    if agent.kind == 'nop':
        return CommandResult(0, 0.0)
    if agent.kind == 'oracle':
        solution = os.path.join(task.path, 'solution')
        if not os.path.isfile(os.path.join(solution, 'solve.sh')):
            raise ValueError(f'Task {task.name} has no solution/solve.sh')
        docker.call(['cp', solution, container_id + ':/solution'])
        return docker.execute(
            container_id,
            ['sh', '/solution/solve.sh'],
            log_path=log_path,
            timeout=timeout,
            no_check=True,
        )
    tokens = {
        'container_id': container_id,
        'workdir': WORKDIR,
        'instruction_file': request['instruction_file'],
        'prompt_file': CONTAINER_PROMPT,
        'output_dir': request['output_dir'],
    }
    command = [replace_tokens(arg, tokens) for arg in (*agent.command, *extra_args)]
    if agent.kind == 'external':
        return run_command(
            command,
            log_path=log_path,
            timeout=timeout,
            input_data=(json.dumps(dict(request)) + '\n').encode(),
        )
    env = [name for name in (*agent.env, *extra_env) if name in os.environ]
    env.extend(f'{key}={value}' for key, value in agent.environment.items())
    if agent.version_command:
        docker.execute(
            container_id,
            agent.version_command,
            user=agent.user,
            env=env,
            log_path=os.path.join(request['output_dir'], 'agent-version.log'),
            timeout=30,
        )
    return docker.execute(
        container_id,
        command,
        user=agent.user,
        env=env,
        log_path=log_path,
        timeout=timeout,
        input_data=task.instruction.encode() if agent.stdin == 'prompt' else None,
        no_check=True,
    )


def run_trial(
        docker: Docker,
        task: Task,
        agent: Agent,
        *,
        task_image: str,
        agent_image: str,
        output_dir: str,
        timeout: float,
        test_timeout: float,
        extra_args: ta.Sequence[str] = (),
        extra_env: ta.Sequence[str] = (),
        keep_containers: bool = False,
) -> dict[str, ta.Any]:
    os.mkdir(output_dir)
    started = time.monotonic()
    containers: list[str] = []
    result: dict[str, ta.Any] = {
        'task': task.name,
        'task_sha256': hash_tree(task.path),
        'agent': agent.name,
        'task_image': task_image,
        'agent_image': agent_image,
        'status': 'infrastructure_error',
    }
    prefix = 'minieval-' + secrets.token_hex(8)
    phase = 'setup'
    try:
        # Register the name before creating it, including if Docker is interrupted after creation.
        containers.append(prefix + '-agent')
        container_id = docker.create(agent_image, name=containers[-1])
        containers[-1] = container_id
        docker.call(['start', container_id])
        initialize_workspace(docker, container_id)
        instruction_file = os.path.join(output_dir, 'instruction.md')
        with open(instruction_file, 'w', encoding='utf-8') as f:
            f.write(task.instruction)
        docker.call(['cp', instruction_file, container_id + ':' + CONTAINER_PROMPT])
        request = {
            'task_id': task.name,
            'container_id': container_id,
            'docker_executable': docker.executable,
            'workdir': WORKDIR,
            'user': 'agent',
            'instruction': task.instruction,
            'instruction_file': instruction_file,
            'container_instruction_file': CONTAINER_PROMPT,
            'output_dir': output_dir,
            'timeout_seconds': timeout,
        }
        write_json(os.path.join(output_dir, 'request.json'), request)
        phase = 'agent'
        attempt = run_agent(
            docker,
            agent,
            task,
            request,
            timeout=timeout,
            extra_args=extra_args,
            extra_env=extra_env,
        )
        result['agent_result'] = dc.asdict(attempt) | {'stdout': None}
        phase = 'snapshot'
        # Stopping the container also kills processes left behind by docker exec.
        docker.call(['stop', '--time', '1', container_id], timeout=30)
        workspace = os.path.join(output_dir, 'workspace')
        os.mkdir(workspace)
        docker.call(['cp', container_id + ':/work/.', workspace])
        remove_path(os.path.join(workspace, '.git'))
        phase = 'grader_setup'
        containers.append(prefix + '-grader')
        grader_id = docker.create(task_image, name=containers[-1], grading=True)
        containers[-1] = grader_id
        docker.call(['start', grader_id])
        initialize_workspace(docker, grader_id)
        restore_workspace(docker, grader_id, workspace)
        docker.execute(grader_id, ['git', 'add', '-f', '-A', '--', '.'])
        patch = docker.execute(
            grader_id,
            ['git', 'diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv', 'HEAD', '--'],
            capture=True,
        ).stdout
        with open(os.path.join(output_dir, 'patch.diff'), 'wb') as f:
            f.write(patch)
        docker.call(['cp', os.path.join(task.path, 'tests'), grader_id + ':/tests'])
        verification = docker.execute(
            grader_id,
            ['sh', '/tests/test.sh'],
            log_path=os.path.join(output_dir, 'verifier.log'),
            timeout=test_timeout,
            no_check=True,
        )
        result['verifier_result'] = dc.asdict(verification) | {'stdout': None}
        result['tests_passed'] = not verification.timed_out and verification.returncode == 0
        result['status'] = classify_result(attempt, verification)
    except KeyboardInterrupt:
        result['status'] = 'interrupted'
        raise
    except Exception as exc:  # noqa
        if result.get('agent_result', {}).get('timed_out'):
            result['status'] = 'agent_timeout'
        elif result.get('agent_result', {}).get('returncode'):
            result['status'] = 'agent_error'
        elif phase == 'snapshot':
            result['status'] = 'submission_error'
        elif phase == 'agent':
            result['status'] = 'agent_error'
        result['phase'] = phase
        result['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        result['seconds'] = time.monotonic() - started
        result['containers'] = containers
        cleanup_errors = []
        for container_id in reversed(containers):
            try:
                args = ['stop', '--time', '1'] if keep_containers else ['rm', '-f']
                cleanup = docker.call([*args, container_id], timeout=30, no_check=True)
                if cleanup.timed_out or cleanup.returncode:
                    cleanup_errors.append(container_id)
            except Exception as exc:  # noqa
                cleanup_errors.append(f'{container_id}: {type(exc).__name__}')
        if cleanup_errors:
            result['cleanup_errors'] = cleanup_errors
        write_json(os.path.join(output_dir, 'result.json'), result)
    return result


##


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--tasks', default='tasks')
    parser.add_argument('--task', action='append', default=[])
    parser.add_argument('--runs', default='runs')
    parser.add_argument('--run-id')
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--platform', choices=['linux/amd64', 'linux/arm64'])
    parser.add_argument('--timeout', type=float, default=600)
    parser.add_argument('--test-timeout', type=float, default=120)
    parser.add_argument('--setup-timeout', type=float, default=1800)
    parser.add_argument('--keep-containers', action='store_true')


def run_suite(args: argparse.Namespace) -> int:
    tasks = load_tasks(args.tasks, args.task)
    if args.action == 'check':
        agents = [Agent('nop', 'nop'), Agent('oracle', 'oracle')]
    else:
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        agents = [load_agent(args.agent, args.agents, command)]
    for value in (args.timeout, args.test_timeout, args.setup_timeout):
        if not (0 < value < float('inf')):
            raise ValueError('Timeouts must be finite positive numbers')
    for agent in agents:
        for name in (*agent.env, *agent.required_env, *getattr(args, 'env', []), *agent.environment):
            if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', name):
                raise ValueError(f'Invalid environment variable name: {name!r}')
        for name in agent.required_env:
            if not os.environ.get(name):
                raise ValueError(f'Agent requires environment variable {name}')
    for name in getattr(args, 'env', []):
        if name not in os.environ:
            raise ValueError(f'Environment variable {name} is not set')
    repeat = getattr(args, 'repeat', 1)
    if repeat < 1:
        raise ValueError('--repeat must be positive')
    run_id = args.run_id or (
        datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ-') + secrets.token_hex(3)
    )
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', run_id):
        raise ValueError('Invalid run ID')
    os.makedirs(args.runs, exist_ok=True)
    run_dir = os.path.abspath(os.path.join(args.runs, run_id))
    os.mkdir(run_dir)
    print(f'Run: {run_dir}', flush=True)
    write_json(os.path.join(run_dir, 'run.json'), vars(args) | {'run_id': run_id})
    docker = Docker(
        executable=args.docker,
        platform=args.platform,
        timeout=args.setup_timeout,
        log_path=os.path.join(run_dir, 'setup.log'),
    )
    info = docker.call(['info', '--format', '{{json .}}'], timeout=30, capture=True)
    daemon = json.loads(info.stdout)
    write_json(os.path.join(run_dir, 'docker.json'), {
        key: daemon.get(key) for key in ('ServerVersion', 'OSType', 'Architecture', 'OperatingSystem')
    })
    results = []
    all_expected = True
    for task in tasks:
        print(f'Building {task.name} ...', flush=True)
        suffix = hashlib.sha256((task.path + str(args.platform)).encode()).hexdigest()[:12]
        task_tag = f'minieval-task-{task.name.lower()}:{suffix}'
        task_image = docker.build(os.path.join(task.path, 'environment'), tag=task_tag)
        for agent in agents:
            agent_image = task_image
            if agent.dockerfile:
                build_args = ['TASK_IMAGE=' + task_tag]
                if args.agent_version:
                    build_args.append('AGENT_VERSION=' + args.agent_version)
                agent_tag = 'minieval-agent:' + secrets.token_hex(8)
                agent_image = docker.build(
                    agent.directory,
                    tag=agent_tag,
                    dockerfile=agent.dockerfile,
                    build_args=build_args,
                )
            for attempt in range(1, repeat + 1):
                trial_name = f'{task.name}-{agent.name}-{attempt}'
                if not re.fullmatch(r'[a-zA-Z0-9_.-]+', trial_name):
                    raise ValueError('Agent name must be a simple filename component')
                print(f'Running {trial_name} ...', flush=True)
                result = run_trial(
                    docker,
                    task,
                    agent,
                    task_image=task_image,
                    agent_image=agent_image,
                    output_dir=os.path.join(run_dir, trial_name),
                    timeout=args.timeout,
                    test_timeout=args.test_timeout,
                    extra_args=getattr(args, 'agent_arg', []),
                    extra_env=getattr(args, 'env', []),
                    keep_containers=args.keep_containers,
                )
                results.append(result)
                with open(os.path.join(run_dir, 'results.jsonl'), 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, sort_keys=True) + '\n')
                expected = 'failed' if args.action == 'check' and agent.kind == 'nop' else 'passed'
                all_expected = all_expected and result['status'] == expected and not result.get('cleanup_errors')
                print(f"  {result['status']} ({result['seconds']:.1f}s)", flush=True)
                if 'error' in result:
                    print('  ' + result['error'], file=sys.stderr, flush=True)
    counts: dict[str, int] = {}
    for result in results:
        status = result['status']
        counts[status] = counts.get(status, 0) + 1
    write_json(os.path.join(run_dir, 'summary.json'), {'attempts': len(results), 'counts': counts})
    print(json.dumps(counts, sort_keys=True), flush=True)
    return 0 if all_expected else 1


def _handle_termination(signum: int, frame: ta.Any) -> None:
    raise KeyboardInterrupt


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='action', required=True)
    listing = subparsers.add_parser('list', help='List tasks without running Docker')
    listing.add_argument('--tasks', default='tasks')
    listing.add_argument('--task', action='append', default=[])
    check = subparsers.add_parser('check', help='Require each starter to fail and each reference fix to pass')
    add_options(check)
    run = subparsers.add_parser('run', help='Run an agent on fresh task containers')
    add_options(run)
    run.add_argument('--agent', default='nop')
    run.add_argument('--agents', default='agents')
    run.add_argument('--agent-version')
    run.add_argument('--agent-arg', action='append', default=[])
    run.add_argument('--env', action='append', default=[], metavar='NAME')
    run.add_argument('--repeat', type=int, default=1)
    run.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, _handle_termination)
    try:
        if args.action == 'list':
            for task in load_tasks(args.tasks, args.task):
                print(f'{task.name}: {task.instruction.splitlines()[0].lstrip("# ")}')
            code = 0
        else:
            code = run_suite(args)
    except KeyboardInterrupt:
        print('Interrupted; container cleanup attempted.', file=sys.stderr)
        code = 130
    except (CommandError, OSError, ValueError, TypeError) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        code = 2
    raise SystemExit(code)


if __name__ == '__main__':
    _main()
