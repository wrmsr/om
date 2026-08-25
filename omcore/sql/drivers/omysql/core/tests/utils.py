"""Support for tests which run against scripted fake servers rather than a real one."""
import socket
import struct

from ...constants import CLIENT
from ...protocol.packets import pack_packet


def make_handshake_packet(*, with_ssl: bool = False) -> bytes:
    """A minimal HandshakeV10, optionally advertising SSL support."""

    caps = (
        CLIENT.LONG_PASSWORD |
        CLIENT.PROTOCOL_41 |
        CLIENT.TRANSACTIONS |
        CLIENT.SECURE_CONNECTION |
        CLIENT.MULTI_RESULTS |
        CLIENT.PLUGIN_AUTH |
        CLIENT.PLUGIN_AUTH_LENENC_CLIENT_DATA |
        CLIENT.CONNECT_ATTRS
    )
    if with_ssl:
        caps |= CLIENT.SSL

    payload = b''.join([
        bytes([10]),                                   # protocol version
        b'8.0.0-test\x00',                             # server version
        struct.pack('<I', 1),                          # thread id
        b'salt5678',                                   # auth plugin data, part 1
        b'\x00',                                       # filler
        struct.pack('<H', caps & 0xffff),              # capabilities, low
        struct.pack('<BHHB', 33, 2, caps >> 16, 21),   # charset, status, capabilities high, auth data length
        b'\x00' * 10,                                  # reserved
        b'salt90123456',                               # auth plugin data, part 2
        b'\x00',
        b'mysql_native_password\x00',
    ])
    return pack_packet(0, payload)


def make_ok_packet(seq: int) -> bytes:
    """A minimal OK packet: nothing affected, autocommit status."""

    return pack_packet(seq, b'\x00\x00\x00\x02\x00\x00\x00')


def tcp_socketpair() -> tuple[socket.socket, socket.socket]:
    """An AF_INET socketpair, as AF_UNIX sockets are treated as secure transports which never attempt SSL."""

    with socket.create_server(('127.0.0.1', 0)) as server:
        client = socket.create_connection(server.getsockname())
        conn, _ = server.accept()
    return client, conn
