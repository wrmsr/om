"""
The repl as an input mode of the chat app: `omdev.repl`'s minitui console, lent the app's own input box and committing
into its scrollback. The python interpreter is a manhole into the harness - the root injector, the agent, the session,
the app - with more seeded through `ReplNamespaceSeeds`; the javascript one evaluates through the harness's job runner.
`/py`, `/js`, and `/chat` switch; a slash command typed while in a repl still goes to the pump, so `/chat` always works.
"""
import typing as ta

from omcore import inject as inj
from omcore import lang
from omdev import minitui as mt
from omdev import repl

from .... import agent as agn
from .... import harness as har
from .... import llm
from ....core.asyncs.base import AsyncJob
from ....core.asyncs.base import AsyncJobRunner
from ..config import Config
from ..inject import harness_commands
from .app import InputMode
from .app import MinituiChatApp


ReplNamespaceSeeds = ta.NewType('ReplNamespaceSeeds', ta.Sequence[ta.Mapping[str, ta.Any]])


##


@lang.cached_function
def repl_namespace_seeds() -> inj.ItemsBinderHelper[ta.Mapping[str, ta.Any]]:
    """Mappings merged into the python repl's namespace - how any module hands the manhole its own objects."""

    return inj.items_binder_helper[ta.Mapping[str, ta.Any]](ReplNamespaceSeeds)


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


##


def _provide_session(
        injector: inj.AsyncInjector,
        agent: agn.Agent,
        harness_session: har.Session,
        app: MinituiChatApp,
        driver: mt.AsyncioDriver,
        job_runner: AsyncJobRunner,
        seeds: ReplNamespaceSeeds,
) -> repl.Session:
    # Not the commands manager: the switch commands need the repl, so that would be a cycle. It is a lookup away.
    namespace: dict[str, ta.Any] = {
        'injector': injector,
        'agent': agent,
        'session': harness_session,
        'app': app,
        'driver': driver,

        'agn': agn,
        'har': har,
        'llm': llm,
        'mt': mt,
    }
    for seed in seeds:
        namespace.update(seed)

    session = repl.Session()

    session.add(repl.DEFAULT_PYTHON_NAME, repl.PythonInterpreter(namespace))

    if repl.quickjs_available():
        session.add(repl.DEFAULT_JAVASCRIPT_NAME, repl.QuickjsInterpreter(
            executor=JobRunnerExecutor(job_runner=job_runner),
        ))

    return session


def bind_repl(config: Config) -> inj.Elements:
    return inj.as_elements(
        repl_namespace_seeds().bind_items_provider(singleton=True),

        inj.bind(repl.Session, singleton=True, to_async_fn=inj.make_async_managed_provider(_provide_session)),

        inj.bind(repl.AsyncioRunner, singleton=True, to_async_fn=inj.make_async_managed_provider(repl.AsyncioRunner)),
        inj.bind(repl.Runner, to_key=repl.AsyncioRunner),

        inj.bind(MinituiRepl, singleton=True),
        inj.bind(har.ReplModeSwitcher, to_key=MinituiRepl),

        inj.bind(har.PyCommand, singleton=True),
        harness_commands().bind_item(to_key=har.PyCommand),

        inj.bind(har.JsCommand, singleton=True),
        harness_commands().bind_item(to_key=har.JsCommand),

        inj.bind(har.ChatCommand, singleton=True),
        harness_commands().bind_item(to_key=har.ChatCommand),
    )
