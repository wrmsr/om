from omcore.term import styled as tst

from ..terminals import LineTerminal


##


RED = '\x1b[0;31m'
BOLD_BLUE = '\x1b[0;1;34m'
RESET = '\x1b[0m'


def feed_all(*chunks, **kwargs):
    terminal = LineTerminal(**kwargs)
    lines: list = []
    for chunk in chunks:
        lines.extend(terminal.feed(chunk))
    return lines, terminal


def test_lines():
    lines, terminal = feed_all('one\r\ntwo\nthr', 'ee\r\n\r\nrest')
    assert lines == ['one', 'two', 'three', '']
    assert terminal.has_partial_line
    assert terminal.flush() == 'rest'
    assert not terminal.has_partial_line
    assert terminal.flush() is None


def test_carriage_return_rewrites_the_line():
    assert feed_all('progress 10%\rprogress 100%\rdone\r\n')[0] == ['doneress 100%']
    assert feed_all('progress 10%\r\x1b[Kdone\r\n')[0] == ['done']
    assert feed_all('working...\r          \rdone\r\n')[0] == ['done']


def test_backspace_and_tab():
    assert feed_all('abc\b\bX\n')[0] == ['aXc']
    assert feed_all('\b\ba\tb\n')[0] == ['a       b']
    assert feed_all('a\tb\n', tab_width=4)[0] == ['a   b']
    assert feed_all('12345678\tx\n')[0] == ['12345678        x']


def test_in_line_cursor_movement_and_erasure():
    assert feed_all('12345\x1b[3D\x1b[Kxy\n')[0] == ['12xy']
    assert feed_all('ab\x1b[2Cc\x1b[1Gz\n')[0] == ['zb  c']
    assert feed_all('abcdef\x1b[3D\x1b[1Kx\n')[0] == ['   xef']
    assert feed_all('abcdef\x1b[2Kx\n')[0] == ['      x']
    assert feed_all('ab\x1b[99Dc\n')[0] == ['cb']


def test_styles_are_kept_and_every_line_stands_alone():
    lines, _ = feed_all('plain \x1b[31mred\r\nstill red\x1b[m no more\r\n\x1b[1;34mbold blue\x1b[0m\r\n')
    assert lines == [
        f'plain {RED}red{RESET}',
        f'{RED}still red{RESET} no more',
        f'{BOLD_BLUE}bold blue{RESET}',
    ]
    assert [tst.strip_ansi_escapes(line) for line in lines] == ['plain red', 'still red no more', 'bold blue']


def test_styles_follow_the_cells_they_were_written_to():
    assert feed_all('\x1b[31mred\x1b[0m\rX\n')[0] == [f'X{RED}ed{RESET}']
    # Blanks written in a style are text; plain ones at the end of a line are not.
    assert feed_all('\x1b[41m  \x1b[0m  \n')[0] == ['\x1b[0;41m  \x1b[0m']


def test_extended_colors():
    assert feed_all('\x1b[38;5;208mx\x1b[38;2;1;2;3my\x1b[39mz\n')[0] == [
        '\x1b[0;38;5;208mx\x1b[0;38;2;1;2;3my\x1b[0mz',
    ]


def test_other_control_sequences_are_dropped():
    lines, _ = feed_all(
        '\x1b]0;window title\x07a'  # an operating system command, bell-terminated
        '\x1b]8;;http://x\x1b\\b'  # ...and string-terminated
        '\x1b(B\x1b=\x1b>c'  # charset and keypad selections
        '\x1b[?25l\x1b[?2004h\x1b[2J\x1b[H\x1b[5A\x1b[>cd'  # private modes, screen addressing, a device query
        '\x1bPdevice control\x1b\\e'
        '\x07\x00\x0e\x7f\x9bf'  # stray controls
        '\n',
    )
    assert lines == ['abcdef']


def test_a_sequence_cut_by_the_end_of_a_feed_is_finished_by_the_next():
    text = 'a\x1b[1;31mb\x1b]0;title\x07c\x1b(Bd\x1b[0me\n'
    expected = feed_all(text)[0]
    assert expected == ['a\x1b[0;1;31mbcd\x1b[0me']
    for i in range(len(text) + 1):
        assert feed_all(text[:i], text[i:])[0] == expected


def test_an_escape_which_is_no_sequence():
    assert feed_all('a\x1b\x01b\n')[0] == ['ab']
    # Unfinished for too long to be one: the escape goes, and what followed it was text after all.
    lines, terminal = feed_all('\x1b]' + 'x' * 100, 'y\n', max_pending_chars=50)
    assert lines == [']' + 'x' * 100 + 'y']


def test_long_lines_are_broken():
    lines, terminal = feed_all('x' * 25 + '\n', max_line_chars=10)
    assert lines == ['x' * 10, 'x' * 10, 'x' * 5]
    lines, terminal = feed_all('a\x1b[999Cb\n', max_line_chars=10)
    assert lines == ['a', 'b']


def test_the_alternate_screen_is_reported_and_not_rendered():
    terminal = LineTerminal()
    states = [terminal.in_alt_screen]

    assert terminal.feed('before\r\n\x1b[?1049h\x1b[2J\x1b[Hall over\r\nthe screen') == ['before']
    states.append(terminal.in_alt_screen)
    assert not terminal.has_partial_line

    assert terminal.feed('\x1b[?1049lafter\r\n') == ['after']
    states.append(terminal.in_alt_screen)

    assert states == [False, True, False]

    for mode in ('47', '1047', '1049', '1049;25'):
        terminal = LineTerminal()
        terminal.feed(f'\x1b[?{mode}h')
        assert terminal.in_alt_screen


def test_unfinished_lines_keep_their_trailing_blanks():
    terminal = LineTerminal()
    terminal.feed('password: ')
    assert terminal.flush() == 'password: '
    assert terminal.feed('typed\n') == ['typed']
