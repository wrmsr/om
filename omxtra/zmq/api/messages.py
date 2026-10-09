import typing as ta

from omcore import dataclasses as dc

from .errors import InvalidMessageError
from .errors import InvalidRoutingIdError


type Message = tuple[bytes, ...]


##


@dc.dataclass(frozen=True)
class MessageLimits:
    """Semantic limits on what a socket accepts for sending and returns from receiving."""

    max_frame_size: int = 8 * 1024 * 1024
    max_message_size: int = 16 * 1024 * 1024
    max_frames: int = 1024

    max_subscription_size: int = 4 * 1024

    def __post_init__(self) -> None:
        if self.max_frames < 1:
            raise ValueError(self.max_frames)
        if not (0 <= self.max_frame_size <= self.max_message_size):
            raise ValueError((self.max_frame_size, self.max_message_size))
        if self.max_subscription_size < 0:
            raise ValueError(self.max_subscription_size)


DEFAULT_MESSAGE_LIMITS = MessageLimits()


@dc.dataclass(frozen=True)
class RoutedMessage:
    """A message received by a router, with the opaque route of the peer it came from."""

    route: bytes
    message: Message


##


def check_message(msg: ta.Any, limits: MessageLimits = DEFAULT_MESSAGE_LIMITS) -> Message:
    """Validate a whole message against limits, normalizing a list of frames to a tuple."""

    if isinstance(msg, tuple):
        frames = msg
    elif isinstance(msg, list):
        frames = tuple(msg)
    else:
        raise InvalidMessageError(f'message must be a tuple or list of bytes frames, not {type(msg).__name__}')

    if not frames:
        raise InvalidMessageError('message must have at least one frame')
    if len(frames) > limits.max_frames:
        raise InvalidMessageError(f'message has {len(frames)} frames, more than {limits.max_frames}')

    total = 0
    for f in frames:
        if not isinstance(f, bytes):
            raise InvalidMessageError(f'message frames must be bytes, not {type(f).__name__}')
        if len(f) > limits.max_frame_size:
            raise InvalidMessageError(f'frame of {len(f)} bytes exceeds {limits.max_frame_size}')
        total += len(f)

    if total > limits.max_message_size:
        raise InvalidMessageError(f'message of {total} bytes exceeds {limits.max_message_size}')

    return frames


def check_subscription(prefix: ta.Any, limits: MessageLimits = DEFAULT_MESSAGE_LIMITS) -> bytes:
    if not isinstance(prefix, bytes):
        raise InvalidMessageError(f'subscription prefix must be bytes, not {type(prefix).__name__}')
    if len(prefix) > limits.max_subscription_size:
        raise InvalidMessageError(f'subscription prefix of {len(prefix)} bytes exceeds {limits.max_subscription_size}')
    return prefix


def check_routing_id(routing_id: ta.Any) -> bytes:
    """Validate an explicitly configured routing id: 1 to 255 bytes, not starting with a zero byte."""

    if not isinstance(routing_id, bytes):
        raise InvalidRoutingIdError(f'routing id must be bytes, not {type(routing_id).__name__}')
    if not (1 <= len(routing_id) <= 255):
        raise InvalidRoutingIdError(f'routing id must be 1 to 255 bytes, not {len(routing_id)}')
    if routing_id[0] == 0:
        raise InvalidRoutingIdError('routing id must not start with a zero byte')
    return routing_id


def check_route(route: ta.Any) -> bytes:
    """Validate a route given to a router send: any nonempty bytes, as received routes may be generated."""

    if not isinstance(route, bytes):
        raise InvalidRoutingIdError(f'route must be bytes, not {type(route).__name__}')
    if not route:
        raise InvalidRoutingIdError('route must not be empty')
    return route
