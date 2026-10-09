import math

from omcore import dataclasses as dc

from .messages import DEFAULT_MESSAGE_LIMITS
from .messages import MessageLimits


##


@dc.dataclass(frozen=True)
class SocketConfig:
    """
    Semantic socket configuration shared by all backends.

    Timeouts are in seconds; `None` means no deadline. Queue sizes are whole messages per peer and direction - native
    high-water marks for the pyzmq backend, bounded queues for the in-house one.
    """

    limits: MessageLimits = DEFAULT_MESSAGE_LIMITS

    send_timeout: float | None = 300.
    recv_timeout: float | None = 300.

    send_queue_size: int = 64
    recv_queue_size: int = 64

    reconnect_interval: float = .1
    reconnect_interval_max: float = 5.

    handshake_timeout: float = 10.

    def __post_init__(self) -> None:
        for t in (self.send_timeout, self.recv_timeout):
            if t is not None and not t > 0:
                raise ValueError(t)
        if self.send_queue_size < 1 or self.recv_queue_size < 1:
            raise ValueError((self.send_queue_size, self.recv_queue_size))
        if not (0 < self.reconnect_interval <= self.reconnect_interval_max):
            raise ValueError((self.reconnect_interval, self.reconnect_interval_max))
        if not self.handshake_timeout > 0:
            raise ValueError(self.handshake_timeout)


DEFAULT_SOCKET_CONFIG = SocketConfig()


def resolve_timeout(timeout: float | None, default: float | None) -> float | None:
    """Resolve an operation's timeout: `None` takes the default, and `math.inf` - or a `None` default - means none."""

    if timeout is None:
        timeout = default
    if timeout is None or timeout == math.inf:
        return None
    if not timeout >= 0:
        raise ValueError(timeout)
    return timeout
