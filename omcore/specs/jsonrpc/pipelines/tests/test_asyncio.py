import asyncio
import contextlib
import socket
import sys
import time
import typing as ta

import pytest

from .....io.pipelines import all as ipl
from ...dispatch import AsyncDictJsonrpcDispatcher
from ...dispatch import JsonrpcMethod
from ...errors import SERVER_SHUTTING_DOWN_ERROR_CODE
from ...errors import JsonrpcConnectionClosedError
from ...errors import JsonrpcRemoteError
from ...errors import JsonrpcTimeoutError
from ...errors import KnownErrors
from ...types import NotSpecified
from ...types import Request
from ...types import notification
from ...types import request
from ..asyncio import AsyncioJsonrpcConnection
from ..asyncio import AsyncioJsonrpcConnections
from ..configs import JsonrpcPipelineConfig
from .echoserver import build_dispatcher


TIMEOUT_S = 10.


@contextlib.asynccontextmanager
async def pair(
        config_a: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
        config_b: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
        *,
        kwargs_a: ta.Mapping[str, ta.Any] | None = None,
        kwargs_b: ta.Mapping[str, ta.Any] | None = None,
) -> ta.AsyncIterator[tuple[AsyncioJsonrpcConnection, AsyncioJsonrpcConnection]]:
    sa, sb = socket.socketpair()
    ra, wa = await asyncio.open_connection(sock=sa)
    rb, wb = await asyncio.open_connection(sock=sb)

    a = AsyncioJsonrpcConnections.of_streams(ra, wa, config_a, **(kwargs_a or {}))
    b = AsyncioJsonrpcConnections.of_streams(rb, wb, config_b, **(kwargs_b or {}))

    try:
        await a.start()
        await b.start()
        yield a, b
    finally:
        # Abortive, so a test which leaves a slow handler running does not wait for it to drain.
        await b.close(graceful=False)
        await a.close(graceful=False)
        wa.close()
        wb.close()


def run(coro):
    async def with_timeout():
        async with asyncio.timeout(TIMEOUT_S):
            await coro
    asyncio.run(with_timeout())


##


def test_request_response():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            assert await a.request('add', {'a': 1, 'b': 2}) == 3
            assert await a.request('add', [3, 4]) == 7
            assert await a.request('echo', {'x': [1, {'y': None}]}) == {'x': [1, {'y': None}]}

    run(go())


def test_remote_error():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            with pytest.raises(JsonrpcRemoteError) as ei:
                await a.request('fail')
            assert ei.value.code == 1234
            assert ei.value.message == 'nope'
            assert ei.value.data == {'why': 'because'}

            with pytest.raises(JsonrpcRemoteError) as ei:
                await a.request('boom')
            assert ei.value.code == KnownErrors.INTERNAL_ERROR.code
            assert ei.value.data is NotSpecified  # details withheld by default

            with pytest.raises(JsonrpcRemoteError) as ei:
                await a.request('nope')
            assert ei.value.code == KnownErrors.METHOD_NOT_FOUND.code

            with pytest.raises(JsonrpcRemoteError) as ei:
                await a.request('add', {'a': 1})
            assert ei.value.code == KnownErrors.INVALID_PARAMS.code

            # The connection is still fine.
            assert await a.request('add', [1, 1]) == 2

    run(go())


def test_no_dispatcher_answers_method_not_found():
    async def go():
        async with pair() as (a, b):
            with pytest.raises(JsonrpcRemoteError) as ei:
                await a.request('anything')
            assert ei.value.code == KnownErrors.METHOD_NOT_FOUND.code

    run(go())


def test_bidirectional_callback():
    async def go():
        client_d = AsyncDictJsonrpcDispatcher({'double': lambda value: value * 2})
        async with pair(
                kwargs_a=dict(dispatcher=client_d),
                kwargs_b=dict(dispatcher=build_dispatcher()),
        ) as (a, b):
            assert await a.request('callback', {'value': 21}) == 42

    run(go())


def test_concurrent_requests():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            results = await asyncio.gather(*[a.request('add', [i, i]) for i in range(50)])
            assert results == [i * 2 for i in range(50)]

    run(go())


def test_notifications():
    async def go():
        got: list[Request] = []
        got_event = asyncio.Event()

        async def on_note(conn, note):
            got.append(note)
            if len(got) == 3:
                got_event.set()

        async with pair(kwargs_b=dict(notification_handler=on_note)) as (a, b):
            for i in range(3):
                await a.notify('tick', {'i': i})
            await got_event.wait()
            assert [dict(n.params or {})['i'] for n in got] == [0, 1, 2]

    run(go())


def test_request_timeout():
    async def go():
        async with pair(
                JsonrpcPipelineConfig(default_request_timeout_s=.2),
                kwargs_b=dict(dispatcher=build_dispatcher()),
        ) as (a, b):
            with pytest.raises(JsonrpcTimeoutError):
                await a.request('sleep', [5.])
            assert not a.is_closed
            assert await a.request('add', [1, 2]) == 3
            assert await a.request('sleep', [.01], timeout_s=None) == 'slept'

    run(go())


def test_inbound_handling_timeout_cancels_handler():
    async def go():
        cancelled = asyncio.Event()

        async def slow():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        async with pair(
                kwargs_b=dict(
                    dispatcher=AsyncDictJsonrpcDispatcher({'slow': slow}),
                ),
                config_b=JsonrpcPipelineConfig(inbound_handling_timeout_s=.2),
        ) as (a, b):
            with pytest.raises(JsonrpcRemoteError):
                await a.request('slow')
            await asyncio.wait_for(cancelled.wait(), 2.)

    run(go())


def test_caller_cancellation_cancels_request():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            t = asyncio.create_task(a.request('sleep', [5.]))
            await asyncio.sleep(.05)
            t.cancel()
            with pytest.raises(asyncio.CancelledError):
                await t
            assert not a.is_closed
            assert await a.request('add', [1, 2]) == 3

    run(go())


def test_graceful_close_from_client():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            assert await a.request('add', [1, 2]) == 3
            await a.close()
            assert a.is_closed
            assert a.close_exception is None
            await asyncio.wait_for(b.wait_closed(), 2.)
            assert b.is_closed
            assert b.close_exception is None

            with pytest.raises(JsonrpcConnectionClosedError):
                await a.request('add', [1, 2])

    run(go())


def test_peer_abortive_close_answers_inflight():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            t = asyncio.create_task(a.request('sleep', [5.]))
            await asyncio.sleep(.05)
            await b.close(graceful=False)
            # The aborting side answers what it had in flight before closing.
            with pytest.raises(JsonrpcRemoteError) as ei:
                await t
            assert ei.value.code == SERVER_SHUTTING_DOWN_ERROR_CODE
            await asyncio.wait_for(a.wait_closed(), 2.)


def test_peer_abortive_close_without_answering_fails_pending():
    async def go():
        async with pair(
                kwargs_b=dict(dispatcher=build_dispatcher()),
                config_b=JsonrpcPipelineConfig(respond_to_aborted_inbound=False),
        ) as (a, b):
            t = asyncio.create_task(a.request('sleep', [5.]))
            await asyncio.sleep(.05)
            await b.close(graceful=False)
            with pytest.raises(JsonrpcConnectionClosedError):
                await t
            await asyncio.wait_for(a.wait_closed(), 2.)

    run(go())


def test_server_shutdown_method():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            assert await a.request('shutdown') == 'bye'
            await asyncio.wait_for(a.wait_closed(), 2.)
            assert a.is_closed

    run(go())


def test_transport_abort():
    async def go():
        sa, sb = socket.socketpair()
        ra, wa = await asyncio.open_connection(sock=sa)
        a = AsyncioJsonrpcConnections.of_streams(ra, wa)
        async with a:
            t = asyncio.create_task(a.request('x'))
            await asyncio.sleep(.05)
            sb.close()
            with pytest.raises(JsonrpcConnectionClosedError):
                await t
            await asyncio.wait_for(a.wait_closed(), 2.)
        wa.close()

    run(go())


def test_unstarted_close():
    async def go():
        sa, sb = socket.socketpair()
        ra, wa = await asyncio.open_connection(sock=sa)
        a = AsyncioJsonrpcConnections.of_streams(ra, wa)
        await a.close()
        assert a.is_closed
        wa.close()
        sb.close()

    run(go())


def test_send_batch():
    async def go():
        async with pair(kwargs_b=dict(dispatcher=build_dispatcher())) as (a, b):
            resps = await a.send_batch([
                request(100, 'add', [1, 2]),
                request(101, 'fail'),
                notification('tick'),
            ])
            assert resps[0] is not None and resps[0].result == 3
            assert resps[1] is not None and resps[1].is_error
            assert resps[2] is None

    run(go())


def test_backpressure_pause_resume():
    async def go():
        # A tiny write watermark and a peer which never reads: sends must block rather than buffer without bound.
        sa, sb = socket.socketpair()
        ra, wa = await asyncio.open_connection(sock=sa)
        a = AsyncioJsonrpcConnections.of_streams(
            ra,
            wa,
            JsonrpcPipelineConfig(write_timeout_s=.5),
            driver_config=ipl.PollAsyncioStreamDriver.Config(write_high_watermark=4096, write_low_watermark=1024),
            send_timeout_s=.3,
        )

        async def flood():
            big = {'x': 'y' * 10000}
            for _ in range(200):
                await a.notify('n', big)

        await a.start()
        with pytest.raises(JsonrpcTimeoutError):
            await flood()

        # Closing against a peer which never reads is bounded by the write timeout, then aborted.
        t0 = time.monotonic()
        await a.close(graceful=False)
        assert time.monotonic() - t0 < 5.
        assert a.is_closed
        wa.close()
        sb.close()

    run(go())


##


@pytest.mark.skipif(sys.platform == 'win32', reason='posix only')
def test_subprocess_stdio():
    async def go():
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            '-m', __package__ + '.echoserver',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        try:
            conn = AsyncioJsonrpcConnections.of_subprocess(
                proc,
                dispatcher=AsyncDictJsonrpcDispatcher({'double': JsonrpcMethod(lambda value: value * 2)}),
            )
            async with conn:
                assert await conn.request('add', {'a': 2, 'b': 3}) == 5
                assert await conn.request('callback', {'value': 4}) == 8
                with pytest.raises(JsonrpcRemoteError):
                    await conn.request('fail')
                await conn.close()

            await asyncio.wait_for(proc.wait(), 5.)
            assert proc.returncode == 0

        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()

    run(go())
