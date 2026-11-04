# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The fdio runtime: a connection hosted in an fdio manager's callbacks, beside any number of others, on one thread.

Nothing in a reactor callback may wait, so this runtime cannot either: its promises are already settled or they raise,
and the connection's waiting operations - `request`, `close`, `wait_closed` - are not for use here. What it serves is
the other direction. Each readiness callback steps the driver and delivers every event it produces to the connection,
under `sync_await`; handlers run inline, to completion, and must never actually suspend, exactly as under the sync
runtime. Answers, notifications to the peer, and closing (`RpcSessionMessages.Close` through `enqueue`, or the
close-after-requests handler) are all fire-and-forget, which is all a server needs.

`RpcSocketFdioHandler` is the fdio handler to register: the pipelines socket handler, with its readiness callbacks
routed through the runtime, and the runtime itself, to build an `RpcConnection` on.
"""
import socket
import typing as ta

from ..asyncs.asynclite.promises import AsynclitePromise
from ..asyncs.asynclite.promises import AsynclitePromiseAlreadySetError
from ..io.pipelines.core import IoPipeline
from ..io.pipelines.drivers.fdio.core import IoPipelineFdioDriver
from ..io.pipelines.drivers.fdio.sockets import IoPipelineDriverSocketFdioHandler
from ..io.pipelines.drivers.types import IoPipelineDriverState
from ..lite.asyncs import sync_await
from ..lite.check import check
from ..lite.maybes import Maybe
from ..logs.modules import get_module_logger
from .runtime import RpcRuntime
from .runtime import RpcRuntimeSink


T = ta.TypeVar('T')


log = get_module_logger(globals())  # noqa


##


class RpcFdioPromise(AsynclitePromise[T]):
    """A promise which can only be waited on once settled: under fdio, nothing waits."""

    def __init__(self) -> None:
        super().__init__()

        self._has_out = False
        self._val: ta.Optional[T] = None
        self._exc: ta.Optional[BaseException] = None

    def is_done(self) -> bool:
        return self._has_out

    def _result(self) -> T:
        if (e := self._exc) is not None:
            raise e
        return ta.cast(T, self._val)

    def poll(self) -> Maybe[T]:
        if not self._has_out:
            return Maybe.nothing()
        return Maybe.just(self._result())

    def set_value(self, v: T) -> None:
        if self._has_out:
            raise AsynclitePromiseAlreadySetError(self)
        self._val = v
        self._has_out = True

    def set_error(self, e: BaseException) -> None:
        if not isinstance(e, BaseException):
            raise TypeError(e)
        if self._has_out:
            raise AsynclitePromiseAlreadySetError(self)
        self._exc = e
        self._has_out = True

    async def wait(self, *, timeout: ta.Optional[float] = None) -> T:
        if not self._has_out:
            raise RuntimeError('an fdio rpc runtime cannot wait: nothing in a reactor callback may')
        return self._result()


##


class FdioRpcRuntime(RpcRuntime):
    def __init__(self, handler: 'RpcSocketFdioHandler') -> None:
        super().__init__()

        self._handler = handler

        self._sink: ta.Optional[RpcRuntimeSink] = None
        self._driver_done = False
        self._closed = False

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._handler!r}>'

    @property
    def is_started(self) -> bool:
        return self._sink is not None

    @property
    def is_driver_done(self) -> bool:
        return self._driver_done

    def make_promise(self) -> AsynclitePromise:
        return RpcFdioPromise()

    def is_cancelled_exception(self, exc: BaseException) -> bool:
        return False

    def enqueue(self, *commands: ta.Any) -> bool:
        if self._driver_done or self._closed or self._handler.closed:
            return False
        try:
            self._handler.enqueue(*commands)
        except Exception:  # noqa
            log.debug('Driver refused commands', exc_info=True)
            return False
        return True

    #

    async def start(self, sink: RpcRuntimeSink) -> None:
        check.none(self._sink, 'already started')
        self._sink = sink

        # Brings the pipeline up, and with it the session, without touching the transport.
        self.step(read=False)

    async def spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        try:
            await fn()
        except Exception:  # noqa
            log.exception('Unhandled error in rpc handler')

    def cancel(self, key: ta.Any) -> None:
        pass

    def cancel_all(self) -> None:
        pass

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        try:
            self._handler.close()
        except Exception:  # noqa
            log.exception('Error closing rpc fdio handler')

        self.report_driver_done(None)

    async def wait_closed(self) -> None:
        pass

    #

    def report_driver_done(self, exc: ta.Optional[BaseException]) -> None:
        if self._driver_done:
            return
        self._driver_done = True
        if (sink := self._sink) is not None:
            sink.on_driver_done(exc)

    def check_driver_stopped(self) -> None:
        if self._handler.closed or self._handler.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED):
            self.report_driver_done(None)

    def deliver(self, out: ta.Any) -> None:
        """Hands one unhandled driver output to the connection. Called from within the driver's stepping."""

        if isinstance(out, BaseException):
            # A failing close the session surfaced: the transport is in trouble, so abort rather than flush.
            try:
                self._handler.close()
            finally:
                self.report_driver_done(out)
            return

        if (sink := self._sink) is None:
            log.warning('Dropping rpc event delivered before start: %r', out)
            return

        sync_await(sink.on_event(out))

    def step(self, *, read: bool) -> None:
        """Steps the driver outside any readiness callback, delivering what it produces."""

        h = self._handler
        while h.is_active or h.state is IoPipelineDriverState.NEW:
            if (out := h.next(read=read, raise_on_stall=False)) is None:
                break
            self.deliver(out)
        self.check_driver_stopped()


##


class RpcSocketFdioHandler(IoPipelineDriverSocketFdioHandler):
    """
    An fdio handler driving an rpc pipeline over a socket. Build the connection on `runtime`, start it (under
    `sync_await`), and register the handler with the manager.
    """

    def __init__(
            self,
            sock: socket.socket,
            addr: ta.Any,
            spec: IoPipeline.Spec,
            config: ta.Optional[IoPipelineFdioDriver.Config] = None,
    ) -> None:
        super().__init__(sock, addr, spec, config)

        self._runtime = FdioRpcRuntime(self)

    @property
    def runtime(self) -> FdioRpcRuntime:
        return self._runtime

    def _run(self, fn: ta.Callable[[], None]) -> None:
        try:
            fn()
        except Exception as e:  # noqa
            # The driver failed itself, or a step raised: the connection is over.
            try:
                self.close()
            finally:
                self._runtime.report_driver_done(e)
        finally:
            self._runtime.check_driver_stopped()

    def on_readable(self) -> None:
        self._run(lambda: self.driver.on_readable(on_unhandled=self._runtime.deliver))

    def on_writable(self) -> None:
        self._run(lambda: self.driver.on_writable(on_unhandled=self._runtime.deliver))

    def on_timeout(self) -> None:
        self._run(lambda: self.driver.on_timeout(on_unhandled=self._runtime.deliver))

    def close(self) -> None:
        try:
            super().close()
        finally:
            self._runtime.check_driver_stopped()
