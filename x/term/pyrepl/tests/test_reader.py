import itertools

from ..readers.reader import Reader
from .harness import code_to_events
from .harness import keys_to_events
from .harness import make_reader
from .harness import read_line


##


def test_basic_input():
    reader = make_reader(code_to_events('hello\n'))
    result = read_line(reader)

    assert result == 'hello'
    assert reader.screen == ['>>> hello']


def test_backspace_edits_buffer():
    events = itertools.chain(
        code_to_events('hellx'),
        keys_to_events('backspace'),
        code_to_events('o\n'),
    )
    reader = make_reader(events)
    result = read_line(reader)

    assert result == 'hello'
    assert reader.screen == ['>>> hello']


def test_cursor_position_simple():
    reader = make_reader(code_to_events('ab\n'))
    read_line(reader)

    # cursor after 'ab' behind the 4-wide prompt
    assert reader.cxy == (6, 0)


def test_multiline_input():
    reader = make_reader(code_to_events('aaa\nbbb\n\n'))
    reader.more_lines = lambda text: not text.endswith('\n')
    result = read_line(reader)

    assert result == 'aaa\nbbb\n'
    assert reader.screen == ['>>> aaa', '... bbb', '... ']


def test_long_line_wraps():
    reader = make_reader(code_to_events('a' * 8 + '\n'), width=10)
    result = read_line(reader)

    assert result == 'a' * 8
    # 10 columns - 4 prompt - 1 continuation marker = 5 chars on the first row
    assert reader.screen == ['>>> aaaaa\\', 'aaa']


def test_error_message_renders_and_clears():
    events = itertools.chain(
        keys_to_events('backspace'),  # can't backspace at start -> error message
        code_to_events('a\n'),
    )
    reader = make_reader(events)
    # ReadlineAlikeReader silences errors; restore base behavior
    reader.error = Reader.error.__get__(reader)  # type: ignore[method-assign]
    result = read_line(reader)

    assert result == 'a'
    # message was cleared by the subsequent keypress
    assert reader.screen == ['>>> a']
    assert reader.console.beeps == 1  # type: ignore[attr-defined]


def test_completion_menu_overlay():
    def completer(stem, state):
        words = ['aaa_bar', 'aaa_foo']
        matches = [w for w in words if w.startswith(stem)]
        if state < len(matches):
            return matches[state]
        return None

    events = itertools.chain(
        code_to_events('aaa_'),
        keys_to_events('\t', '\t'),
    )
    reader = make_reader(events, completer=completer)
    reader.prepare()
    try:
        while True:
            reader.handle1()
    except StopIteration:
        pass

    screen = reader.screen
    assert screen[0] == '>>> aaa_'
    assert 'aaa_bar' in screen[1]
    assert 'aaa_foo' in screen[1]

    # the completion menu is composed as an overlay, not part of the base content
    assert len(reader.rendered_screen.overlays) == 1
    assert reader.rendered_screen.overlays[0].insert


def test_completion_menu_hidden_on_accept():
    def completer(stem, state):
        words = ['aaa_bar', 'aaa_foo']
        matches = [w for w in words if w.startswith(stem)]
        if state < len(matches):
            return matches[state]
        return None

    events = itertools.chain(
        code_to_events('aaa_'),
        keys_to_events('\t', '\t'),
        code_to_events('\n'),
    )
    reader = make_reader(events, completer=completer)
    result = read_line(reader)

    assert result == 'aaa_'
    assert reader.screen == ['>>> aaa_']


def test_history_recall():
    events = itertools.chain(
        keys_to_events('up', 'up'),
        code_to_events('\n'),
    )
    reader = make_reader(events)
    reader.history.extend(['first', 'second'])
    result = read_line(reader)

    assert result == 'first'
    assert reader.screen == ['>>> first']


def test_incremental_typing_reuses_cache():
    reader = make_reader(code_to_events('abc\n'))
    result = read_line(reader)

    assert result == 'abc'
    # each keypress triggered a refresh (plus the initial empty-prompt one)
    assert reader.console.refresh_count >= 4  # type: ignore[attr-defined]


def test_cursor_only_movement_skips_refresh():
    events = itertools.chain(
        code_to_events('ab'),
        keys_to_events('left'),
        code_to_events('\n'),
    )
    reader = make_reader(events)
    read_line(reader)

    # 'left' from the end of a two-char buffer lands between 'a' and 'b', and accept doesn't move it
    assert reader.pos == 1
    assert reader.screen == ['>>> ab']
