import os
import typing as ta

from omcore.term.vt100.terminal import Vt100Terminal

from ..events.keys import Key
from ..events.types import Event
from ..events.types import KeyEvent
from ..events.types import PasteEvent
from ..runtime.drivers import App
from ..runtime.drivers import SyncDriver
from ..screens.cells import Frame
from ..screens.cells import line_from_segments
from ..surfaces.inlines import InlineSurface
from ..text.segments import Segment
from ..text.styles import EMPTY_THEME
from .harness import RecordingTty


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
    # A lone ESC with no follow-up: the loop must fire the parser timeout and deliver the escape key, then EOF ends
    # the run. (The wait is the parser's 50ms escape timeout - real time, but tiny and deterministic in outcome.)
    app, _ = run_driver(b'\x1b')
    assert [e.key for e in app.events if isinstance(e, KeyEvent)] == [Key('escape')]
