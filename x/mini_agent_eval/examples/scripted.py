"""Run the in-repo omllm agent with explicit, offline scripted model turns."""
import argparse
import asyncio
import glob
import json
import os
import sys
import typing as ta

from omcore import inject as inj
from omllm import agent as agn
from omllm import llm
from omllm.core import ui
from omllm.ui.agent.setup import AgentSetup
from omllm.ui.config import UiConfig
from omllm.ui.inject.inject import bind_ui


##


class DenyingPermissionAsker(agn.PermissionAsker):
    async def ask(
            self,
            request: agn.PermissionRequest,
            rule: agn.PermissionRule,
    ) -> agn.DecidedPermissionState:
        return agn.PermissionState.DENY


def load_script(path: str | None) -> llm.BackendScript:
    if path is None:
        return llm.BackendScript([
            llm.BackendScriptTurn(llm.AiMessage([
                llm.ToolCall('inspect', 'bash', {'command': 'pwd'}),
            ], stop_reason='tool_use')),
            llm.BackendScriptTurn(llm.AiMessage([
                llm.TextContent('Offline scripted smoke test complete.'),
            ], stop_reason='stop')),
        ])

    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    if not isinstance(raw, list) or not raw:
        raise ValueError('Script must be a nonempty JSON array of turns')
    turns = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) - {'text', 'tool_calls'}:
            raise ValueError(f'Invalid script turn {index}')
        if ('text' in item) == ('tool_calls' in item):
            raise ValueError(f'Script turn {index} needs text or tool_calls')
        if 'text' in item:
            if not isinstance(item['text'], str):
                raise ValueError(f'Script turn {index} text must be a string')
            message = llm.AiMessage([llm.TextContent(item['text'])], stop_reason='stop')
        else:
            calls = item['tool_calls']
            if not isinstance(calls, list) or not calls:
                raise ValueError(f'Script turn {index} tool_calls must be a nonempty array')
            content = []
            for call_index, call in enumerate(calls):
                if not isinstance(call, dict) or set(call) != {'name', 'args'}:
                    raise TypeError(f'Invalid tool call in script turn {index}')
                if not isinstance(call['name'], str) or not isinstance(call['args'], dict):
                    raise TypeError(f'Invalid tool call in script turn {index}')
                content.append(llm.ToolCall(f'script-{index}-{call_index}', call['name'], call['args']))
            message = llm.AiMessage(content, stop_reason='tool_use')
        turns.append(llm.BackendScriptTurn(message))
    return llm.BackendScript(turns)


async def run_scripted(request: ta.Mapping[str, ta.Any], script: llm.BackendScript) -> None:
    if request.get('runtime') != 'local':
        raise ValueError('The scripted adapter requires a local runtime request')
    workdir = request.get('workdir')
    instruction = request.get('instruction')
    if not isinstance(workdir, str) or not os.path.isdir(workdir) or not isinstance(instruction, str):
        raise ValueError('The request needs a workdir and instruction')

    config = UiConfig(
        model='scripted',
        immediate=True,
        in_memory=True,
        cwd=workdir,
        exec=True,
        fs=True,
    )
    model = llm.Model(key=llm.ModelKey('scripted', 'scripted'), backend='scripted')
    backend = llm.ScriptedImmediateBackend(model, script)

    async with inj.create_asyncio_managed_injector(
            inj.override(
                bind_ui(config),
                inj.bind(agn.BackendManager, to_const=agn.DictBackendManager.of(backend)),
            ),
            inj.bind(ui.NopTextDisplayer()),
            inj.bind(ui.TextDisplayer, to_key=ui.NopTextDisplayer),
            inj.bind(ui.RaiseQuitSignal(SystemExit)),
            inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),
            inj.bind(DenyingPermissionAsker()),
            inj.bind(agn.PermissionAsker, to_key=DenyingPermissionAsker),
    ) as injector:
        agent = await injector[agn.Agent]
        await (await injector[AgentSetup]).run()
        permissions = await injector[agn.PermissionsManager]
        permissions.update_rules(lambda rules: agn.PermissionRules([
            *rules,
            agn.PermissionRule(agn.ExecPermissionMatcher(), agn.PermissionState.ALLOW),
            agn.PermissionRule(
                agn.GlobFsPermissionMatcher(os.path.join(glob.escape(workdir), '**'), modes=['r', 'w']),
                agn.PermissionState.ALLOW,
            ),
        ]))
        result = await agent.prompt(instruction)
        print(f'Agent end reason: {result.reason.name}')
        for message in result.new_messages:
            if isinstance(message, llm.ToolResultMessage):
                print(f'Tool result {message.tool_call_id}: {message.content}')
        if result.reason is not agn.AgentEndReason.COMPLETED:
            raise RuntimeError(f'Agent ended with {result.reason.name}: {result.error}')


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', help='JSON array of scripted turns')
    args = parser.parse_args()
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise TypeError('Expected one JSON request object on stdin')
        asyncio.run(run_scripted(request, load_script(args.script)))
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    _main()
