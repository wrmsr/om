"""
Entry point for the minitui chat backend: `python -m omllm.ui.tui.minitui`.

Structural difference from `bare`: there is no blocking read loop - `AsyncDriver.run(app)` owns the terminal for the
process lifetime, and prompts run as concurrent tasks so the surface keeps rendering stream deltas (and accepting input)
while a turn is in flight. Submissions made mid-turn queue and run in order. Quitting (ctrl+d, `:q`, `/quit`, and the
end of input) drains the pump before the driver stops, so an interrupted turn's cards and marker land in scrollback
rather than being dropped.
"""
import asyncio

from omcore import check
from omcore import inject as inj
from omcore import lang
from omcore.logs import all as logs
from omdev import minitui as mt

from .... import agent as agn
from .... import harness as har
from ...logs import configure_tui_logging
from ...types import UiId
from ..config import Config
from ..inject import AgentEventSubscribers
from ..setup import AgentSetup
from ..types import TargetCwd
from ..yolo import yolo_autoexec
from ..yolo import yolo_process_config
from .app import MinituiChatApp
from .inject import bind_minitui
from .output import AgentEventRenderer
from .promptpump import PromptPump
from .shutdown import Shutdown


##


log = logs.get_module_logger(globals())


async def _a_main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    config = Config.parse_from_arguments(argv)
    config = yolo_process_config(config)

    #

    async with inj.create_async_managed_injector(
        bind_minitui(config),
        factory=inj.create_asyncio_injector,
    ) as injector:
        ui_id = await injector[UiId]
        configure_tui_logging(ui_id)

        agent = await injector[agn.Agent]
        session = await injector[har.Session]
        commands_manager = await injector[har.CommandsManager]
        driver = await injector[mt.AsyncioDriver]
        app = await injector[MinituiChatApp]
        event_renderer = await injector[AgentEventRenderer]

        cwd = check.non_empty_str((await injector[TargetCwd]).v)

        #

        app.set_commands([
            (f'/{name}', cmd.description or '')
            for name, cmd in sorted(commands_manager.get_commands().items())
        ])

        pump = await injector[PromptPump]
        app.on_submit = pump.submit
        app.on_cancel = pump.cancel_current

        shutdown = await injector[Shutdown]
        app.on_quit = shutdown.request

        #

        # The driver starts before any agent activity: its run prologue prepares the surface, and everything the setup
        # below causes to display (e.g. verbose-mode StateUpdateEvents) buffers until then.
        driver_task = asyncio.get_running_loop().create_task(driver.run(app))
        await asyncio.sleep(0)

        try:
            for el in await injector[AgentEventSubscribers]:
                agent.subscribe(el)

            await (await injector[AgentSetup]).run()

            if config.resume is not None:
                event_renderer.display_transcript(await session.resume())

            for ax in [
                    *(yolo_autoexec(cwd) if config.yolo else []),
                    *(config.autoexec or []),
            ]:
                pump.submit(ax)

            await driver_task

        finally:
            # Fallback for the paths that bypass the quit funnel - errors, in practice - in which the pump may still
            # hold a turn.
            if not driver_task.done():
                driver.stop()
                await driver_task
            await pump.aclose()


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    try:
        asyncio.run(_a_main(argv))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    _main()
