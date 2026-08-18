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
from ..events.types import CursorPositionEvent
from ..events.types import Event
from ..events.types import ModeReportEvent
from ..events.types import ResizeEvent
from ..events.xterm import XtermEventParser
from ..screens.cells import Frame
from ..screens.cells import Line
from ..surfaces.base import Surface
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
            surface: Surface,
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

        self._awaiting_origin = False
        self._origin_deadline: float | None = None
        self._pending_commits: list[ta.Sequence[Line]] = []

    @property
    def surface(self) -> Surface:
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
        surface = check.isinstance(self._surface, InlineSurface)
        if self._awaiting_origin:
            # Nothing may touch the terminal until the origin resolves; committed content queues in order.
            self._pending_commits.append(tuple(lines))
        else:
            surface.commit(lines)
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

    def _resolve_origin(self, col: int | None) -> None:
        surface = check.isinstance(self._surface, InlineSurface)
        if col is not None:
            surface.resolve_origin(col)
        else:
            surface.resolve_origin_fallback()
        self._awaiting_origin = False
        self._origin_deadline = None
        pending, self._pending_commits = self._pending_commits, []
        for lines in pending:
            surface.commit(lines)
        self._invalidated = True

    def _dispatch(self, app: App, events: ta.Iterable[Event]) -> None:
        for event in events:
            # Startup negotiations are plumbing, not app events.
            if self._awaiting_origin and isinstance(event, CursorPositionEvent):
                self._resolve_origin(event.x)
                continue
            if isinstance(event, ModeReportEvent) and event.mode == 2026:
                self._surface.set_sync_output(event.value != 0)
                continue
            app.handle_event(event)

    def _next_deadline(self) -> float | None:
        deadline = self._timers.next_fire_at()
        for extra in (self._parser_deadline, self._origin_deadline):
            if extra is not None:
                deadline = min(deadline, extra) if deadline is not None else extra
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
        if isinstance(surface, InlineSurface):
            # Learn where the shell left the cursor before touching the terminal: a mid-line prompt gets a fresh
            # line instead of being overwritten. Rendering and commits hold until the answer (or a short timeout).
            surface.prepare(defer_origin=True)
            surface.request_origin(self._parser)
            surface.request_sync_output_report()
            self._awaiting_origin = True
            self._origin_deadline = self._clock() + .25
        else:
            surface.prepare()
            surface.request_sync_output_report()

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

                if self._invalidated and not self._awaiting_origin:
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

                if self._awaiting_origin and self._origin_deadline is not None and now >= self._origin_deadline:
                    self._resolve_origin(None)

                self._timers.fire_due()

        finally:
            self._running = False
            signal.set_wakeup_fd(old_wakeup)
            os.close(wake_r)
            os.close(wake_w)
            surface.restore()
