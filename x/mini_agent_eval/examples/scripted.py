"""Run the in-repo omllm agent headlessly, with a scripted or configured live backend."""
import argparse
import asyncio
import glob
import json
import os
import sys
import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore.manifests.globals import GlobalManifestLoader
from omcore.manifests.loading import ManifestLoader
from omcore.secrets import all as sec
from omllm import agent as agn
from omllm import llm
from omllm.core import registry as reg
from omllm.core import ui
from omllm.ui.agent.setup import AgentSetup
from omllm.ui.config import UiConfig
from omllm.ui.inject.inject import AgentInjector
from omllm.ui.inject.inject import UiBinder


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


def prepare_source_manifests() -> None:
    roots = [
        path
        for path in sys.path
        if path and os.path.isfile(os.path.join(path, 'omllm', '.om-manifests.json'))
    ]
    if roots:
        GlobalManifestLoader.initialize(ManifestLoader.Config.merge(
            GlobalManifestLoader.default_config(),
            ManifestLoader.Config(discover_packages_fallback_scan_root_dirs=roots),
        ))


async def run_agent(
        request: ta.Mapping[str, ta.Any],
        *,
        model: str,
        script: llm.BackendScript | None,
        api_key: str | None = None,
        max_turns: int,
) -> None:
    if request.get('runtime') != 'local':
        raise ValueError('The omllm adapter requires a local runtime request')
    workdir = request.get('workdir')
    instruction = request.get('instruction')
    if not isinstance(workdir, str) or not os.path.isdir(workdir) or not isinstance(instruction, str):
        raise ValueError('The request needs a workdir and instruction')
    if max_turns < 1:
        raise ValueError('max_turns must be positive')
    if (model == 'scripted') != (script is not None):
        raise ValueError('A script is required exactly when using the scripted model')
    if script is None:
        prepare_source_manifests()

    config = UiConfig(
        model=model,
        immediate=True,
        in_memory=True,
        cwd=workdir,
        exec=True,
        fs=True,
    )
    backend = None
    if script is not None:
        scripted_model = llm.Model(key=llm.ModelKey('scripted', 'scripted'), backend='scripted')
        backend = llm.ScriptedImmediateBackend(scripted_model, script)
    else:
        if not api_key:
            raise ValueError('A live model requires one API key from the runner')
        selected = llm.default_models_by_name()[model]
        llm_model = llm.provider_model_catalog()[selected.key]
        backend_cls = reg.get_registry_cls(llm.ImmediateBackend, llm_model.backend_)
        backend = backend_cls(llm_model, api_key=sec.Secret(value=api_key))

    def rewrite_ui(els: inj.Elements) -> inj.Elements:
        return inj.as_elements(
            els,
            inj.bind(ui.NopTextDisplayer()),
            inj.bind(ui.TextDisplayer, to_key=ui.NopTextDisplayer),
            inj.bind(ui.RaiseQuitSignal(SystemExit)),
            inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),
            inj.bind(DenyingPermissionAsker()),
            inj.bind(agn.PermissionAsker, to_key=DenyingPermissionAsker),
        )

    def rewrite_agent(els: inj.Elements) -> inj.Elements:
        if backend is None:
            return els
        return inj.as_elements(inj.override(
            els,
            inj.bind(agn.BackendManager, to_const=agn.DictBackendManager.of(backend)),
        ))

    async with inj.create_asyncio_managed_injector(
            UiBinder(
                config,
                ui_rewriter=rewrite_ui,
                agent_rewriter=rewrite_agent,
            ).bind_ui(),
    ) as injector:
        agent = await injector[agn.Agent]
        await (await injector[AgentSetup]).run()
        agent_injector = (await injector[AgentInjector]).v
        permissions = await agent_injector[agn.PermissionsManager]
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
        prompt = instruction
        if script is None:
            prompt += (
                f'\nLocal runtime: paths written as /work in this task refer to {workdir}. '
                'Use relative paths here.\n'
            )
        artifact_dir = request.get('artifact_dir')
        if isinstance(artifact_dir, str):
            with open(os.path.join(artifact_dir, 'prompt.txt'), 'w', encoding='utf-8') as f:  # noqa: ASYNC230
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


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', help='JSON array of scripted turns')
    parser.add_argument('--model', default='scripted', help='omllm model alias, such as gpt')
    parser.add_argument('--max-turns', type=int, default=16)
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        api_key = None
        if args.model == 'scripted':
            request = payload
        else:
            if not isinstance(payload, dict):
                raise TypeError('Expected a live request and API key object on stdin')
            request = payload.get('request')
            api_key = payload.get('api_key')
            if not isinstance(api_key, str):
                raise TypeError('Expected one API key on stdin')
        if not isinstance(request, dict):
            raise TypeError('Expected one JSON request object on stdin')
        script = load_script(args.script) if args.model == 'scripted' else None
        asyncio.run(run_agent(request, model=args.model, script=script, api_key=api_key, max_turns=args.max_turns))
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    _main()
