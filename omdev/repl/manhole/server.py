"""
The manhole proper: a python shell inside the running process, as a connection handler any `ManholeServer` can run.
Python only, on purpose - the point is to be *in* the process, poking at its objects, and the process is python; a
language that cannot touch them has no business here.

Each connection gets a `PythonInterpreter` of its own. Its namespace starts with the host's seed - the objects shared,
the dict per connection - laid over the standard seed (`sys`, `os`, `gc`, `threading`), under the module name
`__manhole__`. Its `print` falls back to the connection once its code is called from elsewhere in the process, so a
callback defined at the manhole still reports to whoever wrote it.

Hosting is separate: a dedicated thread with its own loop (`asyncio.AsyncioThreadManhole`, the default behind
`start_manhole`), the host's own loop (`asyncio.AsyncioManholeServer`), or the calling thread, blocking, with no loop at
all (`sync.serve_inline`).

There is no authentication: a unix socket is guarded by its file mode, and tcp binds loopback unless told otherwise.
Whoever can connect has the process.
"""
import gc
import os
import sys
import threading
import typing as ta

from omcore.logs import all as logs

from ..dispatch import Dispatcher
from ..python.interpreter import PythonInterpreter
from ..sessions import Session
from .base import Connection
from .protocol import ManholeProtocol


InterpreterFactory: ta.TypeAlias = ta.Callable[[], PythonInterpreter]


log = logs.get_module_logger(globals())


##


STANDARD_SEED: ta.Mapping[str, ta.Any] = {
    'sys': sys,
    'os': os,
    'gc': gc,
    'threading': threading,
}

MANHOLE_MODULE_NAME = '__manhole__'


def default_banner() -> str:
    return f'manhole: python {sys.version.split()[0]} pid {os.getpid()} - /help for commands, /quit to leave'


class Manhole:
    def __init__(
            self,
            *,
            seed: ta.Mapping[str, ta.Any] | None = None,
            interpreter_factory: InterpreterFactory | None = None,
            banner: str | None = None,
            dispatcher: Dispatcher | None = None,
            allow_await: bool = True,
    ) -> None:
        """
        `seed` lays over the standard seed as every connection's starting namespace. `interpreter_factory` replaces
        the interpreter's construction altogether (`seed` and `allow_await` then go unused). `banner` None is the
        default banner, '' none. `dispatcher` says where the code runs; `allow_await` must be off for the loop-less
        hostings, where an await has nowhere to run.
        """

        super().__init__()

        self._seed: dict[str, ta.Any] = {**STANDARD_SEED, **(seed or {})}
        self._interpreter_factory = interpreter_factory
        self._banner = default_banner() if banner is None else banner
        self._dispatcher = dispatcher
        self._allow_await = allow_await

    @property
    def seed(self) -> ta.Mapping[str, ta.Any]:
        return self._seed

    @property
    def banner(self) -> str:
        return self._banner

    @property
    def allow_await(self) -> bool:
        return self._allow_await

    @property
    def has_interpreter_factory(self) -> bool:
        return self._interpreter_factory is not None

    def make_interpreter(self) -> PythonInterpreter:
        if (factory := self._interpreter_factory) is not None:
            return factory()
        return PythonInterpreter(
            dict(self._seed),
            config=PythonInterpreter.Config(
                module_name=MANHOLE_MODULE_NAME,
                allow_await=self._allow_await,
            ),
        )

    async def handle(self, connection: Connection) -> None:
        """One connection's whole life, banner to goodbye. Closing the connection is the server's job."""

        log.info('Manhole connection from %s', connection.peer)

        interpreter = self.make_interpreter()
        session = Session({'python': interpreter})
        protocol = ManholeProtocol(
            session,
            connection,
            banner=self._banner,
            dispatcher=self._dispatcher,
        )

        # What this connection's code prints when called back later, from anywhere in the process, comes here too.
        interpreter.set_default_sink(protocol.sink)
        try:
            await protocol.run()
        finally:
            interpreter.set_default_sink(None)
            await session.aclose()
            log.info('Manhole connection from %s finished', connection.peer)
