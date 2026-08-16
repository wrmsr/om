import asyncio
import os.path

from omcore import dataclasses as dc
from omcore import inject as inj

from ... import agent as agn
from ... import harness as har
from ...core import ui
from .agent import AgentEventSubscribers
from .agent import bind_agent
from .backends import bind_backends
from .commands import bind_commands
from .config import parse_config
from .input import InputManager
from .input import bind_input
from .output import bind_output
from .permissions import bind_permissions
from .session import bind_sessions
from .tools import bind_tools


##


async def _a_main() -> None:
    config = parse_config()

    #

    cwd = os.path.abspath(os.path.realpath(config.cwd or os.getcwd()))
    config = dc.replace(config, cwd=cwd)  # noqa

    #

    lst: list[inj.Elemental] = [
        bind_agent(config),
        bind_backends(config),
        bind_commands(config),
        bind_input(config),
        bind_output(config),
        bind_permissions(config),
        bind_sessions(config),
        bind_tools(config),
    ]

    #

    lst.extend([
        inj.bind(ui.RaiseQuitSignal(SystemExit)),
        inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),
    ])

    #

    async with inj.create_async_managed_injector(
        *lst,
        factory=inj.create_asyncio_injector,
    ) as injector:
        agent = await injector[agn.Agent]
        tool_set = await injector[agn.ToolSet]
        session = await injector[har.Session]
        input_manager = await injector[InputManager]

        for el in await injector[AgentEventSubscribers]:
            agent.subscribe(el)

        await agent.update_state(
            lambda state: dc.replace(
                state,
                context=dc.replace(
                    state.context,
                    system_prompt='\n\n'.join([
                        f'Current working directory: {cwd}',
                    ]),
                    tools=tool_set,
                ),
                tool_env=agn.ToolEnvironment(
                    cwd=cwd,
                ),
            ),
        )

        #

        for ax in config.autoexec or []:
            await session.prompt(ax)

        while True:
            try:
                entry = await input_manager.input('> ')
            except EOFError:
                break

            await session.prompt(entry)


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
