"""
The asyncio driver: the same App contract as SyncDriver, hosted in an asyncio loop.

The core stays synchronous and single-threaded - this driver only owns pacing: the input fd via `add_reader`, SIGWINCH
via `add_signal_handler`, escape-parser timeouts via `call_later`, and a coalescing `invalidate()` that schedules at
most one render per loop turn (the ptk ten-line trick). `post()` is the *sole* thread-safe entry point: anything outside
the loop (worker threads, other tasks' executors) hands a callable across with it; everything else must be called on the
loop.

asyncio-specific by design (this is the isolation point the rest of the codebase's anyio-vs-asyncio flux doesn't reach):
apps that want structured concurrency layer their own tasks above and talk to the driver through post().

Job control (SIGTSTP / SIGCONT, and `suspend()` for terminals that deliver ctrl+z as a key) runs as loop callbacks, so
a stop never lands mid-render; see `jobcontrol.py`.
"""
import asyncio
import codecs
import os
import signal
import typing as ta

from omcore import check

from ..events.parsing import Read1
from ..events.types import CursorPositionEvent
from ..events.types import Event
from ..events.types import KittyFlagsEvent
from ..events.types import ModeReportEvent
from ..events.types import ResizeEvent
from ..events.types import ResumeEvent
from ..events.types import SuspendEvent
from ..events.xterm import XtermEventParser
from ..screens.cells import Line
from ..surfaces.base import Surface
from ..surfaces.inlines import InlineSurface
from .base import App
from .jobcontrol import JobControl


##


class AsyncioTimer:
    """Cancellation handle duck-compatible with runtime.timers.Timer."""

    def __init__(self) -> None:
        super().__init__()

        self._handle: asyncio.TimerHandle | None = None
        self._cancelled = False

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True
        if self._handle is not None:
            self._handle.cancel()


class AsyncioTimers:
    """
    The call_later/call_every subset of runtime.timers.Timers, backed by the asyncio loop.

    Timers may be created before the driver runs (apps typically register their spinner in __init__); they are held and
    scheduled when the driver binds its loop.
    """

    def __init__(self) -> None:
        super().__init__()

        self._loop: asyncio.AbstractEventLoop | None = None
        self._pending: list[tuple[float, ta.Callable[[], None], AsyncioTimer]] = []

    def _schedule(self, delay_s: float, fn: ta.Callable[[], None], timer: AsyncioTimer) -> None:
        if timer.cancelled:
            return
        if self._loop is None:
            self._pending.append((delay_s, fn, timer))
        else:
            timer._handle = self._loop.call_later(delay_s, fn)  # noqa: SLF001

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        pending, self._pending = self._pending, []
        for delay_s, fn, timer in pending:
            self._schedule(delay_s, fn, timer)

    def unbind(self) -> None:
        self._loop = None

    def call_later(self, delay_s: float, fn: ta.Callable[[], None]) -> AsyncioTimer:
        timer = AsyncioTimer()
        self._schedule(delay_s, fn, timer)
        return timer

    def call_every(self, interval_s: float, fn: ta.Callable[[], None]) -> AsyncioTimer:
        timer = AsyncioTimer()

        def tick() -> None:
            if timer.cancelled:
                return
            self._schedule(interval_s, tick, timer)
            fn()

        self._schedule(interval_s, tick, timer)
        return timer


class AsyncioDriver:
    def __init__(
            self,
            surface: Surface,
            *,
            stop_process: ta.Callable[[], None] | None = None,
    ) -> None:
        super().__init__()

        self._surface = surface

        self._parser = XtermEventParser()
        self._decoder = codecs.getincrementaldecoder('utf-8')('replace')

        self._loop: asyncio.AbstractEventLoop | None = None
        self._timers = AsyncioTimers()
        self._app: App | None = None

        self._invalidated = False
        self._render_scheduled = False
        self._stop_event: asyncio.Event | None = None

        self._parser_flush_handle: asyncio.TimerHandle | None = None
        self._parser_pending: Read1 | None = None

        self._awaiting_origin = False
        self._origin_fallback_handle: asyncio.TimerHandle | None = None
        self._pending_commits: list[ta.Sequence[Line]] = []

        self._has_winch_handler = False
        self._job_control = JobControl(
            suspend=self._suspend_now,
            resume=self._resume_now,
            stop_process=stop_process,
        )
        self._job_signals: list[int] = []

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def timers(self) -> AsyncioTimers:
        return self._timers

    @property
    def parser(self) -> XtermEventParser:
        return self._parser

    ##
    # Loop-side API

    def invalidate(self) -> None:
        self._invalidated = True
        if not self._render_scheduled and self._loop is not None:
            self._render_scheduled = True
            self._loop.call_soon(self._render)

    def commit(self, lines: ta.Sequence[Line]) -> None:
        surface = check.isinstance(self._surface, InlineSurface)
        if self._loop is None or self._awaiting_origin or self._job_control.suspended:
            # Buffered while the origin is unresolved - and likewise before run() has prepared the surface at all
            # (matching AsyncTimers' pre-run buffering) or while suspended: the origin-resolution path flushes.
            self._pending_commits.append(tuple(lines))
        else:
            surface.commit(lines)
        self.invalidate()

    def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()

    ##
    # Cross-thread entry

    def post(self, fn: ta.Callable[[], None]) -> None:
        """Run `fn` on the driver loop; safe to call from any thread. The only thread-safe method here."""

        check.not_none(self._loop).call_soon_threadsafe(fn)

    ##
    # Internals

    def _render(self) -> None:
        self._render_scheduled = False
        if not self._invalidated or self._app is None or self._awaiting_origin or self._job_control.suspended:
            return
        self._invalidated = False

        surface = self._surface
        if surface.take_resized():
            self._app.handle_event(ResizeEvent(surface.height, surface.width))
        surface.present(self._app.render(surface.width, surface.height))

    def _resolve_origin(self, col: int | None) -> None:
        if not self._awaiting_origin:
            return
        surface = check.isinstance(self._surface, InlineSurface)
        if col is not None:
            surface.resolve_origin(col)
        else:
            surface.resolve_origin_fallback()
        self._awaiting_origin = False
        if self._origin_fallback_handle is not None:
            self._origin_fallback_handle.cancel()
            self._origin_fallback_handle = None
        pending, self._pending_commits = self._pending_commits, []
        for lines in pending:
            surface.commit(lines)
        self.invalidate()

    def _dispatch(self, events: ta.Iterable[Event]) -> None:
        app = check.not_none(self._app)
        for event in events:
            if self._awaiting_origin and isinstance(event, CursorPositionEvent):
                self._resolve_origin(event.x)
                continue
            if isinstance(event, KittyFlagsEvent):
                # Kitty-protocol confirmation: with disambiguation active the ESC byte can only start a sequence, so
                # escape parsing may wait indefinitely (immune to laggy split sequences).
                self._parser.set_escape_unambiguous(bool(event.flags & 1))
                continue
            if isinstance(event, ModeReportEvent) and event.mode == 2026:
                self._surface.set_sync_output(event.value != 0)
                continue
            app.handle_event(event)

    def _track_parser_deadline(self) -> None:
        pending = self._parser.pending_read
        if pending is self._parser_pending:
            return
        self._parser_pending = pending
        if self._parser_flush_handle is not None:
            self._parser_flush_handle.cancel()
            self._parser_flush_handle = None
        if pending.timeout_s is not None:
            self._parser_flush_handle = check.not_none(self._loop).call_later(
                pending.timeout_s,
                self._flush_parser,
            )

    def _flush_parser(self) -> None:
        self._parser_flush_handle = None
        self._dispatch(self._parser.flush_timeout())
        self._track_parser_deadline()

    def _on_readable(self) -> None:
        data = os.read(self._surface.tty.input_fd, 4096)
        if not data:
            self._dispatch(self._parser.flush_timeout())
            self.stop()
            return
        self._dispatch(self._parser.feed(self._decoder.decode(data)))
        self._track_parser_deadline()

    def _on_winch(self) -> None:
        self._surface.tty.mark_resized()
        self.invalidate()

    def _watch_winch(self) -> None:
        try:
            check.not_none(self._loop).add_signal_handler(signal.SIGWINCH, self._on_winch)
            self._has_winch_handler = True
        except (ValueError, NotImplementedError):
            pass  # not the main thread; the tty's own handler (installed by prepare) still sets the flag

    def _unwatch_winch(self) -> None:
        if self._has_winch_handler:
            check.not_none(self._loop).remove_signal_handler(signal.SIGWINCH)
            self._has_winch_handler = False

    def _negotiate(self) -> None:
        """On every entry into application mode (startup and resume): the inline origin CPR, the sync-output query."""

        surface = self._surface
        if isinstance(surface, InlineSurface):
            surface.request_origin(self._parser)
            self._awaiting_origin = True
            if self._origin_fallback_handle is not None:
                self._origin_fallback_handle.cancel()
            self._origin_fallback_handle = check.not_none(self._loop).call_later(
                .25,
                lambda: self._resolve_origin(None),
            )
        surface.request_sync_output_report()

    ##
    # Job control

    @property
    def job_control(self) -> JobControl:
        return self._job_control

    def suspend(self) -> None:
        """Suspend the process as ctrl+z would, on the next loop turn - between callbacks, never inside a render."""

        if self._loop is not None:
            self._loop.call_soon(self._job_control.suspend)

    def _install_job_control(self, loop: asyncio.AbstractEventLoop) -> None:
        for signum, handler in (
                (signal.SIGTSTP, self._job_control.suspend),
                (signal.SIGCONT, self._job_control.resume),
        ):
            try:
                loop.add_signal_handler(signum, handler)
            except (ValueError, NotImplementedError):
                break  # not the main thread: job control stays the kernel's
            self._job_signals.append(signum)

    def _uninstall_job_control(self, loop: asyncio.AbstractEventLoop) -> None:
        signums, self._job_signals = self._job_signals, []
        for signum in signums:
            loop.remove_signal_handler(signum)

    def _suspend_now(self) -> None:
        if (app := self._app) is not None:
            app.handle_event(SuspendEvent())
        self._surface.suspend()

    def _resume_now(self) -> bool:
        surface = self._surface
        if not surface.tty.probe_foreground():
            return False
        size = (surface.height, surface.width)
        surface.resume()
        self._watch_winch()  # the tty's restore/prepare pair put its own handler over the loop's
        self._negotiate()
        if (app := self._app) is not None:
            if (surface.height, surface.width) != size:
                app.handle_event(ResizeEvent(surface.height, surface.width))
            app.handle_event(ResumeEvent())
        self.invalidate()
        return True

    ##
    # Lifecycle

    async def run(self, app: App) -> None:
        check.state(self._loop is None)

        loop = asyncio.get_running_loop()
        self._loop = loop
        self._timers.bind(loop)
        self._app = app
        self._stop_event = asyncio.Event()

        surface = self._surface
        if isinstance(surface, InlineSurface):
            surface.prepare(defer_origin=True)
        else:
            surface.prepare()
        self._negotiate()

        input_fd = surface.tty.input_fd
        loop.add_reader(input_fd, self._on_readable)
        self._watch_winch()
        self._install_job_control(loop)

        self.invalidate()

        try:
            await self._stop_event.wait()
        finally:
            if self._awaiting_origin:
                # Stopped before the CPR answer (or its fallback timer): resolve via the fallback now so buffered
                # commits reach the terminal instead of being dropped.
                self._resolve_origin(None)
            if self._origin_fallback_handle is not None:
                self._origin_fallback_handle.cancel()
                self._origin_fallback_handle = None
            if self._parser_flush_handle is not None:
                self._parser_flush_handle.cancel()
            self._uninstall_job_control(loop)
            self._unwatch_winch()
            loop.remove_reader(input_fd)
            surface.restore()
            self._loop = None
            self._timers.unbind()
            self._app = None
            self._stop_event = None
