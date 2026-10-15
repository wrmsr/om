# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
"""One suite of host scenarios run against every host implementation."""
import abc
import asyncio
import gc
import select
import socket
import typing as ta
import weakref

from .....lite.check import check
from .....sockets.endpoints import SocketEndpoint
from .....sockets.endpoints import TcpSocketEndpoint
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerNotifications
from ...core import IoPipelineMessages
from ...drivers.asyncio.hosts import AsyncioHostedIoPipelineDriver
from ...drivers.asyncio.hosts import AsyncioIoPipelineHost
from ...drivers.fdio.hosts import FdioIoPipelineHost
from ...drivers.fdio.running import fdio_run_until
from ...drivers.pure.drivers import PureIoPipelineDriver
from ...drivers.pure.hosts import MemoryIoPipelineHost
from ...drivers.types import IoPipelineDriverState
from ...posting.types import IoPipelinePosting
from ..base import BaseIoPipelineHost
from ..types import ClosedIoPipelineHostError
from ..types import ConnectIoPipelineHostError
from ..types import ConnectTimeoutIoPipelineHostError
from ..types import IoPipelineHost
from ..types import IoPipelineHostedDriver
from ..types import IoPipelineHostedListener
from ..types import IoPipelineHostTransportInfo


##


class _EchoApp(IoPipelineHandler):
    """Echoes uppercased input; on EOF ends. Records what it saw."""

    def __init__(self) -> None:
        super().__init__()

        self.received = bytearray()
        self.saw_final_input = False
        self.infos: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return
        if ByteStreamBuffers.can_bytes(msg):
            data = ByteStreamBuffers.to_bytes(msg, strict=True)
            self.received.extend(data)
            ctx.feed_out(data.upper())
            return
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


class _ClientApp(IoPipelineHandler):
    """Sends `send` and shuts down its output on start; records the reply; ends on EOF."""

    def __init__(self, send: bytes = b'hello') -> None:
        super().__init__()

        self._send = send
        self.received = bytearray()
        self.saw_final_input = False
        self.errors: ta.List[BaseException] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self._send)
            ctx.feed_shutdown_output()
            return
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return
        if ByteStreamBuffers.can_bytes(msg):
            self.received.extend(ByteStreamBuffers.to_bytes(msg, strict=True))
            return
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


class _OwnerApp(IoPipelineHandler):
    """A handler which owns host requests, recording the outcomes delivered to it and the context they came with."""

    def __init__(self) -> None:
        super().__init__()

        self.outcomes: ta.List[ta.Tuple[str, ta.Optional[IoPipelineHandlerContext], ta.Any]] = []
        self.nested = 0
        self._in_turn = False

    def _record(self, name: str, ctx: ta.Optional[IoPipelineHandlerContext], payload: ta.Any) -> None:
        if self._in_turn:
            self.nested += 1
        self._in_turn = True
        try:
            self.outcomes.append((name, ctx, payload))
        finally:
            self._in_turn = False

    def on_connected(self, ctx: ta.Optional[IoPipelineHandlerContext], handle: IoPipelineHostedDriver) -> None:
        self._record('connected', ctx, handle)

    def on_failed(self, ctx: ta.Optional[IoPipelineHandlerContext], exc: BaseException) -> None:
        self._record('failed', ctx, exc)

    def on_accepted(self, ctx: ta.Optional[IoPipelineHandlerContext], handle: IoPipelineHostedDriver) -> None:
        self._record('accepted', ctx, handle)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


class _Outcomes:
    def __init__(self) -> None:
        self.connected: ta.List[IoPipelineHostedDriver] = []
        self.failed: ta.List[BaseException] = []
        self.accepted: ta.List[IoPipelineHostedDriver] = []
        self.ctxs: ta.List[ta.Any] = []

    def on_connected(self, ctx: ta.Any, handle: IoPipelineHostedDriver) -> None:
        self.ctxs.append(ctx)
        self.connected.append(handle)

    def on_failed(self, ctx: ta.Any, exc: BaseException) -> None:
        self.ctxs.append(ctx)
        self.failed.append(exc)

    def on_accepted(self, ctx: ta.Any, handle: IoPipelineHostedDriver) -> None:
        self.ctxs.append(ctx)
        self.accepted.append(handle)


def _pipeline(handle: IoPipelineHostedDriver) -> IoPipeline:
    return check.not_none(handle.pipeline)


##


class _HostHarness(abc.ABC):
    NAME: ta.ClassVar[str]

    host: IoPipelineHost

    @abc.abstractmethod
    async def run_until(self, cond: ta.Callable[[], bool]) -> None:
        raise NotImplementedError

    async def settle(self) -> None:
        """Lets the runtime finish closing what was closed and drop what it no longer needs."""

    async def started(self, handle: IoPipelineHostedDriver) -> None:
        """Returns once the hosted driver has started."""

    @abc.abstractmethod
    def refused_endpoint(self) -> SocketEndpoint:
        raise NotImplementedError

    @abc.abstractmethod
    def hanging_endpoint(self) -> ta.Optional[SocketEndpoint]:
        """An endpoint which never answers a connect, or None where that cannot be arranged."""

        raise NotImplementedError

    def advance_time(self, delay_s: float) -> None:
        pass

    @abc.abstractmethod
    def adoptable_pair(self) -> ta.Tuple[ta.Any, ta.Any]:
        """Two connected transports the host can adopt, like a socket pair."""

        raise NotImplementedError

    def listen_endpoint(self) -> SocketEndpoint:
        return TcpSocketEndpoint('127.0.0.1', 0)

    @abc.abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class _MemoryHostHarness(_HostHarness):
    NAME = 'memory'

    host: MemoryIoPipelineHost

    def __init__(self) -> None:
        super().__init__()

        self.host = MemoryIoPipelineHost()

    async def run_until(self, cond: ta.Callable[[], bool]) -> None:
        self.host.run_until(cond)

    def refused_endpoint(self) -> SocketEndpoint:
        return TcpSocketEndpoint('127.0.0.1', 1)

    def hanging_endpoint(self) -> ta.Optional[SocketEndpoint]:
        ep = TcpSocketEndpoint('127.0.0.1', 2)
        self.host.hang(ep)
        return ep

    def advance_time(self, delay_s: float) -> None:
        self.host.advance_time(delay_s)

    def adoptable_pair(self) -> ta.Tuple[ta.Any, ta.Any]:
        return self.host.pair()

    async def close(self) -> None:
        self.host.close()


class _SocketHostHarness(_HostHarness, abc.ABC):
    def __init__(self) -> None:
        super().__init__()

        self._full: ta.List[socket.socket] = []

    def refused_endpoint(self) -> SocketEndpoint:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return TcpSocketEndpoint('127.0.0.1', s.getsockname()[1])

    def hanging_endpoint(self) -> ta.Optional[SocketEndpoint]:
        # A listener whose backlog is full drops further connection attempts, which then stay in progress - on Linux.
        # darwin completes the loopback handshake regardless and resets the connection, so a probe is given a moment:
        # an attempt the kernel will not leave hanging becomes writable - connected or failed - at once.
        listener = socket.create_server(('127.0.0.1', 0), backlog=1)
        self._full.append(listener)
        port = listener.getsockname()[1]
        for _ in range(8):
            f = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            f.setblocking(False)
            f.connect_ex(('127.0.0.1', port))
            self._full.append(f)
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.setblocking(False)
        try:
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                return None
            _, writable, _ = select.select([], [probe], [], .25)
            if writable:
                return None
        finally:
            probe.close()
        return TcpSocketEndpoint('127.0.0.1', port)

    def adoptable_pair(self) -> ta.Tuple[ta.Any, ta.Any]:
        return socket.socketpair()

    def _close_full(self) -> None:
        for s in self._full:
            s.close()
        self._full.clear()


class _FdioHostHarness(_SocketHostHarness):
    NAME = 'fdio'

    host: FdioIoPipelineHost

    def __init__(self) -> None:
        super().__init__()

        self.manager = FdioManager(SelectFdioPoller())
        self.host = FdioIoPipelineHost(self.manager)

    async def run_until(self, cond: ta.Callable[[], bool]) -> None:
        if not fdio_run_until(self.manager, cond, timeout_s=5.):
            raise TimeoutError('condition not reached')

    async def settle(self) -> None:
        # The manager drops closed handlers at the end of a poll.
        self.manager.poll(timeout=0.)

    async def close(self) -> None:
        self.host.close()
        self._close_full()


class _AsyncioHostHarness(_SocketHostHarness):
    NAME = 'asyncio'

    host: AsyncioIoPipelineHost

    def __init__(self) -> None:
        super().__init__()

        self.host = AsyncioIoPipelineHost()

    async def run_until(self, cond: ta.Callable[[], bool]) -> None:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + 5.
        for _ in range(100_000):
            if cond():
                return
            if loop.time() > deadline:
                break
            await asyncio.sleep(.001)
        raise TimeoutError('condition not reached')

    async def settle(self) -> None:
        for _ in range(50):
            await asyncio.sleep(.001)

    async def started(self, handle: IoPipelineHostedDriver) -> None:
        await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_started()

    async def close(self) -> None:
        self.host.close()
        await self.host.wait_closed()
        self._close_full()


##


class TestIoPipelineHostConformance(AsyncioIsolatedAsyncTestCase):
    HARNESS_TYPES: ta.Tuple[ta.Type[_HostHarness], ...] = (
        _MemoryHostHarness,
        _FdioHostHarness,
        _AsyncioHostHarness,
    )

    async def _with_harnesses(self, fn: ta.Callable[[_HostHarness], ta.Awaitable[None]]) -> None:
        for harness_type in self.HARNESS_TYPES:
            with self.subTest(host=harness_type.NAME):
                harness = harness_type()
                try:
                    await fn(harness)
                finally:
                    await harness.close()

    @staticmethod
    def _echo_factory(_info: IoPipelineHostTransportInfo) -> IoPipeline.Spec:
        return IoPipeline.Spec([_EchoApp()])

    #

    async def test_connect_and_accept_carry_data_both_ways(self) -> None:
        async def run(h: _HostHarness) -> None:
            outcomes = _Outcomes()
            echoes: ta.List[_EchoApp] = []

            def accept_factory(info: IoPipelineHostTransportInfo) -> IoPipeline.Spec:
                echo = _EchoApp()
                echo.infos.append(info)
                echoes.append(echo)
                return IoPipeline.Spec([echo])

            listener = h.host.listen(h.listen_endpoint(), accept_factory, on_accepted=outcomes.on_accepted)
            bound = listener.bound_endpoint
            self.assertIsInstance(bound, TcpSocketEndpoint)
            self.assertNotEqual(ta.cast(TcpSocketEndpoint, bound).port, 0)

            client = _ClientApp(b'hello')
            infos: ta.List[IoPipelineHostTransportInfo] = []

            def client_factory(info: IoPipelineHostTransportInfo) -> IoPipeline.Spec:
                infos.append(info)
                return IoPipeline.Spec([client])

            connect = h.host.connect(
                bound,
                client_factory,
                on_connected=outcomes.on_connected,
                on_failed=outcomes.on_failed,
                timeout_s=5.,
            )

            await h.run_until(lambda: client.saw_final_input and bool(echoes) and echoes[0].saw_final_input)

            self.assertEqual(outcomes.failed, [])
            self.assertEqual(len(outcomes.connected), 1)
            self.assertEqual(len(outcomes.accepted), 1)
            self.assertEqual(outcomes.ctxs, [None, None])
            self.assertTrue(connect.closed)
            self.assertEqual(bytes(client.received), b'HELLO')
            self.assertEqual(bytes(echoes[0].received), b'hello')
            self.assertEqual(client.errors, [])

            self.assertEqual(infos[0].endpoint, bound)
            self.assertIsNotNone(infos[0].peer_address)
            self.assertEqual(echoes[0].infos[0].endpoint, bound)
            self.assertIsNotNone(echoes[0].infos[0].peer_address)

            conn = outcomes.connected[0]
            acc = outcomes.accepted[0]
            await h.run_until(lambda: conn.closed and acc.closed)
            self.assertIs(conn.state, IoPipelineDriverState.CLOSED)
            self.assertIs(acc.state, IoPipelineDriverState.CLOSED)
            self.assertIsNotNone(conn.posting)
            self.assertIs(_pipeline(conn).services[IoPipelineHost], h.host)

            listener.close()
            self.assertTrue(listener.closed)

        await self._with_harnesses(run)

    async def test_connect_refused(self) -> None:
        async def run(h: _HostHarness) -> None:
            outcomes = _Outcomes()
            connect = h.host.connect(
                h.refused_endpoint(),
                self._echo_factory,
                on_connected=outcomes.on_connected,
                on_failed=outcomes.on_failed,
                timeout_s=5.,
            )
            await h.run_until(lambda: bool(outcomes.failed))

            self.assertEqual(outcomes.connected, [])
            exc = outcomes.failed[0]
            self.assertIsInstance(exc, ConnectIoPipelineHostError)
            self.assertNotIsInstance(exc, ConnectTimeoutIoPipelineHostError)
            self.assertTrue(connect.closed)

        await self._with_harnesses(run)

    async def test_connect_reports_client_pipeline_start_failure(self) -> None:
        class BrokenOnAdd(IoPipelineHandler):
            def notify(self, ctx, no) -> None:
                if isinstance(no, IoPipelineHandlerNotifications.Added):
                    raise TypeError('broken spec')

        async def run(h: _HostHarness) -> None:
            outcomes = _Outcomes()
            listener = h.host.listen(h.listen_endpoint(), lambda info: IoPipeline.Spec())
            connect = h.host.connect(
                listener.bound_endpoint,
                lambda info: IoPipeline.Spec([BrokenOnAdd()]),
                on_connected=outcomes.on_connected,
                on_failed=outcomes.on_failed,
            )

            await h.run_until(lambda: connect.closed)
            await h.settle()

            self.assertEqual(outcomes.connected, [])
            self.assertEqual(len(outcomes.failed), 1)
            self.assertIsInstance(outcomes.failed[0], ConnectIoPipelineHostError)

        await self._with_harnesses(run)

    async def test_connect_timeout(self) -> None:
        async def run(h: _HostHarness) -> None:
            if (ep := h.hanging_endpoint()) is None:
                self.skipTest('no hanging endpoint on this host')
            outcomes = _Outcomes()
            h.host.connect(
                ep,
                self._echo_factory,
                on_connected=outcomes.on_connected,
                on_failed=outcomes.on_failed,
                timeout_s=.05,
            )
            h.advance_time(.1)
            await h.run_until(lambda: bool(outcomes.failed))

            self.assertEqual(outcomes.connected, [])
            self.assertIsInstance(outcomes.failed[0], ConnectTimeoutIoPipelineHostError)

        await self._with_harnesses(run)

    async def test_connect_closed_while_connecting(self) -> None:
        async def run(h: _HostHarness) -> None:
            if (ep := h.hanging_endpoint()) is None:
                self.skipTest('no hanging endpoint on this host')
            outcomes = _Outcomes()
            connect = h.host.connect(
                ep,
                self._echo_factory,
                on_connected=outcomes.on_connected,
                on_failed=outcomes.on_failed,
                timeout_s=5.,
            )
            connect.close()
            await h.run_until(lambda: bool(outcomes.failed))

            self.assertIsInstance(outcomes.failed[0], ClosedIoPipelineHostError)
            self.assertTrue(connect.closed)
            connect.close()

        await self._with_harnesses(run)

    async def test_adopted_transports_carry_data(self) -> None:
        async def run(h: _HostHarness) -> None:
            a, b = h.adoptable_pair()
            echo = _EchoApp()
            client = _ClientApp(b'adopted')
            ha = h.host.adopt(a, IoPipeline.Spec([echo]), owned=True)
            hb = h.host.adopt(b, IoPipeline.Spec([client]), owned=True)
            await h.started(ha)
            await h.started(hb)
            self.assertIs(ha.state, IoPipelineDriverState.RUNNING)
            self.assertIsNotNone(ha.pipeline)
            self.assertIsNotNone(ha.posting)

            await h.run_until(lambda: ha.closed and hb.closed)

            self.assertEqual(bytes(client.received), b'ADOPTED')
            self.assertEqual(bytes(echo.received), b'adopted')
            self.assertTrue(echo.saw_final_input)
            self.assertTrue(client.saw_final_input)
            self.assertIs(ha.state, IoPipelineDriverState.CLOSED)

        await self._with_harnesses(run)

    async def _adopt_owner(
            self,
            h: _HostHarness,
            *handlers: IoPipelineHandler,
    ) -> ta.Tuple[IoPipelineHostedDriver, IoPipelineHostedDriver, IoPipeline]:
        a, b = h.adoptable_pair()
        owner_handle = h.host.adopt(a, IoPipeline.Spec(handlers), owned=True)
        other = h.host.adopt(b, IoPipeline.Spec([_EchoApp()]), owned=True)
        await h.started(owner_handle)
        return owner_handle, other, _pipeline(owner_handle)

    async def test_owned_outcomes_are_posted_into_the_owner(self) -> None:
        async def run(h: _HostHarness) -> None:
            owner = _OwnerApp()
            owner_handle, other, owner_pipeline = await self._adopt_owner(h, owner)
            owner_ref = owner_pipeline.handlers()[0]
            listen_endpoint = h.listen_endpoint()
            echo_factory = self._echo_factory

            listeners: ta.List[IoPipelineHostedListener] = []

            def request(ctx: IoPipelineHandlerContext) -> None:
                host = ctx.services[IoPipelineHost]
                listener = host.listen(listen_endpoint, echo_factory, on_accepted=owner.on_accepted, owner=ctx.ref)
                listeners.append(listener)
                host.connect(
                    listener.bound_endpoint,
                    lambda info: IoPipeline.Spec([_ClientApp()]),
                    on_connected=owner.on_connected,
                    on_failed=owner.on_failed,
                    timeout_s=5.,
                    owner=ctx.ref,
                )

            owner_pipeline.services[IoPipelinePosting].post_context(owner_ref, request)
            await h.run_until(lambda: len(owner.outcomes) >= 2)

            names = sorted(name for name, _, _ in owner.outcomes)
            self.assertEqual(names, ['accepted', 'connected'])
            for _, ctx, _ in owner.outcomes:
                self.assertIsNotNone(ctx)
                self.assertIs(ta.cast(IoPipelineHandlerContext, ctx).handler, owner)
                self.assertIs(ta.cast(IoPipelineHandlerContext, ctx).pipeline, owner_pipeline)
            self.assertEqual(owner.nested, 0)

            self.assertIs(listeners[0].owner, owner_ref)
            for _, _, payload in owner.outcomes:
                self.assertIs(ta.cast(IoPipelineHostedDriver, payload).owner, owner_ref)

            other.close()

        await self._with_harnesses(run)

    async def test_removing_the_owner_closes_what_it_owns(self) -> None:
        async def run(h: _HostHarness) -> None:
            owner = _OwnerApp()
            owner_handle, other, owner_pipeline = await self._adopt_owner(h, owner)
            owner_ref = owner_pipeline.handlers()[0]
            listen_endpoint = h.listen_endpoint()
            echo_factory = self._echo_factory
            listeners: ta.List[IoPipelineHostedListener] = []

            def request(ctx: IoPipelineHandlerContext) -> None:
                host = ctx.services[IoPipelineHost]
                listener = host.listen(listen_endpoint, echo_factory, owner=ctx.ref)
                listeners.append(listener)
                host.connect(
                    listener.bound_endpoint,
                    lambda info: IoPipeline.Spec([_OwnerApp()]),
                    on_connected=owner.on_connected,
                    on_failed=owner.on_failed,
                    timeout_s=5.,
                    owner=ctx.ref,
                )

            owner_pipeline.services[IoPipelinePosting].post_context(owner_ref, request)
            await h.run_until(lambda: len(owner.outcomes) >= 1)
            conn = ta.cast(IoPipelineHostedDriver, owner.outcomes[0][2])
            self.assertFalse(conn.closed)
            self.assertFalse(listeners[0].closed)

            owner_pipeline.services[IoPipelinePosting].post_context(
                owner_ref,
                lambda ctx: ctx.pipeline.remove(ctx.ref),
            )
            await h.run_until(lambda: owner_ref.invalidated and listeners[0].closed and conn.closed)

            self.assertIsNone(conn.owner)
            self.assertFalse(owner_handle.closed)

            other.close()

        await self._with_harnesses(run)

    async def test_destroying_the_owner_pipeline_closes_what_it_owns(self) -> None:
        async def run(h: _HostHarness) -> None:
            owner = _OwnerApp()
            owner_handle, other, owner_pipeline = await self._adopt_owner(h, owner)
            owner_ref = owner_pipeline.handlers()[0]
            listen_endpoint = h.listen_endpoint()
            echo_factory = self._echo_factory
            listeners: ta.List[IoPipelineHostedListener] = []

            owner_pipeline.services[IoPipelinePosting].post_context(
                owner_ref,
                lambda ctx: listeners.append(
                    ctx.services[IoPipelineHost].listen(listen_endpoint, echo_factory, owner=ctx.ref),
                ),
            )
            await h.run_until(lambda: bool(listeners))
            self.assertFalse(listeners[0].closed)

            owner_handle.close()
            await h.run_until(lambda: listeners[0].closed and not owner_pipeline.is_ready)

            other.close()

        await self._with_harnesses(run)

    async def test_owner_pipeline_must_have_the_host(self) -> None:
        """
        A handler whose pipeline the host is not a service of cannot own anything: its removal would never reach the
        host, so nothing would close what it owned. The request is refused before anything is done for it.
        """

        async def run(h: _HostHarness) -> None:
            drv = PureIoPipelineDriver(IoPipeline.Spec([_OwnerApp()]))
            try:
                self.assertIsNone(drv.next(read=False))
                ref = drv.pipeline.handlers()[0]
                a, b = h.adoptable_pair()
                try:
                    with self.assertRaises(RuntimeError):
                        h.host.listen(h.listen_endpoint(), self._echo_factory, owner=ref)
                    with self.assertRaises(RuntimeError):
                        h.host.connect(
                            h.refused_endpoint(),
                            self._echo_factory,
                            on_connected=lambda c, x: None,
                            on_failed=lambda c, x: None,
                            owner=ref,
                        )
                    with self.assertRaises(RuntimeError):
                        h.host.adopt(a, self._echo_factory(IoPipelineHostTransportInfo()), owner=ref)
                    self.assertEqual(list(ta.cast(BaseIoPipelineHost, h.host).handles), [])

                    handle = h.host.adopt(b, self._echo_factory(IoPipelineHostTransportInfo()))
                    with self.assertRaises(RuntimeError):
                        handle.transfer(ref)
                    self.assertIsNone(handle.owner)
                    handle.close()
                finally:
                    for t in (a, b):
                        if hasattr(t, 'close'):
                            t.close()
            finally:
                drv.close()

        await self._with_harnesses(run)

    async def test_release_and_transfer(self) -> None:
        async def run(h: _HostHarness) -> None:
            owner_a = _OwnerApp()
            owner_b = _OwnerApp()
            owner_handle, other, owner_pipeline = await self._adopt_owner(h, owner_a, owner_b)
            ref_a, ref_b = owner_pipeline.handlers()
            echo_factory = self._echo_factory
            listen_endpoint = h.listen_endpoint()
            listeners: ta.List[IoPipelineHostedListener] = []

            def request(ctx: IoPipelineHandlerContext) -> None:
                host = ctx.services[IoPipelineHost]
                listeners.append(host.listen(listen_endpoint, echo_factory, owner=ctx.ref))
                listeners.append(host.listen(listen_endpoint, echo_factory, owner=ctx.ref))

            owner_pipeline.services[IoPipelinePosting].post_context(ref_a, request)
            await h.run_until(lambda: len(listeners) == 2)
            transferred, released = listeners
            self.assertIs(transferred.owner, ref_a)

            transferred.transfer(ref_b)
            released.release()
            self.assertIs(transferred.owner, ref_b)
            self.assertIsNone(released.owner)

            owner_pipeline.remove(ref_a)
            self.assertFalse(transferred.closed)
            self.assertFalse(released.closed)

            owner_pipeline.remove(ref_b)
            self.assertTrue(transferred.closed)
            self.assertFalse(released.closed)

            h.host.close()
            await h.settle()
            self.assertTrue(released.closed)
            self.assertTrue(h.host.closed)
            self.assertTrue(other.closed)
            self.assertTrue(owner_handle.closed)

        await self._with_harnesses(run)

    async def test_closed_host_refuses_requests(self) -> None:
        async def run(h: _HostHarness) -> None:
            h.host.close()
            with self.assertRaises(ClosedIoPipelineHostError):
                h.host.listen(h.listen_endpoint(), self._echo_factory)
            with self.assertRaises(ClosedIoPipelineHostError):
                h.host.connect(
                    h.refused_endpoint(),
                    self._echo_factory,
                    on_connected=lambda c, x: None,
                    on_failed=lambda c, x: None,
                )

        await self._with_harnesses(run)

    async def test_closing_the_host_fails_pending_connects(self) -> None:
        """A connect still in progress when the host closes is told so, as one closed by itself is - owner or not."""

        async def run(h: _HostHarness) -> None:
            if (ep := h.hanging_endpoint()) is None:
                self.skipTest('no hanging endpoint on this host')
            outcomes = _Outcomes()
            connect = h.host.connect(
                ep,
                self._echo_factory,
                on_connected=outcomes.on_connected,
                on_failed=outcomes.on_failed,
                timeout_s=5.,
            )
            h.host.close()

            self.assertTrue(connect.closed)
            self.assertEqual(outcomes.connected, [])
            self.assertEqual(len(outcomes.failed), 1)
            self.assertIsInstance(outcomes.failed[0], ClosedIoPipelineHostError)

        await self._with_harnesses(run)

    async def test_finished_connections_are_dropped_by_the_host(self) -> None:
        """
        A hosted driver which ended on its own - gracefully, here - is nothing the host can close any more: its handle
        is dropped without an explicit close, so a long-lived host does not accumulate one per connection served.
        """

        async def run(h: _HostHarness) -> None:
            outcomes = _Outcomes()
            listener = h.host.listen(h.listen_endpoint(), self._echo_factory, on_accepted=outcomes.on_accepted)
            client = _ClientApp()
            h.host.connect(
                listener.bound_endpoint,
                lambda info: IoPipeline.Spec([client]),
                on_connected=outcomes.on_connected,
                on_failed=outcomes.on_failed,
                timeout_s=5.,
            )
            await h.run_until(lambda: client.saw_final_input and len(outcomes.accepted) == 1)
            conn = outcomes.connected[0]
            acc = outcomes.accepted[0]
            await h.run_until(lambda: conn.closed and acc.closed)
            await h.settle()

            self.assertEqual(list(ta.cast(BaseIoPipelineHost, h.host).handles), [listener])

        await self._with_harnesses(run)

    async def test_prompt_release_of_a_closed_listener_and_its_connections(self) -> None:
        async def run(h: _HostHarness) -> None:
            was_enabled = gc.isenabled()
            gc.disable()
            try:
                refs = await self._listen_connect_and_close(h)
                await h.settle()
                self.assertEqual([r() for r in refs], [None] * len(refs))
            finally:
                if was_enabled:
                    gc.enable()

        await self._with_harnesses(run)

    async def _listen_connect_and_close(self, h: _HostHarness) -> ta.List[ta.Any]:
        """Runs a connection to completion and closes everything, returning weak references to what should be gone."""

        outcomes = _Outcomes()
        listener = h.host.listen(h.listen_endpoint(), self._echo_factory, on_accepted=outcomes.on_accepted)
        client = _ClientApp()
        h.host.connect(
            listener.bound_endpoint,
            lambda info: IoPipeline.Spec([client]),
            on_connected=outcomes.on_connected,
            on_failed=outcomes.on_failed,
            timeout_s=5.,
        )
        await h.run_until(lambda: client.saw_final_input and len(outcomes.accepted) == 1)
        conn = outcomes.connected[0]
        acc = outcomes.accepted[0]
        await h.run_until(lambda: conn.closed and acc.closed)

        refs = [weakref.ref(x) for x in (listener, conn, acc, _pipeline(conn), _pipeline(acc))]
        listener.close()
        conn.close()
        acc.close()
        return refs
