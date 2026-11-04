# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
A deterministic in-process link: two pure drivers back to back, each with a sync runtime, stepped together.

Whichever end is waited on pumps both: each step delivers at most one event to one end, or moves bytes across the
link, or - when nothing else can happen - advances a shared virtual clock straight to the earliest scheduled deadline.
Timeouts therefore fire exactly, instantly, and reproducibly, and a wait which nothing could ever satisfy raises
instead of hanging. Both ends run in the waiting thread: a handler on one end runs inline on the other end's wait.

Made for tests - of the toolbox, and of concerns built on it - and for in-process loopback.
"""
import typing as ta

from ..io.pipelines.core import IoPipeline
from ..io.pipelines.drivers.pure.drivers import PureIoPipelineDriver
from ..io.pipelines.drivers.types import IoPipelineDriverState
from ..lite.check import check
from .configs import RpcConfig
from .connection import RpcConnection
from .connection import SyncRpcConnection
from .specs import rpc_build_pipeline_spec
from .sync import BaseSyncRpcRuntime


##


class PureRpcLinkDeadlockError(RuntimeError):
    """Something is waited on which nothing could ever bring about: no work, no bytes in flight, no timer scheduled."""


class PureRpcRuntime(BaseSyncRpcRuntime):
    def __init__(self, link: 'PureRpcLink', side: int) -> None:
        super().__init__()

        self._link = link
        self._side = side

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{"ab"[self._side]}>'

    @property
    def link(self) -> 'PureRpcLink':
        return self._link

    @property
    def driver(self) -> PureIoPipelineDriver:
        return self._link.drivers[self._side]

    def enqueue(self, *commands: ta.Any) -> bool:
        if self._driver_done or self._closed:
            return False
        self.driver.enqueue(*commands)
        return True

    def _now(self) -> float:
        return self._link.now

    async def _step(self, timeout_s: ta.Optional[float]) -> None:
        await self._link.step(timeout_s)

    def _abort_driver(self) -> None:
        self.driver.close()

    def _is_driver_stopped(self) -> bool:
        return self.driver.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    def _check_driver_stopped(self) -> bool:
        if self._is_driver_stopped() and not self._driver_done:
            self._report_driver_done(None)
            return True
        return False

    def _report_link_failure(self, exc: BaseException) -> None:
        self._report_driver_done(exc)

    async def _step_driver(self) -> bool:
        """Steps this end's driver once, delivering at most one event. Returns whether anything happened."""

        if not self.is_started or self._driver_done:
            return False

        if self._check_driver_stopped():
            return True

        d = self.driver
        progressed = d.has_runnable_work
        try:
            out = d.next(read=True, raise_on_stall=False)
        except Exception as e:  # noqa
            self._report_driver_done(e)
            return True

        if out is None:
            return self._check_driver_stopped() or progressed

        await self._deliver(out)
        return True


##


class PureRpcLink:
    def __init__(
            self,
            a_spec: IoPipeline.Spec,
            b_spec: IoPipeline.Spec,
            *,
            a_driver_config: ta.Optional[PureIoPipelineDriver.Config] = None,
            b_driver_config: ta.Optional[PureIoPipelineDriver.Config] = None,
            capacity: ta.Optional[int] = None,
    ) -> None:
        """`capacity` bounds the bytes in flight toward each end, for exercising backpressure."""

        super().__init__()

        self._drivers = (
            PureIoPipelineDriver(a_spec, a_driver_config),
            PureIoPipelineDriver(b_spec, b_driver_config),
        )
        self._capacity = capacity

        self.a = PureRpcRuntime(self, 0)
        self.b = PureRpcRuntime(self, 1)
        self._runtimes = (self.a, self.b)

        self._now = 0.
        self._turn = 0
        self._eof_sent = [False, False]

        self.moved = [0, 0]
        self.max_pending_output = [0, 0]

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<now={self._now}>'

    @property
    def drivers(self) -> ta.Tuple[PureIoPipelineDriver, PureIoPipelineDriver]:
        return self._drivers

    @property
    def now(self) -> float:
        return self._now

    def advance_time(self, delay_s: float) -> None:
        """Advances both ends' clocks. Due timers run on each end's next step."""

        check.arg(delay_s >= 0.)
        for d in self._drivers:
            d.advance_time(delay_s)
        self._now += delay_s

    #

    @staticmethod
    def _is_live(d: PureIoPipelineDriver) -> bool:
        return d.state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING)

    def _move(self, si: int) -> bool:
        src = self._drivers[si]
        di = 1 - si
        dst = self._drivers[di]
        dst_open = dst.state is not IoPipelineDriverState.CLOSED and dst.state is not IoPipelineDriverState.FAILED
        dst_open = dst_open and not self._eof_sent[si]

        moved = False
        if self._is_live(src) and src.has_pending_output:
            self.max_pending_output[si] = max(self.max_pending_output[si], src.pending_output_bytes)

            room: ta.Optional[int] = None
            if self._capacity is not None and dst_open:
                room = max(self._capacity - dst.pending_input_bytes, 0)

            if room is None or room > 0 or not src.pending_output_bytes:
                try:
                    data = src.drain_output(room)
                except Exception as e:  # noqa
                    self._runtimes[si]._report_link_failure(e)  # noqa
                    return True

                if data and dst_open:
                    dst.feed_input(data)
                    self.moved[si] += len(data)
                moved = True

        src_ended = src.output_shutdown or not (self._is_live(src) or src.state is IoPipelineDriverState.NEW)
        if src_ended and not src.has_pending_output and not self._eof_sent[si]:
            self._eof_sent[si] = True
            if dst_open:
                dst.feed_eof()
            moved = True

        return moved

    async def step(self, timeout_s: ta.Optional[float] = None) -> None:
        """
        One unit of progress: an event delivered, bytes moved, or virtual time advanced - by at most `timeout_s`, when
        given. Raises PureRpcLinkDeadlockError when no progress is possible and nothing is scheduled.
        """

        first = self._turn
        for i in (first, 1 - first):
            if await self._runtimes[i]._step_driver():  # noqa
                self._turn = 1 - i
                return

        moved = self._move(0)
        moved |= self._move(1)
        for rt in self._runtimes:
            moved |= rt._check_driver_stopped()  # noqa
        if moved:
            return

        deadlines = [dl for d in self._drivers if (dl := d.next_deadline()) is not None]
        target = min(deadlines) if deadlines else None
        if target is not None and target <= self._now:
            raise PureRpcLinkDeadlockError(f'timer due at {target} did not run: {self!r}')

        if timeout_s is not None:
            wait_deadline = self._now + timeout_s
            if target is None or wait_deadline < target:
                target = wait_deadline

        if target is None:
            raise PureRpcLinkDeadlockError(f'nothing can make progress and nothing is scheduled: {self!r}')

        self.advance_time(target - self._now)

    async def pump(self, max_steps: int = 100_000) -> None:
        """Steps until nothing more happens without advancing time. For tests which want both ends quiescent."""

        for _ in range(max_steps):
            first = self._turn
            progressed = False
            for i in (first, 1 - first):
                if await self._runtimes[i]._step_driver():  # noqa
                    self._turn = 1 - i
                    progressed = True
                    break
            if progressed:
                continue

            moved = self._move(0)
            moved |= self._move(1)
            for rt in self._runtimes:
                moved |= rt._check_driver_stopped()  # noqa
            if not moved:
                return

        raise RuntimeError('pure rpc link did not quiesce')

    def close(self) -> None:
        for d in self._drivers:
            d.close()

    #

    @classmethod
    def of_configs(
            cls,
            a_config: RpcConfig = RpcConfig.DEFAULT,
            b_config: ta.Optional[RpcConfig] = None,
            *,
            a_spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            b_spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            **kwargs: ta.Any,
    ) -> 'PureRpcLink':
        if b_config is None:
            b_config = a_config
        return cls(
            rpc_build_pipeline_spec(a_config, **(a_spec_kwargs or {})),
            rpc_build_pipeline_spec(b_config, **(b_spec_kwargs or {})),
            **kwargs,
        )


##


class PureRpcConnectionPair(ta.NamedTuple):
    link: PureRpcLink
    a: SyncRpcConnection
    b: SyncRpcConnection


def pure_rpc_connection_pair(
        a_config: RpcConfig = RpcConfig.DEFAULT,
        b_config: ta.Optional[RpcConfig] = None,
        *,
        a_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
        b_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
        a_spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
        b_spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
        capacity: ta.Optional[int] = None,
        start: bool = True,
) -> PureRpcConnectionPair:
    """Two sync connections over a pure link, started unless `start` is false. Connection kwargs pass through."""

    if b_config is None:
        b_config = a_config

    link = PureRpcLink.of_configs(
        a_config,
        b_config,
        a_spec_kwargs=a_spec_kwargs,
        b_spec_kwargs=b_spec_kwargs,
        capacity=capacity,
    )

    a = SyncRpcConnection(RpcConnection(link.a, a_config, **(a_kwargs or {})))
    b = SyncRpcConnection(RpcConnection(link.b, b_config, **(b_kwargs or {})))

    if start:
        a.start()
        b.start()

    return PureRpcConnectionPair(link, a, b)
