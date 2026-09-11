"""
Entry point for the minitui chat backend: `python -m omllm.ui.tui.minitui`.

Structural difference from `bare`: there is no blocking read loop - `AsyncDriver.run(app)` owns the terminal for the
process lifetime, and prompts run as concurrent tasks so the surface keeps rendering stream deltas (and accepting input)
while a turn is in flight. Submissions made mid-turn queue and run in order. Quitting (ctrl+d, `:q`, `/quit`, and the
end of input) drains the pump before the driver stops, so an interrupted turn's cards and marker land in scrollback
rather than being dropped.
"""
import asyncio
import os.path

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang
from omcore.logs import all as logs
from omdev import minitui as mt

from .... import agent as agn
from .... import harness as har
from ....core import processes
from ...types import UiId
from ..config import Config
from ..inject import AgentEventSubscribers
from ..logs import configure_tui_logging
from .app import MinituiChatApp
from .inject import bind_minitui
from .promptpump import PromptPump


##


class Shutdown:
    """
    The quit sequence: drain the pump first - cancelling any in-flight turn while the driver is still bound, so the
    abort's cards and marker reach scrollback - then stop the driver. Runs as its own task because `/quit` arrives from
    inside the pump's own task, which cannot await its own teardown.
    """

    def __init__(
            self,
            *,
            pump: PromptPump,
            driver: mt.AsyncioDriver,
    ) -> None:
        super().__init__()

        self._pump = pump
        self._driver = driver

        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        try:
            await self._pump.aclose()
        finally:
            self._driver.stop()

    def request(self) -> None:
        if self._task is None:
            self._task = asyncio.get_running_loop().create_task(self._run())


##


def _parse_config(argv: lang.SequenceNotStr[str] | None = None) -> Config:
    import argparse

    parser = argparse.ArgumentParser()

    # Shoutouts to https://github.com/hyprwm/Hyprland/issues/3728
    parser.add_argument('--i-am-very-stupid', action='store_true')

    config, args = Config.parse_from_arguments_(argv, parser=parser)

    cwd = os.path.abspath(os.path.realpath(config.cwd or os.getcwd()))
    config = dc.replace(config, cwd=cwd)  # noqa

    if args.i_am_very_stupid:
        config = dc.replace(
            config,

            eval=True,
            exec=True,
            fs=True,

            autoexec=[
                *(config.autoexec or []),
                '/permissions clear',
                '/permissions add allow exec {}',
                f'/permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r","w"]}}\'',
                '/echo "YOU ARE VERY STUPID"',
            ],
        )

    return config


log = logs.get_module_logger(globals())


async def _a_main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    config = _parse_config(argv)

    cwd = check.non_empty_str(config.cwd)

    #

    async with inj.create_async_managed_injector(
        bind_minitui(config),
        factory=inj.create_asyncio_injector,
    ) as injector:
        ui_id = await injector[UiId]
        configure_tui_logging(ui_id)

        agent = await injector[agn.Agent]
        tool_set = await injector[agn.ToolSet]
        session = await injector[har.Session]
        commands_manager = await injector[har.CommandsManager]
        driver = await injector[mt.AsyncioDriver]
        app = await injector[MinituiChatApp]

        proc_scope = (await injector[processes.ProcessManager]).root if config.exec else None

        #

        app.set_commands([
            (f'/{name}', cmd.description or '')
            for name, cmd in sorted(commands_manager.get_commands().items())
        ])

        pump = PromptPump(session=session, app=app)
        app.on_submit = pump.submit
        app.on_cancel = pump.cancel_current

        shutdown = Shutdown(pump=pump, driver=driver)
        app.on_quit = shutdown.request

        # The driver starts before any agent activity: its run prologue prepares the surface, and everything the setup
        # below causes to display (e.g. verbose-mode StateUpdateEvents) buffers until then.
        driver_task = asyncio.get_running_loop().create_task(driver.run(app))
        await asyncio.sleep(0)

        try:
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
                    turn_config=agn.TurnConfig(
                        llm_retry=agn.LlmRetryConfig(),
                    ),
                ),
            )

            for ax in config.autoexec or []:
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
