"""
The host's end of one remote agent connection: a single rpc peer over which each remotable concern's client speaks -
today the filesystem (`RemoteFsOps`) and processes (`RemoteProcessManager`). A new remotable concern builds its client
on the same peer here, and its service into the payload in `server.py`.
"""
import asyncio
import typing as ta

from omcore.logs import all as logs

from ...core.processes.managers.types import ManagerConfig
from ...core.processes.remote.client import RemoteProcessManager
from ...core.rpc.channels import RpcChannel
from ...core.rpc.handlers import RpcNotificationRouter
from ...core.rpc.messages import RpcNotificationMessage
from ...core.rpc.peers import RpcPeer
from ..fs.remote.client import RemoteFsOps


log = logs.get_module_logger(globals())


##


class RemoteAgentClient:
    def __init__(
            self,
            channel: RpcChannel,
            *,
            process_config: ManagerConfig | None = None,
    ) -> None:
        super().__init__()

        # The agent only ever notifies the host, never calls it; each concern routes its own notifications.
        self._notifications = RpcNotificationRouter()
        self._peer = RpcPeer(
            channel,
            handler=self._notifications,
            notification_error_handler=self._on_notification_error,
        )

        self._processes = RemoteProcessManager(
            self._peer,
            notifications=self._notifications,
            config=process_config,
        )
        self._fs = RemoteFsOps(self._peer)

        self._started = False

    @property
    def peer(self) -> RpcPeer:
        return self._peer

    @property
    def fs(self) -> RemoteFsOps:
        return self._fs

    @property
    def processes(self) -> RemoteProcessManager:
        return self._processes

    def _on_notification_error(self, message: RpcNotificationMessage, error: BaseException) -> None:
        log.warning('Error handling remote agent event %r: %r', message.method, error)

    async def start(self) -> None:
        if self._started:
            raise RuntimeError('Remote agent client has already been started')
        self._started = True
        await self._peer.start()
        try:
            await self._processes.start()
        except BaseException:
            await self._peer.aclose()
            raise

    async def wait_closed(self) -> None:
        await self._peer.wait_closed()

    async def aclose(self, *, timeout_s: float | None = None) -> None:
        """
        Closes the remote processes, then the connection. `timeout_s` bounds the graceful part: if the agent has not
        finished tearing its processes down by then - or is not answering at all - the connection is severed first,
        which fails every outstanding call and lets the process manager finish on its own.
        """

        if not self._started:
            await self._processes.aclose()
            await self._peer.aclose()
            return

        closing = asyncio.ensure_future(self._processes.aclose())
        try:
            done, _ = await asyncio.wait([closing], timeout=timeout_s)
        except BaseException:
            # Cancelled while waiting: sever the connection so the manager cannot wait on the agent any longer, and
            # still see it through.
            await self._peer.aclose()
            await asyncio.wait([closing])
            raise
        try:
            if not done:
                await self._peer.aclose()
            await closing
        finally:
            await self._peer.aclose()

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
