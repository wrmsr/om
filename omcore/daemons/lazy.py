import threading
import time
import typing as ta

from .. import check
from .. import lang
from .daemon import Daemon
from .waiting import waiter_for


T = ta.TypeVar('T')


##


class LazyDaemon(lang.Final):
    """Coordinates on-demand access to an idle-exiting daemon."""

    def __init__(self, daemon: Daemon) -> None:
        """Constructs a controller around a daemon with readiness and pidfile configuration."""

        super().__init__()

        check.arg(daemon.has_pidfile, 'Lazy daemons require a pidfile')
        check.arg(daemon.config.wait is not None, 'Lazy daemons require a readiness wait')

        self._daemon = daemon
        self._ensure_lock = threading.Lock()

    @property
    def daemon(self) -> Daemon:
        return self._daemon

    def is_ready(self) -> bool:
        return waiter_for(check.not_none(self._daemon.config.wait)).do_wait()

    def _acquire_ensure_lock(self, timeout: lang.Timeout) -> None:
        if timeout.can_expire:
            if not self._ensure_lock.acquire(timeout=timeout()):
                raise TimeoutError('Timed out waiting to ensure lazy daemon')
        else:
            self._ensure_lock.acquire()

    def ensure(
            self,
            timeout: lang.TimeoutLike = lang.Timeout.DEFAULT,
    ) -> bool:
        """Waits until the daemon is ready, launching it if necessary, and returns whether this call launched it."""

        timeout_ = lang.Timeout.of(timeout, self._daemon.config.wait_timeout)
        self._acquire_ensure_lock(timeout_)

        try:
            launched = False

            while True:
                timeout_()

                if self.is_ready():
                    return launched

                if not self._daemon.is_pidfile_locked():
                    launched = self._daemon.launch_no_wait() or launched

                time.sleep(min(self._daemon.config.wait_sleep_s or 0., timeout_()))

        finally:
            self._ensure_lock.release()

    def call(
            self,
            fn: ta.Callable[[], T],
            *,
            is_unavailable: ta.Callable[[Exception], bool],
            timeout: lang.TimeoutLike = lang.Timeout.DEFAULT,
    ) -> T:
        """Calls a retry-safe operation, launching or relaunching the daemon when it is explicitly unavailable."""

        timeout_ = lang.Timeout.of(timeout, self._daemon.config.wait_timeout)

        while True:
            timeout_()

            try:
                return fn()
            except Exception as exc:
                if not is_unavailable(exc):
                    raise

            self.ensure(timeout_)
