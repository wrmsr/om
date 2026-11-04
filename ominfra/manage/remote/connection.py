# ruff: noqa: UP006 UP007 UP043 UP045
import asyncio
import contextlib
import socket
import typing as ta

from omcore.lite.cached import cached_nullary
from omcore.lite.marshal import ObjMarshalerManager
from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import PyremoteBootstrapOptions
from omcore.os.pyremote.core import pyremote_build_bootstrap_source
from omcore.rpc.asyncios import AsyncioRpcConnections
from omcore.rpc.connection import RpcConnection
from omcore.rpc.dispatch import RpcMethodTableHandler

from ..bootstrap import MainBootstrap
from ..commands.local import LocalCommandExecutor
from ._main import _remote_execution_main  # noqa
from .execution import RemoteCommandExecutor
from .execution import _RemoteCommandHandler
from .payload import RemoteExecutionPayloadFile
from .payload import get_remote_payload_src
from .protocol import REMOTE_EXECUTION_BOOTSTRAP_METHOD
from .protocol import REMOTE_EXECUTION_LOG_METHOD
from .spawning import RemoteSpawning


##


def _remote_execution_host_handler() -> RpcMethodTableHandler:
    """The host only ever receives the remote's forwarded log records, applied inline in the order sent."""

    return RpcMethodTableHandler(inline_notifications={
        REMOTE_EXECUTION_LOG_METHOD: RemoteCommandExecutor.handle_log_notification,
    })


##


class PyremoteRemoteExecutionConnector:
    def __init__(
            self,
            *,
            spawning: RemoteSpawning,
            msh: ObjMarshalerManager,
            payload_file: ta.Optional[RemoteExecutionPayloadFile] = None,
    ) -> None:
        super().__init__()

        self._spawning = spawning
        self._msh = msh
        self._payload_file = payload_file

    #

    @cached_nullary
    def _payload_src(self) -> str:
        return get_remote_payload_src(file=self._payload_file)

    @cached_nullary
    def _remote_src(self) -> ta.Sequence[str]:
        return [
            self._payload_src(),
            '_remote_execution_main()',
        ]

    @cached_nullary
    def _spawn_src(self) -> str:
        return pyremote_build_bootstrap_source(__package__ or 'manage')

    #

    @contextlib.asynccontextmanager
    async def connect(
            self,
            tgt: RemoteSpawning.Target,
            bs: MainBootstrap,
    ) -> ta.AsyncGenerator[RemoteCommandExecutor, None]:
        spawn_src = self._spawn_src()
        remote_src = self._remote_src()

        async with self._spawning.spawn(
                tgt,
                spawn_src,
                debug=bs.main_config.debug,
        ) as proc:
            res = await PyremoteBootstrapDriver(  # noqa
                remote_src,
                PyremoteBootstrapOptions(
                    debug=bs.main_config.debug,
                ),
            ).async_run(
                proc.stdout,
                proc.stdin,
            )

            connection = AsyncioRpcConnections.of_streams(
                proc.stdout,
                proc.stdin,
                handler=_remote_execution_host_handler(),
            )

            async with connection:
                await connection.request(
                    REMOTE_EXECUTION_BOOTSTRAP_METHOD,
                    self._msh.marshal_obj(bs, MainBootstrap),
                )

                yield RemoteCommandExecutor(connection, self._msh)


##


class InProcessRemoteExecutionConnector:
    def __init__(
            self,
            *,
            msh: ObjMarshalerManager,
            local_executor: LocalCommandExecutor,
    ) -> None:
        super().__init__()

        self._msh = msh
        self._local_executor = local_executor

    @contextlib.asynccontextmanager
    async def connect(self) -> ta.AsyncGenerator[RemoteCommandExecutor, None]:
        """Both ends in this process, over a socketpair: the whole protocol, short of spawning anything."""

        local_sock, remote_sock = socket.socketpair()
        local_reader, local_writer = await asyncio.open_connection(sock=local_sock)
        remote_reader, remote_writer = await asyncio.open_connection(sock=remote_sock)

        remote: RpcConnection = AsyncioRpcConnections.of_streams(
            remote_reader,
            remote_writer,
            handler=RpcMethodTableHandler(_RemoteCommandHandler(
                self._local_executor,
                self._msh,
            ).method_table()),
        )
        local: RpcConnection = AsyncioRpcConnections.of_streams(
            local_reader,
            local_writer,
            handler=_remote_execution_host_handler(),
        )

        async with remote, local:
            yield RemoteCommandExecutor(local, self._msh)
