"""
The fixed 64-byte ZMTP 3 greeting:

 - signature: 0xff, 8 padding bytes (not validated - native peers may put legacy detection data there), 0x7f
 - version: major and minor bytes
 - mechanism: 20 bytes, an ASCII name padded with NULs
 - as-server: one byte
 - filler: 31 zero bytes
"""
from omcore import dataclasses as dc

from .errors import ZmtpHandshakeError
from .errors import ZmtpProtocolError


##


GREETING_SIZE = 64

SIGNATURE_START = 0xff
SIGNATURE_END = 0x7f

MECHANISM_SIZE = 20

NULL_MECHANISM = b'NULL'


@dc.dataclass(frozen=True)
class ZmtpGreeting:
    major: int = 3
    minor: int = 0
    mechanism: bytes = NULL_MECHANISM
    as_server: bool = False


LOCAL_GREETING = ZmtpGreeting()


def encode_greeting(g: ZmtpGreeting) -> bytes:
    if len(g.mechanism) > MECHANISM_SIZE:
        raise ValueError(g.mechanism)

    return b''.join([
        bytes([SIGNATURE_START]),
        bytes(8),
        bytes([SIGNATURE_END, g.major, g.minor]),
        g.mechanism.ljust(MECHANISM_SIZE, b'\0'),
        bytes([1 if g.as_server else 0]),
        bytes(31),
    ])


def check_greeting_prefix(prefix: bytes | memoryview) -> None:
    """Reject a greeting as early as its first bytes allow, rather than waiting for all 64."""

    if len(prefix) >= 1 and prefix[0] != SIGNATURE_START:
        raise ZmtpProtocolError('invalid greeting signature')
    if len(prefix) >= 10 and prefix[9] != SIGNATURE_END:
        raise ZmtpProtocolError('invalid greeting signature')
    if len(prefix) >= 11 and prefix[10] < 3:
        raise ZmtpHandshakeError(f'unsupported ZMTP version {prefix[10]}')


def decode_greeting(data: bytes) -> ZmtpGreeting:
    if len(data) != GREETING_SIZE:
        raise ValueError(len(data))

    check_greeting_prefix(data)

    mechanism = data[12:12 + MECHANISM_SIZE]
    name = mechanism.rstrip(b'\0')
    if b'\0' in name:
        raise ZmtpProtocolError('invalid greeting mechanism')

    as_server = data[32]
    if as_server not in (0, 1):
        raise ZmtpProtocolError('invalid greeting as-server value')

    return ZmtpGreeting(
        major=data[10],
        minor=data[11],
        mechanism=name,
        as_server=bool(as_server),
    )
