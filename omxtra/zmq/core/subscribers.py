from ..api.messages import Message
from .endpoints import Endpoint
from .endpoints import EndpointConfig
from .endpoints import EndpointListener
from .peers import Peer
from .sockettypes import SocketType
from .subscriptions import SubscriptionCounts


##


class SubEndpoint(Endpoint):
    """
    Keeps reference-counted subscriptions, sends only effective changes to each peer - replaying the whole effective
    set to each new one - and filters what arrives against them.
    """

    SOCKET_TYPE = SocketType.SUB

    def __init__(
            self,
            config: EndpointConfig | None = None,
            *,
            listener: EndpointListener | None = None,
    ) -> None:
        super().__init__(config, listener=listener)

        self._subscriptions = SubscriptionCounts()

    def subscriptions(self) -> list[bytes]:
        return self._subscriptions.prefixes()

    def _on_attach(self, peer: Peer) -> None:
        peer.pending_subscriptions = dict.fromkeys(self._subscriptions.prefixes(), True)

    def _on_message(self, peer: Peer, msg: Message) -> bool:
        # Publishers filter too, but messages published before a cancellation took effect may still arrive.
        if not self._subscriptions.matches(msg[0]):
            return False
        peer.inbound.push(msg)
        return True

    def _propagate(self, prefix: bytes) -> None:
        for peer in list(self._peers.values()):
            pending = peer.pending_subscriptions
            if pending is None:
                raise RuntimeError(peer)

            had_output = peer.has_output()
            # Effective changes alternate per prefix, so a pending change is always the opposite of this one: the two
            # cancel out, and the peer keeps the state it was last sent.
            if prefix in pending:
                del pending[prefix]
            else:
                pending[prefix] = prefix in self._subscriptions

            if not had_output and peer.has_output():
                peer.sink.wake_send()

    def subscribe(self, prefix: bytes) -> None:
        if self._subscriptions.add(prefix):
            self._propagate(prefix)

    def unsubscribe(self, prefix: bytes) -> None:
        if self._subscriptions.remove(prefix):
            self._propagate(prefix)

    def recv(self) -> Message | None:
        if (r := self._pop_received()) is None:
            return None
        return r[1]
