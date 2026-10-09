"""
Sans-I/O endpoints: one per logical socket, owning its ready peers, their bounded queues, and the pattern's routing.

Sessions call `attach` when a connection becomes ready, `deliver` with each message it receives, `can_receive` after
each batch to decide whether to keep reading, `take_output` to pull messages to send, and `detach` when it ends. The
application side calls the pattern's operations. All are synchronous, and every notification - to a peer's sink or to
the endpoint listener - is made after the state change it reports is complete.
"""
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..api.messages import DEFAULT_MESSAGE_LIMITS
from ..api.messages import Message
from ..api.messages import MessageLimits
from .errors import PeerRejectedError
from .fairqueues import FairQueue
from .peers import Peer
from .peers import PeerSink
from .queues import MessageQueue
from .sockettypes import SocketType
from .sockettypes import is_supported_peer


##


class EndpointListener(lang.Abstract):
    """Synchronous notifications to the endpoint's owner, which must not call back into the endpoint synchronously."""

    @abc.abstractmethod
    def on_readable(self) -> None:
        """A receive may now succeed."""

        raise NotImplementedError

    @abc.abstractmethod
    def on_writable(self) -> None:
        """A send which waits for capacity may now succeed."""

        raise NotImplementedError


class NopEndpointListener(EndpointListener):
    def on_readable(self) -> None:
        pass

    def on_writable(self) -> None:
        pass


@dc.dataclass(frozen=True)
class EndpointConfig:
    limits: MessageLimits = DEFAULT_MESSAGE_LIMITS

    send_queue_size: int = 64
    recv_queue_size: int = 64
    max_queue_bytes: int = 32 * 1024 * 1024

    max_peers: int = 64
    max_peer_subscriptions: int = 1024

    def __post_init__(self) -> None:
        if min(self.send_queue_size, self.recv_queue_size, self.max_queue_bytes, self.max_peers) < 1:
            raise ValueError(self)


class Endpoint(lang.Abstract):
    SOCKET_TYPE: ta.ClassVar[SocketType]

    def __init__(
            self,
            config: EndpointConfig | None = None,
            *,
            listener: EndpointListener | None = None,
    ) -> None:
        super().__init__()

        if config is None:
            config = EndpointConfig()
        self._config = config
        self._listener = listener if listener is not None else NopEndpointListener()

        self._peers: dict[int, Peer] = {}
        self._readable: FairQueue[Peer] = FairQueue()
        self._next_token = 0
        self._closed = False

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def config(self) -> EndpointConfig:
        return self._config

    @property
    def closed(self) -> bool:
        return self._closed

    def peers(self) -> list[Peer]:
        return list(self._peers.values())

    #

    def _route_for(self, identity: bytes) -> bytes:
        return identity

    def _on_attach(self, peer: Peer) -> None:
        pass

    def _on_detach(self, peer: Peer) -> None:
        pass

    @abc.abstractmethod
    def _on_message(self, peer: Peer, msg: Message) -> bool:
        """Handle a delivered message, returning whether it was queued for the application."""

        raise NotImplementedError

    #

    def attach(self, *, socket_type: SocketType, identity: bytes, sink: PeerSink) -> Peer:
        if self._closed:
            raise PeerRejectedError('endpoint closed')
        if not is_supported_peer(self.SOCKET_TYPE, socket_type):
            raise PeerRejectedError(f'{self.SOCKET_TYPE.value} cannot connect to {socket_type.value}')
        if len(self._peers) >= self._config.max_peers:
            raise PeerRejectedError(f'more than {self._config.max_peers} peers')

        route = self._route_for(identity)

        self._next_token += 1
        peer = Peer(
            token=self._next_token,
            socket_type=socket_type,
            route=route,
            sink=sink,
            inbound=MessageQueue(max_messages=self._config.recv_queue_size, max_bytes=self._config.max_queue_bytes),
            outbound=MessageQueue(max_messages=self._config.send_queue_size, max_bytes=self._config.max_queue_bytes),
        )
        self._peers[peer.token] = peer
        self._on_attach(peer)

        if peer.has_output():
            sink.wake_send()
        self._listener.on_writable()
        return peer

    def _remove(self, peer: Peer) -> bool:
        if not peer.attached or self._peers.get(peer.token) is not peer:
            return False

        peer.attached = False
        del self._peers[peer.token]
        self._on_detach(peer)

        # Unsent messages are discarded with their connection, never migrated to another. Messages already received
        # whole stay receivable, as a native socket delivers them too.
        peer.outbound.clear()
        peer.pending_subscriptions = None
        if not peer.inbound:
            self._readable.remove(peer)
        return True

    def detach(self, peer: Peer) -> None:
        self._remove(peer)

    def deliver(self, peer: Peer, msg: Message) -> None:
        if not peer.attached:
            return

        if self._on_message(peer, msg):
            self._readable.add(peer)
            self._listener.on_readable()

    def can_receive(self, peer: Peer) -> bool:
        """Whether the peer's connection may read more input. When not, wake_recv follows once room returns."""

        if not peer.attached:
            return False
        if peer.inbound.has_room():
            return True
        peer.recv_paused = True
        return False

    def take_output(self, peer: Peer) -> Message | None:
        if not peer.attached:
            return None

        if (pending := peer.pending_subscriptions):
            prefix, subscribe = next(iter(pending.items()))
            del pending[prefix]
            return ((b'\x01' if subscribe else b'\x00') + prefix,)

        if not peer.outbound:
            return None

        was_full = not peer.outbound.has_room()
        msg = peer.outbound.pop()
        if was_full and peer.outbound.has_room():
            self._listener.on_writable()
        return msg

    #

    def _queue_output(self, peer: Peer, msg: Message) -> None:
        had_output = peer.has_output()
        peer.outbound.push(msg)
        if not had_output:
            peer.sink.wake_send()

    def _pop_received(self) -> tuple[Peer, Message] | None:
        if (peer := self._readable.pop()) is None:
            return None

        msg = peer.inbound.pop()
        if peer.inbound:
            self._readable.add(peer)

        if peer.attached and peer.recv_paused and peer.inbound.has_room():
            peer.recv_paused = False
            peer.sink.wake_recv()
        return peer, msg

    def has_received(self) -> bool:
        return bool(self._readable)

    def close(self) -> None:
        """Abortively drop every peer, telling each connection to end. Queued messages are discarded."""

        if self._closed:
            return
        self._closed = True

        dropped = [p for p in list(self._peers.values()) if self._remove(p)]
        while (p := self._readable.pop()) is not None:
            p.inbound.clear()
        for p in dropped:
            p.sink.close()

        self._listener.on_readable()
        self._listener.on_writable()
