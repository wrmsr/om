import asyncio

from omcore import check
from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from ....core import ui
from ...logs import configure_tui_logging
from ...types import UiId
from ..config import Config
from ..inject import AgentEventSubscribers
from ..setup import AgentSetup
from ..types import TargetCwd
from ..yolo import yolo_autoexec
from ..yolo import yolo_process_config
from .inject import bind_bare
from .input import InputManager
from .output import display_transcript
from .prompting import Prompter


##


async def _a_main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    config = Config.parse_from_arguments(argv)
    config = yolo_process_config(config)

    #

    async with inj.create_async_managed_injector(
        bind_bare(config),
        factory=inj.create_asyncio_injector,
    ) as injector:
        ui_id = await injector[UiId]
        configure_tui_logging(ui_id)

        agent = await injector[agn.Agent]
        session = await injector[agn.Session]
        input_manager = await injector[InputManager]
        text_displayer = await injector[ui.TextDisplayer]
        prompter = await injector[Prompter]

        cwd = check.non_empty_str((await injector[TargetCwd]).v)

        #

        for el in await injector[AgentEventSubscribers]:
            agent.subscribe(el)

        await (await injector[AgentSetup]).run()

        if config.resume is not None:
            await display_transcript(await session.resume(), text_displayer)

        #

        for ax in [
            *yolo_autoexec(config, cwd),
            *(config.autoexec or []),
        ]:
            await prompter.prompt(ax, echo=True)

        while True:
            try:
                entry = await input_manager.input('> ')
            except EOFError:
                break

            await prompter.prompt(entry)


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    asyncio.run(_a_main(argv))


if __name__ == '__main__':
    _main()
