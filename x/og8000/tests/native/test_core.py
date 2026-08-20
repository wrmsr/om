from io import BytesIO

import pytest

from ...core import NULL_BYTE
from ...core import PASSWORD
from ...core import Context
from ...core import CoreConnection
from ...core import _create_message
from ...core import _make_socket
from ...core import _read
from ...native import InterfaceError


def test_make_socket(mocker):
    unix_sock = None
    sock = mocker.Mock()
    host = 'localhost'
    port = 5432
    timeout = None
    source_address = None
    tcp_keepalive = True
    ssl_context = None
    _make_socket(
        unix_sock, sock, host, port, timeout, source_address, tcp_keepalive, ssl_context,
    )


def test_handle_AUTHENTICATION_3(mocker):
    """Shouldn't send a FLUSH message, as FLUSH only used in extended-query"""

    mocker.patch.object(CoreConnection, '__init__', lambda x: None)
    con = CoreConnection()
    password = 'barbour'.encode('utf8')
    con.password = password
    con._sock = mocker.Mock()
    buf = BytesIO()
    con._sock.write = buf.write
    CoreConnection.handle_AUTHENTICATION_REQUEST(con, b'\x00\x00\x00\x03', None)
    assert buf.getvalue() == _create_message(PASSWORD, password + NULL_BYTE)


def test_create_message():
    msg = _create_message(PASSWORD, 'barbour'.encode('utf8') + NULL_BYTE)
    assert msg == b'p\x00\x00\x00\x0cbarbour\x00'


def test_handle_ERROR_RESPONSE(mocker):
    """Check it handles invalid encodings in the error messages"""

    mocker.patch.object(CoreConnection, '__init__', lambda x: None)
    con = CoreConnection()
    con._client_encoding = 'utf8'
    data = b'S\xc2err' + NULL_BYTE + NULL_BYTE
    context = Context(None)
    CoreConnection.handle_ERROR_RESPONSE(con, data, context)
    assert str(context.error) == "{'S': '�err'}"


def test_read(mocker):
    mock_socket = mocker.Mock()
    mock_socket.read = mocker.Mock(return_value=b'')
    with pytest.raises(InterfaceError, match='network error'):
        _read(mock_socket, 5)
