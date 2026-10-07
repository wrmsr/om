"""
The sane default session: a python interpreter and, when the engine is built, a javascript one, under the names the
frontends' switch commands know. Hosts wanting more (seeded namespaces, shared engine contexts, several interpreters of
one language) build their own `Session` the same way.
"""
import typing as ta

from .executors import Executor
from .python.interpreter import PythonInterpreter
from .quickjs.interpreter import QuickjsInterpreter
from .quickjs.interpreter import quickjs_available
from .sessions import Session


##


DEFAULT_PYTHON_NAME = 'py'
DEFAULT_JAVASCRIPT_NAME = 'js'


def make_default_session(
        *,
        namespace: ta.Mapping[str, ta.Any] | None = None,
        allow_await: bool = True,
        javascript: bool = True,
        blocking_executor: Executor | None = None,
) -> Session:
    """
    `namespace` seeds the python interpreter; `blocking_executor` is where the javascript engine evaluates (inline when
    None - under asyncio pass an `AsyncioThreadExecutor` so the loop stays live).
    """

    session = Session()

    session.add(DEFAULT_PYTHON_NAME, PythonInterpreter(
        namespace,
        config=PythonInterpreter.Config(allow_await=allow_await),
    ))

    if javascript and quickjs_available():
        session.add(DEFAULT_JAVASCRIPT_NAME, QuickjsInterpreter(
            executor=blocking_executor,
        ))

    return session
