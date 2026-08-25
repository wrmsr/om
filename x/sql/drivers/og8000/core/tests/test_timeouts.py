"""
Timeout tests. The live-server cases need the harness-provided database; the stalled-peer cases run against sockets
with no server behind them at all.
"""
import asyncio
import socket

import pytest

from omcore.io.pipelines.drivers.sync import SyncSocketIoPipelineDriver

from ...errors import InterfaceError
from ...protocol.session import ProtocolSession
from ..asyncio import AsyncioCoreConnection
from ..handlers import OperationDone
from ..handlers import OperationRequest
from ..handlers import OperationTimeoutsIoPipelineHandler
from ..handlers import make_pipeline_spec
from ..sync import SyncCoreConnection


# An address from a reserved range assumed to blackhole (rather than reject) connection attempts.
UNROUTABLE_HOST = '10.255.255.1'


##
# Validation


@pytest.mark.parametrize('value', [0., -1., float('inf'), float('nan')])
def test_invalid_timeouts(value):
    with pytest.raises(ValueError):  # noqa: PT011
        OperationTimeoutsIoPipelineHandler(read_timeout_s=value)
    with pytest.raises(ValueError):  # noqa: PT011
        OperationTimeoutsIoPipelineHandler(write_timeout_s=value)


##
# Read timeouts, against a live server


def test_read_timeout_sync(db_kwargs):
    con = SyncCoreConnection(**db_kwargs, read_timeout=.15)

    assert con.execute_simple('select 1').rows == [[1]]

    with pytest.raises(InterfaceError, match='Read timed out'):
        con.execute_simple('select pg_sleep(5)')

    # The timeout is fatal to the connection.
    with pytest.raises(InterfaceError):
        con.execute_simple('select 1')


def test_read_timeout_asyncio(db_kwargs):
    async def main():
        con = await AsyncioCoreConnection.connect(**db_kwargs, read_timeout=.15)

        assert (await con.execute_simple('select 1')).rows == [[1]]

        with pytest.raises(InterfaceError, match='Read timed out'):
            await con.execute_simple('select pg_sleep(5)')

        with pytest.raises(InterfaceError):
            await con.execute_simple('select 1')

    asyncio.run(main())


##
# Connect timeouts


def test_connect_timeout_sync(db_kwargs):
    with SyncCoreConnection(**db_kwargs, connect_timeout=10.) as con:
        assert con.execute_simple('select 1').rows == [[1]]


def test_connect_timeout_sync_unreachable():
    with pytest.raises(InterfaceError, match="Can't create a connection"):
        SyncCoreConnection(user='u', host=UNROUTABLE_HOST, connect_timeout=.2)


def test_connect_timeout_asyncio_unreachable():
    async def main():
        with pytest.raises(InterfaceError, match='timed out'):
            await AsyncioCoreConnection.connect(user='u', host=UNROUTABLE_HOST, connect_timeout=.2)

    asyncio.run(main())


##
# Write timeouts, against a peer which never reads


def test_write_timeout_sync():
    sock, peer = socket.socketpair()
    try:
        session = ProtocolSession(user=b'u', startup_params={'user': b'u'})
        driver = SyncSocketIoPipelineDriver(make_pipeline_spec(session, write_timeout=.15), sock)
        try:
            # Far more than the kernel will buffer for us, so the write stalls with the peer not reading.
            op = session.execute_simple('select ' + 'x' * (16 * 1024 * 1024))
            driver.enqueue(OperationRequest(op))
            while not isinstance(driver.next(), OperationDone):
                pass
            with pytest.raises(InterfaceError, match='Write timed out'):
                op.result()
        finally:
            driver.close()
    finally:
        sock.close()
        peer.close()


##
# Timeouts through the SSL stages, against a peer which accepts SSL and then goes silent


def test_read_timeout_through_ssl_sync():
    sock, peer = socket.socketpair()
    try:
        # The reply to the SSLRequest the connection will send: the server agrees to SSL. The TLS handshake then stalls
        # as the peer never sends a ServerHello, and the startup operation's read deadline must catch it.
        peer.sendall(b'S')
        with pytest.raises(InterfaceError, match='Read timed out'):
            SyncCoreConnection(user='u', password='pw', sock=sock, read_timeout=.15)  # noqa: S106
    finally:
        sock.close()
        peer.close()


def test_ssl_handshake_timeout_sync():
    sock, peer = socket.socketpair()
    try:
        # As above, but with only a connect timeout: the TLS handler's own handshake deadline must catch the stall.
        peer.sendall(b'S')
        with pytest.raises(InterfaceError, match='timed out'):
            SyncCoreConnection(user='u', password='pw', sock=sock, connect_timeout=.15)  # noqa: S106
    finally:
        sock.close()
        peer.close()


def test_read_timeout_through_ssl_asyncio():
    async def main():
        sock, peer = socket.socketpair()
        try:
            peer.sendall(b'S')
            sock.setblocking(False)
            reader, writer = await asyncio.open_connection(sock=sock)
            conn = AsyncioCoreConnection(reader, writer, user='u', password='pw', read_timeout=.15)  # noqa: S106
            try:
                with pytest.raises(InterfaceError, match='Read timed out'):
                    await conn._start()  # noqa: SLF001
            finally:
                await conn._driver.close()  # noqa: SLF001
        finally:
            peer.close()

    asyncio.run(main())
