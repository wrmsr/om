"""Parsing of server packet payloads into typed messages. Pure functions of the payload and the needed context."""
import struct

from ..errors import ProtocolError
from .messages import AuthMoreData
from .messages import AuthSwitchRequest
from .messages import ColumnDefinition
from .messages import EofPacket
from .messages import ErrPacket
from .messages import Handshake
from .messages import LocalInfileRequest
from .messages import OkPacket
from .packets import PacketReader


##
# Classification of the first byte


def is_ok(payload: bytes) -> bool:
    return payload[0] == 0 and len(payload) >= 7


def is_eof(payload: bytes) -> bool:
    # 0xFE may also begin a length encoded integer, which would be followed by 8 more bytes.
    return payload[0] == 0xFE and len(payload) < 9


def is_err(payload: bytes) -> bool:
    return payload[0] == 0xFF


def is_local_infile(payload: bytes) -> bool:
    return payload[0] == 0xFB


def is_auth_switch(payload: bytes) -> bool:
    return payload[0] == 0xFE


def is_auth_more_data(payload: bytes) -> bool:
    return payload[0] == 0x01


##


def parse_handshake(payload: bytes) -> Handshake:
    r = PacketReader(payload)
    protocol_version = r.read_uint8()
    server_version = r.read_cstring().decode('latin1')
    thread_id = r.read_uint32()
    auth_plugin_data = r.read(8)
    r.skip(1)  # filler
    capabilities = r.read_uint16()

    charset_id: int | None = None
    status_flags = 0
    auth_plugin_data_len = 0
    if r.remaining >= 6:
        charset_id, status_flags, cap_high, auth_plugin_data_len = r.read_struct('<BHHB')
        capabilities |= cap_high << 16
        auth_plugin_data_len = max(12, auth_plugin_data_len - 9)

    if r.remaining >= 10:
        r.skip(10)  # reserved

    if r.remaining >= auth_plugin_data_len:
        auth_plugin_data += r.read(auth_plugin_data_len)
    if r.remaining:
        r.skip(1)  # the trailing NUL of the auth plugin data

    auth_plugin_name = ''
    if r.remaining:
        # Due to Bug#59453 the auth plugin name may be missing its terminating NUL in old versions.
        rest = r.read_all()
        end = rest.find(b'\0')
        auth_plugin_name = (rest if end < 0 else rest[:end]).decode('utf-8')

    return Handshake(
        protocol_version=protocol_version,
        server_version=server_version,
        thread_id=thread_id,
        auth_plugin_data=auth_plugin_data,
        capabilities=capabilities,
        charset_id=charset_id,
        status_flags=status_flags,
        auth_plugin_name=auth_plugin_name,
    )


def parse_ok(payload: bytes) -> OkPacket:
    if not is_ok(payload):
        raise ProtocolError('Not an OK packet')
    r = PacketReader(payload)
    r.skip(1)
    affected_rows = r.read_lenenc_int()
    insert_id = r.read_lenenc_int()
    status_flags, warning_count = r.read_struct('<HH')
    return OkPacket(
        affected_rows=affected_rows or 0,
        insert_id=insert_id or 0,
        status_flags=status_flags,
        warning_count=warning_count,
        message=r.read_all(),
    )


def parse_eof(payload: bytes) -> EofPacket:
    if not is_eof(payload):
        raise ProtocolError('Not an EOF packet')
    warning_count, status_flags = struct.unpack('<xhh', payload[:5])
    return EofPacket(warning_count=warning_count, status_flags=status_flags)


def parse_err(payload: bytes) -> ErrPacket:
    if not is_err(payload):
        raise ProtocolError('Not an ERR packet')
    errno = struct.unpack('<h', payload[1:3])[0]
    # The sqlstate is optional: 5 bytes prefixed by '#'.
    if len(payload) > 3 and payload[3] == 0x23:
        sqlstate: str | None = payload[4:9].decode()
        message = payload[9:].decode('utf-8', 'replace')
    else:
        sqlstate = None
        message = payload[3:].decode('utf-8', 'replace')
    return ErrPacket(errno=errno, sqlstate=sqlstate, message=message)


def parse_auth_switch(payload: bytes) -> AuthSwitchRequest:
    r = PacketReader(payload)
    r.skip(1)
    plugin_name = r.read_cstring().decode('ascii')
    return AuthSwitchRequest(plugin_name=plugin_name, data=r.read_all())


def parse_auth_more_data(payload: bytes) -> AuthMoreData:
    return AuthMoreData(payload[1:])


def parse_local_infile(payload: bytes) -> LocalInfileRequest:
    return LocalInfileRequest(payload[1:])


def parse_column_definition(payload: bytes, encoding: str) -> ColumnDefinition:
    r = PacketReader(payload)
    catalog = r.read_lenenc_str() or b''
    db = r.read_lenenc_str() or b''
    table_name = (r.read_lenenc_str() or b'').decode(encoding)
    org_table = (r.read_lenenc_str() or b'').decode(encoding)
    name = (r.read_lenenc_str() or b'').decode(encoding)
    org_name = (r.read_lenenc_str() or b'').decode(encoding)
    charsetnr, length, type_code, flags, scale = r.read_struct('<xHIBHBxx')
    return ColumnDefinition(
        catalog=catalog,
        db=db,
        table_name=table_name,
        org_table=org_table,
        name=name,
        org_name=org_name,
        charsetnr=charsetnr,
        length=length,
        type_code=type_code,
        flags=flags,
        scale=scale,
    )


def parse_text_row(payload: bytes) -> list[bytes | None]:
    """Parses a text protocol result set row into its raw column values."""

    r = PacketReader(payload)
    values: list[bytes | None] = []
    while r.remaining:
        values.append(r.read_lenenc_str())
    return values
