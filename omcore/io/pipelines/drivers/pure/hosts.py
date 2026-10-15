# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The in-memory transport host: listeners are registered by endpoint in the host, and connecting to one yields two
pure-driven pipelines wired back to back through a bounded simulated link, stepped explicitly. It is the deterministic
test bed for anything involving a second transport, and a product in its own right: nothing in it is a test helper.

Time is the host's: `advance_time` moves the clock of every hosted driver, and connect deadlines, forward. Outcomes
for requests without an owner are delivered on the next `step`, so that no callback runs inside the call which made
the request; owned requests have theirs posted into the owner's pipeline as every host does.
"""
import collections
import typing as ta
import weakref

from .....lite.check import check
from .....sockets.endpoints import SocketEndpoint
from .....sockets.endpoints import TcpSocketEndpoint
from .....sockets.endpoints import UnixSocketEndpoint
from ...core import IoPipeline
from ...core import IoPipelineHandlerRef
from ...hosts.base import BaseIoPipelineHost
from ...hosts.base import BaseIoPipelineHostHandle
from ...hosts.types import ClosedIoPipelineHostError
from ...hosts.types import ConnectIoPipelineHostError
from ...hosts.types import ConnectTimeoutIoPipelineHostError
from ...hosts.types import IoPipelineHostCallback
from ...hosts.types import IoPipelineHostedConnect
from ...hosts.types import IoPipelineHostedDriver
from ...hosts.types import IoPipelineHostedListener
from ...hosts.types import IoPipelineHostError
from ...hosts.types import IoPipelineHostSpecFactory
from ...hosts.types import IoPipelineHostTransportInfo
from ...hosts.types import ListenIoPipelineHostError
from ...posting.types import IoPipelinePosting
from ..types import IoPipelineDriverState
from .drivers import PureIoPipelineDriver
from .links import PureLink


##


class MemoryIoPipelineLink:
    """Two ends, each adoptable by the memory host once; linked by a `PureLink` once both have drivers."""

    def __init__(self, *, capacity: ta.Optional[int] = None) -> None:
        super().__init__()

        self._capacity = capacity
        self._ends = (MemoryIoPipelineLinkEnd(self, 0), MemoryIoPipelineLinkEnd(self, 1))
        self._drivers: ta.List[ta.Optional[PureIoPipelineDriver]] = [None, None]
        self._pure_link: ta.Optional[PureLink] = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def ends(self) -> ta.Tuple['MemoryIoPipelineLinkEnd', 'MemoryIoPipelineLinkEnd']:
        return self._ends

    @property
    def pure_link(self) -> ta.Optional[PureLink]:
        return self._pure_link

    def _attach(self, side: int, driver: PureIoPipelineDriver) -> None:
        check.none(self._drivers[side])
        self._drivers[side] = driver
        if all(d is not None for d in self._drivers):
            self._pure_link = PureLink(
                check.not_none(self._drivers[0]),
                check.not_none(self._drivers[1]),
                capacity=self._capacity,
            )

    def pump_once(self) -> bool:
        if (link := self._pure_link) is not None:
            return link.pump_once()
        return False

    @property
    def done(self) -> bool:
        """Whether every attached driver has closed or failed: nothing will move through the link again."""

        drivers = [d for d in self._drivers if d is not None]
        return bool(drivers) and all(
            d.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED) for d in drivers
        )


@ta.final
class MemoryIoPipelineLinkEnd:
    """
    What the memory host adopts: one end of a link, whose other end is held by whoever has the pair. The link is held
    only weakly - the host holds it until its drivers are done - so that a finished link, its drivers, and their
    pipelines are released without cyclic collection.
    """

    def __init__(self, link: MemoryIoPipelineLink, side: int) -> None:
        super().__init__()

        self.__link_ref = weakref.ref(link)
        self._side = side
        self._driver: ta.Optional[PureIoPipelineDriver] = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._side}>'

    @property
    def link(self) -> ta.Optional[MemoryIoPipelineLink]:
        return self.__link_ref()

    @property
    def side(self) -> int:
        return self._side

    @property
    def driver(self) -> ta.Optional[PureIoPipelineDriver]:
        return self._driver

    @property
    def adopted(self) -> bool:
        return self._driver is not None

    def _attach(self, driver: PureIoPipelineDriver) -> None:
        check.none(self._driver)
        self._driver = driver
        check.not_none(self.link)._attach(self._side, driver)  # noqa


##


class MemoryHostedIoPipelineDriver(BaseIoPipelineHostHandle, IoPipelineHostedDriver):
    _closes_first = False

    def __init__(
            self,
            host: 'MemoryIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            driver: PureIoPipelineDriver,
            end: MemoryIoPipelineLinkEnd,
            info: IoPipelineHostTransportInfo,
    ) -> None:
        self._driver = driver
        self._end = end
        self._info = info
        self.unhandled: ta.List[ta.Any] = []

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver.state.name}>'

    @property
    def driver(self) -> PureIoPipelineDriver:
        return self._driver

    @property
    def end(self) -> MemoryIoPipelineLinkEnd:
        return self._end

    @property
    def info(self) -> IoPipelineHostTransportInfo:
        return self._info

    @property
    def state(self) -> IoPipelineDriverState:
        return self._driver.state

    @property
    def pipeline(self) -> ta.Optional[IoPipeline]:
        return self._driver.pipeline

    @property
    def posting(self) -> IoPipelinePosting:
        return self._driver.posting

    @property
    def closed(self) -> bool:
        return self._driver.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    def close(self) -> None:
        try:
            self._driver.close()
        finally:
            self._unregister()

    def _step(self) -> bool:
        """Steps a driver which is not linked - its peer end was never adopted - collecting its unhandled output."""

        d = self._driver
        progressed = d.has_runnable_work
        while d.is_running or d.state is IoPipelineDriverState.NEW:
            out = d.next(read=True, raise_on_stall=False)
            if out is None:
                break
            self.unhandled.append(out)
            progressed = True
        return progressed


class MemoryHostedIoPipelineListener(BaseIoPipelineHostHandle, IoPipelineHostedListener):
    _closes_first = True

    def __init__(
            self,
            host: 'MemoryIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            bound_endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            on_accepted: ta.Optional[IoPipelineHostCallback[IoPipelineHostedDriver]],
    ) -> None:
        self._bound_endpoint = bound_endpoint
        self._spec_factory = spec_factory
        self._on_accepted = on_accepted
        self._closed = False

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._bound_endpoint!r}>'

    @property
    def bound_endpoint(self) -> SocketEndpoint:
        return self._bound_endpoint

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if (host := self._host) is not None:
            ta.cast('MemoryIoPipelineHost', host)._listeners.pop(self._bound_endpoint, None)  # noqa
        self._unregister()


class MemoryHostedIoPipelineConnect(BaseIoPipelineHostHandle, IoPipelineHostedConnect):
    _closes_first = False

    def __init__(
            self,
            host: 'MemoryIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            on_connected: IoPipelineHostCallback[IoPipelineHostedDriver],
            on_failed: IoPipelineHostCallback[IoPipelineHostError],
            deadline: ta.Optional[float],
    ) -> None:
        self._endpoint = endpoint
        self._spec_factory = spec_factory
        self._on_connected = on_connected
        self._on_failed = on_failed
        self._deadline = deadline
        self._done = False

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._endpoint!r}>'

    @property
    def endpoint(self) -> SocketEndpoint:
        return self._endpoint

    @property
    def closed(self) -> bool:
        return self._done

    def _finish(self) -> None:
        self._done = True
        self._unregister()

    def close(self) -> None:
        if self._done:
            return
        self._finish()
        self._deliver(self._on_failed, ClosedIoPipelineHostError('connect closed'))

    def _fail(self, exc: IoPipelineHostError) -> None:
        self._finish()
        self._deliver(self._on_failed, exc)


##


class MemoryIoPipelineHost(BaseIoPipelineHost):
    """
    Adopts `MemoryIoPipelineLinkEnd`s - `pair()` makes a linked two - and connects to its own listeners. An endpoint
    given to `hang` accepts no connection and never answers, so a connect to it can only time out, by `advance_time`.
    """

    def __init__(
            self,
            *,
            link_capacity: ta.Optional[int] = None,
            driver_config: ta.Optional[PureIoPipelineDriver.Config] = None,
    ) -> None:
        super().__init__()

        self._link_capacity = link_capacity
        self._driver_config = driver_config

        self._now = 0.
        self._next_port = 49152
        self._next_address = 1

        self._listeners: ta.Dict[SocketEndpoint, MemoryHostedIoPipelineListener] = {}
        self._hanging: ta.Set[SocketEndpoint] = set()
        self._connects: ta.List[MemoryHostedIoPipelineConnect] = []
        self._drivers: ta.Dict[int, MemoryHostedIoPipelineDriver] = {}
        self._links: ta.List[MemoryIoPipelineLink] = []
        self._later: ta.Deque[ta.Callable[[], None]] = collections.deque()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{len(self._drivers)}>'

    @property
    def now(self) -> float:
        return self._now

    @property
    def drivers(self) -> ta.Sequence[MemoryHostedIoPipelineDriver]:
        return list(self._drivers.values())

    @property
    def listeners(self) -> ta.Mapping[SocketEndpoint, MemoryHostedIoPipelineListener]:
        return dict(self._listeners)

    #

    def _run_unowned(self, fn: ta.Callable[[], None]) -> None:
        self._later.append(fn)

    def pair(self) -> ta.Tuple[MemoryIoPipelineLinkEnd, MemoryIoPipelineLinkEnd]:
        """A fresh link's two ends, like a socket pair: adopt either, or both."""

        link = MemoryIoPipelineLink(capacity=self._link_capacity)
        self._links.append(link)
        return link.ends

    def hang(self, endpoint: SocketEndpoint) -> None:
        """Makes connects to the endpoint stay pending until their deadline, as to a host which drops them."""

        self._hanging.add(endpoint)

    def _address(self) -> ta.Tuple[str, int]:
        n = self._next_address
        self._next_address += 1
        return ('memory', n)

    def _host_driver(
            self,
            end: MemoryIoPipelineLinkEnd,
            spec: IoPipeline.Spec,
            info: IoPipelineHostTransportInfo,
            owner: ta.Optional[IoPipelineHandlerRef],
    ) -> MemoryHostedIoPipelineDriver:
        driver = PureIoPipelineDriver(self._hosted_spec(spec), self._driver_config)
        end._attach(driver)  # noqa
        handle = MemoryHostedIoPipelineDriver(self, owner, driver, end, info)
        self._drivers[id(handle)] = handle

        # A hosted pipeline exists, and has had InitialInput, from the start; what it emits at once is kept.
        try:
            while (out := driver.next(read=False)) is not None:
                handle.unhandled.append(out)
        except BaseException:
            handle.close()
            raise

        return handle

    def _unregister_handle(self, handle: BaseIoPipelineHostHandle) -> None:
        super()._unregister_handle(handle)
        self._drivers.pop(id(handle), None)
        self._prune_links()

    def _prune_links(self) -> None:
        """A link whose drivers are all done is dropped, so that nothing keeps their pipelines alive."""

        self._links = [link for link in self._links if not link.done]

    #

    def connect(
            self,
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            *,
            on_connected: IoPipelineHostCallback[IoPipelineHostedDriver],
            on_failed: IoPipelineHostCallback[IoPipelineHostError],
            timeout_s: ta.Optional[float] = None,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedConnect:
        self._check_open()
        check.isinstance(endpoint, SocketEndpoint)
        if timeout_s is not None and timeout_s < 0.:
            raise ValueError(timeout_s)

        handle = MemoryHostedIoPipelineConnect(
            self,
            owner,
            endpoint,
            spec_factory,
            on_connected,
            on_failed,
            None if timeout_s is None else self._now + timeout_s,
        )
        self._connects.append(handle)
        return handle

    def _settle_connect(self, c: MemoryHostedIoPipelineConnect) -> bool:
        if c.closed:
            return True

        endpoint = c.endpoint
        if endpoint in self._hanging:
            if c._deadline is not None and self._now >= c._deadline:  # noqa
                c._fail(ConnectTimeoutIoPipelineHostError(endpoint, [TimeoutError('connect timed out')]))  # noqa
                return True
            return False

        if (listener := self._listeners.get(endpoint)) is None:
            c._fail(ConnectIoPipelineHostError(endpoint, [ConnectionRefusedError('no listener')]))  # noqa
            return True

        client_address = self._address()
        server_address = self._address()
        client_info = IoPipelineHostTransportInfo(
            endpoint=endpoint,
            local_address=client_address,
            peer_address=server_address,
        )
        server_info = IoPipelineHostTransportInfo(
            endpoint=listener.bound_endpoint,
            local_address=server_address,
            peer_address=client_address,
        )

        try:
            server_spec = listener._spec_factory(server_info)  # noqa
        except Exception as e:  # noqa
            # The listener's factory refused the connection: as a real peer would see it, the connection is closed
            # before anything crossed it, which here is a refusal.
            c._fail(ConnectIoPipelineHostError(endpoint, [e]))  # noqa
            return True

        try:
            client_spec = c._spec_factory(client_info)  # noqa
        except Exception as e:  # noqa
            c._fail(ConnectIoPipelineHostError(endpoint, [e]))  # noqa
            return True

        client_end, server_end = self.pair()
        server: ta.Optional[MemoryHostedIoPipelineDriver] = None
        try:
            server = self._host_driver(server_end, server_spec, server_info, listener.owner)
            client = self._host_driver(client_end, client_spec, client_info, c.owner)
        except Exception as e:  # noqa
            if server is not None:
                server.close()
            c._fail(ConnectIoPipelineHostError(endpoint, [e]))  # noqa
            return True

        c._finish()  # noqa
        if (on_accepted := listener._on_accepted) is not None:  # noqa
            listener._deliver(on_accepted, server)  # noqa
        c._deliver(c._on_connected, client)  # noqa
        return True

    def listen(
            self,
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            *,
            on_accepted: ta.Optional[IoPipelineHostCallback[IoPipelineHostedDriver]] = None,
            backlog: int = 128,
            unix_socket_mode: int = 0o600,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedListener:
        self._check_open()
        check.arg(backlog > 0)

        bound: SocketEndpoint
        if isinstance(endpoint, TcpSocketEndpoint):
            if endpoint.port == 0:
                while (bound := TcpSocketEndpoint(endpoint.host, self._next_port)) in self._listeners:
                    self._next_port += 1
                self._next_port += 1
            else:
                bound = endpoint
        elif isinstance(endpoint, UnixSocketEndpoint):
            bound = endpoint
        else:
            raise TypeError(endpoint)

        if bound in self._listeners:
            raise ListenIoPipelineHostError(f'endpoint in use: {bound!r}')

        listener = MemoryHostedIoPipelineListener(self, owner, bound, spec_factory, on_accepted)
        self._listeners[bound] = listener
        return listener

    def adopt(
            self,
            transport: ta.Any,
            spec: IoPipeline.Spec,
            *,
            info: ta.Optional[IoPipelineHostTransportInfo] = None,
            owned: bool = False,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedDriver:
        self._check_open()
        end = check.isinstance(transport, MemoryIoPipelineLinkEnd)
        check.state(not end.adopted)
        link = check.not_none(end.link, 'the link is gone: its drivers are done')
        if link not in self._links:
            self._links.append(link)

        if info is None:
            info = IoPipelineHostTransportInfo(local_address=self._address())
        return self._host_driver(end, spec, info, owner)

    #

    def step(self) -> bool:
        """
        Settles pending connects, runs outcomes waiting for delivery, and pumps every link and unlinked driver once;
        returns whether anything progressed.
        """

        progressed = False

        if self._connects:
            pending = self._connects
            self._connects = []
            for c in pending:
                if self._settle_connect(c):
                    progressed = True
                else:
                    self._connects.append(c)

        while self._later:
            self._later.popleft()()
            progressed = True

        for link in list(self._links):
            progressed |= link.pump_once()

        for handle in list(self._drivers.values()):
            if handle.closed:
                handle._unregister()  # noqa
            elif (end_link := handle.end.link) is None or end_link.pure_link is None:
                progressed |= handle._step()  # noqa

        return progressed

    def run(self, *, max_rounds: int = 100_000) -> int:
        """Steps until nothing progresses, returning the number of steps which did."""

        for n in range(max_rounds):
            if not self.step():
                return n
        raise RuntimeError('host did not quiesce')

    def run_until(self, cond: ta.Callable[[], bool], *, max_rounds: int = 100_000) -> None:
        for _ in range(max_rounds):
            if cond():
                return
            if not self.step():
                raise RuntimeError('host quiesced before condition')
        raise RuntimeError('host did not reach condition')

    def advance_time(self, delay_s: float) -> None:
        """Advances the host's clock and every hosted driver's: due connect deadlines are settled by the next step."""

        if delay_s < 0.:
            raise ValueError(delay_s)
        self._now += delay_s
        for handle in list(self._drivers.values()):
            if not handle.closed:
                handle.driver.advance_time(delay_s)

    #

    def close(self) -> None:
        if self.closed:
            return
        self._hanging.clear()
        try:
            super().close()
        finally:
            self._connects.clear()
            self._drivers.clear()
            self._listeners.clear()
            self._links.clear()
            self._later.clear()
