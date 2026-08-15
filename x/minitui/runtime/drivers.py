"""
The synchronous driver: one loop owning input, timers, and frame scheduling.

The app is passive and pure-ish: it renders frames on demand and handles typed events; all pacing lives here. Redraws
coalesce through a single `invalidate()` flag - any number of invalidations between iterations costs one render, and
the retained-frame diff downstream makes even that render cheap when nothing visibly changed.

Wakeups: input fd readability, timer deadlines, the escape-parser's pending timeout, and a self-pipe written by the
signal machinery (Python's poll retries EINTR per PEP 475, so SIGWINCH would otherwise not wake the loop at all).
"""
import abc
import codecs
import os
import select
import signal
import time
import typing as ta

from omcore import check
from omcore import lang

from ..events.parsing import Read1
from ..events.types import Event
from ..events.types import ResizeEvent
from ..events.xterm import XtermEventParser
from ..screens.cells import Frame
from ..screens.cells import Line
from ..surfaces.inlines import InlineSurface
from .timers import Timers


##


class App(lang.Abstract):
    @abc.abstractmethod
    def render(self, width: int, max_height: int) -> Frame:
        """Build the live-region frame. Must fit: height <= max_height, content wrapped to width."""

        raise NotImplementedError

    @abc.abstractmethod
    def handle_event(self, event: Event) -> None:
        raise NotImplementedError


class SyncDriver:
    def __init__(
            self,
            surface: InlineSurface,
            *,
            clock: ta.Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__()

        self._surface = surface
        self._clock = clock

        self._parser = XtermEventParser()
        self._timers = Timers(clock)
        self._decoder = codecs.getincrementaldecoder('utf-8')('replace')

        self._invalidated = True
        self._running = False

        self._parser_deadline: float | None = None
        self._parser_pending: Read1 | None = None

    @property
    def surface(self) -> InlineSurface:
        return self._surface

    @property
    def timers(self) -> Timers:
        return self._timers

    @property
    def parser(self) -> XtermEventParser:
        return self._parser

    #

    def invalidate(self) -> None:
        self._invalidated = True

    def commit(self, lines: ta.Sequence[Line]) -> None:
        self._surface.commit(lines)
        self._invalidated = True

    def stop(self) -> None:
        self._running = False

    def _stopped(self) -> bool:
        # Also defeats mypy's (unsound here) attribute narrowing: handlers may call stop() mid-iteration.
        return not self._running

    #

    def _track_parser_deadline(self) -> None:
        pending = self._parser.pending_read
        if pending.timeout_s is None:
            self._parser_deadline = None
        elif pending is not self._parser_pending:
            self._parser_deadline = self._clock() + pending.timeout_s
        self._parser_pending = pending

    def _dispatch(self, app: App, events: ta.Iterable[Event]) -> None:
        for event in events:
            app.handle_event(event)

    def _next_deadline(self) -> float | None:
        deadline = self._timers.next_fire_at()
        if self._parser_deadline is not None:
            deadline = min(deadline, self._parser_deadline) if deadline is not None else self._parser_deadline
        return deadline

    def _render(self, app: App) -> None:
        self._invalidated = False
        surface = self._surface
        frame = app.render(surface.width, surface.height)
        surface.present(frame)

    def run(self, app: App) -> None:
        check.state(not self._running)
        self._running = True

        surface = self._surface
        surface.prepare()

        # PEP 475 makes poll() retry on EINTR, so signals need a self-pipe to actually wake the loop.
        wake_r, wake_w = os.pipe()
        os.set_blocking(wake_r, False)
        os.set_blocking(wake_w, False)
        old_wakeup = signal.set_wakeup_fd(wake_w, warn_on_full_buffer=False)

        input_fd = surface.tty.input_fd
        poller = select.poll()
        poller.register(input_fd, select.POLLIN)
        poller.register(wake_r, select.POLLIN)

        try:
            while self._running:
                if surface.take_resized():
                    app.handle_event(ResizeEvent(surface.height, surface.width))
                    self._invalidated = True
                    if self._stopped():
                        continue

                if self._invalidated:
                    self._render(app)

                now = self._clock()
                deadline = self._next_deadline()
                timeout_ms: int | None = None
                if deadline is not None:
                    timeout_ms = max(int((deadline - now) * 1000), 0)

                ready = {fd for fd, _ in poller.poll(timeout_ms)}

                if wake_r in ready:
                    while True:
                        try:
                            if not os.read(wake_r, 4096):
                                break
                        except BlockingIOError:
                            break

                if input_fd in ready:
                    data = os.read(input_fd, 4096)
                    if not data:
                        # Input EOF: no more bytes are ever coming, so resolve any pending escape immediately.
                        self._dispatch(app, self._parser.flush_timeout())
                        break
                    self._dispatch(app, self._parser.feed(self._decoder.decode(data)))
                    self._track_parser_deadline()

                now = self._clock()
                if self._parser_deadline is not None and now >= self._parser_deadline:
                    self._parser_deadline = None
                    self._dispatch(app, self._parser.flush_timeout())
                    self._track_parser_deadline()

                self._timers.fire_due()

        finally:
            self._running = False
            signal.set_wakeup_fd(old_wakeup)
            os.close(wake_r)
            os.close(wake_w)
            surface.restore()
