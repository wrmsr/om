"""chatdemo end to end under a real pty: f12 in, f12 out, quit - the alt-screen round trip through a live SyncDriver."""
import os.path
import sys

from omcore.term.vt100.terminal import Vt100Terminal

from ...ptys import PtyRun


##


ALT_ON = b'\x1b[?1049h'
ALT_OFF = b'\x1b[?1049l'
F12 = b'\x1b[24~'

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 5)))


def test_chatdemo_f12_round_trip():
    run = PtyRun([sys.executable, '-m', 'omdev.minitui.tests.apps.chatdemo'], cwd=_REPO_ROOT)
    try:
        run.read_until(b'\x1b[?2004h', timeout_s=30.)  # application mode: bracketed paste on (imports take a moment)
        run.read_until(b'ai')  # the first canned response's header committed

        run.send(F12)
        run.read_until(ALT_ON)
        run.read_until(b'BROWSE')

        run.send(F12)
        run.read_until(ALT_OFF)

        run.send(b'\x04')
        rc = run.finish()
    except BaseException:
        run.kill()
        raise

    assert rc == 0
    data = bytes(run.output)
    assert data.index(ALT_ON) < data.rindex(ALT_OFF)
    assert data.count(ALT_ON) == 1

    term = Vt100Terminal(rows=24, cols=80)
    term.feed(data)
    assert not term.in_alt_screen
    lines = term.all_lines()
    assert any(line.startswith('ai') for line in lines)  # history is real scrollback, browse mode or not
    assert not any(line.startswith('BROWSE') for line in lines)  # nothing drawn fullscreen survives


def test_chatdemo_browse_menu_over_a_message():
    # Browsing, a click on the first response's header floats its context menu; enter runs '/show 1', whose raw source
    # lands in the transcript (and the browse view, still following); q closes browse mode, and nothing fullscreen -
    # the menu included - survives on the main screen.
    run = PtyRun([sys.executable, '-m', 'omdev.minitui.tests.apps.chatdemo'], cwd=_REPO_ROOT)
    try:
        run.read_until(b'\x1b[?2004h', timeout_s=30.)
        run.read_until(b'ai')
        run.send(F12)
        run.read_until(b'BROWSE')

        term = Vt100Terminal(rows=24, cols=80)
        term.feed(bytes(run.output))
        assert term.in_alt_screen
        row = next(i for i, line in enumerate(term.screen_lines()) if line.startswith('ai'))
        run.send(f'\x1b[<0;1;{row + 1}M'.encode())  # SGR press, 1-based column 1 on that row
        run.read_until(b'show raw source of [1]')

        run.send(b'\r')
        run.read_until(b'(raw source)')

        run.send(b'q')
        run.read_until(ALT_OFF)
        run.send(b'\x04')
        rc = run.finish()
    except BaseException:
        run.kill()
        raise

    assert rc == 0
    term = Vt100Terminal(rows=24, cols=80)
    term.feed(bytes(run.output))
    assert not term.in_alt_screen
    lines = term.all_lines()
    assert any('(raw source)' in line for line in lines)  # the menu's action committed for real
    assert not any('show raw source' in line for line in lines)  # the menu itself was fullscreen-only
