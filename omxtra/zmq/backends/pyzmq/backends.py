import math
import typing as ta

from omcore import check
from omcore import lang

from ...api.backends import Backend
from ...api.configs import DEFAULT_SOCKET_CONFIG
from ...api.configs import SocketConfig
from ...api.errors import SocketClosedError
from ...api.messages import check_routing_id
from .imports import check_pyzmq_available
from .sockets import PyzmqDealer
from .sockets import PyzmqPublisher
from .sockets import PyzmqRouter
from .sockets import PyzmqSocket
from .sockets import PyzmqSubscriber


with lang.auto_proxy_import(globals()):
    import zmq
    import zmq.asyncio


PyzmqSocketT = ta.TypeVar('PyzmqSocketT', bound=PyzmqSocket)


##


# The largest interval natively representable, standing in for an unbounded one.
_MAX_MS = (1 << 31) - 1


def _ms(s: float, *, inf: int = _MAX_MS) -> int:
    if math.isinf(s):
        return inf
    return min(max(1, round(s * 1000)), _MAX_MS)


class PyzmqBackend(Backend):
    """
    A backend using pyzmq's asyncio sockets. By default it owns a fresh native context, terminated once all its sockets
    are closed; a given context remains the caller's and is never terminated here.
    """

    def __init__(self, *, context: zmq.asyncio.Context | None = None) -> None:
        super().__init__()

        check_pyzmq_available()

        if context is None:
            self._context = zmq.asyncio.Context()
            self._owns_context = True
        else:
            self._context = check.isinstance(context, zmq.asyncio.Context)
            self._owns_context = False

        self._sockets: dict[PyzmqSocket, None] = {}
        self._closed = False

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    #

    def _new_socket(
            self,
            cls: type[PyzmqSocketT],
            zmq_type: int,
            config: SocketConfig | None,
            *,
            routing_id: bytes | None = None,
            options: ta.Mapping[int, int] | None = None,
    ) -> PyzmqSocketT:
        if self._closed:
            raise SocketClosedError('backend closed')

        if config is None:
            config = DEFAULT_SOCKET_CONFIG
        if routing_id is not None:
            check_routing_id(routing_id)

        zs = self._context.socket(zmq_type)
        try:
            # Options precede any attachment, as some only apply to later ones.
            zs.setsockopt(zmq.LINGER, 0)
            zs.setsockopt(zmq.SNDHWM, config.send_queue_size)
            zs.setsockopt(zmq.RCVHWM, config.recv_queue_size)
            zs.setsockopt(zmq.MAXMSGSIZE, config.limits.max_frame_size)
            # Natively a reconnect interval of -1 never reconnects, and a handshake interval of 0 has no deadline.
            zs.setsockopt(zmq.RECONNECT_IVL, _ms(config.reconnect_interval, inf=-1))
            zs.setsockopt(zmq.RECONNECT_IVL_MAX, _ms(config.reconnect_interval_max))
            zs.setsockopt(zmq.HANDSHAKE_IVL, _ms(config.handshake_timeout, inf=0))
            if routing_id is not None:
                zs.setsockopt(zmq.ROUTING_ID, routing_id)
            for k, v in (options or {}).items():
                zs.setsockopt(k, v)

        except BaseException:
            zs.close(linger=0)
            raise

        sock = cls(zs, config, on_close=self._on_socket_closed)
        self._sockets[sock] = None
        return sock

    def _on_socket_closed(self, sock: PyzmqSocket) -> None:
        self._sockets.pop(sock, None)

    #

    def create_publisher(self, config: SocketConfig | None = None) -> PyzmqPublisher:
        return self._new_socket(PyzmqPublisher, zmq.PUB, config)

    def create_subscriber(self, config: SocketConfig | None = None) -> PyzmqSubscriber:
        return self._new_socket(PyzmqSubscriber, zmq.SUB, config)

    def create_dealer(
            self,
            config: SocketConfig | None = None,
            *,
            routing_id: bytes | None = None,
    ) -> PyzmqDealer:
        return self._new_socket(
            PyzmqDealer,
            zmq.DEALER,
            config,
            routing_id=routing_id,
            options={
                # Only queue to connections which completed their handshake.
                zmq.IMMEDIATE: 1,
            },
        )

    def create_router(
            self,
            config: SocketConfig | None = None,
            *,
            routing_id: bytes | None = None,
    ) -> PyzmqRouter:
        return self._new_socket(
            PyzmqRouter,
            zmq.ROUTER,
            config,
            routing_id=routing_id,
            options={
                # Fail unroutable sends rather than silently dropping them.
                zmq.ROUTER_MANDATORY: 1,
                # A duplicate identity never takes over an existing route.
                zmq.ROUTER_HANDOVER: 0,
            },
        )

    async def aclose(self) -> None:
        if self._closed:
            return

        self._closed = True
        for sock in list(self._sockets):
            await sock.aclose()

        if self._owns_context:
            # Every owned socket is closed with zero linger, so this does not block.
            self._context.term()
