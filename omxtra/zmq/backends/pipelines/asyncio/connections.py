"""
One transport connection: a fresh pipeline under its own asyncio driver, run by its own task until it ends. It is the
PeerSink of its endpoint peer, turning the endpoint's notifications into wakes fed through the driver's entry point.
"""
import asyncio
import typing as ta

from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from omcore.io.pipelines.drivers.types import IoPipelineDriverState
from omcore.logs import all as logs

from ....core.endpoints import Endpoint
from ....core.peers import PeerSink
from ....zmtp.pipelines.sessions import ZmtpSessionEnded
from ....zmtp.pipelines.sessions import ZmtpSessionIoPipelineHandler
from ....zmtp.pipelines.sessions import ZmtpSessionWake


log = logs.get_module_logger(globals())


##


class Connection(PeerSink):
    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            *,
            endpoint: Endpoint,
            new_spec: ta.Callable[[ZmtpSessionIoPipelineHandler], IoPipeline.Spec],
            turn_output_budget: int,
            driver_config: PollAsyncioStreamIoPipelineDriver.Config,
            on_done: ta.Callable[[Connection], None],
            name: str = '',
    ) -> None:
        super().__init__()

        self._session = ZmtpSessionIoPipelineHandler(endpoint, self, turn_output_budget=turn_output_budget)
        self._driver = PollAsyncioStreamIoPipelineDriver(new_spec(self._session), reader, writer, driver_config)
        self._on_done = on_done
        self._name = name

        self._closing = False
        self._abort_requested = False
        self._running = False
        self._error: BaseException | None = None
        self._done = asyncio.Event()
        self._task: asyncio.Task | None = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self._name}>@{id(self):x}'

    @property
    def was_ready(self) -> bool:
        return self._session.was_ready

    @property
    def failure(self) -> BaseException | None:
        return self._session.failure or self._error

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f'zmq connection {self._name}')

    async def wait_done(self) -> None:
        await self._done.wait()

    def abort(self) -> None:
        # At most once: a second cancellation would interrupt the first one's cleanup. And a task which has not begun
        # running is not cancelled at all - it would then never run, nor clean up - but finds the request when it does.
        self._closing = True
        if self._abort_requested:
            return
        self._abort_requested = True
        if self._running and (task := self._task) is not None:
            task.cancel()

    #

    async def _run(self) -> None:
        self._running = True
        drv = self._driver
        try:
            while (
                    not self._abort_requested and
                    drv.state in (IoPipelineDriverState.NEW, IoPipelineDriverState.RUNNING)
            ):
                # Not raising on stalls: a connection whose endpoint has no room reads nothing and has no timers, and
                # simply waits for a wake.
                if (out := await drv.next(raise_on_stall=False)) is not None:
                    if isinstance(out, ZmtpSessionEnded):
                        break
                    raise TypeError(out)
                if not drv.pipeline.is_ready:
                    break

        except asyncio.CancelledError:
            pass

        except Exception as e:  # noqa
            self._error = e

        finally:
            self._closing = True
            try:
                try:
                    await drv.close()
                except BaseException as e:  # noqa
                    log.debug('Error closing %s: %r', self, e)

                if (f := self.failure) is not None:
                    log.debug('%s ended: %r', self, f)

            finally:
                self._done.set()
                self._on_done(self)

    #

    def _wake(self, kind: ta.Literal['send', 'recv']) -> None:
        if not self._closing and self._driver.state not in (IoPipelineDriverState.FAILED, IoPipelineDriverState.CLOSED):
            self._driver.enqueue(ZmtpSessionWake(kind))

    def wake_send(self) -> None:
        self._wake('send')

    def wake_recv(self) -> None:
        self._wake('recv')

    def close(self) -> None:
        self.abort()
