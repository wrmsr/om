# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
"""Connection behavior over the deterministic pure link: both ends in one thread, on one virtual clock."""
import typing as ta
import unittest

from ...asyncs.asynclite.promises import AsynclitePromiseWaitTimeoutError
from ...lite.asyncs import sync_await
from ..configs import RpcConfig
from ..connection import RpcConnection
from ..dispatch import RpcHandler
from ..dispatch import RpcMethodTableHandler
from ..dispatch import rpc_async_method
from ..errors import RpcConnectionClosedError
from ..errors import RpcErrorCodes
from ..errors import RpcRemoteError
from ..errors import RpcRemoteMethodNotFoundError
from ..errors import RpcTimeoutError
from ..ids import UuidRpcIdCreator
from ..messages import RpcNotificationMessage
from ..pure import PureRpcLinkDeadlockError
from ..pure import pure_rpc_connection_pair


##


def _raise_value_error(p: ta.Any) -> ta.Any:
    raise ValueError(f'bad {p}')


def _echo_table(**extra: ta.Any) -> RpcMethodTableHandler:
    return RpcMethodTableHandler({
        'echo': rpc_async_method(lambda p: p),
        'fail': rpc_async_method(_raise_value_error),
        **extra,
    })


class TestBasics(unittest.TestCase):
    def test_roundtrip(self):
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=_echo_table()))
        for v in [None, 1, 2.5, 'x', [1, [2]], {'a': {'b': None}}, True]:
            self.assertEqual(pair.a.request('echo', v), v)
        for i in range(200):
            self.assertEqual(pair.a.request('echo', i), i)
        self.assertEqual(pair.link.now, 0.)

    def test_symmetric(self):
        pair = pure_rpc_connection_pair(
            a_kwargs=dict(handler=_echo_table()),
            b_kwargs=dict(handler=_echo_table()),
        )
        self.assertEqual(pair.a.request('echo', 'from a'), 'from a')
        self.assertEqual(pair.b.request('echo', 'from b'), 'from b')

    def test_remote_error(self):
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=_echo_table()))
        with self.assertRaises(RpcRemoteError) as cm:
            pair.a.request('fail', 3)
        e = cm.exception
        self.assertEqual(e.code, RpcErrorCodes.REMOTE)
        self.assertEqual(e.remote_type, 'builtins.ValueError')
        self.assertEqual(e.remote_message, 'bad 3')
        self.assertIn('_raise_value_error', e.remote_traceback or '')

        # The connection survives handler errors.
        self.assertEqual(pair.a.request('echo', 1), 1)

    def test_traceback_policy(self):
        pair = pure_rpc_connection_pair(
            b_config=RpcConfig(include_tracebacks=False),
            b_kwargs=dict(handler=_echo_table()),
        )
        with self.assertRaises(RpcRemoteError) as cm:
            pair.a.request('fail', 1)
        self.assertIsNone(cm.exception.remote_traceback)

        pair = pure_rpc_connection_pair(
            b_config=RpcConfig(max_traceback_chars=20),
            b_kwargs=dict(handler=_echo_table()),
        )
        with self.assertRaises(RpcRemoteError) as cm:
            pair.a.request('fail', 1)
        tb = cm.exception.remote_traceback or ''
        self.assertEqual(len(tb), 20)
        self.assertTrue(tb.endswith('ValueError: bad 1\n'))

    def test_method_not_found(self):
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=_echo_table()))
        with self.assertRaises(RpcRemoteMethodNotFoundError) as cm:
            pair.a.request('nope')
        self.assertEqual(cm.exception.code, RpcErrorCodes.METHOD_NOT_FOUND)

        pair = pure_rpc_connection_pair()
        with self.assertRaises(RpcRemoteMethodNotFoundError):
            pair.a.request('nope')

    def test_set_handler_late(self):
        pair = pure_rpc_connection_pair()
        with self.assertRaises(RpcRemoteMethodNotFoundError):
            pair.a.request('echo', 1)
        pair.b.set_handler(_echo_table())
        self.assertEqual(pair.a.request('echo', 1), 1)

    def test_ping(self):
        pair = pure_rpc_connection_pair()
        pair.a.ping()
        pair.b.ping()

    def test_ids(self):
        pair = pure_rpc_connection_pair(
            a_kwargs=dict(id_creator=UuidRpcIdCreator()),
            b_kwargs=dict(handler=_echo_table()),
        )
        self.assertEqual(pair.a.request('echo', 1), 1)

        pair = pure_rpc_connection_pair(
            a_kwargs=dict(id_creator=lambda: 'same'),
            b_kwargs=dict(handler=_echo_table()),
        )
        self.assertEqual(pair.a.request('echo', 1), 1)
        self.assertEqual(pair.a.request('echo', 2), 2)

    def test_not_started(self):
        pair = pure_rpc_connection_pair(start=False)
        with self.assertRaises(Exception):  # noqa
            pair.a.request('echo')
        pair.a.close()
        self.assertTrue(pair.a.is_closed)


class TestNotifications(unittest.TestCase):
    def test_spawned_and_inline(self):
        got: ta.List[ta.Any] = []

        async def spawned(p):
            got.append(('spawned', p))

        h = RpcMethodTableHandler(
            notifications={'s': spawned},
            inline_notifications={'i': lambda p: got.append(('inline', p))},
        )
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=h))
        pair.a.notify('s', 1)
        pair.a.notify('i', 2)
        pair.a.notify('unknown', 3)
        pair.a.ping()
        self.assertEqual(got, [('spawned', 1), ('inline', 2)])

    def test_inline_wire_order(self):
        # The streaming recipe: the server pushes notifications while handling a request, then answers it. By the time
        # the client sees the answer, every notification sent before it has been applied.
        received: ta.List[int] = []
        conns: ta.Dict[str, RpcConnection] = {}

        async def produce(n):
            for i in range(n):
                await conns['b'].notify('chunk', i)
            return 'done'

        pair = pure_rpc_connection_pair(
            a_kwargs=dict(handler=RpcMethodTableHandler(inline_notifications={'chunk': received.append})),
            b_kwargs=dict(handler=RpcMethodTableHandler({'produce': produce})),
        )
        conns['b'] = pair.b.connection
        self.assertEqual(pair.a.request('produce', 50), 'done')
        self.assertEqual(received, list(range(50)))

    def test_notification_errors(self):
        errs: ta.List[ta.Any] = []

        async def bad(p):
            raise KeyError(p)

        def bad_inline(p):
            raise IndexError(p)

        h = RpcMethodTableHandler(notifications={'s': bad}, inline_notifications={'i': bad_inline})
        pair = pure_rpc_connection_pair(
            b_kwargs=dict(handler=h, notification_error_handler=lambda n, e: errs.append((n.method, type(e)))),
        )
        pair.a.notify('s', 1)
        pair.a.notify('i', 2)
        pair.a.ping()
        self.assertEqual(errs, [('s', KeyError), ('i', IndexError)])

    def test_inline_default_falls_through(self):
        got: ta.List[ta.Any] = []

        class H(RpcHandler):
            async def handle_request(self, method, params):
                raise NotImplementedError

            async def handle_notification(self, method, params):
                got.append((method, params))

        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=H()))
        pair.a.notify('x', 1)
        pair.a.ping()
        self.assertEqual(got, [('x', 1)])


class TestCallbacks(unittest.TestCase):
    def test_nested_callbacks(self):
        # Each side's handler calls the other back, several levels deep, all inline in one thread.
        conns: ta.Dict[str, RpcConnection] = {}

        def make(me: str, other: str) -> RpcHandler:
            async def countdown(n):
                if n <= 0:
                    return [me]
                return [me, *(await conns[me].request('countdown', n - 1))]

            return RpcMethodTableHandler({'countdown': countdown})

        pair = pure_rpc_connection_pair(
            a_kwargs=dict(handler=make('a', 'b')),
            b_kwargs=dict(handler=make('b', 'a')),
        )
        conns['a'] = pair.a.connection
        conns['b'] = pair.b.connection

        self.assertEqual(pair.a.request('countdown', 5), ['b', 'a', 'b', 'a', 'b', 'a'])


class TestTimeouts(unittest.TestCase):
    def test_request_timeout_unresponsive_peer(self):
        pair = pure_rpc_connection_pair(start=False)
        pair.a.start()
        with self.assertRaises(RpcTimeoutError):
            pair.a.request('echo', timeout_s=5.)
        self.assertEqual(pair.link.now, 5.)

        pair.a.connection.config  # noqa
        with self.assertRaises(RpcTimeoutError):
            pair.a.ping(timeout_s=2.)
        self.assertEqual(pair.link.now, 7.)

    def test_default_request_timeout(self):
        pair = pure_rpc_connection_pair(RpcConfig(default_request_timeout_s=30.), start=False)
        pair.a.start()
        with self.assertRaises(RpcTimeoutError):
            pair.a.request('echo')
        self.assertEqual(pair.link.now, 30.)

    def test_no_timeout_deadlock_detected(self):
        pair = pure_rpc_connection_pair(RpcConfig(default_ping_timeout_s=None), start=False)
        pair.a.start()
        with self.assertRaises(PureRpcLinkDeadlockError):
            pair.a.request('echo')

    def test_send_timeout_under_backpressure(self):
        pair = pure_rpc_connection_pair(
            a_kwargs=dict(send_timeout_s=4.),
            capacity=1024,
            start=False,
        )
        pair.a.start()
        with self.assertRaises(RpcTimeoutError):
            pair.a.notify('big', 'x' * 200_000)
        self.assertEqual(pair.link.now, 4.)

    def test_idle_timeout(self):
        pair = pure_rpc_connection_pair(RpcConfig(idle_timeout_s=60.), b_kwargs=dict(handler=_echo_table()))
        pair.a.request('echo', 1)
        pair.a.wait_closed()
        self.assertEqual(pair.link.now, 60.)
        self.assertIsInstance(pair.a.close_exception, RpcTimeoutError)


class TestKeepalive(unittest.TestCase):
    _CONFIG = RpcConfig(keepalive_interval_s=10., keepalive_timeout_s=3.)

    def test_live_peer(self):
        pair = pure_rpc_connection_pair(self._CONFIG)
        with self.assertRaises(AsynclitePromiseWaitTimeoutError):
            sync_await(pair.link.a.pump_until(lambda: False, 1000.))
        self.assertEqual(pair.link.now, 1000.)
        self.assertFalse(pair.a.is_closed)
        self.assertFalse(pair.b.is_closed)
        self.assertGreater(pair.link.moved[0], 0)

    def test_dead_peer(self):
        pair = pure_rpc_connection_pair(self._CONFIG, start=False)
        pair.a.start()
        pair.a.wait_closed()
        self.assertEqual(pair.link.now, 13.)
        self.assertIsInstance(pair.a.close_exception, RpcTimeoutError)


class TestEncoding(unittest.TestCase):
    def test_unencodable_params(self):
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=_echo_table()))
        with self.assertRaises(ValueError):
            pair.a.request('echo', object())
        self.assertEqual(pair.a.request('echo', 1), 1)

    def test_unencodable_result(self):
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=_echo_table(obj=rpc_async_method(lambda p: object()))))
        with self.assertRaises(RpcRemoteError) as cm:
            pair.a.request('obj')
        self.assertEqual(cm.exception.code, RpcErrorCodes.RESULT_ENCODING)
        self.assertEqual(pair.a.request('echo', 1), 1)

    def test_backpressure_bounds_pending_output(self):
        got: ta.List[int] = []
        pair = pure_rpc_connection_pair(
            b_kwargs=dict(handler=RpcMethodTableHandler(inline_notifications={'n': lambda p: got.append(len(p))})),
            capacity=4096,
        )
        for _ in range(20):
            pair.a.notify('n', 'x' * 20_000)
        pair.a.ping()
        self.assertEqual(got, [20_000] * 20)
        self.assertLess(pair.link.max_pending_output[0], 2 * 20_100)


class TestClosing(unittest.TestCase):
    def test_graceful_close(self):
        closed: ta.List[str] = []
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=_echo_table()))
        pair.a.add_close_callback(lambda c: closed.append('a'))
        pair.b.add_close_callback(lambda c: closed.append('b'))

        pair.a.request('echo', 1)
        pair.a.close()
        self.assertTrue(pair.a.is_closed)
        self.assertIsNone(pair.a.close_exception)
        pair.b.wait_closed()
        self.assertTrue(pair.b.is_closed)
        self.assertIsNone(pair.b.close_exception)
        self.assertEqual(sorted(closed), ['a', 'b'])

        pair.a.close()
        pair.a.wait_closed()
        self.assertEqual(sorted(closed), ['a', 'b'])

        late: ta.List[str] = []
        pair.a.add_close_callback(lambda c: late.append('late'))
        self.assertEqual(late, ['late'])

        with self.assertRaises(RpcConnectionClosedError):
            pair.a.request('echo', 1)
        with self.assertRaises(RpcConnectionClosedError):
            pair.a.notify('n')

    def test_peer_closes_during_request(self):
        conns: ta.Dict[str, RpcConnection] = {}

        async def die(p):
            await conns['b'].close(graceful=False)
            return 'never'

        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=RpcMethodTableHandler({'die': die})))
        conns['b'] = pair.b.connection

        # Even an abortive close answers what is in flight, so the caller gets a definite answer - one which is also a
        # connection-closed error, as that is what it means.
        with self.assertRaises(RpcRemoteError) as cm:
            pair.a.request('die')
        self.assertEqual(cm.exception.code, RpcErrorCodes.SHUTTING_DOWN)
        self.assertIsInstance(cm.exception, RpcConnectionClosedError)

        pair.a.wait_closed()
        self.assertTrue(pair.a.is_closed)
        self.assertIsNone(pair.a.close_exception)

    def test_peer_vanishes_during_request(self):
        conns: ta.Dict[str, RpcConnection] = {}

        async def vanish(p):
            await conns['b'].runtime.close()
            return 'never'

        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=RpcMethodTableHandler({'vanish': vanish})))
        conns['b'] = pair.b.connection

        with self.assertRaises(RpcConnectionClosedError):
            pair.a.request('vanish')

    def test_graceful_close_from_own_handler_is_bounded(self):
        # The documented footgun: a graceful close awaited from inside a request handler waits for that very request,
        # so it is only ended by the drain timeout - which, on the virtual clock, passes instantly.
        conns: ta.Dict[str, RpcConnection] = {}

        async def shutdown(p):
            await conns['b'].close()
            return 'closed'

        pair = pure_rpc_connection_pair(
            b_config=RpcConfig(close_drain_timeout_s=5.),
            b_kwargs=dict(handler=RpcMethodTableHandler({'shutdown': shutdown})),
        )
        conns['b'] = pair.b.connection
        with self.assertRaises(RpcRemoteError) as cm:
            pair.a.request('shutdown')
        self.assertEqual(cm.exception.code, RpcErrorCodes.SHUTTING_DOWN)
        self.assertEqual(pair.link.now, 5.)
        self.assertIsInstance(pair.b.close_exception, RpcTimeoutError)

    def test_abortive_close(self):
        pair = pure_rpc_connection_pair()
        pair.a.close(graceful=False)
        pair.b.wait_closed()
        self.assertTrue(pair.a.is_closed)
        self.assertTrue(pair.b.is_closed)

    def test_context_manager(self):
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=_echo_table()), start=False)
        pair.b.start()
        with pair.a as a:
            self.assertEqual(a.request('echo', 1), 1)
        self.assertTrue(pair.a.is_closed)

    def test_base_exception_propagates(self):
        async def interrupt(p):
            raise KeyboardInterrupt

        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=RpcMethodTableHandler({'interrupt': interrupt})))
        with self.assertRaises(KeyboardInterrupt):
            pair.a.request('interrupt')


class TestNotificationMessage(unittest.TestCase):
    def test_notification_message_repr(self):
        self.assertIn('n', repr(RpcNotificationMessage('n')))
