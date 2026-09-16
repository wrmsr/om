"""
Browse mode: f12 takes the chat surface fullscreen over its own transcript, esc (or f12) brings the live view back,
and the transcript records every commit tagged by turn.
"""
from omdev import minitui as mt

from ..app import MinituiChatApp
from ..app import TurnRecord
from .utils import Driver
from .utils import frame_lines
from .utils import make_app


##


def press(app, *keys):
    for k in keys:
        key = mt.Key(k) if isinstance(k, str) else k
        app.handle_event(mt.KeyEvent(key, text=mt.key_text(key)))


def type_text(app, text):
    for c in text:
        press(app, c if c != ' ' else 'space')


def wheel(app, kind, y=0):
    app.handle_event(mt.MouseEvent(kind, 0, y))


def _fill(app, n):
    for i in range(n):
        app.display_text(f'row {i}')


##


def test_f12_enters_browse_and_esc_leaves():
    app, driver = make_app()
    app.show_user_message('hello there')
    type_text(app, 'draft')

    press(app, 'f12')
    entered = (app.is_browsing, driver.alt_screen)
    lines = frame_lines(app)
    assert len(lines) == 24  # fullscreen: the view pads to the terminal
    assert any('hello there' in line for line in lines)
    assert lines[-1].startswith('BROWSE')
    assert 'following' in lines[-1]
    assert not any('draft' in line for line in lines)  # the input is not part of the browse view

    press(app, 'escape')
    assert (entered, app.is_browsing, driver.alt_screen) == ((True, True), False, False)
    lines = frame_lines(app)
    assert any('draft' in line for line in lines)  # the live view, untouched
    assert not any('hello there' in line for line in lines)  # that is scrollback, not the live region

    press(app, 'f12', 'f12')
    assert not app.is_browsing


def test_browse_scrolls_with_wheel_and_keys():
    app, driver = make_app()
    _fill(app, 60)
    press(app, 'f12')

    lines = frame_lines(app)
    assert 'row 59' in lines[-3]  # pinned to the present on entry (the last commit ends with a blank separator)
    assert 'following' in lines[-1]

    wheel(app, mt.MouseEventKind.SCROLL_UP)
    lines = frame_lines(app)
    assert 'row 59' not in '\n'.join(lines)
    assert 'following' not in lines[-1]
    top_after_wheel = lines[0]

    press(app, 'k')
    lines = frame_lines(app)
    assert lines[1] == top_after_wheel

    press(app, 'G')
    lines = frame_lines(app)
    assert 'row 59' in lines[-3]
    assert 'following' in lines[-1]

    press(app, 'g')
    assert frame_lines(app)[0] == 'row 0'


def test_browse_keeps_following_new_content():
    app, driver = make_app()
    _fill(app, 40)
    press(app, 'f12')
    app.display_text('brand new')
    assert 'brand new' in frame_lines(app)[-3]

    # Scrolled up, new content does not move the view.
    wheel(app, mt.MouseEventKind.SCROLL_UP)
    before = frame_lines(app)[:-1]
    app.display_text('even newer')
    assert frame_lines(app)[:-1] == before


def test_browse_shows_live_tail_and_cards():
    app, driver = make_app()
    app.begin_ai_turn()
    app.stream_feed('Settled paragraph.\n\nstill streaming')
    app.tool_started('k1', 'exec', [[mt.Segment('args: {}', 'card.detail')]])
    press(app, 'f12')

    text = '\n'.join(frame_lines(app))
    assert 'Settled paragraph.' in text
    assert 'still streaming' in text
    assert 'exec' in text

    # A click on the live card's header row toggles it, through the view.
    lines = frame_lines(app)
    card_row = next(i for i, line in enumerate(lines) if 'exec' in line)
    app.handle_event(mt.MouseEvent(mt.MouseEventKind.DOWN, 0, card_row))
    assert 'args: {}' in '\n'.join(frame_lines(app))


def test_browse_ignores_typing_by_default():
    app, driver = make_app()
    press(app, 'f12')
    type_text(app, 'xy')
    press(app, 'tab')
    assert app.is_browsing
    press(app, 'escape')
    assert frame_lines(app)[0] == '1 '  # nothing reached the input


def test_browse_type_returns_option():
    driver = Driver()
    app = MinituiChatApp(driver, browse_type_returns=True)  # type: ignore[arg-type]
    press(app, 'f12')
    type_text(app, 'x')
    assert not app.is_browsing
    assert not driver.alt_screen
    assert frame_lines(app)[0] == '1 x'


def test_browse_passes_global_keys_but_not_input_keys():
    app, driver = make_app()
    app.show_user_message('one')
    press(app, 'f12')

    # History and popup keys belong to the input and do nothing here.
    press(app, mt.Key('p', ctrl=True), 'tab')
    assert app.is_browsing

    press(app, mt.Key('d', ctrl=True))
    assert driver.stopped


def test_escape_in_live_mode_is_vims():
    app, driver = make_app()
    type_text(app, 'abc')
    press(app, 'escape')
    type_text(app, ':q')
    press(app, 'enter')
    assert driver.stopped
    assert not app.is_browsing


def test_transcript_records_commits_tagged_by_turn():
    app, driver = make_app()
    app.show_user_message('hi')
    [user_block] = app.transcript.blocks
    assert isinstance(user_block.tag, TurnRecord)
    assert (user_block.tag.speaker, user_block.tag.text) == ('you', 'hi')

    app.begin_ai_turn()
    app.stream_feed('First.\n\nSecond.\n\n')
    app.stream_break()
    app.end_ai_turn()
    ai_blocks = list(app.transcript.blocks)[1:]
    assert len(ai_blocks) >= 3
    tags = {id(block.tag) for block in ai_blocks}
    assert len(tags) == 1
    assert ai_blocks[0].tag.speaker == 'ai'

    # Harness output outside a turn is untagged, and the transcript mirrors the commits line for line.
    app.display_text('note')
    assert app.transcript.blocks[-1].tag is None
    assert [list(block.lines) for block in app.transcript.blocks] == [list(commit) for commit in driver.commits]
