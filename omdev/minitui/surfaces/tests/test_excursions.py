"""The inline surface's alt-screen excursion, and the origin-row tracking that translates mouse rows."""
from ...tests.harness import SurfaceHarness


##


def test_alt_excursion_preserves_live_region():
    h = SurfaceHarness(height=8, width=40)
    h.present(h.frame('alpha', 'beta', 'gamma'))
    before = h.screen()

    s = h.surface
    s.set_alt_screen(True)
    requested = s.alt_screen
    assert h.pump() == b''  # entry is byte-free until the first present

    data = h.present(h.frame('FULL 1', 'FULL 2'))
    entered = h.terminal.in_alt_screen
    assert b'\x1b[?1049h' in data
    assert b'\x1b[?1000h' in data  # the wheel is the point: mouse tracking comes on for the excursion
    assert h.screen()[:2] == ['FULL 1', 'FULL 2']
    assert h.scrollback() == []

    # Identical alt frame: just the sync bracket.
    assert h.present(h.frame('FULL 1', 'FULL 2')) == b'\x1b[?2026h\x1b[?2026l'

    s.set_alt_screen(False)
    data = h.pump()
    # (Snapshots rather than step-by-step asserts: mypy narrows an asserted attribute and reads the contradicting
    # assert later as unreachable.)
    assert (requested, s.alt_screen) == (True, False)
    assert (entered, h.terminal.in_alt_screen) == (True, False)
    assert b'\x1b[?1000l' in data  # back to the live region's (off) setting
    assert h.screen() == before

    # Relative tracking survived the interlude: a minimal update lands on the right row.
    data = h.present(h.frame('alpha', 'BETA', 'gamma'))
    assert b'alpha' not in data
    assert h.screen()[:3] == ['alpha', 'BETA', 'gamma']


def test_alt_excursion_then_commit():
    h = SurfaceHarness(height=6, width=20)
    h.present(h.frame('one', 'two', 'three'))

    h.surface.set_alt_screen(True)
    h.present(h.frame('browse'))
    h.surface.set_alt_screen(False)
    h.pump()

    h.commit([h.line('one'), h.line('two')])
    h.present(h.frame('three', 'four'))
    assert h.screen() == ['one', 'two', 'three', 'four', '', '']


def test_alt_excursion_never_entered_is_free():
    h = SurfaceHarness()
    h.present(h.frame('live'))
    h.surface.set_alt_screen(True)
    h.surface.set_alt_screen(False)
    assert h.pump() == b''
    assert not h.terminal.in_alt_screen


def test_alt_excursion_resize_repaints_live_region_on_return():
    h = SurfaceHarness(height=8, width=40)
    h.present(h.frame('alpha', 'beta'))

    s = h.surface
    s.set_alt_screen(True)
    h.present(h.frame('browse'))

    h.tty.resize(height=8, width=30)
    assert s.take_resized()  # absorbed fullscreen: the alt grid is cleared, the live region untouched
    assert s.frame.height == 2

    s.set_alt_screen(False)
    h.pump()
    # Re-marked on the way out: the usual resize path erases and forgets the live region.
    assert s.take_resized()
    assert s.frame.height == 0
    assert not s.take_resized()


def test_alt_excursion_cursor_visibility_is_one_mode():
    h = SurfaceHarness()
    h.present(h.frame('live', cursor_visible=False))
    visible = [h.terminal.cursor_visible]

    h.surface.set_alt_screen(True)
    h.present(h.frame('browse', cursor_visible=True))
    visible.append(h.terminal.cursor_visible)

    h.surface.set_alt_screen(False)
    h.pump()
    h.present(h.frame('live', cursor_visible=False))
    visible.append(h.terminal.cursor_visible)
    assert visible == [False, True, False]


def test_suspend_in_alt_excursion_leaves_it():
    h = SurfaceHarness()
    h.present(h.frame('live'))
    h.surface.set_alt_screen(True)
    h.present(h.frame('browse'))
    was_alt = h.terminal.in_alt_screen

    h.surface.suspend()
    h.pump()
    assert (was_alt, h.terminal.in_alt_screen, h.surface.alt_screen) == (True, False, False)
    assert h.screen()[0] == ''  # the live region is erased on the way out, as on any suspend


def test_restore_in_alt_excursion_leaves_it():
    h = SurfaceHarness()
    h.present(h.frame('live'))
    h.surface.set_alt_screen(True)
    h.present(h.frame('browse'))

    h.surface.restore()
    h.pump()
    assert not h.terminal.in_alt_screen
    assert h.screen()[0] == 'live'


##
# Origin tracking


def test_frame_row_assumes_bottom_when_origin_unknown():
    h = SurfaceHarness(height=6, width=20)
    s = h.surface
    h.present(h.frame('a', 'b'))
    assert s.origin_row is None
    assert s.frame_row(5) == 1
    assert s.frame_row(4) == 0
    assert s.frame_row(3) == -1


def test_origin_row_follows_scrolls_and_commits():
    h = SurfaceHarness(height=6, width=20)
    h.terminal.feed(b'\r\n\r\n')  # the shell left us on row 2
    s = h.surface
    s.resolve_origin(0, 2)
    h.pump()
    assert s.origin_row == 2

    h.present(h.frame('a', 'b', 'c'))
    assert s.origin_row == 2
    assert s.frame_row(3) == 1

    # Growing past the bottom scrolls the terminal once: everything, origin included, moves up a row.
    h.present(h.frame('a', 'b', 'c', 'd', 'e'))
    assert s.origin_row == 1
    assert h.screen() == ['', 'a', 'b', 'c', 'd', 'e']
    assert h.terminal.cursor_row == s.origin_row + 4

    # A commit moves the origin down past the committed rows.
    h.commit([h.line('a'), h.line('b')])
    assert s.origin_row == 3
    assert s.frame_row(3) == 0
    assert s.frame_row(1) == -2
    h.present(h.frame('c', 'd', 'e'))
    assert h.screen() == ['', 'a', 'b', 'c', 'd', 'e']

    # A commit taller than the terminal ends with the origin on the bottom row.
    h.commit([h.line(str(i)) for i in range(10)])
    assert s.origin_row == 5
    assert h.terminal.cursor_row == 5
    assert h.screen() == ['5', '6', '7', '8', '9', '']


def test_origin_row_fresh_line_and_alt_identity():
    h = SurfaceHarness(height=6, width=20)
    s = h.surface
    s.resolve_origin(4, 2)  # mid-line on row 2: a fresh line, so the origin is row 3
    assert s.origin_row == 3

    h.present(h.frame('x'))
    s.set_alt_screen(True)
    assert s.frame_row(4) == 4  # fullscreen: the frame is the screen
    s.set_alt_screen(False)
    assert s.frame_row(4) == 1

    s.resolve_origin(4, 5)  # mid-line on the bottom row: the fresh line scrolls, and is still the bottom row
    assert s.origin_row == 5
