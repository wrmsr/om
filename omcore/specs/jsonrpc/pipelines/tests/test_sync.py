import socket
import subprocess
import sys
import threading
import time

import pytest

from ...dispatch import DictJsonrpcDispatcher
from ...dispatch import JsonrpcDispatchContext
from ...dispatch import JsonrpcMethod
from ...errors import JsonrpcConnectionClosedError
from ...errors import JsonrpcRemoteError
from ...errors import JsonrpcTimeoutError
from ...errors import KnownErrors
from ...types import notification
from ...types import request
from ..configs import JsonrpcPipelineConfig
from ..sync import SyncJsonrpcConnection
from ..sync import SyncJsonrpcConnections


def _sync_dispatcher() -> DictJsonrpcDispatcher:
    def add(a: int, b: int) -> int:
        return a + b

    def callback(ctx: JsonrpcDispatchContext, value: int) -> int:
        # A handler calling back into the peer, from inside the pump.
        conn: SyncJsonrpcConnection = ctx.connection
        return conn.request('double', {'value': value})

    def slow(s: float) -> str:
        time.sleep(s)
        return 'slept'

    def boom() -> None:
        raise RuntimeError('boom')

    return DictJsonrpcDispatcher({
        'add': add,
        'callback': JsonrpcMethod(callback, with_context=True),
        'slow': slow,
        'boom': boom,
        'double': lambda value: value * 2,
    })


def _is_closed(conn: SyncJsonrpcConnection) -> bool:
    return conn.is_closed


##
# sync <-> asyncio subprocess over stdio


@pytest.mark.skipif(sys.platform == 'win32', reason='posix only')
def test_subprocess_stdio():
    proc = subprocess.Popen(
        [sys.executable, '-m', __package__ + '.echoserver'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    try:
        conn = SyncJsonrpcConnections.of_subprocess(
            proc,
            JsonrpcPipelineConfig(default_request_timeout_s=10.),
            dispatcher=_sync_dispatcher(),
        )
        with conn:
            assert conn.request('add', {'a': 2, 'b': 3}) == 5
            assert conn.request('add', [4, 5]) == 9
            assert conn.request('echo', {'x': 1}) == {'x': 1}

            # The server calls back into us while we wait for its response.
            assert conn.request('callback', {'value': 21}) == 42

            with pytest.raises(JsonrpcRemoteError) as ei:
                conn.request('fail')
            assert ei.value.code == 1234

            with pytest.raises(JsonrpcTimeoutError):
                conn.request('sleep', [5.], timeout_s=.2)
            assert not conn.is_closed

            conn.notify('nothing')
            assert conn.request('add', [1, 1]) == 2

            resps = conn.send_batch([request(100, 'add', [1, 2]), notification('n'), request(101, 'fail')])
            assert resps[0] is not None and resps[0].result == 3
            assert resps[1] is None
            assert resps[2] is not None and resps[2].is_error

        assert _is_closed(conn)
        # Closing the connection closed the child's stdin, so it exits on its own.
        assert proc.wait(timeout=5.) == 0

    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


##
# sync <-> sync over a socketpair, one thread per side


class _Peer(threading.Thread):
    """Runs a sync connection on its own thread, serving until closed."""

    def __init__(self, sock: socket.socket, **kwargs) -> None:
        super().__init__(daemon=True)
        self.conn = SyncJsonrpcConnections.of_socket(sock, **kwargs)
        self.error: BaseException | None = None

    def run(self) -> None:
        try:
            with self.conn:
                self.conn.serve()
        except BaseException as e:  # noqa
            self.error = e


def test_sync_pair():
    sa, sb = socket.socketpair()
    server = _Peer(sb, dispatcher=_sync_dispatcher())
    server.start()

    conn = SyncJsonrpcConnections.of_socket(sa, dispatcher=_sync_dispatcher())
    with conn:
        assert conn.request('add', [1, 2]) == 3
        assert conn.request('callback', {'value': 4}) == 8

        with pytest.raises(JsonrpcRemoteError) as ei:
            conn.request('boom')
        assert ei.value.code == KnownErrors.INTERNAL_ERROR.code

        with pytest.raises(JsonrpcRemoteError) as ei:
            conn.request('nope')
        assert ei.value.code == KnownErrors.METHOD_NOT_FOUND.code

        with pytest.raises(JsonrpcTimeoutError):
            conn.request('slow', [2.], timeout_s=.2)

    server.join(5.)
    assert not server.is_alive()
    assert server.error is None
    assert server.conn.is_closed


def test_peer_disappears():
    sa, sb = socket.socketpair()
    conn = SyncJsonrpcConnections.of_socket(sa)
    with conn:
        # Close the far side while a request is pending.
        def later():
            time.sleep(.1)
            sb.close()
        threading.Thread(target=later, daemon=True).start()
        with pytest.raises(JsonrpcConnectionClosedError):
            conn.request('x')


def test_cross_thread_use_refused():
    sa, sb = socket.socketpair()
    server = _Peer(sb, dispatcher=_sync_dispatcher())
    server.start()

    conn = SyncJsonrpcConnections.of_socket(sa, dispatcher=DictJsonrpcDispatcher({
        'hold': lambda: time.sleep(.3),
    }))
    with conn:
        errors: list[BaseException] = []

        def intruder():
            try:
                conn.request('add', [1, 1])
            except BaseException as e:  # noqa
                errors.append(e)

        # Occupy the connection from this thread via a request whose handler on the far side calls back to us,
        # keeping us inside the pump, while another thread tries to use it.
        t = threading.Thread(target=intruder)

        def double(value: int) -> int:
            t.start()
            t.join()
            return value * 2

        conn._dispatcher = DictJsonrpcDispatcher({'double': double})  # noqa
        assert conn.request('callback', {'value': 1}) == 2
        assert len(errors) == 1
        assert isinstance(errors[0], RuntimeError)

    server.join(5.)


def test_close_with_unread_peer_is_bounded():
    sa, sb = socket.socketpair()
    conn = SyncJsonrpcConnections.of_socket(sa, JsonrpcPipelineConfig(write_timeout_s=.3))
    with conn:
        pass
    # Clean close of an idle connection completes without waiting on the peer.
    assert conn.is_closed
    sb.close()
