import asyncio

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from .... import harness as har
from ....core import processes
from ....core import ui
from ...logs import configure_tui_logging
from ...types import UiId
from ..config import Config
from ..config import TargetCwd
from ..inject import AgentEventSubscribers
from ..inject import bind_tui
from ..setup import AgentInitializer
from .input import InputManager
from .input import bind_input
from .output import bind_output
from .output import display_transcript


##


async def _a_main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    config = Config.parse_from_arguments(argv)

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
        ui_id = await injector[UiId]
        configure_tui_logging(ui_id)

        agent = await injector[agn.Agent]
        session = await injector[har.Session]
        input_manager = await injector[InputManager]
        text_displayer = await injector[ui.TextDisplayer]

        cwd = (await injector[TargetCwd]).v

        proc_scope = (await injector[processes.ProcessManager]).root if config.exec else None

        for el in await injector[AgentEventSubscribers]:
            agent.subscribe(el)

        await (await injector[AgentInitializer]).initialize(tool_env=agn.ToolEnvironment(
            cwd=cwd,
            processes=proc_scope,
        ))

        if config.resume is not None:
            await display_transcript(await session.resume(), text_displayer)

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
