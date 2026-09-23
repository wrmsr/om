# ruff: noqa: UP006 UP007 UP045
import asyncio
import socket
import struct
import typing as ta
import unittest

from ..channels import AsyncioStreamRpcChannel
from ..errors import RpcConnectionClosedError
from ..errors import RpcMethodNotFoundError
from ..errors import RpcProtocolError
from ..errors import RpcRemoteError
from ..handlers import RpcHandler
from ..handlers import RpcMethodHandler
from ..peers import RpcPeer
from .support import memory_rpc_stream_pair


##


def _peer_pair(
        left_handler=None,
        right_handler=None,
        *,
        left_notification_error_handler=None,
        right_notification_error_handler=None,
):
    (left_reader, left_writer), (right_reader, right_writer) = memory_rpc_stream_pair()
    return (
        RpcPeer(
            AsyncioStreamRpcChannel(left_reader, left_writer),
            handler=left_handler,
            notification_error_handler=left_notification_error_handler,
        ),
        RpcPeer(
            AsyncioStreamRpcChannel(right_reader, right_writer),
            handler=right_handler,
            notification_error_handler=right_notification_error_handler,
        ),
    )


class TestRpcPeer(unittest.IsolatedAsyncioTestCase):
    async def test_protocol_failure_closes_peer_and_serve_raises(self) -> None:
        (left_reader, left_writer), (_, right_writer) = memory_rpc_stream_pair()
        left = RpcPeer(AsyncioStreamRpcChannel(left_reader, left_writer))
        serving = asyncio.create_task(left.serve())

        right_writer.write(struct.pack('!I', 1) + b'!')
        with self.assertRaises(RpcProtocolError):
            await serving
        self.assertTrue(left.closed)
        self.assertIsInstance(left.failure, RpcProtocolError)
        right_writer.close()

    async def test_real_asyncio_streams(self) -> None:
        left_socket, right_socket = socket.socketpair()
        left_reader, left_writer = await asyncio.open_connection(sock=left_socket)
        right_reader, right_writer = await asyncio.open_connection(sock=right_socket)

        async def identity(value):
            return value

        left = RpcPeer(AsyncioStreamRpcChannel(left_reader, left_writer))
        right = RpcPeer(
            AsyncioStreamRpcChannel(right_reader, right_writer),
            handler=RpcMethodHandler({'identity': identity}),
        )
        await left.start()
        await right.start()
        try:
            self.assertEqual(await left.call('identity', {'real': 'streams'}), {'real': 'streams'})
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_bidirectional_calls_notifications_and_ping(self) -> None:
        left_notified = asyncio.Event()

        async def left_double(value):
            return value * 2

        async def left_notice(value):
            self.assertEqual(value, 'hello')
            left_notified.set()

        async def right_add(values):
            return sum(values)

        left, right = _peer_pair(
            RpcMethodHandler({'double': left_double, 'notice': left_notice}),
            RpcMethodHandler({'add': right_add}),
        )
        await left.start()
        await right.start()
        try:
            left_result, right_result = await asyncio.gather(
                left.call('add', [2, 3]),
                right.call('double', 6),
            )
            self.assertEqual(left_result, 5)
            self.assertEqual(right_result, 12)

            await right.notify('notice', 'hello')
            await left_notified.wait()

            await asyncio.gather(left.ping(), right.ping())
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_remote_error_does_not_close_connection(self) -> None:
        async def fail(params):
            raise ValueError(f'bad value: {params}')

        async def identity(params):
            return params

        left, right = _peer_pair(
            None,
            RpcMethodHandler({'fail': fail, 'identity': identity}),
        )
        await left.start()
        await right.start()
        try:
            with self.assertRaises(RpcRemoteError) as raised:
                await left.call('fail', 42)
            self.assertEqual(raised.exception.code, 'remote')
            self.assertEqual(raised.exception.remote_type, 'builtins.ValueError')
            self.assertEqual(raised.exception.remote_message, 'bad value: 42')
            self.assertIn('ValueError: bad value: 42', raised.exception.remote_traceback or '')

            with self.assertRaises(RpcRemoteError) as missing:
                await left.call('missing')
            self.assertEqual(missing.exception.code, 'method_not_found')

            self.assertEqual(await left.call('identity', 'still alive'), 'still alive')
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_concurrent_calls_are_correlated(self) -> None:
        started = {1: asyncio.Event(), 2: asyncio.Event()}
        release = {1: asyncio.Event(), 2: asyncio.Event()}

        async def controlled(value):
            started[value].set()
            await release[value].wait()
            return value

        left, right = _peer_pair(None, RpcMethodHandler({'controlled': controlled}))
        await left.start()
        await right.start()
        try:
            first = asyncio.create_task(left.call('controlled', 1))
            second = asyncio.create_task(left.call('controlled', 2))
            await asyncio.gather(started[1].wait(), started[2].wait())

            release[2].set()
            self.assertEqual(await second, 2)
            self.assertFalse(first.done())

            release[1].set()
            self.assertEqual(await first, 1)
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_unencodable_result_is_a_remote_error(self) -> None:
        async def unencodable(params):
            return object()

        async def identity(params):
            return params

        left, right = _peer_pair(
            None,
            RpcMethodHandler({'unencodable': unencodable, 'identity': identity}),
        )
        await left.start()
        await right.start()
        try:
            with self.assertRaises(RpcRemoteError) as raised:
                await left.call('unencodable')
            self.assertEqual(raised.exception.code, 'result_encoding')
            self.assertEqual(await left.call('identity', 42), 42)
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_notification_error_is_reported(self) -> None:
        reported = asyncio.Event()
        errors = []

        async def fail(params):
            raise ValueError(params)

        def on_error(message, error):
            errors.append((message, error))
            reported.set()

        left_with_handler, right_with_handler = _peer_pair(
            None,
            RpcMethodHandler({'fail': fail}),
            right_notification_error_handler=on_error,
        )
        await left_with_handler.start()
        await right_with_handler.start()
        try:
            await left_with_handler.notify('fail', 'notice failed')
            await reported.wait()
            self.assertEqual(len(errors), 1)
            self.assertEqual(str(errors[0][1]), 'notice failed')
            await left_with_handler.ping()
        finally:
            await asyncio.gather(left_with_handler.aclose(), right_with_handler.aclose())

    async def test_in_flight_limit_returns_error(self) -> None:
        started = asyncio.Event()
        release = asyncio.Event()

        async def wait(params):
            started.set()
            await release.wait()
            return params

        (left_reader, left_writer), (right_reader, right_writer) = memory_rpc_stream_pair()
        left = RpcPeer(AsyncioStreamRpcChannel(left_reader, left_writer))
        right = RpcPeer(
            AsyncioStreamRpcChannel(right_reader, right_writer),
            handler=RpcMethodHandler({'wait': wait}),
            max_in_flight=1,
        )
        await left.start()
        await right.start()
        try:
            first = asyncio.create_task(left.call('wait', 1))
            await started.wait()
            with self.assertRaises(RpcRemoteError) as raised:
                await left.call('wait', 2)
            self.assertEqual(raised.exception.code, 'busy')

            release.set()
            self.assertEqual(await first, 1)
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_call_cancellation_cancels_remote_handler(self) -> None:
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def wait_forever(params):
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        left, right = _peer_pair(None, RpcMethodHandler({'wait': wait_forever}))
        await left.start()
        await right.start()
        try:
            call = asyncio.create_task(left.call('wait'))
            await started.wait()
            call.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await call
            await cancelled.wait()
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_close_fails_pending_calls_and_cancels_handlers(self) -> None:
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def wait_forever(params):
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        left, right = _peer_pair(None, RpcMethodHandler({'wait': wait_forever}))
        await left.start()
        await right.start()

        call = asyncio.create_task(left.call('wait'))
        await started.wait()
        await right.aclose()

        with self.assertRaises(RpcConnectionClosedError):
            await call
        await cancelled.wait()
        await left.wait_closed()
        self.assertTrue(left.closed)
        self.assertTrue(right.closed)


##


class _InlineNoteHandler(RpcHandler):
    def __init__(self) -> None:
        super().__init__()

        self.notes: ta.List[ta.Any] = []
        self.fail_on: ta.Any = None

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        if method != 'note':
            return False
        if params == self.fail_on:
            raise ValueError(f'bad note: {params!r}')
        self.notes.append(params)
        return True

    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        if method == 'notes':
            return list(self.notes)
        raise RpcMethodNotFoundError(method)


class TestRpcPeerTeardownAndOrdering(unittest.IsolatedAsyncioTestCase):
    async def _socket_peer_pair(self, right_handler=None):
        left_socket, right_socket = socket.socketpair()
        left_reader, left_writer = await asyncio.open_connection(sock=left_socket)
        right_reader, right_writer = await asyncio.open_connection(sock=right_socket)
        return (
            RpcPeer(AsyncioStreamRpcChannel(left_reader, left_writer)),
            RpcPeer(AsyncioStreamRpcChannel(right_reader, right_writer), handler=right_handler),
        )

    async def test_close_with_in_flight_handler_over_sockets(self) -> None:
        # Closing a socket channel wakes the peer's own receive loop into its teardown before `aclose` gets around to
        # cancelling it; that cancel must not interrupt the teardown, or nothing waiting on the peer is ever released.
        started = asyncio.Event()

        async def wait_forever(params):
            started.set()
            await asyncio.Event().wait()

        left, right = await self._socket_peer_pair(RpcMethodHandler({'wait': wait_forever}))
        await left.start()
        await right.start()

        call = asyncio.create_task(left.call('wait'))
        await started.wait()
        await asyncio.wait_for(right.aclose(), 5.)
        self.assertTrue(right.closed)
        await asyncio.wait_for(right.wait_closed(), 5.)
        with self.assertRaises(RpcConnectionClosedError):
            await asyncio.wait_for(call, 5.)
        await left.aclose()

    async def test_late_pong_to_timed_out_ping_is_ignored(self) -> None:
        (left_reader, left_writer), (right_reader, right_writer) = memory_rpc_stream_pair()
        left = RpcPeer(AsyncioStreamRpcChannel(left_reader, left_writer))
        right = RpcPeer(AsyncioStreamRpcChannel(right_reader, right_writer))
        await left.start()

        # The other side is not serving yet, so its pong can only arrive after the ping has been given up on.
        with self.assertRaises(asyncio.TimeoutError):  # noqa: UP041
            await asyncio.wait_for(left.ping(), .05)
        await right.start()
        await left.ping()
        self.assertFalse(left.closed)
        self.assertIsNone(left.failure)
        await asyncio.gather(left.aclose(), right.aclose())

    async def test_late_result_to_cancelled_call_is_ignored(self) -> None:
        started = asyncio.Event()

        async def stubborn(params):
            # Finishes regardless of cancellation, so its result arrives after the caller has given up on it.
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            return params

        async def identity(params):
            return params

        left, right = _peer_pair(None, RpcMethodHandler({'stubborn': stubborn, 'identity': identity}))
        await left.start()
        await right.start()
        try:
            call = asyncio.create_task(left.call('stubborn', 1))
            await started.wait()
            call.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await call
            self.assertEqual(left.num_outgoing, 0)

            self.assertEqual(await left.call('identity', 2), 2)
            self.assertFalse(left.closed)
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_reply_for_an_id_never_issued_is_a_protocol_error(self) -> None:
        (left_reader, left_writer), (_, right_writer) = memory_rpc_stream_pair()
        left = RpcPeer(AsyncioStreamRpcChannel(left_reader, left_writer))
        serving = asyncio.create_task(left.serve())

        payload = b'{"type":"result","id":7,"result":null}'
        right_writer.write(struct.pack('!I', len(payload)) + payload)
        with self.assertRaises(RpcProtocolError):
            await serving
        right_writer.close()

    async def test_inline_notifications_are_applied_in_wire_order(self) -> None:
        handler = _InlineNoteHandler()
        left, right = _peer_pair(None, handler)
        await left.start()
        await right.start()
        try:
            await left.notify('note', 'a')
            await left.notify('note', 'b')
            # A call sent after the notifications finds them already applied: the stream's order is the delivery order.
            self.assertEqual(await left.call('notes'), ['a', 'b'])
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_inline_notification_error_is_reported_and_survived(self) -> None:
        errors = []
        handler = _InlineNoteHandler()
        handler.fail_on = 'bad'

        (left_reader, left_writer), (right_reader, right_writer) = memory_rpc_stream_pair()
        left = RpcPeer(AsyncioStreamRpcChannel(left_reader, left_writer))
        right = RpcPeer(
            AsyncioStreamRpcChannel(right_reader, right_writer),
            handler=handler,
            notification_error_handler=lambda message, error: errors.append((message, error)),
        )
        await left.start()
        await right.start()
        try:
            await left.notify('note', 'bad')
            await left.notify('note', 'good')
            self.assertEqual(await left.call('notes'), ['good'])
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0][0].params, 'bad')
            self.assertIsInstance(errors[0][1], ValueError)
        finally:
            await asyncio.gather(left.aclose(), right.aclose())

    async def test_close_callbacks_run_before_wait_closed_returns(self) -> None:
        seen: ta.List[ta.Any] = []
        left, right = _peer_pair()
        left.add_close_callback(lambda peer: seen.append(('closed', peer.closed, peer.failure)))
        await left.start()
        await right.start()

        async def wait_and_record():
            await left.wait_closed()
            return list(seen)

        waiter = asyncio.create_task(wait_and_record())
        await right.aclose()
        self.assertEqual(await waiter, [('closed', True, None)])

        left.add_close_callback(lambda peer: seen.append('late'))
        self.assertEqual(seen, [('closed', True, None), 'late'])
        await left.aclose()
