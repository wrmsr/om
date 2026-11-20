import glob
import json
import os
import shutil
import sys
import tempfile
import time
import typing as ta

from omcore import dataclasses as dc

from .commands import CommandResult
from .commands import checked
from .commands import read_text
from .commands import remove_path
from .commands import replace_tokens
from .commands import run_command
from .commands import write_json
from .harness import run_harness
from .landlock import local_agent_read_access
from .landlock import local_environment
from .landlock import local_grader_read_access
from .landlock import prepare_local_scratch
from .models import Agent
from .models import Task
from .models import classify_result
from .models import hash_tree


##


def prepare_local_workspace(task: Task, workdir: str, log_path: str) -> None:
    dockerfile = read_text(os.path.join(task.path, 'environment', 'Dockerfile'))
    copy_lines = [line.strip() for line in dockerfile.splitlines() if line.lstrip().startswith(('COPY ', 'ADD '))]
    if copy_lines != ['COPY *.py ./']:
        raise ValueError(f'Task {task.name} needs a local task setup; supported Dockerfile copy: COPY *.py ./')
    os.mkdir(workdir)
    for source in sorted(glob.glob(os.path.join(task.path, 'environment', '*.py'))):
        shutil.copy2(source, workdir)
    for command in (
            ['git', 'init', '-q'],
            ['git', 'config', 'user.name', 'Mini Eval'],
            ['git', 'config', 'user.email', 'minieval@localhost'],
            ['git', 'add', '-f', '-A', '--', '.'],
            ['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Initial task', '--allow-empty'],
    ):
        checked(run_command(command, cwd=workdir, log_path=log_path, timeout=30), log_path)


def run_local_agent(
        agent: Agent,
        task: Task,
        request: ta.Mapping[str, ta.Any],
        *,
        scratch: str,
        timeout: float,
        extra_args: ta.Sequence[str],
        extra_env: ta.Sequence[str],
        script: str | None,
) -> CommandResult:
    workdir = request['workdir']
    log_path = os.path.join(request['output_dir'], 'agent.log')
    if agent.kind == 'nop':
        return CommandResult(0, 0.0)
    if extra_env:
        raise ValueError('--env is not supported with the local runtime: it could expose other secrets')
    if agent.kind in {'scripted', 'om'}:
        return run_harness(
            {**request, 'scratch': scratch, 'task_path': task.path},
            kind=agent.kind,
            timeout=timeout,
            extra_args=extra_args,
            script=script,
        )

    env = local_environment(workdir, scratch)
    read_files: list[str] = [request['instruction_file']]
    read_trees: list[str] = []
    if agent.kind == 'oracle':
        solution = os.path.join(task.path, 'solution')
        if not os.path.isfile(os.path.join(solution, 'solve.sh')):
            raise ValueError(f'Task {task.name} has no solution/solve.sh')
        env['MINIEVAL_SOLUTION_DIR'] = solution
        read_trees.append(solution)
        command = ['sh', os.path.join(solution, 'solve.sh')]
        input_data = None
    elif agent.kind == 'external':
        tokens = {
            'workdir': workdir,
            'instruction_file': request['instruction_file'],
            'prompt_file': request['container_instruction_file'],
            'output_dir': request['output_dir'],
        }
        command = [replace_tokens(arg, tokens) for arg in (*agent.command, *extra_args)]
        if len(command) > 1 and command[0] == sys.executable and os.path.isfile(command[1]):
            read_files.append(command[1])
        input_data = (json.dumps(dict(request)) + '\n').encode()
    else:
        raise ValueError(f'Agent {agent.name} requires the Docker runtime')
    return run_command(
        command,
        cwd=workdir,
        env=env,
        log_path=log_path,
        timeout=timeout,
        input_data=input_data,
        local_write_paths=[workdir, scratch, request['artifact_dir']],
        local_read_access=local_agent_read_access(blocked=task.path, files=read_files, trees=read_trees),
        cleanup_group=True,
    )


def run_local_trial(
        task: Task,
        agent: Agent,
        *,
        output_dir: str,
        timeout: float,
        test_timeout: float,
        extra_args: ta.Sequence[str] = (),
        extra_env: ta.Sequence[str] = (),
        script: str | None = None,
) -> dict[str, ta.Any]:
    os.mkdir(output_dir)
    started = time.monotonic()
    result: dict[str, ta.Any] = {
        'task': task.name,
        'task_sha256': hash_tree(task.path),
        'agent': agent.name,
        'runtime': 'local',
        'task_image': None,
        'agent_image': None,
        'status': 'infrastructure_error',
    }
    phase = 'setup'
    try:
        with tempfile.TemporaryDirectory(prefix='local-', dir=output_dir) as temporary:
            agent_workdir = os.path.join(temporary, 'agent')
            agent_scratch = os.path.join(temporary, 'agent-tmp')
            prepare_local_scratch(agent_scratch)
            prepare_local_workspace(task, agent_workdir, os.path.join(output_dir, 'setup.log'))
            instruction_file = os.path.join(output_dir, 'instruction.md')
            with open(instruction_file, 'w', encoding='utf-8') as f:
                f.write(task.instruction)
            artifact_dir = os.path.join(output_dir, 'agent-artifacts')
            os.mkdir(artifact_dir)
            request = {
                'task_id': task.name,
                'runtime': 'local',
                'workdir': agent_workdir,
                'instruction': task.instruction,
                'instruction_file': instruction_file,
                'container_instruction_file': instruction_file,
                'output_dir': output_dir,
                'artifact_dir': artifact_dir,
                'timeout_seconds': timeout,
            }
            write_json(os.path.join(output_dir, 'request.json'), request)
            phase = 'agent'
            attempt = run_local_agent(
                agent,
                task,
                request,
                scratch=agent_scratch,
                timeout=timeout,
                extra_args=extra_args,
                extra_env=extra_env,
                script=script,
            )
            result['agent_result'] = dc.asdict(attempt) | {'stdout': None}
            phase = 'snapshot'
            workspace = os.path.join(output_dir, 'workspace')
            shutil.copytree(
                agent_workdir,
                workspace,
                symlinks=True,
                ignore=shutil.ignore_patterns('.git', '__pycache__'),
            )
            phase = 'grader_setup'
            grader_workdir = os.path.join(temporary, 'grader')
            grader_scratch = os.path.join(temporary, 'grader-tmp')
            tests = os.path.join(temporary, 'tests')
            prepare_local_scratch(grader_scratch)
            prepare_local_workspace(task, grader_workdir, os.path.join(output_dir, 'setup.log'))
            for name in os.listdir(grader_workdir):
                if name != '.git':
                    remove_path(os.path.join(grader_workdir, name))
            shutil.copytree(workspace, grader_workdir, dirs_exist_ok=True, symlinks=True)
            shutil.copytree(os.path.join(task.path, 'tests'), tests)
            for command in (
                    ['git', 'add', '-f', '-A', '--', '.'],
                    ['git', 'diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv', 'HEAD', '--'],
            ):
                command_result = checked(run_command(
                    command,
                    cwd=grader_workdir,
                    log_path=os.path.join(output_dir, 'setup.log'),
                    timeout=30,
                    capture=command[1] == 'diff',
                ), os.path.join(output_dir, 'setup.log'))
            with open(os.path.join(output_dir, 'patch.diff'), 'wb') as f:
                f.write(command_result.stdout)
            phase = 'grader'
            verification = run_command(
                ['sh', os.path.join(tests, 'test.sh')],
                cwd=grader_workdir,
                env=local_environment(grader_workdir, grader_scratch, tests=tests),
                log_path=os.path.join(output_dir, 'verifier.log'),
                timeout=test_timeout,
                local_write_paths=[grader_workdir, grader_scratch],
                local_read_access=local_grader_read_access(tests),
                cleanup_group=True,
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
        write_json(os.path.join(output_dir, 'result.json'), result)
    return result


##
