import asyncio
import os.path

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from .... import harness as har
from ....core import processes
from ....core import ui
from ..agent import AgentEventSubscribers
from ..config import parse_config
from ..inject import bind_tui
from .input import InputManager
from .input import bind_input
from .output import bind_output


##


async def _a_main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    config = parse_config(argv)

    #

    cwd = os.path.abspath(os.path.realpath(config.cwd or os.getcwd()))
    config = dc.replace(config, cwd=cwd)  # noqa

    #

    lst: list[inj.Elemental] = [
        bind_tui(config),

        bind_input(config),
        bind_output(config),
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

        proc_scope = (await injector[processes.ProcessManager]).root if config.exec else None

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
                    processes=proc_scope,
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


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    asyncio.run(_a_main(argv))


if __name__ == '__main__':
    _main()
