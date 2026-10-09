"""
ZMTP commands: a command frame body is a one-byte name length, the name, and command data. READY carries metadata
properties, each a one-byte name length, the name, a four-byte network-order value length, and the value. ERROR carries
a one-byte reason length and the reason.
"""
import typing as ta

from omcore import dataclasses as dc

from ..core.sockettypes import IDENTITY_SOCKET_TYPES
from ..core.sockettypes import SocketType
from .errors import ZmtpHandshakeError
from .errors import ZmtpProtocolError


##


READY = b'READY'
ERROR = b'ERROR'

SOCKET_TYPE_PROPERTY = 'Socket-Type'
IDENTITY_PROPERTY = 'Identity'

_PROPERTY_NAME_CHARS = frozenset(b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.+')


@dc.dataclass(frozen=True)
class ZmtpCommand:
    name: bytes
    data: bytes = b''


def decode_command_body(body: bytes) -> ZmtpCommand:
    if not body or not (1 <= body[0] <= len(body) - 1):
        raise ZmtpProtocolError('malformed command name')
    n = body[0]
    return ZmtpCommand(body[1:1 + n], body[1 + n:])


##
# Metadata


def encode_metadata(props: ta.Iterable[tuple[str, bytes]]) -> bytes:
    parts: list[bytes] = []
    for name, value in props:
        nb = name.encode('ascii')
        if not (1 <= len(nb) <= 0xff) or not set(nb) <= _PROPERTY_NAME_CHARS:
            raise ValueError(name)
        parts.append(bytes([len(nb)]) + nb + len(value).to_bytes(4, 'big') + value)
    return b''.join(parts)


def decode_metadata(data: bytes, *, max_properties: int) -> list[tuple[str, bytes]]:
    props: list[tuple[str, bytes]] = []
    pos = 0
    while pos < len(data):
        if len(props) >= max_properties:
            raise ZmtpProtocolError(f'more than {max_properties} metadata properties')

        n = data[pos]
        pos += 1
        nb = data[pos:pos + n]
        if not n or len(nb) != n or not set(nb) <= _PROPERTY_NAME_CHARS:
            raise ZmtpProtocolError('malformed metadata property name')
        pos += n

        if pos + 4 > len(data):
            raise ZmtpProtocolError('truncated metadata property')
        vn = int.from_bytes(data[pos:pos + 4], 'big')
        pos += 4
        if pos + vn > len(data):
            raise ZmtpProtocolError('truncated metadata property value')
        props.append((nb.decode('ascii'), data[pos:pos + vn]))
        pos += vn

    return props


##
# READY


@dc.dataclass(frozen=True)
class ZmtpReady:
    socket_type: SocketType
    identity: bytes = b''
    properties: ta.Sequence[tuple[str, bytes]] = ()


def encode_ready(socket_type: SocketType, *, identity: bytes = b'') -> ZmtpCommand:
    props: list[tuple[str, bytes]] = [(SOCKET_TYPE_PROPERTY, socket_type.value.encode('ascii'))]
    if socket_type in IDENTITY_SOCKET_TYPES:
        props.append((IDENTITY_PROPERTY, identity))
    elif identity:
        raise ValueError(f'{socket_type} sockets carry no identity')
    return ZmtpCommand(READY, encode_metadata(props))


def decode_ready(data: bytes, *, max_properties: int = 64) -> ZmtpReady:
    props = decode_metadata(data, max_properties=max_properties)

    found: dict[str, bytes] = {}
    for name, value in props:
        key = name.lower()
        if key in (SOCKET_TYPE_PROPERTY.lower(), IDENTITY_PROPERTY.lower()):
            if key in found:
                raise ZmtpHandshakeError(f'duplicate {name} property')
            found[key] = value

    try:
        raw_type = found[SOCKET_TYPE_PROPERTY.lower()]
    except KeyError:
        raise ZmtpHandshakeError('missing Socket-Type property') from None
    try:
        socket_type = SocketType(raw_type.decode('ascii'))
    except (UnicodeDecodeError, ValueError):
        raise ZmtpHandshakeError(f'unknown socket type {raw_type!r}') from None

    identity = found.get(IDENTITY_PROPERTY.lower(), b'')
    if len(identity) > 0xff:
        raise ZmtpHandshakeError('identity longer than 255 bytes')

    return ZmtpReady(socket_type, identity, props)


##
# ERROR


def encode_error(reason: bytes) -> ZmtpCommand:
    reason = reason[:0xff]
    return ZmtpCommand(ERROR, bytes([len(reason)]) + reason)


def decode_error(data: bytes) -> bytes:
    if not data or data[0] != len(data) - 1:
        raise ZmtpProtocolError('malformed ERROR command')
    return data[1:]
