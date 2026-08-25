"""Live tests of the sync and async MySQL connections against the server described by tests/dbs.py."""
import asyncio
import socket

import pytest

from ...errors import InterfaceError
from ...errors import OperationalError
from ..asyncio import AsyncioConnection
from ..sync import SyncConnection
from .utils import make_handshake_packet
from .utils import make_ok_packet


def _kwargs(db, **over):
    params = {k: v for k, v in db.items() if k not in ('use_unicode', 'local_infile')}
    params['password'] = params.pop('passwd', '')
    params.update(over)
    return params


def test_sync_ssl_connect(databases):
    con = SyncConnection(**_kwargs(databases[0]))
    try:
        assert con.is_ssl
        con.query('select 1')
        assert con.result is not None and con.result.rows == ((1,),)
    finally:
        con.close()


def test_sync_no_ssl_connect(databases):
    con = SyncConnection(**_kwargs(databases[0], ssl_disabled=True))
    try:
        assert not con.is_ssl
        con.query('select 2')
        assert con.result is not None and con.result.rows == ((2,),)
    finally:
        con.close()


def test_sync_bad_password(databases):
    with pytest.raises(OperationalError):
        SyncConnection(**_kwargs(databases[0], password='definitely-wrong'))  # noqa: S106


def test_async_ssl_connect(databases):
    async def main():
        con = await AsyncioConnection.connect(**_kwargs(databases[0]))
        try:
            assert con.is_ssl
            await con.query('select 1')
            assert con.result is not None and con.result.rows == ((1,),)
        finally:
            await con.close()

    asyncio.run(main())


def test_async_queries_and_unbuffered(databases):
    async def main():
        async with await AsyncioConnection.connect(**_kwargs(databases[0])) as con:
            await con.query('drop table if exists og_async_t')
            await con.query('create temporary table og_async_t (a int)')
            await con.query('insert into og_async_t values (1),(2),(3)')
            await con.query('select a from og_async_t order by a')
            assert con.result is not None and con.result.rows == ((1,), (2,), (3,))

            await con.query('select a from og_async_t order by a', unbuffered=True)
            rows = []
            while (row := await con.fetch_unbuffered_row()) is not None:
                rows.append(row)
            assert rows == [(1,), (2,), (3,)]

    asyncio.run(main())


##
# Closing after the server disconnects


def test_close_after_clean_disconnect_sync():
    """A server which disconnects cleanly (EOF, not a reset) must not break a subsequent close()."""

    sock, peer = socket.socketpair()
    try:
        # A scripted handshake and authentication OK. The OK carries the next inbound sequence number, since it is
        # decoded before the client's own numbered response goes out, and sits in the session handler's pending queue
        # until the authentication operation begins. The unix socketpair counts as a secure transport, so no SSL is
        # attempted.
        peer.sendall(make_handshake_packet())
        peer.sendall(make_ok_packet(1))

        con = SyncConnection(user='u', password='p', sock=sock)  # noqa: S106

        # A clean EOF (not a reset), with the peer still accepting writes.
        peer.shutdown(socket.SHUT_WR)
        with pytest.raises(InterfaceError, match='Lost connection'):
            con.query('select 1')
        con.close()
        assert not con.open
    finally:
        sock.close()
        peer.close()


def test_close_after_clean_disconnect_asyncio():
    async def main():
        sock, peer = socket.socketpair()
        try:
            peer.sendall(make_handshake_packet())
            peer.sendall(make_ok_packet(1))
            sock.setblocking(False)

            reader, writer = await asyncio.open_connection(sock=sock)
            con = AsyncioConnection(reader, writer, user='u', password='p')  # noqa: S106
            con._mark_secure_transport()  # noqa: SLF001
            await con._start()  # noqa: SLF001

            peer.shutdown(socket.SHUT_WR)
            with pytest.raises(InterfaceError, match='Lost connection'):
                await con.query('select 1')
            await con.close()
            assert not con.open
        finally:
            peer.close()

    asyncio.run(main())
