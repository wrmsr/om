import enum
import math
import os
import time

from .. import check
from .. import dataclasses as dc
from .. import lang
from ..os.pidfiles.pidfile import Pidfile
from .inspection import DaemonInspection
from .inspection import DaemonInspector


##


class DaemonWaitStoppedReason(enum.Enum):
    ALREADY_STOPPED = enum.auto()
    STOPPED = enum.auto()
    REPLACED = enum.auto()


@dc.dataclass(frozen=True, kw_only=True)
class DaemonWaitStoppedResult:
    reason: DaemonWaitStoppedReason
    initial: DaemonInspection
    final: DaemonInspection

    @property
    def stopped(self) -> bool:
        return self.reason in (
            DaemonWaitStoppedReason.ALREADY_STOPPED,
            DaemonWaitStoppedReason.STOPPED,
        )

    @property
    def replaced(self) -> bool:
        return self.reason is DaemonWaitStoppedReason.REPLACED


class DaemonWaitStoppedTimeoutError(TimeoutError):
    def __init__(
            self,
            initial: DaemonInspection,
            last: DaemonInspection,
    ) -> None:
        super().__init__(f'Timed out waiting for daemon to stop: {initial.pid_file!r}')

        self._initial = initial
        self._last = last

    @property
    def initial(self) -> DaemonInspection:
        return self._initial

    @property
    def last(self) -> DaemonInspection:
        return self._last


##


def _inspection_was_replaced(
        initial: DaemonInspection,
        current: DaemonInspection,
) -> bool:
    if current.pidfile_inode != initial.pidfile_inode:
        return True

    if initial.info is not None and current.info is not None:
        if current.info.instance_id != initial.info.instance_id:
            return True

    if initial.pid is not None and current.pid is not None:
        if current.pid != initial.pid:
            return True

    return False


class DaemonStoppedWaiter(lang.Final):
    DEFAULT_TIMEOUT_S = 10.
    DEFAULT_SLEEP_S = .05

    def __init__(
            self,
            pid_file: str,
            *,
            sleep_s: float = DEFAULT_SLEEP_S,
    ) -> None:
        super().__init__()

        self._pid_file = check.non_empty_str(pid_file)
        check.arg(math.isfinite(sleep_s))
        check.arg(sleep_s >= 0.)
        self._sleep_s = sleep_s

        self._inspector = DaemonInspector(self._pid_file)

    @property
    def pid_file(self) -> str:
        return self._pid_file

    def _result(
            self,
            reason: DaemonWaitStoppedReason,
            initial: DaemonInspection,
    ) -> DaemonWaitStoppedResult:
        return DaemonWaitStoppedResult(
            reason=reason,
            initial=initial,
            final=self._inspector.inspect(),
        )

    def wait(
            self,
            *,
            initial: DaemonInspection | None = None,
            timeout: lang.TimeoutLike = DEFAULT_TIMEOUT_S,
    ) -> DaemonWaitStoppedResult:
        if initial is None:
            initial = self._inspector.inspect()
        else:
            check.arg(initial.pid_file == self._pid_file)

        if not initial.running:
            return DaemonWaitStoppedResult(
                reason=DaemonWaitStoppedReason.ALREADY_STOPPED,
                initial=initial,
                final=initial,
            )

        initial_inode = check.not_none(initial.pidfile_inode)
        timeout_ = lang.Timeout.of(timeout)
        last = initial

        try:
            pidfile_context = Pidfile(
                self._pid_file,
                inheritable=False,
                no_create=True,
            )
            with pidfile_context as pidfile:
                fd = check.not_none(pidfile.fileno())
                fd_stat = os.fstat(fd)
                if initial_inode != (fd_stat.st_dev, fd_stat.st_ino):
                    return self._result(DaemonWaitStoppedReason.REPLACED, initial)

                while True:
                    if pidfile.try_acquire_lock():
                        reason = DaemonWaitStoppedReason.STOPPED
                        break

                    current = self._inspector.inspect()
                    last = current
                    if _inspection_was_replaced(initial, current):
                        return self._result(DaemonWaitStoppedReason.REPLACED, initial)

                    if timeout_.expired():
                        raise DaemonWaitStoppedTimeoutError(initial, last)

                    time.sleep(max(0., min(self._sleep_s, timeout_.remaining())))

        except FileNotFoundError:
            return self._result(DaemonWaitStoppedReason.REPLACED, initial)

        return self._result(reason, initial)


def wait_daemon_stopped(
        pid_file: str,
        *,
        initial: DaemonInspection | None = None,
        timeout: lang.TimeoutLike = DaemonStoppedWaiter.DEFAULT_TIMEOUT_S,
        sleep_s: float = DaemonStoppedWaiter.DEFAULT_SLEEP_S,
) -> DaemonWaitStoppedResult:
    return DaemonStoppedWaiter(
        pid_file,
        sleep_s=sleep_s,
    ).wait(
        initial=initial,
        timeout=timeout,
    )
