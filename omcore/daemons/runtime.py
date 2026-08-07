import enum
import math
import signal
import threading
import time
import types
import typing as ta

from .. import check
from .. import dataclasses as dc


##


class ShutdownReason(enum.Enum):
    REQUESTED = enum.auto()
    IDLE = enum.auto()
    SIGNAL = enum.auto()


@dc.dataclass(frozen=True, kw_only=True)
class ShutdownRequest:
    reason: ShutdownReason
    requested_at: float

    message: str | None = None
    signal: int | None = None


class ActivityRejectedError(RuntimeError):
    def __init__(self, request: ShutdownRequest) -> None:
        super().__init__(f'Activity rejected after shutdown was requested: {request.reason.name}')

        self._request = request

    @property
    def request(self) -> ShutdownRequest:
        return self._request


class DrainTimeoutError(TimeoutError):
    pass


##


class _ServiceRuntimeState:
    def __init__(
            self,
            config: ServiceRuntime.Config,
            clock: ta.Callable[[], float],
    ) -> None:
        super().__init__()

        self.config = config
        self.clock = clock

        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)

        self.started = False
        self.closed = False

        self.shutdown_request: ShutdownRequest | None = None

        self.active_count = 0
        self.idle_deadline: float | None = None

    def request_shutdown_locked(
            self,
            reason: ShutdownReason,
            *,
            message: str | None = None,
            signal: int | None = None,  # noqa
    ) -> bool:
        if self.shutdown_request is not None:
            return False

        self.shutdown_request = ShutdownRequest(
            reason=reason,
            requested_at=self.clock(),
            message=message,
            signal=signal,
        )
        self.condition.notify_all()
        return True


##


class ShutdownController:
    def __init__(self, state: _ServiceRuntimeState) -> None:
        super().__init__()

        self._state = state

    @property
    def request_(self) -> ShutdownRequest | None:
        with self._state.lock:
            return self._state.shutdown_request

    @property
    def requested(self) -> bool:
        return self.request_ is not None

    def request(
            self,
            reason: ShutdownReason = ShutdownReason.REQUESTED,
            *,
            message: str | None = None,
            signal: int | None = None,  # noqa
    ) -> bool:
        with self._state.condition:
            return self._state.request_shutdown_locked(
                reason,
                message=message,
                signal=signal,
            )

    def wait(self, timeout_s: float | None = None) -> ShutdownRequest | None:
        deadline = time.monotonic() + timeout_s if timeout_s is not None else None

        with self._state.condition:
            while self._state.shutdown_request is None:
                if deadline is None:
                    self._state.condition.wait()
                    continue

                remaining_s = deadline - time.monotonic()
                if remaining_s <= 0.:
                    return None
                self._state.condition.wait(remaining_s)

            return self._state.shutdown_request


##


class Activity:
    def __init__(self, lease: ActivityLease) -> None:
        super().__init__()

        self._lease = lease
        self._lock = threading.Lock()
        self._closed = False

    def close(self) -> bool:
        with self._lock:
            if self._closed:
                return False
            self._closed = True

        self._lease._release()  # noqa
        return True

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ActivityLease:
    def __init__(self, state: _ServiceRuntimeState) -> None:
        super().__init__()

        self._state = state

    @property
    def active_count(self) -> int:
        with self._state.lock:
            return self._state.active_count

    @property
    def idle_timeout_s(self) -> float | None:
        return self._state.config.idle_timeout_s

    @property
    def idle_deadline(self) -> float | None:
        with self._state.lock:
            return self._state.idle_deadline

    def acquire(self) -> Activity:
        with self._state.condition:
            if (request := self._state.shutdown_request) is not None:
                raise ActivityRejectedError(request)
            if self._state.closed:
                raise RuntimeError('Service runtime is closed')

            self._state.active_count += 1
            self._state.idle_deadline = None
            self._state.condition.notify_all()

        return Activity(self)

    def _release(self) -> None:
        with self._state.condition:
            check.state(self._state.active_count > 0)

            self._state.active_count -= 1
            if not self._state.active_count and self._state.config.idle_timeout_s is not None:
                self._state.idle_deadline = self._state.clock() + self._state.config.idle_timeout_s
            self._state.condition.notify_all()

    def touch(self) -> None:
        with self._state.condition:
            if not self._state.active_count and self._state.config.idle_timeout_s is not None:
                self._state.idle_deadline = self._state.clock() + self._state.config.idle_timeout_s
            self._state.condition.notify_all()

    def wait_inactive(self, timeout_s: float | None = None) -> bool:
        deadline = time.monotonic() + timeout_s if timeout_s is not None else None

        with self._state.condition:
            while self._state.active_count:
                if deadline is None:
                    self._state.condition.wait()
                    continue

                remaining_s = deadline - time.monotonic()
                if remaining_s <= 0.:
                    return False
                self._state.condition.wait(remaining_s)

            return True


##


class ServiceRuntime:
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        idle_timeout_s: float | None = None
        drain_timeout_s: float | None = 30.

        no_signals: bool = False
        shutdown_signals: tuple[int, ...] = (signal.SIGINT, signal.SIGTERM)

        def __post_init__(self) -> None:
            for timeout_s in [self.idle_timeout_s, self.drain_timeout_s]:
                if timeout_s is not None:
                    check.arg(math.isfinite(timeout_s))
                    check.arg(timeout_s > 0.)

    def __init__(
            self,
            config: Config = Config(),
            *,
            clock: ta.Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__()

        self._config = config
        self._state = _ServiceRuntimeState(config, clock)

        self._shutdown = ShutdownController(self._state)
        self._activity = ActivityLease(self._state)

        self._idle_thread: threading.Thread | None = None
        self._old_signal_handlers: dict[int, ta.Any] = {}

    @property
    def config(self) -> Config:
        return self._config

    @property
    def shutdown(self) -> ShutdownController:
        return self._shutdown

    @property
    def activity(self) -> ActivityLease:
        return self._activity

    def _run_idle_monitor(self) -> None:
        with self._state.condition:
            while not self._state.closed and self._state.shutdown_request is None:
                if self._state.active_count or self._state.idle_deadline is None:
                    self._state.condition.wait()
                    continue

                remaining_s = self._state.idle_deadline - self._state.clock()
                if remaining_s > 0.:
                    self._state.condition.wait(remaining_s)
                    continue

                self._state.request_shutdown_locked(ShutdownReason.IDLE)

    def _handle_signal(self, signum: int, frame: types.FrameType | None) -> None:
        self._shutdown.request(
            ShutdownReason.SIGNAL,
            signal=signum,
        )

    def _install_signal_handlers(self) -> None:
        if self._config.no_signals or threading.current_thread() is not threading.main_thread():
            return

        for signum in self._config.shutdown_signals:
            self._old_signal_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, self._handle_signal)

    def _restore_signal_handlers(self) -> None:
        for signum, handler in self._old_signal_handlers.items():
            signal.signal(signum, handler)
        self._old_signal_handlers.clear()

    def __enter__(self) -> ta.Self:
        with self._state.condition:
            check.state(not self._state.started)
            check.state(not self._state.closed)

            self._state.started = True
            if self._config.idle_timeout_s is not None:
                self._state.idle_deadline = self._state.clock() + self._config.idle_timeout_s

        try:
            self._install_signal_handlers()

            if self._config.idle_timeout_s is not None:
                self._idle_thread = threading.Thread(
                    target=self._run_idle_monitor,
                    name='ServiceRuntimeIdleMonitor',
                    daemon=True,
                )
                self._idle_thread.start()

        except BaseException:
            self.close()
            raise

        return self

    def close(self) -> bool:
        with self._state.condition:
            if self._state.closed:
                return False
            self._state.closed = True
            self._state.condition.notify_all()

        if self._idle_thread is not None:
            self._idle_thread.join()
            self._idle_thread = None

        self._restore_signal_handlers()
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
