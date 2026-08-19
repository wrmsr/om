"""
Exit observation without reaping: one small daemon thread per child blocks in `waitid(P_PID, pid, WEXITED | WNOWAIT)`
and hands the result back to the owner via a thread-safe `post` callable (for asyncio, `loop.call_soon_threadsafe`).
The child stays a zombie - its pid and pgid remain unrecyclable and therefore safe to signal - until the handle
deliberately reaps it. (This is the same shape as 3.14's own threaded child watcher, but under our control: it never
reaps.) A Linux pidfd path is a possible thread-free replacement.
"""
import os
import threading
import typing as ta

from omcore.logs import all as logs


log = logs.get_module_logger(globals())


##


def waitid_returncode(si_code: int, si_status: int) -> int:
    if si_code == os.CLD_EXITED:
        return si_status
    # CLD_KILLED / CLD_DUMPED: si_status is the signal number.
    return -si_status


class ExitWatcher:
    def __init__(
            self,
            pid: int,
            *,
            post: ta.Callable[..., None],
            on_exit: ta.Callable[[int], None],
            on_error: ta.Callable[[BaseException], None],
    ) -> None:
        """
        `post(fn, *args)` must schedule `fn(*args)` on the owner's thread, raising RuntimeError if it no longer can.
        """

        super().__init__()

        self._pid = pid
        self._post = post
        self._on_exit = on_exit
        self._on_error = on_error

        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError('Already started')
        self._thread = t = threading.Thread(
            target=self._run,
            name=f'processes-exit-watcher-{self._pid}',
            daemon=True,
        )
        t.start()

    def _call(self, fn: ta.Callable, *args: ta.Any) -> None:
        try:
            self._post(fn, *args)
        except RuntimeError:
            # Owner gone underneath us (loop closed) - nothing to notify.
            log.warning('processes exit watcher for pid %d: owner gone before exit could be delivered', self._pid)

    def _run(self) -> None:
        pid = self._pid
        try:
            while True:
                res = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT)
                if res is None:  # pragma: no cover
                    continue
                self._call(self._on_exit, waitid_returncode(res.si_code, res.si_status))
                return
        except BaseException as e:  # noqa
            # ChildProcessError here means something else reaped our child - the caller poisons the handle.
            self._call(self._on_error, e)
