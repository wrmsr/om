import json
import os
import re
import secrets
import time
import typing as ta

from omcore import dataclasses as dc

from .commands import CommandError
from .commands import CommandResult
from .commands import checked
from .commands import remove_path
from .commands import replace_tokens
from .commands import run_command
from .commands import write_json
from .harness import run_harness
from .models import Agent
from .models import Task
from .models import classify_result
from .models import hash_tree


##


WORKDIR = '/work'
CONTAINER_PROMPT = '/tmp/mini-eval-instruction.md'  # noqa


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
        script: str | None = None,
) -> CommandResult:
    container_id = request['container_id']
    log_path = os.path.join(request['output_dir'], 'agent.log')
    if agent.kind == 'nop':
        return CommandResult(0, 0.0)
    if agent.kind in {'scripted', 'om'}:
        return run_harness(
            request,
            kind=agent.kind,
            timeout=timeout,
            extra_args=extra_args,
            script=script,
        )
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
        script: str | None = None,
) -> dict[str, ta.Any]:
    os.mkdir(output_dir)
    started = time.monotonic()
    containers: list[str] = []
    result: dict[str, ta.Any] = {
        'task': task.name,
        'task_sha256': hash_tree(task.path),
        'agent': agent.name,
        'runtime': 'docker',
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
        artifact_dir = os.path.join(output_dir, 'agent-artifacts')
        os.mkdir(artifact_dir)
        request = {
            'task_id': task.name,
            'runtime': 'docker',
            'container_id': container_id,
            'docker_executable': docker.executable,
            'workdir': WORKDIR,
            'user': 'agent',
            'instruction': task.instruction,
            'instruction_file': instruction_file,
            'container_instruction_file': CONTAINER_PROMPT,
            'output_dir': output_dir,
            'artifact_dir': artifact_dir,
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
            script=script,
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
