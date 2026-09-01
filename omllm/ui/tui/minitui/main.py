"""
Entry point for the minitui chat backend: `python -m omllm.ui.tui.minitui`.

Structural difference from `bare`: there is no blocking read loop - `AsyncDriver.run(app)` owns the terminal for the
process lifetime, and prompts run as concurrent tasks so the surface keeps rendering stream deltas (and accepting input)
while a turn is in flight. Submissions made mid-turn queue and run in order.
"""
import asyncio
import os.path

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang
from omdev.tui import minitui as mt

from .... import agent as agn
from .... import harness as har
from ....core import processes
from ....core import ui
from ..config import parse_config
from ..inject import AgentEventSubscribers
from ..inject import bind_tui
from .app import MinituiChatApp
from .app import bind_app
from .input import bind_input
from .output import bind_output


##


class DriverQuitSignal(ui.QuitSignal):
    """Stops the driver (unwinding through its terminal-restore path) instead of raising through the turn."""

    def __init__(self, *, driver: mt.AsyncioDriver) -> None:
        super().__init__()

        self._driver = driver

    async def quit(self) -> None:
        self._driver.stop()


##


class PromptPump:
    """Runs prompts one at a time as loop tasks; mid-turn submissions queue in order."""

    def __init__(
            self,
            *,
            session: har.Session,
            app: MinituiChatApp,
    ) -> None:
        super().__init__()

        self._session = session
        self._app = app

        self._queue: list[str] = []
        self._task: asyncio.Task | None = None
        self._closing = False

    def submit(self, text: str) -> None:
        if self._closing or not text.strip():
            return
        if text.startswith('/'):
            self._app.show_command_echo(text)
        else:
            self._app.show_user_message(text)
        self._queue.append(text)
        self._maybe_start()

    def _maybe_start(self) -> None:
        if self._closing or self._task is not None or not self._queue:
            return
        text = self._queue.pop(0)
        task = asyncio.get_running_loop().create_task(self._run_one(text))
        self._task = task
        # Slot bookkeeping lives in a done callback rather than in _run_one's finally: a task cancelled before its first
        # step never runs its body at all, and the pump must not wedge on it.
        task.add_done_callback(self._on_task_done)

    async def _run_one(self, text: str) -> None:
        try:
            await self._session.prompt(text)
        except Exception as e:  # noqa: BLE001
            self._app.display_text(f'error: {e!r}', 'error')

    def _on_task_done(self, task: asyncio.Task) -> None:
        if self._task is task:
            self._task = None
        self._maybe_start()

    def cancel_current(self) -> bool:
        if (task := self._task) is None or task.done():
            return False
        if not task.cancelling():
            task.cancel()
        return True

    async def aclose(self) -> None:
        self._closing = True
        self._queue.clear()
        if (task := self._task) is not None:
            if not task.cancelling():
                task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001, S110
                pass  # unwound at shutdown; errors already surfaced by _run_one


##


async def _a_main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    config = parse_config(argv)

    cwd = os.path.abspath(os.path.realpath(config.cwd or os.getcwd()))
    config = dc.replace(config, cwd=cwd)  # noqa

    #

    lst: list[inj.Elemental] = [
        inj.bind(config),

        bind_tui(config),

        bind_app(config),
        bind_input(config),
        bind_output(config),

        inj.bind(DriverQuitSignal, singleton=True),
        inj.bind(ui.QuitSignal, to_key=DriverQuitSignal),
    ]

    #

    async with inj.create_async_managed_injector(
        *lst,
        factory=inj.create_asyncio_injector,
    ) as injector:
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
                ),
            )

            for ax in config.autoexec or []:
                pump.submit(ax)

            await driver_task

        finally:
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
