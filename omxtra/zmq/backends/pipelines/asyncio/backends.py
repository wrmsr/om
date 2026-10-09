import typing as ta

from ....api.backends import Backend
from ....api.configs import DEFAULT_SOCKET_CONFIG
from ....api.configs import SocketConfig
from ....api.errors import SocketClosedError
from ....api.messages import check_routing_id
from .configs import DEFAULT_PIPELINES_BACKEND_CONFIG
from .configs import PipelinesBackendConfig
from .sockets import PipelinesDealer
from .sockets import PipelinesPublisher
from .sockets import PipelinesRouter
from .sockets import PipelinesSocket
from .sockets import PipelinesSubscriber


PipelinesSocketT = ta.TypeVar('PipelinesSocketT', bound=PipelinesSocket)


##


class AsyncioPipelinesBackend(Backend):
    """The in-house backend: ZMTP over I/O pipelines, each connection driven by an asyncio pipeline driver."""

    def __init__(self, config: PipelinesBackendConfig | None = None) -> None:
        super().__init__()

        if config is None:
            config = DEFAULT_PIPELINES_BACKEND_CONFIG
        self._config = config

        self._sockets: dict[PipelinesSocket, None] = {}
        self._closed = False

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    def _new_socket(
            self,
            cls: type[PipelinesSocketT],
            config: SocketConfig | None,
            *,
            routing_id: bytes | None = None,
    ) -> PipelinesSocketT:
        if self._closed:
            raise SocketClosedError('backend closed')

        sock = cls(
            config if config is not None else DEFAULT_SOCKET_CONFIG,
            self._config,
            identity=check_routing_id(routing_id) if routing_id is not None else b'',
            on_close=self._on_socket_closed,
        )
        self._sockets[sock] = None
        return sock

    def _on_socket_closed(self, sock: PipelinesSocket) -> None:
        self._sockets.pop(sock, None)

    def create_publisher(self, config: SocketConfig | None = None) -> PipelinesPublisher:
        return self._new_socket(PipelinesPublisher, config)

    def create_subscriber(self, config: SocketConfig | None = None) -> PipelinesSubscriber:
        return self._new_socket(PipelinesSubscriber, config)

    def create_dealer(
            self,
            config: SocketConfig | None = None,
            *,
            routing_id: bytes | None = None,
    ) -> PipelinesDealer:
        return self._new_socket(PipelinesDealer, config, routing_id=routing_id)

    def create_router(
            self,
            config: SocketConfig | None = None,
            *,
            routing_id: bytes | None = None,
    ) -> PipelinesRouter:
        return self._new_socket(PipelinesRouter, config, routing_id=routing_id)

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        for sock in list(self._sockets):
            await sock.aclose()
