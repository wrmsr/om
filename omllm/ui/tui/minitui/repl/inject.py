import typing as ta

from omcore import inject as inj
from omcore import lang
from omdev import minitui as mt
from omdev import repl

from ..... import agent as agn
from ..... import harness as har
from ..... import llm
from .....core import processes as procs
from .....core.asyncs.base import AsyncJobRunner
from ...config import Config
from ...inject import harness_commands
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
        harness_session: har.Session,
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

        inj.bind(har.BashCommand, singleton=True),
        harness_commands().bind_item(to_key=har.BashCommand),

        inj.bind(har.ChatCommand, singleton=True),
        harness_commands().bind_item(to_key=har.ChatCommand),
    )
