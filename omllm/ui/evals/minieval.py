"""The CLI for the bundled coding-agent evals."""
import argparse
import datetime
import hashlib
import importlib.resources
import json
import os
import platform
import re
import secrets
import shutil
import signal
import sys
import typing as ta

from omcore import lang

from .assets import eval_resources
from .commands import CommandError
from .commands import write_json
from .docker import Docker
from .docker import run_trial
from .landlock import check_local_runtime
from .local import run_local_trial
from .models import Agent
from .models import load_agent
from .models import load_tasks


##


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--tasks')
    parser.add_argument('--task', action='append', default=[])
    parser.add_argument('--runs', default='runs')
    parser.add_argument('--run-id')
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--runtime', choices=['docker', 'local'], default='docker')
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
    script = getattr(args, 'script', None)
    if script is not None and agents[0].kind != 'scripted':
        raise ValueError('--script requires --agent scripted')
    if agents[0].kind == 'scripted' and getattr(args, 'agent_arg', []):
        raise ValueError('--agent-arg is not supported with --agent scripted')
    if getattr(args, 'env', []) and (args.runtime == 'local' or agents[0].kind in {'om', 'scripted'}):
        raise ValueError('--env is only supported for non-native Docker adapters')
    if script is not None:
        script = os.path.abspath(script)
        if not os.path.isfile(script):
            raise ValueError(f'Script file does not exist: {script}')
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
    if script is not None:
        copied_script = os.path.join(run_dir, 'script.json')
        shutil.copy2(script, copied_script)
        script = copied_script
    if args.runtime == 'local':
        if args.platform or args.keep_containers:
            raise ValueError('--platform and --keep-containers require the Docker runtime')
        for agent in agents:
            if agent.kind == 'container':
                raise ValueError(f'Agent {agent.name} requires the Docker runtime')
        abi = check_local_runtime()
        local_info: dict[str, ta.Any] = {
            'landlock_abi': abi,
            'platform': platform.platform(),
            'python': sys.version,
            'python_executable': sys.executable,
        }
        if script is not None:
            with open(script, 'rb') as f:
                local_info['script_sha256'] = hashlib.sha256(f.read()).hexdigest()
        write_json(os.path.join(run_dir, 'local.json'), local_info)
        results = []
        all_expected = True
        for task in tasks:
            for agent in agents:
                for attempt in range(1, repeat + 1):
                    trial_name = f'{task.name}-{agent.name}-{attempt}'
                    print(f'Running {trial_name} ...', flush=True)
                    result = run_local_trial(
                        task,
                        agent,
                        output_dir=os.path.join(run_dir, trial_name),
                        timeout=args.timeout,
                        test_timeout=args.test_timeout,
                        extra_args=getattr(args, 'agent_arg', []),
                        extra_env=getattr(args, 'env', []),
                        script=script,
                    )
                    results.append(result)
                    with open(os.path.join(run_dir, 'results.jsonl'), 'a', encoding='utf-8') as f:
                        f.write(json.dumps(result, sort_keys=True) + '\n')
                    expected = 'failed' if args.action == 'check' and agent.kind == 'nop' else 'passed'
                    all_expected = all_expected and result['status'] == expected
                    print(f"  {result['status']} ({result['seconds']:.1f}s)", flush=True)
                    if 'error' in result:
                        print('  ' + result['error'], file=sys.stderr, flush=True)
        local_counts: dict[str, int] = {}
        for result in results:
            status = result['status']
            local_counts[status] = local_counts.get(status, 0) + 1
        write_json(os.path.join(run_dir, 'summary.json'), {'attempts': len(results), 'counts': local_counts})
        print(json.dumps(local_counts, sort_keys=True), flush=True)
        return 0 if all_expected else 1
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
                    script=script,
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


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='action', required=True)
    listing = subparsers.add_parser('list', help='List tasks without running Docker')
    listing.add_argument('--tasks')
    listing.add_argument('--task', action='append', default=[])
    check = subparsers.add_parser('check', help='Require each starter to fail and each reference fix to pass')
    add_options(check)
    run = subparsers.add_parser('run', help='Run an agent on fresh task containers')
    add_options(run)
    run.add_argument('--agent', default='nop')
    run.add_argument('--agents')
    run.add_argument('--agent-version')
    run.add_argument('--agent-arg', action='append', default=[])
    run.add_argument('--script', help='JSON turns for the scripted omllm backend')
    run.add_argument('--env', action='append', default=[], metavar='NAME')
    run.add_argument('--repeat', type=int, default=1)
    run.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    signal.signal(signal.SIGTERM, _handle_termination)
    try:
        with importlib.resources.as_file(eval_resources()) as assets:
            if args.tasks is None:
                args.tasks = os.path.join(assets, 'tasks')
            if args.action == 'list':
                for task in load_tasks(args.tasks, args.task):
                    print(f'{task.name}: {task.instruction.splitlines()[0].lstrip("# ")}')
                code = 0
            else:
                if args.action == 'run' and args.agents is None:
                    args.agents = os.path.join(assets, 'agents')
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
