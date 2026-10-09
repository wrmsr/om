import abc

from omcore import lang

from .queues import MessageQueue
from .sockettypes import SocketType
from .subscriptions import SubscriptionCounts


##


class PeerSink(lang.Abstract):
    """
    Synchronous notifications from an endpoint to the owner of one peer's connection. Implementations must not call
    back into the endpoint synchronously: they arrange for the connection to act later, in its own turn.
    """

    @abc.abstractmethod
    def wake_send(self) -> None:
        """The peer has queued output to take."""

        raise NotImplementedError

    @abc.abstractmethod
    def wake_recv(self) -> None:
        """The peer's inbound queue regained room after the connection was told to stop reading."""

        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """The endpoint dropped the peer, abortively: the connection should end."""

        raise NotImplementedError


class Peer:
    """
    An endpoint's state for one ready connection. The token increases monotonically across an endpoint's peers, so a
    stale reference never aliases a later connection.
    """

    def __init__(
            self,
            *,
            token: int,
            socket_type: SocketType,
            route: bytes,
            sink: PeerSink,
            inbound: MessageQueue,
            outbound: MessageQueue,
    ) -> None:
        super().__init__()

        self.token = token
        self.socket_type = socket_type
        self.route = route
        self.sink = sink
        self.inbound = inbound
        self.outbound = outbound

        self.attached = True

        # Whether the connection was told to stop reading, and so awaits wake_recv.
        self.recv_paused = False

        # Publisher side: what the peer subscribed to.
        self.subscriptions: SubscriptionCounts | None = None

        # Subscriber side: subscription changes not yet sent to the peer, coalesced per prefix.
        self.pending_subscriptions: dict[bytes, bool] | None = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self.token} {self.socket_type.value} {self.route!r}>'

    def has_output(self) -> bool:
        return bool(self.outbound) or bool(self.pending_subscriptions)
