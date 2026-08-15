import pytest

from ..events.keymaps import Keymap
from ..events.keymaps import KeymapMatcher
from ..events.keys import Key
from ..events.keys import KeySpecError
from ..events.keys import key_from_char
from ..events.keys import parse_key
from ..events.types import CursorPositionEvent
from ..events.types import FocusEvent
from ..events.types import KeyEvent
from ..events.types import KittyFlagsEvent
from ..events.types import ModeReportEvent
from ..events.types import MouseEvent
from ..events.types import MouseEventKind
from ..events.types import PasteEvent
from ..events.types import UnknownSequenceEvent
from ..events.xterm import XtermEventParser


##


def test_key_specs():
    assert parse_key('ctrl+x') == Key('x', ctrl=True)
    assert parse_key('ctrl+alt+delete') == Key('delete', ctrl=True, alt=True)
    assert parse_key('A') == Key('A')
    assert parse_key('shift+tab') == Key('tab', shift=True)
    assert parse_key('ctrl++') == Key('+', ctrl=True)
    assert parse_key('space') == Key('space')
    assert str(Key('enter', ctrl=True)) == 'ctrl+enter'
    with pytest.raises(KeySpecError):
        parse_key('bogus+x')
    with pytest.raises(KeySpecError):
        parse_key('')


def test_key_from_char():
    assert key_from_char('a') == Key('a')
    assert key_from_char('\x01') == Key('a', ctrl=True)
    assert key_from_char('\x09') == Key('tab')
    assert key_from_char('\x0d') == Key('enter')
    assert key_from_char('\x7f') == Key('backspace')
    assert key_from_char(' ') == Key('space')
    assert key_from_char('\x00') == Key('space', ctrl=True)
    assert key_from_char('x', alt=True) == Key('x', alt=True)


##


def keys(events):
    assert all(isinstance(e, KeyEvent) for e in events)
    return [e.key for e in events]


def test_parse_plain_and_control():
    p = XtermEventParser()
    events = p.feed('ab\x03')
    assert keys(events) == [Key('a'), Key('b'), Key('c', ctrl=True)]
    assert isinstance(events[0], KeyEvent) and events[0].text == 'a'
    assert isinstance(events[2], KeyEvent) and events[2].text is None


def test_parse_utf8_and_wide():
    p = XtermEventParser()
    assert keys(p.feed('é漢')) == [Key('é'), Key('漢')]


def test_bare_escape_via_timeout():
    p = XtermEventParser()
    assert p.feed('\x1b') == []
    assert p.pending_timeout_s is not None
    assert keys(p.flush_timeout()) == [Key('escape')]
    assert p.pending_timeout_s is None


def test_alt_keys():
    p = XtermEventParser()
    assert keys(p.feed('\x1bx')) == [Key('x', alt=True)]
    assert keys(p.feed('\x1b\x7f')) == [Key('backspace', alt=True)]


def test_double_escape():
    p = XtermEventParser()
    assert keys(p.feed('\x1b\x1bx')) == [Key('escape'), Key('x', alt=True)]


def test_csi_arrows_and_modifiers():
    p = XtermEventParser()
    assert keys(p.feed('\x1b[A')) == [Key('up')]
    assert keys(p.feed('\x1b[1;5C')) == [Key('right', ctrl=True)]
    assert keys(p.feed('\x1b[1;4B')) == [Key('down', alt=True, shift=True)]
    assert keys(p.feed('\x1b[Z')) == [Key('tab', shift=True)]
    assert keys(p.feed('\x1b[H\x1b[F')) == [Key('home'), Key('end')]


def test_csi_tilde_keys():
    p = XtermEventParser()
    assert keys(p.feed('\x1b[3~')) == [Key('delete')]
    assert keys(p.feed('\x1b[5~\x1b[6~')) == [Key('pageup'), Key('pagedown')]
    assert keys(p.feed('\x1b[15~')) == [Key('f5')]
    assert keys(p.feed('\x1b[3;5~')) == [Key('delete', ctrl=True)]


def test_ss3_keys():
    p = XtermEventParser()
    assert keys(p.feed('\x1bOP\x1bOA')) == [Key('f1'), Key('up')]


def test_bracketed_paste():
    p = XtermEventParser()
    events = p.feed('\x1b[200~hello\r\nworld\x1b[201~')
    assert events == [PasteEvent('hello\nworld')]
    # Pasted escape-ish content is not interpreted.
    events = p.feed('\x1b[200~a\x1b[Ab\x1b[201~')
    assert events == [PasteEvent('a\x1b[Ab')]


def test_sgr_mouse():
    p = XtermEventParser()
    (down,) = p.feed('\x1b[<0;10;5M')
    assert down == MouseEvent(MouseEventKind.DOWN, 9, 4, button=0)
    (up,) = p.feed('\x1b[<0;10;5m')
    assert isinstance(up, MouseEvent) and up.kind is MouseEventKind.UP
    (scroll,) = p.feed('\x1b[<64;1;1M')
    assert isinstance(scroll, MouseEvent) and scroll.kind is MouseEventKind.SCROLL_UP
    (ctrl_click,) = p.feed('\x1b[<16;3;3M')
    assert isinstance(ctrl_click, MouseEvent) and ctrl_click.ctrl and ctrl_click.kind is MouseEventKind.DOWN


def test_cpr_vs_f3():
    p = XtermEventParser()
    # Without an outstanding request, R is (modified) F3.
    assert keys(p.feed('\x1b[1;2R')) == [Key('f3', shift=True)]
    # With one, it's a CPR (1-based row;col -> 0-based x,y).
    p.expect_cursor_position_report()
    assert p.feed('\x1b[12;40R') == [CursorPositionEvent(39, 11)]
    # And the flag clears.
    assert keys(p.feed('\x1b[1;2R')) == [Key('f3', shift=True)]


def test_mode_report_and_kitty_flags():
    p = XtermEventParser()
    assert p.feed('\x1b[?2026;1$y') == [ModeReportEvent(2026, 1)]
    assert p.feed('\x1b[?1u') == [KittyFlagsEvent(1)]


def test_kitty_extended_keys():
    p = XtermEventParser()
    assert keys(p.feed('\x1b[13;5u')) == [Key('enter', ctrl=True)]
    assert keys(p.feed('\x1b[97;5u')) == [Key('a', ctrl=True)]
    assert keys(p.feed('\x1b[13;2u')) == [Key('enter', shift=True)]
    # Release events are swallowed.
    assert p.feed('\x1b[97;1:3u') == []


def test_focus_events():
    p = XtermEventParser()
    assert p.feed('\x1b[I\x1b[O') == [FocusEvent(True), FocusEvent(False)]


def test_unknown_sequences_surface():
    p = XtermEventParser()
    (event,) = p.feed('\x1b[99;99X')
    assert isinstance(event, UnknownSequenceEvent)


##


def test_keymap_simple_and_chord():
    km = Keymap({
        'ctrl+d': 'quit',
        'ctrl+x ctrl+u': 'upcase',
        'g g': 'top',
    })
    m = KeymapMatcher(km)

    assert m.push(Key('d', ctrl=True)).commands == ('quit',)

    assert m.push(Key('x', ctrl=True)).is_pending
    pending_timeout = m.pending_timeout_s
    assert pending_timeout is not None
    assert m.push(Key('u', ctrl=True)).commands == ('upcase',)
    idle_timeout = m.pending_timeout_s
    assert idle_timeout is None

    assert m.push(Key('g')).is_pending
    assert m.push(Key('g')).commands == ('top',)


def test_keymap_unmatched_replay():
    km = Keymap({'g g': 'top'})
    m = KeymapMatcher(km)

    assert m.push(Key('x')).unmatched == (Key('x'),)

    # A broken chord replays the prefix and the breaking key.
    assert m.push(Key('g')).is_pending
    result = m.push(Key('q'))
    assert result.unmatched == (Key('g'), Key('q'))


def test_keymap_prefix_timeout_resolves_shorter_binding():
    km = Keymap({
        'g': 'g-alone',
        'g g': 'top',
    })
    m = KeymapMatcher(km)

    # 'g' is both bound and a prefix: it waits...
    assert m.push(Key('g')).is_pending
    # ...and resolves to its own binding on timeout.
    assert m.flush().commands == ('g-alone',)

    # But a second g in time gives the chord.
    assert m.push(Key('g')).is_pending
    assert m.push(Key('g')).commands == ('top',)
