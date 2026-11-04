# ruff: noqa: UP006 UP007 UP045
import asyncio
import functools
import logging
import os
import signal
import threading
import time
import typing as ta

from omcore.asyncs.asyncio.streams import asyncio_open_stream_reader
from omcore.asyncs.asyncio.streams import asyncio_open_stream_writer
from omcore.lite.cached import cached_nullary
from omcore.lite.check import check
from omcore.lite.inject import Injector
from omcore.lite.marshal import ObjMarshalerManager
from omcore.lite.marshal import unmarshal_obj
from omcore.lite.pycharm import pycharm_debug_connect
from omcore.logs.modules import get_module_logger
from omcore.os.deathsig import set_process_deathsig
from omcore.os.pyremote.core import pyremote_bootstrap_finalize
from omcore.rpc.asyncios import AsyncioRpcConnections
from omcore.rpc.connection import RpcConnection
from omcore.rpc.dispatch import RpcMethodTableHandler

from ..bootstrap import MainBootstrap
from ..commands.local import LocalCommandExecutor
from .execution import _RemoteCommandHandler
from .execution import _RemoteLogHandler
from .protocol import REMOTE_EXECUTION_BOOTSTRAP_METHOD


if ta.TYPE_CHECKING:
    from ..bootstrap_ import main_bootstrap
else:
    main_bootstrap: ta.Any = None


log = get_module_logger(globals())  # noqa


##


class _RemoteExecutionMain:
    """
    The remote end of a manage connection. It serves `manage.bootstrap` first; once that has built the injector, the
    command handler's `manage.execute` is added to the connection's method table.
    """

    def __init__(self) -> None:
        super().__init__()

        self._handler = RpcMethodTableHandler({
            REMOTE_EXECUTION_BOOTSTRAP_METHOD: self._rpc_bootstrap,
        })

        self.__connection: ta.Optional[RpcConnection] = None
        self.__bootstrap: ta.Optional[MainBootstrap] = None
        self.__injector: ta.Optional[Injector] = None

    @property
    def handler(self) -> RpcMethodTableHandler:
        return self._handler

    def set_connection(self, connection: RpcConnection) -> None:
        check.none(self.__connection)
        self.__connection = connection

    @property
    def _connection(self) -> RpcConnection:
        return check.not_none(self.__connection)

    @property
    def _bootstrap(self) -> MainBootstrap:
        return check.not_none(self.__bootstrap)

    @property
    def _injector(self) -> Injector:
        return check.not_none(self.__injector)

    #

    def _timebomb_main(
            self,
            delay_s: float,
            *,
            sig: int = signal.SIGINT,
            code: int = 1,
    ) -> None:
        time.sleep(delay_s)

        if (pgid := os.getpgid(0)) == os.getpid():
            os.killpg(pgid, sig)

        os._exit(code)  # noqa

    @cached_nullary
    def _timebomb_thread(self) -> ta.Optional[threading.Thread]:
        if (tbd := self._bootstrap.remote_config.timebomb_delay_s) is None:
            return None

        thr = threading.Thread(
            target=functools.partial(self._timebomb_main, tbd),
            name=f'{self.__class__.__name__}.timebomb',
            daemon=True,
        )

        thr.start()

        log.debug('Started timebomb thread: %r', thr)

        return thr

    #

    @cached_nullary
    def _log_handler(self) -> _RemoteLogHandler:
        return _RemoteLogHandler(self._connection, asyncio.get_running_loop())

    #

    async def _rpc_bootstrap(self, params: ta.Any) -> None:
        check.none(self.__bootstrap, 'already bootstrapped')

        # Unmarshaled with the default marshaler: the configured one comes from the injector this builds.
        self.__bootstrap = unmarshal_obj(params, MainBootstrap)

        if (prd := self._bootstrap.remote_config.pycharm_remote_debug) is not None:
            pycharm_debug_connect(prd)

        self.__injector = main_bootstrap(self._bootstrap)

        # Post-bootstrap

        if self._bootstrap.remote_config.set_pgid:
            if os.getpgid(0) != os.getpid():
                log.debug('Setting pgid')
                os.setpgid(0, 0)

        if (ds := self._bootstrap.remote_config.deathsig) is not None:
            log.debug('Setting deathsig: %s', ds)
            set_process_deathsig(int(signal.Signals[f'SIG{ds.upper()}']))

        self._timebomb_thread()

        if self._bootstrap.remote_config.forward_logging:
            log.debug('Installing log forwarder')
            logging.root.addHandler(self._log_handler())

        self._handler.add_methods(_RemoteCommandHandler(
            self._injector[LocalCommandExecutor],
            self._injector[ObjMarshalerManager],
        ).method_table())


def _remote_execution_main() -> None:
    rt = pyremote_bootstrap_finalize()  # noqa

    async def inner() -> None:
        input = await asyncio_open_stream_reader(rt.input)  # noqa
        output = await asyncio_open_stream_writer(rt.output)

        main = _RemoteExecutionMain()
        connection = AsyncioRpcConnections.of_streams(input, output, handler=main.handler)
        main.set_connection(connection)

        await connection.start()
        try:
            await connection.serve()
        finally:
            await connection.close()

    asyncio.run(inner())
