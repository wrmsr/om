from ..api.errors import UnroutableError
from ..api.errors import WouldBlockError
from ..api.messages import Message
from ..api.messages import RoutedMessage
from .endpoints import Endpoint
from .endpoints import EndpointConfig
from .endpoints import EndpointListener
from .errors import PeerRejectedError
from .peers import Peer
from .sockettypes import SocketType


##


class RouterEndpoint(Endpoint):
    """
    Routes by peer identity, generating a route for peers without one. A peer claiming an identity already in use is
    rejected - an existing route is never taken over - and a route is released only by the peer which holds it.
    """

    SOCKET_TYPE = SocketType.ROUTER

    def __init__(
            self,
            config: EndpointConfig | None = None,
            *,
            listener: EndpointListener | None = None,
    ) -> None:
        super().__init__(config, listener=listener)

        self._routes: dict[bytes, Peer] = {}
        self._route_counter = 0

    def routes(self) -> list[bytes]:
        return list(self._routes)

    def _route_for(self, identity: bytes) -> bytes:
        if identity:
            if identity in self._routes:
                raise PeerRejectedError(f'identity {identity!r} already in use')
            return identity

        # Generated routes start with a zero byte, which configured identities may not.
        while True:
            self._route_counter = (self._route_counter + 1) & 0xffffffff
            route = b'\x00' + self._route_counter.to_bytes(4, 'big')
            if route not in self._routes:
                return route

    def _on_attach(self, peer: Peer) -> None:
        self._routes[peer.route] = peer

    def _on_detach(self, peer: Peer) -> None:
        if self._routes.get(peer.route) is peer:
            del self._routes[peer.route]

    def _on_message(self, peer: Peer, msg: Message) -> bool:
        peer.inbound.push(msg)
        return True

    def send(self, route: bytes, msg: Message) -> None:
        if (peer := self._routes.get(route)) is None:
            raise UnroutableError(route)
        if not peer.outbound.has_room():
            raise WouldBlockError(route)
        self._queue_output(peer, msg)

    def recv(self) -> RoutedMessage | None:
        if (r := self._pop_received()) is None:
            return None
        peer, msg = r
        return RoutedMessage(peer.route, msg)
