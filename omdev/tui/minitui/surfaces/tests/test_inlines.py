from ...tests.harness import SurfaceHarness
from ...text.colors import RED
from ...text.styles import Style
from ...text.styles import Theme


##


def test_present_basic():
    h = SurfaceHarness(height=6, width=20)

    h.present(h.frame('one', 'two', 'three'))
    assert h.screen() == ['one', 'two', 'three', '', '', '']
    assert h.scrollback() == []
    assert (h.terminal.cursor_row, h.terminal.cursor_col) == (2, 0)


def test_present_identical_frame_is_nearly_free():
    h = SurfaceHarness(height=6, width=20)

    frame = h.frame('one', 'two')
    h.present(frame)
    data = h.present(frame)

    # Only the synchronized-output bracket; no content bytes, no cursor churn.
    assert data == b'\x1b[?2026h\x1b[?2026l'


def test_present_minimal_line_update():
    h = SurfaceHarness(height=6, width=20)

    h.present(h.frame('hello world', 'stat'))
    data = h.present(h.frame('hello waldo', 'stat'))

    assert h.screen() == ['hello waldo', 'stat', '', '', '', '']
    # The changed span is 4 cells; the full first line (11 cells) must not have been resent.
    assert b'aldo' in data
    assert b'hello' not in data


def test_present_shrink_erases():
    h = SurfaceHarness(height=6, width=20)

    h.present(h.frame('one', 'two', 'three', 'four'))
    h.present(h.frame('one'))

    assert h.screen() == ['one', '', '', '', '', '']


def test_grow_scrolls_at_bottom():
    h = SurfaceHarness(height=4, width=20)

    h.present(h.frame('a', 'b', 'c', 'd'))
    assert h.scrollback() == []

    # Committing everything then presenting anew pushes old content up into scrollback as the new live region grows.
    h.commit(h.surface.frame.lines)
    h.present(h.frame('e', 'f'))

    assert h.all_lines() == ['a', 'b', 'c', 'd', 'e', 'f']
    assert h.scrollback() == ['a', 'b']


def test_commit_partial_reanchors():
    h = SurfaceHarness(height=6, width=20)

    h.present(h.frame('msg1', 'msg2', 'status'))

    # Commit the first displayed line exactly as shown, then keep going below it.
    h.commit([h.line('msg1')])
    h.present(h.frame('msg2', 'status+'))

    assert h.screen() == ['msg1', 'msg2', 'status+', '', '', '']

    # msg1 is now dead history: later presents never touch row 0.
    h.present(h.frame('msg2 edited', 'status+'))
    assert h.screen() == ['msg1', 'msg2 edited', 'status+', '', '', '']


def test_commit_identical_content_costs_nothing():
    h = SurfaceHarness(height=6, width=20)

    h.present(h.frame('done line', 'tail'))
    data = h.commit([h.line('done line')])

    # The committed line matched what was displayed - no content was rewritten.
    assert b'done' not in data


def test_commit_differing_content_rewrites():
    h = SurfaceHarness(height=6, width=20)

    h.present(h.frame('streaming...', 'tail'))
    h.commit([h.line('final text')])
    h.present(h.frame('tail'))

    assert h.screen() == ['final text', 'tail', '', '', '', '']


def test_commit_taller_than_live_region():
    h = SurfaceHarness(height=4, width=20)

    h.present(h.frame('live'))
    h.commit([h.line(f'line{i}') for i in range(6)])
    h.present(h.frame('new live'))

    assert h.all_lines() == ['line0', 'line1', 'line2', 'line3', 'line4', 'line5', 'new live']


def test_styled_cells_roundtrip():
    theme = Theme({'err': Style(fg=RED, bold=True)})
    h = SurfaceHarness(height=4, width=20, theme=theme)

    h.present(h.frame(h.line('ok ', ('bad', 'err'))))

    assert h.screen()[0] == 'ok bad'
    cell = h.terminal.cell(0, 3)
    assert cell.char == 'b'
    assert cell.fg == ('named', 1)
    assert cell.bold
    plain = h.terminal.cell(0, 0)
    assert plain.fg is None
    assert not plain.bold


def test_autowrap_disabled_no_desync():
    h = SurfaceHarness(height=4, width=10)

    # A width-exact line must not wrap (autowrap is disabled by prepare); subsequent updates stay aligned.
    h.present(h.frame('0123456789', 'below'))
    assert h.screen() == ['0123456789', 'below', '', '']

    h.present(h.frame('0123456789', 'below!'))
    assert h.screen() == ['0123456789', 'below!', '', '']


def test_resize_erases_and_redraws():
    h = SurfaceHarness(height=6, width=20)

    h.present(h.frame('aaa', 'bbb'))
    h.tty.resize(height=6, width=15)

    # The next present absorbs the resize: live region erased and fully redrawn.
    h.present(h.frame('ccc'))
    assert h.screen() == ['ccc', '', '', '', '', '']


def test_cursor_position_and_visibility():
    h = SurfaceHarness(height=4, width=20)

    h.present(h.frame('input: x', cursor=(8, 0)))
    assert (h.terminal.cursor_row, h.terminal.cursor_col) == (0, 8)
    assert h.terminal.cursor_visible

    h.present(h.frame('input: x', cursor=(8, 0), cursor_visible=False))
    assert not h.terminal.cursor_visible


##
# Job control


def test_suspend_erases_live_region_and_resume_repaints():
    h = SurfaceHarness(height=6, width=20)

    h.commit([h.line('done')])
    h.present(h.frame('live', 'status'))
    assert h.all_lines()[:3] == ['done', 'live', 'status']

    h.surface.suspend()
    data = h.pump()
    # The live region is gone and the committed line stays; the cursor waits at the origin for the shell's chatter, and
    # the terminal modes are back to normal.
    assert h.all_lines()[:3] == ['done', '', '']
    assert (h.terminal.cursor_row, h.terminal.cursor_col) == (1, 0)
    assert b'\x1b[?2004l' in data
    assert b'\x1b[?7h' in data
    assert h.terminal.cursor_visible

    # Resume defers the origin like startup; the driver resolves it from the CPR answer.
    h.surface.resume()
    data = h.pump()
    assert b'\x1b[?2004h' in data
    h.surface.resolve_origin(0)
    h.pump()
    h.present(h.frame('live again', 'status'))
    assert h.all_lines()[:3] == ['done', 'live again', 'status']
