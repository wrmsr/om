"""
The repl as an input mode of the chat app: `omdev.repl`'s minitui console, lent the app's own input box and committing
into its scrollback. The python interpreter is a manhole into the harness - the root injector, the agent, the session,
the app - with more seeded through `ReplNamespaceSeeds`; the javascript one evaluates through the harness's job runner.
`/py`, `/js`, and `/chat` switch; a slash command typed while in a repl still goes to the pump, so `/chat` always works.
"""
import typing as ta

from omdev import minitui as mt
from omdev import repl

from ..... import harness as har
from .....core.asyncs.base import AsyncJob
from .....core.asyncs.base import AsyncJobRunner
from ..app import InputMode
from ..app import MinituiChatApp


ReplNamespaceSeeds = ta.NewType('ReplNamespaceSeeds', ta.Sequence[ta.Mapping[str, ta.Any]])


##


class JobRunnerExecutor(repl.Executor):
    """The repl's blocking-work seam over the harness's job runner: its threads, its interruption, its close."""

    class _Job(AsyncJob[ta.Any]):
        def __init__(self, fn: ta.Callable[[], ta.Any], interrupt: ta.Callable[[], None] | None) -> None:
            super().__init__()

            self._fn = fn
            self._interrupt = interrupt

        def run(self) -> ta.Any:
            return self._fn()

        def interrupt(self) -> None:
            if (fn := self._interrupt) is not None:
                fn()

    def __init__(self, *, job_runner: AsyncJobRunner) -> None:
        super().__init__()

        self._job_runner = job_runner

    def run(
            self,
            fn: ta.Callable[[], ta.Any],
            *,
            interrupt: ta.Callable[[], None] | None = None,
    ) -> ta.Awaitable[ta.Any]:
        return self._job_runner.run(self._Job(fn, interrupt))


##


class _ReplInputMode(InputMode):
    def __init__(self, owner: MinituiRepl) -> None:
        super().__init__()

        self._owner = owner

    @property
    def label(self) -> str:
        return self._owner.console.language.display_name

    def submit(self, text: str) -> None:
        if text.startswith('/') and '\n' not in text:
            # Slash commands keep working from inside a repl - that is how one gets back out.
            self._owner.app.chat_mode.submit(text)
        else:
            self._owner.console.submit(text)

    def suggestions(self, text: str) -> ta.Sequence[mt.SuggestionItem]:
        return self._owner.app.chat_mode.suggestions(text)

    def activate(self) -> None:
        self._owner.console.activate()

    def deactivate(self) -> None:
        self._owner.console.deactivate()


class MinituiRepl(har.ReplModeSwitcher):
    def __init__(
            self,
            *,
            app: MinituiChatApp,
            driver: mt.AsyncioDriver,
            session: repl.Session,
            runner: repl.Runner,
    ) -> None:
        super().__init__()

        self._app = app
        self._session = session

        self._console = repl.minitui.Console(
            session,
            app.input_area,
            runner=runner,
            commit=app.commit_rows,
            width=lambda: app.width,
            on_exit=self.leave,
            on_change=driver.invalidate,
        )
        self._mode = _ReplInputMode(self)

    @property
    def app(self) -> MinituiChatApp:
        return self._app

    @property
    def console(self) -> repl.minitui.Console:
        return self._console

    @property
    def names(self) -> ta.Sequence[str]:
        return self._session.names

    async def switch(self, name: str | None) -> None:
        if name is None:
            self.leave()
            return

        try:
            self._session.switch(name)
        except repl.NoSuchInterpreterError:
            have = ', '.join(self._session.names) or 'none'
            raise har.ReplSwitchError(f'No such repl: {name} (have: {have})') from None

        self._app.set_input_mode(self._mode)

    def leave(self) -> None:
        self._app.set_input_mode(self._app.chat_mode)
