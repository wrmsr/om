# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import collections
import os
import threading
import typing as ta

from .handlers import FdioHandler


##


class WakeupFdioHandler(FdioHandler):
    """
    A self-pipe registered with an `FdioManager`: `wake()` makes the manager's poll return, and `post()` hands a
    callback to the manager's thread, where it runs from this handler's dispatch. Both may be called from any thread -
    the one deliberate cross-thread entry into an fdio loop, for the few things which must happen elsewhere, such as
    name resolution on a worker thread or a signal handler. Everything else about the loop remains single-threaded.
    """

    def __init__(self) -> None:
        super().__init__()

        r, w = os.pipe()
        os.set_blocking(r, False)
        os.set_blocking(w, False)
        self._r: ta.Optional[int] = r
        self._w: ta.Optional[int] = w

        self._lock = threading.Lock()
        self._callbacks: ta.Deque[ta.Callable[[], None]] = collections.deque()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    #

    def wake(self) -> None:
        """Thread-safe."""

        if (w := self._w) is None:
            return
        try:
            os.write(w, b'\0')
        except BlockingIOError:
            pass  # A wake is already pending.
        except OSError:
            pass  # Closed meanwhile.

    def post(self, fn: ta.Callable[[], None]) -> None:
        """Thread-safe: `fn` runs on the manager's thread, in order with other posts, at the next poll."""

        with self._lock:
            self._callbacks.append(fn)
        self.wake()

    #

    def fd(self) -> int:
        if (r := self._r) is None:
            raise ValueError('closed')
        return r

    @property
    def closed(self) -> bool:
        return self._r is None

    def close(self) -> None:
        r, w = self._r, self._w
        self._r = self._w = None
        for fd in (w, r):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        with self._lock:
            self._callbacks.clear()

    def readable(self) -> bool:
        return self._r is not None

    def on_readable(self) -> None:
        if (r := self._r) is None:
            return

        while True:
            try:
                if not os.read(r, 4096):
                    break
            except BlockingIOError:
                break
            except OSError:
                break

        with self._lock:
            callbacks = list(self._callbacks)
            self._callbacks.clear()

        for fn in callbacks:
            fn()
