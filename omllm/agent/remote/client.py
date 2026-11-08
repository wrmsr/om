"""
The host's end of one remote agent connection: a single rpc connection over which each remotable concern's client
speaks - today the environment (`RemoteEnvironmentOps`), the filesystem (`RemoteFsOps`), and processes
(`RemoteProcessManager`). A new remotable concern builds its client on the same connection here, and its service into
the payload in `server.py`.
"""
import asyncio
import typing as ta

from omcore.logs import all as logs
from omcore.rpc.connection import RpcConnection
from omcore.rpc.dispatch import RpcMethodTableHandler

from ...core.processes.managers.types import ManagerConfig
from ...core.processes.remote.client import RemoteProcessManager
from ..environment.remote.client import RemoteEnvironmentOps
from ..fs.remote.client import RemoteFsOps


log = logs.get_module_logger(globals())


##


class RemoteAgentClient:
    def __init__(
            self,
            connection: RpcConnection,
            *,
            process_config: ManagerConfig | None = None,
    ) -> None:
        """Takes an unstarted connection to the agent, whose handler it installs."""

        super().__init__()

        # The agent only ever notifies the host, never calls it; each concern routes its own notifications.
        self._notifications = RpcMethodTableHandler()
        self._connection = connection
        connection.set_handler(self._notifications)

        self._processes = RemoteProcessManager(
            self._connection,
            notifications=self._notifications,
            config=process_config,
        )
        self._fs = RemoteFsOps(self._connection)
        self._environment = RemoteEnvironmentOps(self._connection)

        self._started = False

    @property
    def connection(self) -> RpcConnection:
        return self._connection

    @property
    def environment(self) -> RemoteEnvironmentOps:
        return self._environment

    @property
    def fs(self) -> RemoteFsOps:
        return self._fs

    @property
    def processes(self) -> RemoteProcessManager:
        return self._processes

    async def start(self) -> None:
        if self._started:
            raise RuntimeError('Remote agent client has already been started')
        self._started = True
        await self._connection.start()
        try:
            await self._processes.start()
        except BaseException:
            await self._connection.close(graceful=False)
            raise

    async def wait_closed(self) -> None:
        await self._connection.wait_closed()

    async def aclose(self, *, timeout_s: float | None = None) -> None:
        """
        Closes the remote processes, then the connection. `timeout_s` bounds the graceful part: if the agent has not
        finished tearing its processes down by then - or is not answering at all - the connection is severed first,
        which fails every outstanding call and lets the process manager finish on its own.
        """

        if not self._started:
            await self._processes.aclose()
            await self._connection.close(graceful=False)
            return

        closing = asyncio.ensure_future(self._processes.aclose())
        try:
            done, _ = await asyncio.wait([closing], timeout=timeout_s)
        except BaseException:
            # Cancelled while waiting: sever the connection so the manager cannot wait on the agent any longer, and
            # still see it through.
            await self._connection.close(graceful=False)
            await asyncio.wait([closing])
            raise
        try:
            if not done:
                await self._connection.close(graceful=False)
            await closing
        finally:
            await self._connection.close(graceful=False)

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
