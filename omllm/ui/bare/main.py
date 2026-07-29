import argparse
import asyncio
import functools
import os
import sys

from omcore import dataclasses as dc
from omdev.home.secrets import load_secrets

from ... import agent as ag
from ... import llm
from ...agent.fs.tools.ls import LsTool
from ...agent.fs.tools.read import ReadTool
from ...agent.shell.tools.bash import BashTool


##


async def _a_main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument('--fs', action='store_true')
    parser.add_argument('--bash', action='store_true')

    args = parser.parse_args()

    #

    model_key = llm.ModelKey('openai', 'gpt-5.4-mini')
    api_key_name = 'openai_api_key'
    backend_cls = llm.OpenaiCompletionsImmediateBackend

    cwd = os.path.abspath(os.path.realpath(os.getcwd()))

    #

    svc = backend_cls(
        llm.default_model_catalog()[model_key],  # noqa
        api_key=load_secrets().get(api_key_name),
    )

    async def on_event(ev: ag.Event) -> None:
        if isinstance(ev, ag.TurnEndEvent):
            print(ev.message)

    agent = ag.Agent(
        backends=ag.DictBackendManager({llm.ImmediateBackend: {None: svc}}),  # type: ignore
        sink=on_event,
    )

    tools = ag.ToolSet([
        *([
            BashTool().tool(),
        ] if args.bash else []),

        *([
            LsTool().tool(),
            ReadTool().tool(),
        ] if args.fs else []),
    ])

    await agent.modify_state(
        lambda state: dc.replace(
            state,
            context=dc.replace(
                state.context,
                system_prompt='\n\n'.join([
                    f'Current working directory: {cwd}',
                ]),
                tools=tools,
            ),
            tool_env=ag.ToolEnvironment(
                cwd=cwd,
            ),
        ),
    )

    #

    if sys.stdin.isatty():
        try:
            import readline  # noqa
        except ImportError:
            pass

    while True:
        entry = await asyncio.to_thread(functools.partial(input, '> '))

        if entry == '/quit':
            break

        print(entry)

        await agent.prompt(entry)


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
