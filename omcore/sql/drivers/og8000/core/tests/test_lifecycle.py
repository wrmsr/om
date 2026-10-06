import socket

import pytest

from ...errors import InterfaceError
from ..sync import SyncCoreConnection


##


AUTH_OK = b'R\x00\x00\x00\x08\x00\x00\x00\x00'
READY_FOR_QUERY = b'Z\x00\x00\x00\x05I'


@pytest.mark.parametrize('use_context_manager', [False, True])
def test_sync_close_releases_socket(use_context_manager):
    sock, peer = socket.socketpair()
    with sock, peer:
        peer.sendall(AUTH_OK + READY_FOR_QUERY)
        con = SyncCoreConnection(user='u', sock=sock, ssl_context=False)

        if use_context_manager:
            with con:
                assert sock.fileno() >= 0
        else:
            con.close()

        # Keep the connection and socket alive: releasing the descriptor must not depend on garbage collection.
        assert con.is_closed
        assert sock.fileno() == -1
        with pytest.raises(InterfaceError, match='closed'):
            con.close()


@pytest.mark.parametrize('failed', [False, True])
def test_sync_close_releases_socket_after_driver_stops(failed):
    sock, peer = socket.socketpair()
    with sock, peer:
        peer.sendall(AUTH_OK + READY_FOR_QUERY)
        con = SyncCoreConnection(user='u', sock=sock, ssl_context=False)

        if failed:
            con._driver._fail()  # noqa: SLF001
        else:
            con._driver.close()  # noqa: SLF001

        assert con.is_closed
        assert sock.fileno() >= 0
        with pytest.raises(InterfaceError, match='closed'):
            con.close()
        assert sock.fileno() == -1


def test_sync_startup_failure_releases_socket():
    sock, peer = socket.socketpair()
    with sock, peer:
        peer.sendall(b'N')
        with pytest.raises(InterfaceError, match='Server refuses SSL'):
            SyncCoreConnection(user='u', sock=sock, ssl_context=True)
        assert sock.fileno() == -1


def test_sync_pipeline_construction_failure_releases_socket():
    sock, peer = socket.socketpair()
    with sock, peer:
        with pytest.raises(ValueError, match=r'^0\.0$'):
            SyncCoreConnection(
                user='u',
                sock=sock,
                ssl_context=False,
                read_timeout=0.,
            )
        assert sock.fileno() == -1


def test_sync_driver_close_failure_releases_socket(monkeypatch):
    sock, peer = socket.socketpair()
    with sock, peer:
        peer.sendall(AUTH_OK + READY_FOR_QUERY)
        con = SyncCoreConnection(user='u', sock=sock, ssl_context=False)
        driver = con._driver  # noqa: SLF001
        close_driver = driver.close

        def failing_close():
            close_driver()
            raise RuntimeError('driver cleanup failed')

        # Inject a teardown error at the ownership boundary, after the driver has released its pipeline resources.
        monkeypatch.setattr(driver, 'close', failing_close)
        with pytest.raises(RuntimeError, match='driver cleanup failed'):
            con.close()
        assert sock.fileno() == -1
