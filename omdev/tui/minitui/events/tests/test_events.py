# @om-precheck-allow-any-unicode
import pytest

from ..keymaps import Keymap
from ..keymaps import KeymapMatcher
from ..keys import Key
from ..keys import KeySpecError
from ..keys import key_from_char
from ..keys import parse_key
from ..types import CursorPositionEvent
from ..types import FocusEvent
from ..types import KeyEvent
from ..types import KittyFlagsEvent
from ..types import ModeReportEvent
from ..types import MouseEvent
from ..types import MouseEventKind
from ..types import PasteEvent
from ..types import UnknownSequenceEvent
from ..xterm import SS3_TIMEOUT_S
from ..xterm import XtermEventParser


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


def test_modify_other_keys_sequences():
    p = XtermEventParser()
    # xterm modifyOtherKeys format: CSI 27;mod;codepoint~
    assert keys(p.feed('\x1b[27;5;13~')) == [Key('enter', ctrl=True)]
    assert keys(p.feed('\x1b[27;2;13~')) == [Key('enter', shift=True)]
    assert keys(p.feed('\x1b[27;5;106~')) == [Key('j', ctrl=True)]
    assert keys(p.feed('\x1b[27;2;97~')) == [Key('A')]  # shifted printable becomes its character
    assert keys(p.feed('\x1b[27;3;13~')) == [Key('enter', alt=True)]
    # Plain tilde keys are unaffected.
    assert keys(p.feed('\x1b[3~')) == [Key('delete')]


def test_extended_ctrl_aliases_fold_to_legacy_keys():
    # On the legacy wire ctrl+[ / ctrl+m / ctrl+i ARE escape / enter / tab; the extended protocols report them as
    # ctrl+letter codepoints. Both wires must produce the same keys - vim's ctrl+[ escape especially.
    p = XtermEventParser()
    assert keys(p.feed('\x1b[91;5u')) == [Key('escape')]      # kitty ctrl+[
    assert keys(p.feed('\x1b[27;5;91~')) == [Key('escape')]   # modifyOtherKeys ctrl+[
    assert keys(p.feed('\x1b[91;7u')) == [Key('escape', alt=True)]  # ctrl+alt+[ keeps alt, like legacy ESC-prefix
    assert keys(p.feed('\x1b[109;5u')) == [Key('enter')]      # ctrl+m
    assert keys(p.feed('\x1b[105;5u')) == [Key('tab')]        # ctrl+i


def test_extended_ctrl_aliases_leave_distinctions_intact():
    p = XtermEventParser()
    assert keys(p.feed('\x1b[91;1u')) == [Key('[')]                 # plain [
    assert keys(p.feed('\x1b[13;5u')) == [Key('enter', ctrl=True)]  # the real ctrl+enter (submit chord)
    assert keys(p.feed('\x1b[105;6u')) == [Key('I', ctrl=True)]     # ctrl+shift+i is not tab
    assert keys(p.feed('\x1b[104;5u')) == [Key('h', ctrl=True)]     # ctrl+h already agrees across wires


def test_ss3_tail_survives_delay():
    # F1-F4 are SS3-encoded (ESC O P..S); their final byte may lag well past the bare-ESC window (relays, load).
    # The SS3 continuation window is generous, like the CSI path - a 50ms window silently ate F1-F4 while F5+
    # (CSI-form) kept working.
    p = XtermEventParser()
    evs = list(p.feed('\x1bO'))
    assert p.pending_timeout_s == SS3_TIMEOUT_S
    evs += list(p.feed('Q'))
    assert keys(evs) == [Key('f2')]


def test_ss3_timeout_is_alt_shift_o():
    # A lone ESC O that really times out means alt+shift+o on the legacy wire - not a silent swallow.
    p = XtermEventParser()
    evs = list(p.feed('\x1bO'))
    evs += list(p.flush_timeout())
    assert keys(evs) == [Key('O', alt=True)]


def test_kitty_numeric_function_keys():
    # Report-all-keys kitty implementations send numeric functional codes instead of legacy CSI/SS3 forms.
    p = XtermEventParser()
    assert keys(p.feed('\x1b[57364;1u')) == [Key('f1')]
    assert keys(p.feed('\x1b[57365;1u')) == [Key('f2')]
    assert keys(p.feed('\x1b[57373u')) == [Key('f10')]


def test_iterm2_kitty_fkeys_csi_tilde():
    # iTerm2's kitty-protocol mode reports F1-F4 as CSI 11~..14~ (not SS3 / CSI P..S).
    p = XtermEventParser()
    assert keys(p.feed('\x1b[11~\x1b[12~\x1b[13~\x1b[14~')) == [Key('f1'), Key('f2'), Key('f3'), Key('f4')]
