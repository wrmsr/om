import typing as ta

from omcore import dataclasses as dc
from omcore.io.pipelines.core import IoPipelineMessages

from ...core.sockettypes import SocketType


##


@dc.dataclass(frozen=True)
class ZmtpMessage:
    """A whole multipart application message, in either direction."""

    frames: tuple[bytes, ...]


@dc.dataclass(frozen=True)
class ZmtpPeerReady(IoPipelineMessages.NeverOutbound):
    """Emitted inbound once the handshake completed: everything after it is ordinary traffic from a compatible peer."""

    socket_type: SocketType
    identity: bytes = b''
    properties: ta.Sequence[tuple[str, bytes]] = ()
