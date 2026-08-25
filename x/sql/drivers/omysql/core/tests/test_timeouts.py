"""
Timeout tests. The live-server cases need the harness-provided database; the stalled-peer cases run against sockets
with no real server behind them at all.
"""
import asyncio
import socket

import pytest

from omcore.io.pipelines.drivers.sync import SyncSocketIoPipelineDriver

from ...errors import Error
from ...errors import OperationalError
from ...protocol.session import ProtocolSession
from ..asyncio import AsyncioConnection
from ..handlers import OperationDone
from ..handlers import OperationRequest
from ..handlers import OperationTimeoutsIoPipelineHandler
from ..handlers import make_pipeline_spec
from ..sync import SyncConnection
from .utils import make_handshake_packet
from .utils import tcp_socketpair


# An address from a reserved range assumed to blackhole (rather than reject) connection attempts.
UNROUTABLE_HOST = '10.255.255.1'


def _kwargs(db, **over):
    params = {k: v for k, v in db.items() if k not in ('use_unicode', 'local_infile')}
    params['password'] = params.pop('passwd', '')
    params.update(over)
    return params


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


def test_read_timeout_sync(databases):
    con = SyncConnection(**_kwargs(databases[0], read_timeout=.15))
    try:
        con.query('select 1')
        assert con.result is not None and con.result.rows == ((1,),)

        with pytest.raises(OperationalError, match='Read timed out'):
            con.query('select sleep(5)')

        # The timeout is fatal to the connection.
        with pytest.raises(Error):
            con.query('select 1')
    finally:
        if con.open:
            con.close()


def test_read_timeout_asyncio(databases):
    async def main():
        con = await AsyncioConnection.connect(**_kwargs(databases[0], read_timeout=.15))
        try:
            await con.query('select 1')
            assert con.result is not None and con.result.rows == ((1,),)

            with pytest.raises(OperationalError, match='Read timed out'):
                await con.query('select sleep(5)')

            with pytest.raises(Error):
                await con.query('select 1')
        finally:
            if con.open:
                await con.close()

    asyncio.run(main())


##
# Connect timeouts


def test_connect_timeout_sync(databases):
    con = SyncConnection(**_kwargs(databases[0], connect_timeout=10.))
    try:
        con.query('select 1')
        assert con.result is not None and con.result.rows == ((1,),)
    finally:
        con.close()


def test_connect_timeout_sync_unreachable():
    with pytest.raises(OperationalError, match="Can't connect"):
        SyncConnection(user='u', host=UNROUTABLE_HOST, connect_timeout=.2)


def test_connect_timeout_asyncio_unreachable():
    async def main():
        with pytest.raises(OperationalError, match='timed out'):
            await AsyncioConnection.connect(user='u', host=UNROUTABLE_HOST, connect_timeout=.2)

    asyncio.run(main())


##
# Write timeouts, against a peer which never reads


def test_write_timeout_sync():
    sock, peer = socket.socketpair()
    try:
        session = ProtocolSession(user=b'u')
        driver = SyncSocketIoPipelineDriver(make_pipeline_spec(session, write_timeout=.15), sock)
        try:
            # Far more than the kernel will buffer for us, so the write stalls with the peer not reading.
            op = session.query(b'select ' + b'x' * (16 * 1024 * 1024))
            driver.enqueue(OperationRequest(op))
            while not isinstance(driver.next(), OperationDone):
                pass
            with pytest.raises(OperationalError, match='Write timed out'):
                op.result()
        finally:
            driver.close()
    finally:
        sock.close()
        peer.close()


##
# Timeouts through the SSL stages, against a peer which advertises SSL and then goes silent


def test_read_timeout_through_ssl_sync():
    client, server = tcp_socketpair()
    try:
        # The client reads this handshake, agrees to SSL, and starts a TLS handshake which then stalls as the peer
        # never sends a ServerHello. The authentication operation's read deadline must catch it.
        server.sendall(make_handshake_packet(with_ssl=True))
        with pytest.raises(OperationalError, match='Read timed out'):
            SyncConnection(user='u', password='p', sock=client, read_timeout=.15)  # noqa: S106
    finally:
        client.close()
        server.close()


def test_ssl_handshake_timeout_sync():
    client, server = tcp_socketpair()
    try:
        # As above, but with only a connect timeout: the TLS handler's own handshake deadline must catch the stall.
        server.sendall(make_handshake_packet(with_ssl=True))
        with pytest.raises(OperationalError, match='timed out'):
            SyncConnection(user='u', password='p', sock=client, connect_timeout=.15)  # noqa: S106
    finally:
        client.close()
        server.close()


def test_read_timeout_through_ssl_asyncio():
    async def main():
        client, server = tcp_socketpair()
        try:
            server.sendall(make_handshake_packet(with_ssl=True))
            client.setblocking(False)
            reader, writer = await asyncio.open_connection(sock=client)
            conn = AsyncioConnection(reader, writer, user='u', password='p', read_timeout=.15)  # noqa: S106
            try:
                with pytest.raises(OperationalError, match='Read timed out'):
                    await conn._start()  # noqa: SLF001
            finally:
                await conn._driver.close()  # noqa: SLF001
        finally:
            server.close()

    asyncio.run(main())
