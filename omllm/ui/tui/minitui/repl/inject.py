import typing as ta

from omcore import inject as inj
from omcore import lang
from omdev import minitui as mt
from omdev import repl

from ..... import agent as agn
from ..... import llm
from .....core import processes as procs
from .....core.asyncs.base import AsyncJobRunner
from ....commands.repl import BashCommand
from ....commands.repl import ChatCommand
from ....commands.repl import JsCommand
from ....commands.repl import PyCommand
from ....commands.repl import ReplModeSwitcher
from ...config import TuiConfig
from ....inject.commands import commands_binder
from ...types import TargetCwd
from ..app import MinituiChatApp
from .ptys import ProcessScopePtySpawner
from .repl import JobRunnerExecutor
from .repl import MinituiRepl
from .repl import ReplNamespaceSeeds


##


@lang.cached_function
def repl_namespace_seeds() -> inj.ItemsBinderHelper[ta.Mapping[str, ta.Any]]:
    """Mappings merged into the python repl's namespace - how any module hands the manhole its own objects."""

    return inj.items_binder_helper[ta.Mapping[str, ta.Any]](ReplNamespaceSeeds)


##


# The process scope the repl's own processes live in, under the root: the user's, and out of sight of the agent's
# process tools, which see the root's alone.
REPL_PROCESS_SCOPE_NAME = 'repl'

# The rows of the terminal a shell is given. There is no screen behind it to have a height: just what a program asking
# is told.
REPL_PTY_ROWS = 50


def _provide_session(
        injector: inj.AsyncInjector,
        agent: agn.Agent,
        harness_session: agn.Session,
        app: MinituiChatApp,
        driver: mt.AsyncioDriver,
        job_runner: AsyncJobRunner,
        seeds: ReplNamespaceSeeds,
        cwd: TargetCwd | None = None,
        root_process_scope: procs.RootProcessScope | None = None,
) -> repl.Session:
    # Not the commands manager: the switch commands need the repl, so that would be a cycle. It is a lookup away.
    namespace: dict[str, ta.Any] = {
        'injector': injector,
        'agent': agent,
        'session': harness_session,
        'app': app,
        'driver': driver,

        'agn': agn,
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

    if root_process_scope is not None:
        # Wherever the bound process manager runs things - here, or in the container the tools are in. Nothing is
        # started until the shell is first used.
        session.add(repl.DEFAULT_BASH_NAME, repl.BashInterpreter(
            ProcessScopePtySpawner(
                root_process_scope.child(REPL_PROCESS_SCOPE_NAME),
                cwd=cwd.v if cwd is not None else None,
            ),
            size=lambda: (REPL_PTY_ROWS, app.width),
        ))

    return session


def bind_repl(config: TuiConfig) -> inj.Elements:
    return inj.as_elements(
        repl_namespace_seeds().bind_items_provider(singleton=True),

        inj.bind(repl.Session, singleton=True, to_async_fn=inj.make_async_managed_provider(_provide_session)),

        inj.bind(repl.AsyncioRunner, singleton=True, to_async_fn=inj.make_async_managed_provider(repl.AsyncioRunner)),
        inj.bind(repl.Runner, to_key=repl.AsyncioRunner),

        inj.bind(MinituiRepl, singleton=True),
        inj.bind(ReplModeSwitcher, to_key=MinituiRepl),

        inj.bind(PyCommand, singleton=True),
        commands_binder().bind_item(to_key=PyCommand),

        inj.bind(JsCommand, singleton=True),
        commands_binder().bind_item(to_key=JsCommand),

        inj.bind(BashCommand, singleton=True),
        commands_binder().bind_item(to_key=BashCommand),

        inj.bind(ChatCommand, singleton=True),
        commands_binder().bind_item(to_key=ChatCommand),
    )
