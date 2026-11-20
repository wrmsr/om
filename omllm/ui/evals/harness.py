"""Run a single native omllm eval attempt in a fresh host process."""
import argparse
import asyncio
import contextlib
import glob
import json
import os
import signal
import sys
import typing as ta

from omcore import dataclasses as dc

from ... import agent as agn
from ... import llm
from .commands import CommandResult
from .commands import run_command
from .inject import eval_agent
from .remote import local_remote_agent
from .scripts import load_script


##


def run_harness(
        request: ta.Mapping[str, ta.Any],
        *,
        kind: str,
        timeout: float,
        extra_args: ta.Sequence[str],
        script: str | None,
) -> CommandResult:
    command = [sys.executable, '-m', f'{__package__}.harness']
    if kind == 'scripted':
        command.extend(['--model', 'scripted'])
        if script is not None:
            command.extend(['--script', script])
    else:
        command.extend(extra_args)
    return run_command(
        command,
        log_path=os.path.join(request['output_dir'], 'agent.log'),
        timeout=timeout,
        input_data=json.dumps(dict(request)).encode(),
    )


async def _run(
        request: ta.Mapping[str, ta.Any],
        *,
        model: str,
        script: llm.BackendScript | None,
        max_turns: int,
) -> None:
    workdir = request['workdir']
    prompt = request['instruction']
    async with contextlib.AsyncExitStack() as stack:
        if request['runtime'] == 'local':
            client = await stack.enter_async_context(local_remote_agent(
                workdir,
                scratch=request['scratch'],
                task_path=request['task_path'],
            ))
            container = None
            prompt += f'\nLocal runtime: paths written as /work in this task refer to {workdir}. Use relative paths.\n'
        else:
            client = None
            container = agn.DockerContainerId(request['container_id'], user=request['user'])

        agent, permissions = await stack.enter_async_context(eval_agent(
            cwd=workdir,
            model=model,
            script=script,
            container=container,
            docker=request.get('docker_executable', 'docker'),
            remote_client=client,
        ))
        permissions.update_rules(lambda rules: agn.PermissionRules([
            *rules,
            agn.PermissionRule(agn.ExecPermissionMatcher(), agn.PermissionState.ALLOW),
            agn.PermissionRule(
                agn.GlobFsPermissionMatcher(os.path.join(glob.escape(workdir), '**'), modes=['r', 'w']),
                agn.PermissionState.ALLOW,
            ),
        ]))
        await agent.update_state(lambda state: dc.replace(
            state,
            turn_config=dc.replace(state.turn_config or agn.TurnConfig(), max_turns=max_turns),
        ))

        with open(os.path.join(request['artifact_dir'], 'prompt.txt'), 'w', encoding='utf-8') as f:  # noqa: ASYNC230
            f.write(prompt)
        result = await agent.prompt(prompt)

    print(f'Agent end reason: {result.reason.name}')
    for message in result.new_messages:
        if isinstance(message, llm.AiMessage):
            for content in message.content:
                if isinstance(content, llm.TextContent):
                    print(f'AI: {content.text}')
                elif isinstance(content, llm.ToolCall):
                    print(f'Tool call: {content.name} {json.dumps(content.args)}')
        if isinstance(message, llm.ToolResultMessage):
            print(f'Tool result {message.tool_call_id}: {str(message.content)[:3000]}')
    if result.reason is not agn.AgentEndReason.COMPLETED:
        raise RuntimeError(f'Agent ended with {result.reason.name}: {result.error}')


async def _run_attempt(request: ta.Mapping[str, ta.Any], args: argparse.Namespace) -> None:
    script = load_script(args.script) if args.model == 'scripted' else None
    task = asyncio.current_task()
    if task is None:
        raise RuntimeError('The eval attempt must run in an asyncio task')
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, task.cancel)
    try:
        await _run(request, model=args.model, script=script, max_turns=args.max_turns)
    finally:
        loop.remove_signal_handler(signal.SIGTERM)


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script')
    parser.add_argument('--model', default=llm.DEFAULT_MODEL_SHORT_ID)
    parser.add_argument('--max-turns', type=int, default=16)
    args = parser.parse_args()
    if args.max_turns < 1:
        parser.error('--max-turns must be positive')
    if args.script is not None and args.model != 'scripted':
        parser.error('--script requires the scripted model')
    try:
        asyncio.run(_run_attempt(json.load(sys.stdin), args))
    except asyncio.CancelledError:
        raise SystemExit(130) from None
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    _main()
