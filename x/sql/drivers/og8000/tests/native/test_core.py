import socket

import pytest

from ...core.sockets import connect_socket
from ...errors import InterfaceError


def test_connect_socket_passes_through_given_socket():
    client, server = socket.socketpair()
    with client, server:
        assert connect_socket(sock=client) is client


def test_connect_socket_rejects_sock_with_unix_sock():
    client, server = socket.socketpair()
    with client, server, pytest.raises(InterfaceError, match='sock must be None'):
        connect_socket(unix_sock='/x', sock=client)


def test_connect_socket_missing_unix_socket():
    with pytest.raises(InterfaceError, match='communication error'):
        connect_socket(unix_sock='/file-does-not-exist')


def test_connect_socket_requires_a_target():
    with pytest.raises(InterfaceError, match='one of host, sock or unix_sock'):
        connect_socket()
