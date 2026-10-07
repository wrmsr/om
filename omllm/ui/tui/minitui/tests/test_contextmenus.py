import pytest

from omdev import minitui as mt

from ..app import ContextTarget
from ..app import ToolCardRecord
from ..app import TurnRecord
from .utils import frame_lines
from .utils import make_app


##


def press(app, key):
    app.handle_event(mt.KeyEvent(mt.Key(key), text=mt.key_text(mt.Key(key))))


def click(app, x, y):
    app.handle_event(mt.MouseEvent(mt.MouseEventKind.DOWN, x, y))


def row_of(app, text):
    return next(i for i, line in enumerate(frame_lines(app)) if text in line)


def open_menu(app, text, x=8):
    click(app, x, row_of(app, text))
    assert 'Placeholder action' in '\n'.join(frame_lines(app))


@pytest.mark.parametrize('part', ['header', 'settled', 'tail'])
def test_ai_message_parts_resolve_to_the_same_turn(part):
    app, _ = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.begin_ai_turn()
    turn = app.transcript.blocks[0].tag
    app.stream_feed('Settled paragraph.\n\nlive tail')
    press(app, 'f12')
    open_menu(app, {'header': 'ai ', 'settled': 'Settled paragraph.', 'tail': 'live tail'}[part])
    press(app, 'enter')
    assert selected == [turn]
    assert isinstance(selected[0], TurnRecord)
    assert 'Placeholder action' not in '\n'.join(frame_lines(app))
    assert bool(app.is_browsing)


def test_user_message_menu_mouse_activation_and_identity():
    app, _ = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.show_user_message('first message')
    app.show_user_message('second message')
    first, second = app.transcript.blocks
    press(app, 'f12')
    open_menu(app, 'first message')
    click(app, 9, row_of(app, 'Placeholder action'))
    assert selected == [first.tag]
    open_menu(app, 'second message')
    press(app, 'enter')
    assert selected == [first.tag, second.tag]
    assert isinstance(selected[0], TurnRecord)
    assert selected[0].text == 'first message'


def test_immediate_and_restored_message_output_is_tagged_by_turn():
    app, _ = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.begin_ai_turn()
    turn = app.transcript.blocks[0].tag
    app.display_markdown('Non-streamed response')
    app.end_ai_turn()
    press(app, 'f12')
    open_menu(app, 'Non-streamed response')
    press(app, 'enter')
    assert selected == [turn]


def test_untagged_output_menu_receives_the_block():
    app, _ = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.display_text('standalone output')
    [block] = app.transcript.blocks
    press(app, 'f12')
    open_menu(app, 'standalone output')
    press(app, 'enter')
    assert selected == [block]


def test_live_card_expander_and_detail_menu_then_finalization():
    app, driver = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.begin_ai_turn()
    turn = app.transcript.blocks[0].tag
    app.tool_started('call-a', 'alpha', [[mt.Segment('alpha detail')]])
    press(app, 'f12')
    click(app, 1, row_of(app, 'alpha'))
    assert 'alpha detail' in '\n'.join(frame_lines(app))
    assert 'Placeholder action' not in '\n'.join(frame_lines(app))

    open_menu(app, 'alpha detail')
    # The menu captures the exact widget, not a lookup into the collection of currently live cards.
    app.tool_finished('call-a', 'alpha', ok=True)
    driver.fire_after(.8)
    frame_lines(app)
    press(app, 'enter')
    [record] = selected
    assert isinstance(record, ToolCardRecord)
    assert record.key == 'call-a'
    assert record.turn is turn
    assert record.card.state is mt.CardState.COMPLETE
    assert app.transcript.blocks[-1].tag is record

    open_menu(app, 'alpha detail')
    press(app, 'enter')
    assert selected == [record, record]
    open_menu(app, 'alpha  done')
    press(app, 'enter')
    assert selected == [record, record, record]


def test_reused_tool_key_does_not_retarget_historical_menu():
    app, driver = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.tool_started('same-key', 'old card', ())
    app.tool_finished('same-key', 'old card', ok=True)
    driver.fire_after(.8)
    old = app.transcript.blocks[-1].tag
    assert isinstance(old, ToolCardRecord)
    app.tool_started('same-key', 'new card', ())
    press(app, 'f12')
    open_menu(app, 'old card')
    press(app, 'enter')
    open_menu(app, 'new card')
    press(app, 'enter')
    assert selected[0] is old
    assert isinstance(selected[1], ToolCardRecord)
    assert selected[1].key == old.key
    assert selected[1].card is not old.card


def test_menu_dismissal_navigation_and_browse_exit():
    app, _ = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.show_user_message('message')
    press(app, 'f12')
    open_menu(app, 'message')
    press(app, 'escape')
    assert bool(app.is_browsing)
    assert 'Placeholder action' not in '\n'.join(frame_lines(app))

    open_menu(app, 'message')
    press(app, 'q')
    assert bool(app.is_browsing)
    open_menu(app, 'message')
    click(app, 0, 20)  # outside the menu: dismiss without activating or clicking through
    assert 'Placeholder action' not in '\n'.join(frame_lines(app))

    open_menu(app, 'message')
    press(app, 'j')
    press(app, 'enter')  # Close, not the placeholder
    assert selected == []
    open_menu(app, 'message')
    press(app, 'f12')
    assert not app.is_browsing
    press(app, 'f12')
    assert 'Placeholder action' not in '\n'.join(frame_lines(app))


def test_scrolled_and_edge_clamped_menu_uses_overlay_hit_coordinates():
    app, _ = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    for i in range(40):
        app.show_user_message(f'message {i}')
    press(app, 'f12')
    frame_lines(app)
    press(app, 'g')
    open_menu(app, 'message 0', x=79)
    # At the right edge the overlay shifts left. Route using its actual box, not the original click position.
    lines = frame_lines(app)
    y = next(i for i, line in enumerate(lines) if 'Placeholder action' in line)
    x = lines[y].index('Placeholder action')
    click(app, x, y)
    assert selected == [app.transcript.blocks[0].tag]


def test_live_permission_widget_click_does_not_answer_permission():
    app, _ = make_app()
    responses: list[bool] = []
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.begin_permission_card('permission', 'exec', (), responses.append)
    press(app, 'f12')
    open_menu(app, 'allow (f10)')
    press(app, 'enter')
    assert responses == []
    assert isinstance(selected[0], ToolCardRecord)
    assert selected[0].card.state is mt.CardState.CONFIRMING


def test_card_without_detail_has_no_expander_to_capture_clicks():
    app, _ = make_app()
    selected: list[ContextTarget] = []
    app.on_context_action = selected.append
    app.tool_started('empty', 'empty card', ())
    press(app, 'f12')
    open_menu(app, 'empty card', x=1)
    press(app, 'enter')
    assert isinstance(selected[0], ToolCardRecord)
    assert selected[0].key == 'empty'


def test_live_spacer_and_browse_padding_do_not_open_menus():
    app, _ = make_app()
    app.tool_started('call', 'tool widget', ())
    press(app, 'f12')
    click(app, 8, row_of(app, 'tool widget') + 1)
    assert 'Placeholder action' not in '\n'.join(frame_lines(app))
    click(app, 8, 20)
    assert 'Placeholder action' not in '\n'.join(frame_lines(app))


def test_menu_preserves_global_permission_keys():
    app, _ = make_app()
    responses: list[bool] = []
    app.begin_permission_card('permission', 'exec', (), responses.append)
    press(app, 'f12')
    open_menu(app, 'exec')
    press(app, 'f10')
    assert responses == [True]
    assert 'Placeholder action' in '\n'.join(frame_lines(app))
    press(app, 'escape')
    assert bool(app.is_browsing)
