import os
import typing as ta

from omcore.term.vt100.terminal import Vt100Terminal

from ...events.keys import Key
from ...events.types import Event
from ...events.types import KeyEvent
from ...events.types import ModeReportEvent
from ...events.types import PasteEvent
from ...screens.cells import Frame
from ...screens.cells import line_from_segments
from ...surfaces.inlines import InlineSurface
from ...tests.harness import RecordingTty
from ...text.segments import Segment
from ...text.styles import EMPTY_THEME
from ..base import App
from ..sync import SyncDriver


##


class PipeTty(RecordingTty):
    """A recording tty whose input side is a real pipe fd, so the driver's poll loop runs for real."""

    def __init__(self, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)

        self.read_fd, self.write_fd = os.pipe()
        self._input_fd = self.read_fd

    def send(self, data: bytes) -> None:
        os.write(self.write_fd, data)

    def close_input(self) -> None:
        os.close(self.write_fd)


class RecordingApp(App):
    """Echoes received events into a one-line frame; stops on ctrl+d."""

    def __init__(self, driver: SyncDriver) -> None:
        super().__init__()

        self._driver = driver
        self.events: list[Event] = []

    def handle_event(self, event: Event) -> None:
        self.events.append(event)
        if isinstance(event, KeyEvent) and event.key == Key('d', ctrl=True):
            self._driver.stop()
        self._driver.invalidate()

    def render(self, width: int, max_height: int) -> Frame:
        text = f'events: {len(self.events)}'
        return Frame((line_from_segments([Segment(text)], EMPTY_THEME),))


def run_driver(
        data: bytes,
        *,
        then: bytes | None = None,
        height: int = 6,
        width: int = 40,
) -> tuple[RecordingApp, PipeTty]:
    tty = PipeTty(height=height, width=width)
    driver = SyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)
    # Answer the startup origin CPR like a real terminal (row 3, col 1) so rendering isn't timeout-delayed.
    tty.send(b'\x1b[3;1R')
    tty.send(data)
    if then is not None:
        # Deliver the second chunk from inside the loop, guaranteeing a render happens between the two reads.
        def send_then() -> None:
            tty.send(then)
            tty.close_input()

        driver.timers.call_later(.01, send_then)
    else:
        tty.close_input()
    try:
        driver.run(app)
    finally:
        os.close(tty.read_fd)
    return app, tty


def test_driver_dispatches_and_renders():
    app, tty = run_driver(b'ab\x1b[A', then=b'\x04')

    keys = [e.key for e in app.events if isinstance(e, KeyEvent)]
    assert keys == [Key('a'), Key('b'), Key('up'), Key('d', ctrl=True)]

    term = Vt100Terminal(rows=6, cols=40)
    term.feed(b''.join(tty.writes))
    # The render between the two reads counted the first three events.
    assert 'events: 3' in term.all_lines()


def test_driver_eof_stops():
    app, _ = run_driver(b'x')
    assert [e.key for e in app.events if isinstance(e, KeyEvent)] == [Key('x')]


def test_driver_paste_roundtrip():
    app, _ = run_driver(b'\x1b[200~hello\rworld\x1b[201~\x04')
    pastes = [e for e in app.events if isinstance(e, PasteEvent)]
    assert pastes == [PasteEvent('hello\nworld')]


def test_driver_escape_timeout_fires():
    # A lone ESC with no follow-up: the loop must fire the parser timeout and deliver the escape key, then EOF ends the
    # run. (The wait is real time - shrink the window so the test stays fast.)
    tty = PipeTty(height=6, width=40)
    driver = SyncDriver(InlineSurface(tty, term='xterm-256color'))
    driver.parser.escape_timeout_s = .05
    app = RecordingApp(driver)
    tty.send(b'\x1b[3;1R')
    tty.send(b'\x1b')
    tty.close_input()
    try:
        driver.run(app)
    finally:
        os.close(tty.read_fd)
    assert [e.key for e in app.events if isinstance(e, KeyEvent)] == [Key('escape')]


def test_origin_cpr_midline_gets_fresh_line():
    # A shell left its prompt mid-line (col 5). The driver's CPR dance must move to a fresh line instead of overwriting
    # it.
    tty = PipeTty(height=6, width=40)
    driver = SyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)

    term = Vt100Terminal(rows=6, cols=40)
    term.feed('sh$ x')  # the partial prompt line, cursor now at col 5

    tty.send(b'\x1b[1;6R')  # CPR answer: row 1, col 6 (1-based) = col 5

    def quit_later() -> None:
        tty.send(b'\x04')
        tty.close_input()

    driver.timers.call_later(.02, quit_later)
    try:
        driver.run(app)
    finally:
        os.close(tty.read_fd)

    term.feed(b''.join(tty.writes))
    lines = term.all_lines()
    assert lines[0] == 'sh$ x'  # the prompt survived
    assert any(line.startswith('events:') for line in lines[1:])  # our output started below it


def test_sync_output_negotiation_disables_bracket():
    # The terminal reports DECRQM mode 2026 as unrecognized (value 0): frames stop being sync-bracketed.
    tty = PipeTty(height=6, width=40)
    driver = SyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)

    tty.send(b'\x1b[3;1R')      # origin CPR
    tty.send(b'\x1b[?2026;0$y')  # sync output: unrecognized

    def quit_later() -> None:
        tty.send(b'\x04')
        tty.close_input()

    def type_and_quit() -> None:
        tty.send(b'x')
        driver.timers.call_later(.02, quit_later)

    driver.timers.call_later(.02, type_and_quit)
    try:
        driver.run(app)
    finally:
        os.close(tty.read_fd)

    # The mode report was consumed as plumbing, never forwarded.
    assert not any(isinstance(e, ModeReportEvent) for e in app.events)

    # Renders after the report carry no sync bracket.
    late = b''.join(tty.writes[-6:])
    assert b'events:' in b''.join(tty.writes)
    assert b'\x1b[?2026h' not in late


def test_driver_commit_before_run_buffers():
    # Commits made before run() prepares the surface buffer and flush once the origin resolves.
    tty = PipeTty(height=6, width=40)
    driver = SyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)

    driver.commit([line_from_segments([Segment('early bird')], EMPTY_THEME)])  # must not raise

    tty.send(b'\x1b[3;1R')
    tty.send(b'\x04')
    driver.run(app)

    term = Vt100Terminal(rows=6, cols=40)
    term.feed(b''.join(tty.writes))
    assert 'early bird' in term.all_lines()


def test_driver_stop_before_origin_flushes_commits():
    # Stopping (EOF here) before the CPR answer must still land buffered commits, not drop them.
    tty = PipeTty(height=6, width=40)
    driver = SyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)

    driver.commit([line_from_segments([Segment('parting words')], EMPTY_THEME)])
    # No CPR answer: close input immediately so the loop exits (EOF) while the origin is still unresolved.
    tty.close_input()
    driver.run(app)

    term = Vt100Terminal(rows=6, cols=40)
    term.feed(b''.join(tty.writes))
    assert 'parting words' in term.all_lines()


def test_kitty_flags_reply_relaxes_escape_parsing():
    # The prepare-time CSI ?u query's reply is plumbing: the driver flips the parser into unambiguous-escape mode
    # instead of forwarding it to the app.
    app, tty = run_driver(b'\x1b[?1u', then=b'\x04')
    assert not any(isinstance(e, ModeReportEvent) or type(e).__name__ == 'KittyFlagsEvent' for e in app.events)


def test_kitty_query_sent_when_enabled():
    tty = PipeTty(height=6, width=40)
    surface = InlineSurface(tty, term='xterm-256color', kitty_keys=True)
    surface.prepare(defer_origin=True)
    assert b'\x1b[?u' in b''.join(tty.writes)
    surface.restore()
