from ..api.messages import Message
from .endpoints import Endpoint
from .endpoints import EndpointConfig
from .endpoints import EndpointListener
from .fairqueues import FairQueue
from .peers import Peer
from .sockettypes import SocketType


##


class DealerEndpoint(Endpoint):
    """Sends round robin to peers with capacity, skipping blocked ones, and receives fairly from all."""

    SOCKET_TYPE = SocketType.DEALER

    def __init__(
            self,
            config: EndpointConfig | None = None,
            *,
            listener: EndpointListener | None = None,
    ) -> None:
        super().__init__(config, listener=listener)

        self._send_order: FairQueue[Peer] = FairQueue()

    def _on_attach(self, peer: Peer) -> None:
        self._send_order.add(peer)

    def _on_detach(self, peer: Peer) -> None:
        self._send_order.remove(peer)

    def _on_message(self, peer: Peer, msg: Message) -> bool:
        peer.inbound.push(msg)
        return True

    def try_send(self, msg: Message) -> bool:
        """Queue to the next peer with capacity, returning False - without effect - when there is none."""

        if (peer := self._send_order.find(lambda p: p.outbound.has_room())) is None:
            return False
        self._queue_output(peer, msg)
        return True

    def recv(self) -> Message | None:
        if (r := self._pop_received()) is None:
            return None
        return r[1]
