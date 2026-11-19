# ruff: noqa: UP006 UP007 UP045
import asyncio
import dataclasses as dc
import logging
import typing as ta

from omcore.lite.check import check
from omcore.lite.marshal import ObjMarshalerManager
from omcore.logs.modules import get_module_logger
from omcore.logs.protocols import LoggerLike
from omcore.rpc.connection import RpcConnection
from omcore.rpc.dispatch import RpcMethodFn
from omcore.rpc.serde import LiteMarshalRpcSerde
from omcore.rpc.serde import RpcTypedCaller
from omcore.rpc.serde import rpc_typed_method

from ..commands.base import Command
from ..commands.base import CommandException
from ..commands.base import CommandExecutor
from ..commands.base import CommandOutputOrException
from ..commands.base import CommandOutputOrExceptionData
from .protocol import REMOTE_EXECUTION_EXECUTE_METHOD
from .protocol import REMOTE_EXECUTION_LOG_METHOD


log = get_module_logger(globals())  # noqa


##


class _RemoteLogHandler(logging.Handler):
    """
    Forwards the remote's log records to the host as notifications, from any thread.

    Only records at INFO and above are forwarded: the transport itself logs every message it moves at DEBUG, and
    forwarding those would feed back on itself without end. Debug records still reach the remote's own handlers.
    """

    def __init__(
            self,
            connection: RpcConnection,
            loop: ta.Any = None,
    ) -> None:
        super().__init__(level=logging.INFO)

        self._connection = connection
        self._loop = loop

    def emit(self, record):
        msg = self.format(record)

        async def inner():
            try:
                await self._connection.notify(REMOTE_EXECUTION_LOG_METHOD, msg)
            except Exception:  # noqa
                # The connection owns its failure; a record which cannot be forwarded is still in the remote's own logs.
                pass

        loop = self._loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return
        asyncio.run_coroutine_threadsafe(inner(), loop)


##


class _RemoteCommandHandler:
    """The remote end of `manage.execute`: runs each command through the local executor, one task per request."""

    def __init__(
            self,
            executor: CommandExecutor,
            msh: ObjMarshalerManager,
    ) -> None:
        super().__init__()

        self._executor = executor
        self._msh = msh

    async def _execute(self, cmd: Command) -> CommandOutputOrExceptionData:
        res = await self._executor.try_execute(
            cmd,
            log=log,
            omit_exc_object=True,
        )

        return CommandOutputOrExceptionData(
            output=res.output,
            exception=res.exception,
        )

    def method_table(self) -> ta.Mapping[str, RpcMethodFn]:
        return {
            REMOTE_EXECUTION_EXECUTE_METHOD: rpc_typed_method(
                self._execute,
                Command,
                CommandOutputOrExceptionData,
                serde=LiteMarshalRpcSerde(self._msh),
            ),
        }


##


@dc.dataclass()
class RemoteCommandError(Exception):
    e: CommandException


class RemoteCommandExecutor(CommandExecutor):
    """The host end: a `CommandExecutor` whose commands run on the other end of an rpc connection."""

    def __init__(
            self,
            connection: RpcConnection,
            msh: ObjMarshalerManager,
    ) -> None:
        super().__init__()

        self._connection = connection
        self._caller = RpcTypedCaller(connection, LiteMarshalRpcSerde(msh))

    @property
    def connection(self) -> RpcConnection:
        return self._connection

    @staticmethod
    def handle_log_notification(params: ta.Any) -> None:
        log.info(check.isinstance(params, str))

    #

    async def _remote_execute(self, cmd: Command) -> CommandOutputOrException:
        return await self._caller.call(
            REMOTE_EXECUTION_EXECUTE_METHOD,
            cmd,
            CommandOutputOrExceptionData,
            params_type=Command,
        )

    # @ta.override
    async def execute(self, cmd: Command) -> Command.Output:
        r = await self._remote_execute(cmd)
        if (e := r.exception) is not None:
            raise RemoteCommandError(e)
        else:
            return check.not_none(r.output)

    # @ta.override
    async def try_execute(
            self,
            cmd: Command,
            *,
            log: ta.Optional[LoggerLike] = None,  # noqa
            omit_exc_object: bool = False,
    ) -> CommandOutputOrException:
        try:
            r = await self._remote_execute(cmd)

        except Exception as e:  # noqa
            if log is not None:
                log.exception('Exception executing remote command: %r', type(cmd))

            return CommandOutputOrExceptionData(exception=CommandException.of(
                e,
                omit_exc_object=omit_exc_object,
                cmd=cmd,
            ))

        else:
            return r
