import pytest

from omdev import minitui as mt

from .....core import ui
from ..app import THEME
from .utils import ListClipboard
from .utils import frame_lines
from .utils import make_app


##


def press(app, key):
    app.handle_event(mt.KeyEvent(mt.Key(key), text=mt.key_text(mt.Key(key))))


def click(app, x, y):
    app.handle_event(mt.MouseEvent(mt.MouseEventKind.DOWN, x, y))


def move(app, x, y):
    app.handle_event(mt.MouseEvent(mt.MouseEventKind.MOVE, x, y))


def row_of(app, text):
    return next(i for i, line in enumerate(frame_lines(app)) if text in line)


def row_style(app, text):
    """The resolved style of the first cell of `text` on the row it is found on."""

    frame = app.render(80, 24)
    y = next(i for i, line in enumerate(frame.lines) if text in line.text)
    return frame.lines[y].cells[frame.lines[y].text.index(text)].style


def menu_open(app):
    return 'Copy' in '\n'.join(frame_lines(app))


def open_menu(app, text, x=8):
    click(app, x, row_of(app, text))
    assert menu_open(app)


def copy_app():
    clipboard = ListClipboard()
    app, driver = make_app(clipboard=clipboard)
    return app, driver, clipboard


@pytest.mark.parametrize('part', ['header', 'settled', 'tail'])
def test_ai_message_parts_copy_the_same_turn(part):
    app, _, clipboard = copy_app()
    app.begin_ai_turn()
    app.stream_feed('Settled paragraph.\n\nlive tail')
    press(app, 'f12')
    open_menu(app, {'header': 'ai ', 'settled': 'Settled paragraph.', 'tail': 'live tail'}[part])
    press(app, 'enter')
    assert clipboard.texts == ['Settled paragraph.\n\nlive tail']
    assert not menu_open(app)
    assert bool(app.is_browsing)


def test_user_message_menu_mouse_activation_and_identity():
    app, _, clipboard = copy_app()
    app.show_user_message('first message')
    app.show_user_message('second message')
    press(app, 'f12')
    open_menu(app, 'first message')
    click(app, 9, row_of(app, 'Copy'))
    assert clipboard.texts == ['first message']
    open_menu(app, 'second message')
    press(app, 'enter')
    assert clipboard.texts == ['first message', 'second message']


def test_immediate_and_restored_message_output_copies_its_source():
    app, _, clipboard = copy_app()
    app.begin_ai_turn()
    app.display_markdown('Non-streamed *response*')
    app.end_ai_turn()
    press(app, 'f12')
    open_menu(app, 'Non-streamed response')
    press(app, 'enter')
    assert clipboard.texts == ['Non-streamed *response*']


def test_immediate_mode_ui_text_copies_markdown_source():
    app, _, clipboard = copy_app()
    app.begin_ai_turn()
    app.display_ui_text(ui.MarkdownText('A **bold** claim.'))
    app.end_ai_turn()
    press(app, 'f12')
    open_menu(app, 'A bold claim.')
    press(app, 'enter')
    assert clipboard.texts == ['A **bold** claim.']


def test_streamed_ai_turn_copies_raw_markdown_across_content_blocks():
    app, _, clipboard = copy_app()
    app.begin_ai_turn()
    for chunk in ['# Title\n\n- one\n', '- two']:
        app.stream_feed(chunk)
    app.stream_break()
    app.stream_feed('Then **more**.')
    app.stream_break()
    app.display_text('retrying in 5s', 'status.dim')  # a note in the turn, not the model's text
    app.end_ai_turn()
    press(app, 'f12')
    open_menu(app, 'Title')
    press(app, 'enter')
    assert clipboard.texts == ['# Title\n\n- one\n- two\n\nThen **more**.']


def test_ai_turn_without_text_has_copy_disabled():
    app, _, clipboard = copy_app()
    app.begin_ai_turn()
    app.display_text('tool: foo()', 'status.dim')
    app.end_ai_turn()
    press(app, 'f12')
    open_menu(app, 'tool: foo()')
    click(app, 9, row_of(app, 'Copy'))  # a disabled item: a click on it is not an activation
    assert menu_open(app)
    press(app, 'k')
    press(app, 'enter')  # the selection never lands on the disabled item, so this is Close
    assert not menu_open(app)
    assert clipboard.texts == []
    assert 'nothing to copy' not in '\n'.join(frame_lines(app))


def test_untagged_output_menu_copies_the_block_text():
    app, _, clipboard = copy_app()
    app.display_text('standalone output', 'status.dim')
    press(app, 'f12')
    open_menu(app, 'standalone output')
    press(app, 'enter')
    assert clipboard.texts == ['standalone output']


def test_live_card_expander_and_detail_menu_then_finalization():
    app, driver, clipboard = copy_app()
    app.begin_ai_turn()
    app.tool_started('call-a', 'alpha', [[mt.Segment('alpha detail')]])
    press(app, 'f12')
    click(app, 1, row_of(app, 'alpha'))
    assert 'alpha detail' in '\n'.join(frame_lines(app))
    assert not menu_open(app)

    open_menu(app, 'alpha detail')
    # The menu captures the exact widget, not a lookup into the collection of currently live cards - and reads it as it
    # is when it copies.
    app.tool_finished('call-a', 'alpha', ok=True)
    driver.fire_after(.8)
    frame_lines(app)
    press(app, 'enter')
    assert clipboard.texts == ['alpha  done\nalpha detail']
    assert app.transcript.blocks[-1].tag.card.state is mt.CardState.COMPLETE

    open_menu(app, 'alpha detail')
    press(app, 'enter')
    open_menu(app, 'alpha  done')
    press(app, 'enter')
    assert clipboard.texts == ['alpha  done\nalpha detail'] * 3


def test_collapsed_card_copies_its_detail_too():
    app, driver, clipboard = copy_app()
    app.tool_started('call', 'tool', [[mt.Segment('args: {}')]])
    app.tool_finished(
        'call',
        'tool',
        ok=True,
        detail_rows=[[mt.Segment('args: {}')], [mt.Segment('line 1')], [mt.Segment('line 2  ')]],
    )
    driver.fire_after(.8)
    press(app, 'f12')
    assert 'line 1' not in '\n'.join(frame_lines(app))
    open_menu(app, 'tool  done')
    press(app, 'enter')
    assert clipboard.texts == ['tool  done\nargs: {}\nline 1\nline 2']


def test_reused_tool_key_does_not_retarget_historical_menu():
    app, driver, clipboard = copy_app()
    app.tool_started('same-key', 'old card', ())
    app.tool_finished('same-key', 'old card', ok=True)
    driver.fire_after(.8)
    app.tool_started('same-key', 'new card', ())
    press(app, 'f12')
    open_menu(app, 'old card')
    press(app, 'enter')
    open_menu(app, 'new card')
    press(app, 'enter')
    assert clipboard.texts == ['old card  done', 'new card  running...']


def test_menu_dismissal_navigation_and_browse_exit():
    app, _, clipboard = copy_app()
    app.show_user_message('message')
    press(app, 'f12')
    open_menu(app, 'message')
    press(app, 'escape')
    assert bool(app.is_browsing)
    assert not menu_open(app)

    open_menu(app, 'message')
    press(app, 'q')
    assert bool(app.is_browsing)
    open_menu(app, 'message')
    click(app, 0, 20)  # outside the menu: dismiss without activating or clicking through
    assert not menu_open(app)

    open_menu(app, 'message')
    press(app, 'j')
    press(app, 'enter')  # Close, not Copy
    assert clipboard.texts == []
    open_menu(app, 'message')
    press(app, 'f12')
    assert not app.is_browsing
    press(app, 'f12')
    assert not menu_open(app)


def test_scrolled_and_edge_clamped_menu_uses_overlay_hit_coordinates():
    app, _, clipboard = copy_app()
    for i in range(40):
        app.show_user_message(f'message {i}')
    press(app, 'f12')
    frame_lines(app)
    press(app, 'g')
    open_menu(app, 'message 0', x=79)
    # At the right edge the overlay shifts left. Route using its actual box, not the original click position.
    lines = frame_lines(app)
    y = next(i for i, line in enumerate(lines) if 'Copy' in line)
    x = lines[y].index('Copy')
    click(app, x, y)
    assert clipboard.texts == ['message 0']


def test_live_permission_widget_click_does_not_answer_permission():
    app, _, clipboard = copy_app()
    responses: list[bool] = []
    app.begin_permission_card('permission', 'exec', (), responses.append)
    press(app, 'f12')
    open_menu(app, 'allow (f10)')
    press(app, 'enter')
    assert responses == []
    assert clipboard.texts == ['exec  awaiting confirmation']


def test_card_without_detail_has_no_expander_to_capture_clicks():
    app, _, clipboard = copy_app()
    app.tool_started('empty', 'empty card', ())
    press(app, 'f12')
    open_menu(app, 'empty card', x=1)
    press(app, 'enter')
    assert clipboard.texts == ['empty card  running...']


def test_live_spacer_and_browse_padding_do_not_open_menus():
    app, _ = make_app()
    app.tool_started('call', 'tool widget', ())
    press(app, 'f12')
    click(app, 8, row_of(app, 'tool widget') + 1)
    assert not menu_open(app)
    click(app, 8, 20)
    assert not menu_open(app)


def test_menu_preserves_global_permission_keys():
    app, _ = make_app()
    responses: list[bool] = []
    app.begin_permission_card('permission', 'exec', (), responses.append)
    press(app, 'f12')
    open_menu(app, 'exec')
    press(app, 'f10')
    assert responses == [True]
    assert menu_open(app)
    press(app, 'escape')
    assert bool(app.is_browsing)


def test_copied_note_shows_then_clears():
    app, driver, clipboard = copy_app()
    app.show_user_message('message')
    press(app, 'f12')
    open_menu(app, 'message')
    press(app, 'enter')
    assert clipboard.texts == ['message']
    assert 'copied 7 chars' in '\n'.join(frame_lines(app))
    driver.fire_after(2.)
    assert 'copied' not in '\n'.join(frame_lines(app))
    assert 'BROWSE' in '\n'.join(frame_lines(app))


def test_copy_without_a_clipboard_says_so():
    app, driver = make_app()
    app.show_user_message('message')
    press(app, 'f12')
    open_menu(app, 'message')
    press(app, 'enter')
    assert 'no clipboard available' in '\n'.join(frame_lines(app))
    assert bool(app.is_browsing)
    driver.fire_after(2.)
    assert 'no clipboard available' not in '\n'.join(frame_lines(app))


def test_copy_failure_is_reported_not_raised():
    class BrokenClipboard(ListClipboard):
        def put(self, c):
            raise RuntimeError('no display')

    app, _ = make_app(clipboard=BrokenClipboard())
    app.show_user_message('message')
    press(app, 'f12')
    open_menu(app, 'message')
    press(app, 'enter')
    assert "copy failed: RuntimeError('no display')" in '\n'.join(frame_lines(app))
    assert bool(app.is_browsing)


def test_hover_follows_the_pointer_while_the_menu_is_up():
    app, driver, clipboard = copy_app()
    app.show_user_message('message')
    press(app, 'f12')
    assert not driver.mouse_motion

    open_menu(app, 'message')
    assert driver.mouse_motion
    assert row_style(app, 'Copy') == THEME.resolve('menu.selected')

    # Over Close: the selection follows, for one frame.
    n = driver.invalidations
    move(app, 9, row_of(app, 'Close'))
    assert driver.invalidations == n + 1
    assert row_style(app, 'Close') == THEME.resolve('menu.selected')
    assert row_style(app, 'Copy') == THEME.resolve('menu.item')

    # Still over Close, and then off the menu entirely: nothing moves, and nothing is repainted for it.
    n = driver.invalidations
    move(app, 10, row_of(app, 'Close'))
    move(app, 0, 20)
    assert driver.invalidations == n
    assert row_style(app, 'Close') == THEME.resolve('menu.selected')

    # Enter takes what hover selected.
    press(app, 'enter')
    assert clipboard.texts == []
    assert not menu_open(app)
    assert not driver.mouse_motion


def test_motion_without_a_menu_is_inert():
    app, driver = make_app()
    app.show_user_message('message')
    press(app, 'f12')
    n = driver.invalidations
    move(app, 5, row_of(app, 'message'))
    assert driver.invalidations == n
    assert not menu_open(app)

    # Every way out of the menu turns motion back off.
    open_menu(app, 'message')
    press(app, 'escape')
    assert not driver.mouse_motion
    open_menu(app, 'message')
    click(app, 0, 20)
    assert not driver.mouse_motion
    open_menu(app, 'message')
    press(app, 'f12')
    assert not app.is_browsing
    assert not driver.mouse_motion
