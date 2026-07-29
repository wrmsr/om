# ruff: noqa: UP006 UP007 UP045
import math
import time
import typing as ta

from .handlers import FdioHandler
from .pollers import FdioPoller


##


class FdioManager:
    def __init__(
            self,
            poller: FdioPoller,
    ) -> None:
        super().__init__()

        self._poller = poller

        self._handlers: ta.Dict[int, FdioHandler] = {}  # Preserves insertion order

    def register(self, h: FdioHandler) -> None:
        if (hid := id(h)) in self._handlers:
            raise KeyError(h)
        self._handlers[hid] = h

    def unregister(self, h: FdioHandler) -> None:
        del self._handlers[id(h)]

    @staticmethod
    def _validate_timeout(timeout: float) -> float:
        if timeout < 0. or not math.isfinite(timeout):
            raise ValueError(timeout)
        return timeout

    def _poll_timeout(
            self,
            hs: ta.Iterable[FdioHandler],
            timeout: ta.Optional[float],
    ) -> ta.Optional[float]:
        if timeout is not None:
            timeout = self._validate_timeout(timeout)

        now = time.monotonic()
        for h in hs:
            if (deadline := h.next_deadline()) is None:
                continue
            if not math.isfinite(deadline):
                raise ValueError(deadline)

            delay = max(0., deadline - now)
            if timeout is None or delay < timeout:
                timeout = delay

        return timeout

    def _is_registered(self, h: FdioHandler) -> bool:
        return self._handlers.get(id(h)) is h

    def poll(self, *, timeout: ta.Optional[float] = None) -> None:
        """Wait for descriptor readiness or the earliest handler deadline, then dispatch all work that is ready."""

        hs = [h for h in self._handlers.values() if not h.closed]
        rd = {h.fd(): h for h in hs if h.readable()}
        wd = {h.fd(): h for h in hs if h.writable()}

        self._poller.update(set(rd), set(wd))

        pr = self._poller.poll(self._poll_timeout(hs, timeout))

        for f in pr.r:
            if self._is_registered(h := rd[f]) and not h.closed:
                h.on_readable()
        for f in pr.w:
            if self._is_registered(h := wd[f]) and not h.closed:
                h.on_writable()

        for h in list(self._handlers.values()):
            if not self._is_registered(h) or h.closed:
                continue
            if (deadline := h.next_deadline()) is not None and deadline <= time.monotonic():
                h.on_timeout()

        self._handlers = {id(h): h for h in self._handlers.values() if not h.closed}
