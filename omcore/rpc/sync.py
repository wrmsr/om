# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
Sync runtimes: the caller's thread is the pump.

Waiting on one of a sync runtime's promises steps the pipeline driver in the waiting thread until the promise is done,
delivering each event to the connection as it comes out. Nothing ever actually suspends, which is what lets the async
connection run under `sync_await`. Handlers run inline, one at a time, as the events which caused them are delivered -
so a handler which itself calls out to the peer pumps reentrantly, and events arriving meanwhile, including further
requests, are handled within its wait. That is inherent to a single-threaded inline model; it keeps a request/callback
exchange between two sync peers from deadlocking, at the cost of stack depth under a peer which nests deeply.

There is no cancellation: handlers run to completion, and a request the session gives up on is answered and dropped.

A pipeline which can make no further progress while something is waited on - nothing to read, nothing to write, no
timer scheduled - is a deadlock, not a wait, and fails the connection rather than hanging.
"""
import abc
import errno
import os
import socket
import subprocess
import sys
import time
import typing as ta

from ..asyncs.asynclite.promises import AsynclitePromise
from ..asyncs.asynclite.promises import AsynclitePromiseAlreadySetError
from ..asyncs.asynclite.promises import AsynclitePromiseWaitTimeoutError
from ..io.pipelines.drivers.sync.core import SyncIoPipelineDriver
from ..io.pipelines.drivers.sync.fds import FdSyncIoPipelineDriver
from ..io.pipelines.drivers.sync.sockets import SocketSyncIoPipelineDriver
from ..io.pipelines.drivers.types import IoPipelineDriverState
from ..lite.abstract import Abstract
from ..lite.check import check
from ..lite.maybes import Maybe
from ..logs.modules import get_module_logger
from .configs import RpcConfig
from .connection import RpcConnection
from .connection import SyncRpcConnection
from .errors import RpcConnectionClosedError
from .runtime import RpcRuntime
from .runtime import RpcRuntimeSink
from .specs import rpc_build_pipeline_spec


T = ta.TypeVar('T')


log = get_module_logger(globals())  # noqa


##


class RpcSyncPromise(AsynclitePromise[T]):
    """A promise whose wait pumps its runtime until it is done. Single-threaded, like the runtime."""

    def __init__(self, runtime: 'BaseSyncRpcRuntime') -> None:
        super().__init__()

        self._runtime = runtime
        self._has_out = False
        self._val: ta.Optional[T] = None
        self._exc: ta.Optional[BaseException] = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{"done" if self._has_out else "pending"}>'

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
            await self._runtime.pump_until(self.is_done, timeout)
        return self._result()


##


class BaseSyncRpcRuntime(RpcRuntime, Abstract):
    def __init__(
            self,
            *,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
    ) -> None:
        super().__init__()

        self._closers = list(closers)

        self._sink: ta.Optional[RpcRuntimeSink] = None
        self._driver_done = False
        self._closed = False

    @property
    def is_started(self) -> bool:
        return self._sink is not None

    @property
    def is_driver_done(self) -> bool:
        return self._driver_done

    async def start(self, sink: RpcRuntimeSink) -> None:
        check.none(self._sink, 'already started')
        self._sink = sink

    def make_promise(self) -> AsynclitePromise:
        return RpcSyncPromise(self)

    def is_cancelled_exception(self, exc: BaseException) -> bool:
        return False

    #

    async def spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        try:
            await fn()
        except Exception:  # noqa
            log.exception('Unhandled error in rpc handler')

    def cancel(self, key: ta.Any) -> None:
        pass

    def cancel_all(self) -> None:
        pass

    #

    def _report_driver_done(self, exc: ta.Optional[BaseException]) -> None:
        if self._driver_done:
            return
        self._driver_done = True
        try:
            if (sink := self._sink) is not None:
                sink.on_driver_done(exc)
        finally:
            self._release_transport()

    def _release_transport(self) -> None:
        """
        Once the driver is done, however that came about, it lets go of the transport and the closers run - closing a
        child's stdin, say, so it sees EOF. Idempotent: the closers run once.
        """

        try:
            self._abort_driver()
        except Exception:  # noqa
            log.exception('Error closing rpc driver')

        closers, self._closers = self._closers, []
        for c in closers:
            try:
                c()
            except Exception:  # noqa
                log.exception('Error in rpc runtime closer %r', c)

    async def _deliver(self, out: ta.Any) -> None:
        if isinstance(out, BaseException):
            # A failing close the session surfaced: the driver may be stuck flushing to a stalled peer, so do not wait
            # for its orderly shutdown.
            self._abort_driver()
            self._report_driver_done(out)
            return

        await check.not_none(self._sink).on_event(out)

    @abc.abstractmethod
    def _now(self) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    async def _step(self, timeout_s: ta.Optional[float]) -> None:
        """
        Advances the driver one step, delivering at most one event, waiting at most `timeout_s` (None: indefinitely)
        for something to happen. Reports the driver done when it stops. Never suspends.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def _abort_driver(self) -> None:
        raise NotImplementedError

    async def pump_until(self, pred: ta.Callable[[], bool], timeout_s: ta.Optional[float] = None) -> None:
        """Pumps until `pred` holds, raising `AsynclitePromiseWaitTimeoutError` if `timeout_s` elapses first."""

        deadline = None if timeout_s is None else self._now() + timeout_s
        while not pred():
            if self._driver_done:
                raise RpcConnectionClosedError('rpc driver has stopped')

            remaining: ta.Optional[float] = None
            if deadline is not None:
                remaining = deadline - self._now()
                if remaining <= 0.:
                    raise AsynclitePromiseWaitTimeoutError

            await self._step(remaining)

    #

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        if not self._driver_done:
            try:
                self._abort_driver()
            except Exception:  # noqa
                log.exception('Error closing rpc driver')

            self._report_driver_done(None)

        else:
            self._release_transport()

    async def wait_closed(self) -> None:
        pass


##


class SyncRpcRuntime(BaseSyncRpcRuntime):
    """A sync runtime over a `SyncIoPipelineDriver`: sockets, fd pairs, a subprocess's stdio."""

    def __init__(
            self,
            driver: SyncIoPipelineDriver,
            *,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
    ) -> None:
        super().__init__(closers=closers)

        self._driver = driver

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver!r}>'

    @property
    def driver(self) -> SyncIoPipelineDriver:
        return self._driver

    def enqueue(self, *commands: ta.Any) -> bool:
        if self._driver_done or self._closed:
            return False
        try:
            self._driver.enqueue(*commands)
        except Exception:  # noqa
            log.debug('Driver refused commands', exc_info=True)
            return False
        return True

    def _now(self) -> float:
        return time.monotonic()

    def _abort_driver(self) -> None:
        self._driver.close()

    def _is_driver_stopped(self) -> bool:
        return self._driver.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    def _check_driver_stopped(self) -> None:
        if self._is_driver_stopped():
            self._report_driver_done(None)

    async def _step(self, timeout_s: ta.Optional[float]) -> None:
        d = self._driver
        if self._is_driver_stopped():
            self._report_driver_done(None)
            return

        d.wait_timeout_s = timeout_s
        try:
            out = d.next(read=True, raise_on_stall=True)

        except TimeoutError:
            # The wait bound elapsed with nothing to do; the caller rechecks its deadline.
            self._check_driver_stopped()
            return

        except RuntimeError as e:
            if not self._is_driver_stopped():
                # Raised without failing the driver: a stall. Nothing can progress, so nothing waited for ever will.
                log.warning('Rpc pipeline stalled, failing the connection: %r', d)
                self._abort_driver()
                self._report_driver_done(RpcConnectionClosedError('rpc pipeline stalled'))
                return
            self._report_driver_done(e)
            return

        except Exception as e:  # noqa
            # A transport failure: the driver has failed itself and destroyed the pipeline.
            self._report_driver_done(e)
            return

        finally:
            d.wait_timeout_s = None

        if out is None:
            self._check_driver_stopped()
            return

        await self._deliver(out)


##


def _rpc_syncs_try_set_nodelay(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as e:
        if e.errno != errno.ENOPROTOOPT:
            raise


class SyncRpcConnections:
    """
    Factories taping a sync connection onto sockets, file descriptor pairs, a subprocess's stdio, or our own.

    Sockets are left with no timeout: every timeout is enforced by the session, and a socket timeout would surface as a
    spurious timeout from the pump. Connection keyword arguments (`handler`, `id_creator`, ...) pass through.
    """

    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    @staticmethod
    def of_driver(
            driver: SyncIoPipelineDriver,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> SyncRpcConnection:
        return SyncRpcConnection(RpcConnection(
            SyncRpcRuntime(driver, closers=closers),
            config,
            **kwargs,
        ))

    @classmethod
    def of_socket(
            cls,
            sock: socket.socket,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            close_socket: bool = True,
            driver_config: ta.Optional[SyncIoPipelineDriver.Config] = None,
            spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> SyncRpcConnection:
        """
        The socket is closed when the connection closes unless `close_socket` is false. TLS is a transport handler:
        `spec_kwargs=dict(transport_handlers=[SslIoPipelineHandler(...)])`.
        """

        spec = rpc_build_pipeline_spec(
            config,
            **(spec_kwargs or {}),
        )
        return cls.of_driver(
            SocketSyncIoPipelineDriver(spec, sock, driver_config),
            config,
            closers=[*([sock.close] if close_socket else []), *closers],
            **kwargs,
        )

    @classmethod
    def of_fds(
            cls,
            read_fd: int,
            write_fd: int,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            close_fds: bool = False,
            driver_config: ta.Optional[SyncIoPipelineDriver.Config] = None,
            spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> SyncRpcConnection:
        """The descriptors are left open when the connection closes unless `close_fds` is true."""

        spec = rpc_build_pipeline_spec(
            config,
            **(spec_kwargs or {}),
        )

        def close_fds_() -> None:
            for fd in {read_fd, write_fd}:
                try:
                    os.close(fd)
                except OSError:
                    pass

        return cls.of_driver(
            FdSyncIoPipelineDriver(spec, read_fd, write_fd, driver_config),
            config,
            closers=[*([close_fds_] if close_fds else []), *closers],
            **kwargs,
        )

    @classmethod
    def connect_tcp(
            cls,
            host: str,
            port: int,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            connect_timeout_s: ta.Optional[float] = 10.,
            **kwargs: ta.Any,
    ) -> SyncRpcConnection:
        sock = socket.create_connection((host, port), timeout=connect_timeout_s)
        try:
            sock.settimeout(None)
            _rpc_syncs_try_set_nodelay(sock)

            return cls.of_socket(sock, config, **kwargs)

        except BaseException:
            sock.close()
            raise

    @classmethod
    def connect_unix(
            cls,
            path: str,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            connect_timeout_s: ta.Optional[float] = 10.,
            **kwargs: ta.Any,
    ) -> SyncRpcConnection:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(connect_timeout_s)
            sock.connect(path)
            sock.settimeout(None)
            return cls.of_socket(sock, config, **kwargs)

        except BaseException:
            sock.close()
            raise

    @classmethod
    def of_subprocess(
            cls,
            proc: subprocess.Popen,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> SyncRpcConnection:
        """
        Talks to a child process over its stdio. The process must have been created with piped stdin and stdout. Its
        stdin is closed when the connection closes so it sees EOF.
        """

        stdin = check.not_none(proc.stdin)
        return cls.of_fds(
            check.not_none(proc.stdout).fileno(),
            stdin.fileno(),
            config,
            closers=[stdin.close, *closers],
            **kwargs,
        )

    @classmethod
    def of_stdio(
            cls,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            stdin: ta.Optional[ta.IO] = None,
            stdout: ta.Optional[ta.IO] = None,
            **kwargs: ta.Any,
    ) -> SyncRpcConnection:
        """Serves or talks over this process's own stdio."""

        return cls.of_fds(
            (stdin if stdin is not None else sys.stdin).fileno(),
            (stdout if stdout is not None else sys.stdout).fileno(),
            config,
            **kwargs,
        )
