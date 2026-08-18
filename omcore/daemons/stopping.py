import enum
import os
import signal

from .. import check
from .. import dataclasses as dc
from .. import lang
from ..os.pidfiles.pinning import LslocksPidfdPidfilePinner
from ..os.pidfiles.pinning import PidfilePinner
from ..os.pidfiles.pinning import UnverifiedPidfilePinner
from .inspection import DaemonInspection
from .inspection import DaemonInspector
from .operations import DaemonStoppedWaiter
from .operations import DaemonWaitStoppedResult
from .operations import DaemonWaitStoppedTimeoutError
from .operations import _inspection_was_replaced


##


class DaemonStopSafety(enum.Enum):
    REQUIRE_VERIFIED = enum.auto()
    ALLOW_UNVERIFIED = enum.auto()


@dc.dataclass(frozen=True, kw_only=True)
class DaemonStopResult:
    pid: int | None
    signal: int
    signal_sent: bool
    wait_result: DaemonWaitStoppedResult

    @property
    def stopped(self) -> bool:
        return self.wait_result.stopped

    @property
    def replaced(self) -> bool:
        return self.wait_result.replaced


class DaemonStopError(RuntimeError):
    pass


class DaemonStopUnavailableError(DaemonStopError):
    pass


class DaemonStopIdentityError(DaemonStopError):
    pass


class DaemonStopSignalError(DaemonStopError):
    pass


class DaemonStopTimeoutError(DaemonStopError, TimeoutError):
    def __init__(
            self,
            *,
            initial: DaemonInspection,
            last: DaemonInspection,
            pid: int | None,
            signal: int,
            signal_sent: bool,
    ) -> None:
        super().__init__(f'Timed out stopping daemon: {initial.pid_file!r}')

        self._initial = initial
        self._last = last
        self._pid = pid
        self._signal = signal
        self._signal_sent = signal_sent

    @property
    def initial(self) -> DaemonInspection:
        return self._initial

    @property
    def last(self) -> DaemonInspection:
        return self._last

    @property
    def pid(self) -> int | None:
        return self._pid

    @property
    def signal(self) -> int:
        return self._signal

    @property
    def signal_sent(self) -> bool:
        return self._signal_sent


##


class DaemonStopper(lang.Final):
    def __init__(
            self,
            pid_file: str,
            *,
            pinner: PidfilePinner | None = None,
            safety: DaemonStopSafety = DaemonStopSafety.REQUIRE_VERIFIED,
            sleep_s: float = DaemonStoppedWaiter.DEFAULT_SLEEP_S,
    ) -> None:
        super().__init__()

        self._pid_file = check.non_empty_str(pid_file)
        self._pinner = pinner
        self._safety = check.isinstance(safety, DaemonStopSafety)
        self._sleep_s = sleep_s

        self._inspector = DaemonInspector(self._pid_file)
        self._stopped_waiter = DaemonStoppedWaiter(
            self._pid_file,
            sleep_s=sleep_s,
        )

    @property
    def pid_file(self) -> str:
        return self._pid_file

    def _get_pinner(self) -> PidfilePinner:
        if (pinner := self._pinner) is None:
            pinner = PidfilePinner.default_impl()(sleep_s=self._sleep_s)

        if (
                self._safety is DaemonStopSafety.REQUIRE_VERIFIED and
                isinstance(pinner, UnverifiedPidfilePinner)
        ):
            raise DaemonStopUnavailableError(
                'No verified pidfile-owner pinner is available; '
                'select ALLOW_UNVERIFIED to permit raw PID signaling',
            )

        return pinner

    @staticmethod
    def _validate_identity(
            initial: DaemonInspection,
            current: DaemonInspection,
            pinned_pid: int,
    ) -> None:
        if _inspection_was_replaced(initial, current):
            raise DaemonStopIdentityError('Daemon identity was replaced before signaling')
        if not current.running:
            raise DaemonStopIdentityError('Daemon stopped before signaling')
        if initial.pidfile_error is not None or current.pidfile_error is not None:
            raise DaemonStopIdentityError('Daemon pidfile identity is malformed')
        if initial.pid is None or current.pid is None:
            raise DaemonStopIdentityError('Daemon pidfile does not contain a PID')
        if initial.pid != pinned_pid or current.pid != pinned_pid:
            raise DaemonStopIdentityError(f'Pidfile owner {pinned_pid} does not match recorded daemon PID')
        if initial.info is not None and current.info is None:
            raise DaemonStopIdentityError('Structured daemon identity disappeared before signaling')

    def _wait(
            self,
            *,
            initial: DaemonInspection,
            timeout: lang.Timeout,
            pid: int | None,
            signum: int,
            signal_sent: bool,
    ) -> DaemonStopResult:
        try:
            wait_result = self._stopped_waiter.wait(
                initial=initial,
                timeout=timeout,
            )
        except DaemonWaitStoppedTimeoutError as exc:
            raise DaemonStopTimeoutError(
                initial=exc.initial,
                last=exc.last,
                pid=pid,
                signal=signum,
                signal_sent=signal_sent,
            ) from exc

        return DaemonStopResult(
            pid=pid,
            signal=signum,
            signal_sent=signal_sent,
            wait_result=wait_result,
        )

    def _send_signal(
            self,
            *,
            pinner: PidfilePinner,
            pinned_pid: int,
            initial: DaemonInspection,
            signum: int,
    ) -> bool:
        if isinstance(pinner, LslocksPidfdPidfilePinner):
            pidfd_open = getattr(os, 'pidfd_open', None)
            pidfd_send_signal = getattr(signal, 'pidfd_send_signal', None)
            if pidfd_open is None or pidfd_send_signal is None:
                raise DaemonStopUnavailableError('Verified Linux stop requires pidfd_open and pidfd_send_signal')

            try:
                pidfd = pidfd_open(pinned_pid)
            except ProcessLookupError:
                return False
            except OSError as exc:
                raise DaemonStopSignalError(f'Failed to open daemon pidfd: {exc}') from exc

            try:
                self._validate_identity(initial, self._inspector.inspect(), pinned_pid)
                try:
                    pidfd_send_signal(pidfd, signum)
                except ProcessLookupError:
                    return False
                except OSError as exc:
                    raise DaemonStopSignalError(f'Failed to signal daemon process: {exc}') from exc
            finally:
                os.close(pidfd)

        else:
            self._validate_identity(initial, self._inspector.inspect(), pinned_pid)
            try:
                os.kill(pinned_pid, signum)
            except ProcessLookupError:
                return False
            except OSError as exc:
                raise DaemonStopSignalError(f'Failed to signal daemon process: {exc}') from exc

        return True

    def stop(
            self,
            *,
            initial: DaemonInspection | None = None,
            signum: int = signal.SIGTERM,
            timeout: lang.TimeoutLike = DaemonStoppedWaiter.DEFAULT_TIMEOUT_S,
    ) -> DaemonStopResult:
        check.arg(signum in signal.valid_signals())
        timeout_ = lang.Timeout.of(timeout)

        if initial is None:
            initial = self._inspector.inspect()
        else:
            check.arg(initial.pid_file == self._pid_file)

        if not initial.running:
            return self._wait(
                initial=initial,
                timeout=timeout_,
                pid=None,
                signum=signum,
                signal_sent=False,
            )
        if initial.pidfile_error is not None or initial.pid is None:
            raise DaemonStopIdentityError('Daemon pidfile does not contain a valid identity')

        current = self._inspector.inspect()
        if not current.running or _inspection_was_replaced(initial, current):
            return self._wait(
                initial=initial,
                timeout=timeout_,
                pid=None,
                signum=signum,
                signal_sent=False,
            )

        pinner = self._get_pinner()
        pinned_pid: int | None = None
        signal_sent = False
        try:
            with pinner.pin_pidfile_owner(
                    self._pid_file,
                    timeout=timeout_,
                    no_create=True,
            ) as pinned_pid:
                self._validate_identity(initial, self._inspector.inspect(), pinned_pid)
                signal_sent = self._send_signal(
                    pinner=pinner,
                    pinned_pid=pinned_pid,
                    initial=initial,
                    signum=signum,
                )

        except PidfilePinner.NoOwnerError:
            pass
        except TimeoutError as exc:
            raise DaemonStopTimeoutError(
                initial=initial,
                last=self._inspector.inspect(),
                pid=pinned_pid,
                signal=signum,
                signal_sent=signal_sent,
            ) from exc

        return self._wait(
            initial=initial,
            timeout=timeout_,
            pid=pinned_pid,
            signum=signum,
            signal_sent=signal_sent,
        )


def stop_daemon(
        pid_file: str,
        *,
        initial: DaemonInspection | None = None,
        signum: int = signal.SIGTERM,
        timeout: lang.TimeoutLike = DaemonStoppedWaiter.DEFAULT_TIMEOUT_S,
        pinner: PidfilePinner | None = None,
        safety: DaemonStopSafety = DaemonStopSafety.REQUIRE_VERIFIED,
        sleep_s: float = DaemonStoppedWaiter.DEFAULT_SLEEP_S,
) -> DaemonStopResult:
    return DaemonStopper(
        pid_file,
        pinner=pinner,
        safety=safety,
        sleep_s=sleep_s,
    ).stop(
        initial=initial,
        signum=signum,
        timeout=timeout,
    )
