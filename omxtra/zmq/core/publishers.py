from ..api.messages import Message
from .endpoints import Endpoint
from .errors import PeerViolationError
from .peers import Peer
from .sockettypes import SocketType
from .subscriptions import SubscriptionCounts


##


class PubEndpoint(Endpoint):
    """Fans publications out to subscribed peers, dropping for any without capacity rather than waiting."""

    SOCKET_TYPE = SocketType.PUB

    def _on_attach(self, peer: Peer) -> None:
        peer.subscriptions = SubscriptionCounts(max_prefixes=self._config.max_peer_subscriptions)

    def _on_message(self, peer: Peer, msg: Message) -> bool:
        # ZMTP 3.0 subscriptions are single-frame messages led by 1 (subscribe) or 0 (cancel). Anything else - which an
        # XSUB peer may send - is not publication input, and is dropped.
        if len(msg) == 1 and msg[0][:1] in (b'\x00', b'\x01'):
            prefix = msg[0][1:]
            if len(prefix) > self._config.limits.max_subscription_size:
                raise PeerViolationError(f'subscription prefix of {len(prefix)} bytes')

            subs = peer.subscriptions
            if subs is None:
                raise RuntimeError(peer)
            if msg[0][0]:
                subs.add(prefix)
            else:
                subs.remove(prefix)

        return False

    def publish(self, msg: Message) -> None:
        topic = msg[0]
        for peer in list(self._peers.values()):
            subs = peer.subscriptions
            if subs is not None and subs.matches(topic) and peer.outbound.has_room():
                self._queue_output(peer, msg)
