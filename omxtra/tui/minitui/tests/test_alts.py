from omcore.term.vt100.terminal import Vt100Terminal

from ..screens.cells import Frame
from ..screens.cells import line_from_segments
from ..surfaces.alts import AltSurface
from ..text.segments import Segment
from ..text.styles import EMPTY_THEME
from .harness import RecordingTty


##


class AltHarness:
    def __init__(self, *, height=8, width=30):
        self.tty = RecordingTty(height=height, width=width)
        self.surface = AltSurface(self.tty, term='xterm-256color')
        self.terminal = Vt100Terminal(rows=height, cols=width)
        self._fed = 0
        self.surface.prepare()
        self.pump()

    def pump(self) -> bytes:
        data = b''.join(self.tty.writes[self._fed:])
        self._fed = len(self.tty.writes)
        self.terminal.feed(data)
        return data

    def frame(self, *lines, cursor=(0, 0), cursor_visible=True):
        return Frame(
            tuple(line_from_segments([Segment(text)], EMPTY_THEME) for text in lines),
            cursor=cursor,
            cursor_visible=cursor_visible,
        )

    def present(self, frame) -> bytes:
        self.surface.present(frame)
        return self.pump()


def test_alt_prepare_enters_alt_screen():
    h = AltHarness()
    assert h.terminal.in_alt_screen


def test_alt_present_and_diff():
    h = AltHarness(height=6, width=20)

    h.present(h.frame('alpha', 'beta', 'gamma'))
    assert h.terminal.screen_lines() == ['alpha', 'beta', 'gamma', '', '', '']

    data = h.present(h.frame('alpha', 'betas', 'gamma'))
    assert b'alpha' not in data  # unchanged rows aren't resent
    assert h.terminal.screen_lines()[1] == 'betas'

    # Identical frame: just the sync bracket.
    data = h.present(h.frame('alpha', 'betas', 'gamma'))
    assert data == b'\x1b[?2026h\x1b[?2026l'


def test_alt_shrink_erases():
    h = AltHarness(height=6, width=20)
    h.present(h.frame('a', 'b', 'c', 'd'))
    h.present(h.frame('a'))
    assert h.terminal.screen_lines() == ['a', '', '', '', '', '']


def test_alt_cursor():
    h = AltHarness(height=6, width=20)
    h.present(h.frame('hello', cursor=(3, 0)))
    assert (h.terminal.cursor_row, h.terminal.cursor_col) == (0, 3)
    assert h.terminal.cursor_visible

    h.present(h.frame('hello', cursor=(3, 0), cursor_visible=False))
    assert not h.terminal.cursor_visible


def test_alt_restore_leaves_alt_screen():
    h = AltHarness()
    h.present(h.frame('fullscreen stuff'))
    h.surface.restore()
    h.pump()
    assert not h.terminal.in_alt_screen


def test_alt_content_never_touches_scrollback():
    h = AltHarness(height=4)
    for i in range(10):
        h.present(h.frame(*(f'r{i}-{j}' for j in range(4))))
    assert h.terminal.scrollback_lines() == []
