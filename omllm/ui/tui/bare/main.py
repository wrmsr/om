import asyncio

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from .... import harness as har
from ....core import ui
from ...logs import configure_tui_logging
from ...types import UiId
from ..config import Config
from ..inject import AgentEventSubscribers
from ..inject import bind_tui
from ..setup import AgentSetup
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
        commands = await injector[har.CommandsManager]

        for el in await injector[AgentEventSubscribers]:
            agent.subscribe(el)

        await (await injector[AgentSetup]).run()

        if config.resume is not None:
            await display_transcript(await session.resume(), text_displayer)

        #

        async def prompt(input: str) -> None:  # noqa
            if not input:
                return

            if input[0] == '/':
                try:
                    await (await commands.parse(input[1:])).run()
                except har.ParseCommandError as e:
                    if e.message is not None:
                        await text_displayer.display_text(e.message)
                return

            await agent.prompt(input)

        for ax in config.autoexec or []:
            await prompt(ax)

        while True:
            try:
                entry = await input_manager.input('> ')
            except EOFError:
                break

            await prompt(entry)


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    asyncio.run(_a_main(argv))


if __name__ == '__main__':
    _main()
