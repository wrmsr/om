from ...events.keys import Key
from ...events.types import KeyEvent
from ...events.types import MouseEvent
from ...events.types import MouseEventKind
from ..menus import Menu
from ..menus import MenuItem


##


def _texts(rows):
    return [''.join(seg.text for seg in row) for row in rows]


def _tags(rows):
    return [row[0].style for row in rows]


def _menu(calls):
    return Menu(
        [
            MenuItem('open', on_select=lambda: calls.append('open')),
            MenuItem('copy raw', disabled=True),
            MenuItem('close'),
        ],
        on_close=lambda: calls.append('closed'),
    )


def test_menu_render_and_width():
    m = _menu([])
    assert m.width == 10
    rows = m.render(m.width)
    assert _texts(rows) == [' open     ', ' copy raw ', ' close    ']
    assert _tags(rows) == ['menu.selected', 'menu.disabled', 'menu.item']

    # Narrower than its labels: they clip inside the padding.
    assert _texts(m.render(6)) == [' open ', ' copy ', ' clos ']

    assert Menu(min_width=12).width == 12
    assert Menu().render(5) == []


def test_menu_moves_over_enabled_items_and_wraps():
    m = _menu([])
    steps = [m.selected_index]
    m.move(1)
    steps.append(m.selected_index)  # skips the disabled item
    m.move(1)
    steps.append(m.selected_index)  # wraps
    m.move(-1)
    steps.append(m.selected_index)
    m.select(1)
    steps.append(m.selected_index)  # a disabled item cannot be selected
    m.select(0)
    steps.append(m.selected_index)
    assert steps == [0, 2, 0, 2, 2, 0]


def test_menu_keys():
    calls: list[str] = []
    m = _menu(calls)
    assert m.handle_event(KeyEvent(Key('j')))
    assert m.selected.label == 'close'
    assert m.handle_event(KeyEvent(Key('k')))
    assert m.handle_event(KeyEvent(Key('enter')))
    assert calls == ['open', 'closed']  # an activation runs the action, then the menu closes itself

    assert m.handle_event(KeyEvent(Key('q')))
    assert m.handle_event(KeyEvent(Key('escape')))
    assert calls == ['open', 'closed', 'closed', 'closed']
    assert not m.handle_event(KeyEvent(Key('x')))
    assert calls[-1] == 'closed' and len(calls) == 4


def test_menu_clicks():
    calls: list[str] = []
    m = _menu(calls)
    assert not m.handle_event(MouseEvent(MouseEventKind.DOWN, 0, 1))  # disabled row: nothing
    assert calls == []
    assert not m.handle_event(MouseEvent(MouseEventKind.DOWN, 0, 5))  # off the end
    assert m.handle_event(MouseEvent(MouseEventKind.DOWN, 3, 0))
    assert calls == ['open', 'closed']
    assert not m.handle_event(MouseEvent(MouseEventKind.SCROLL_UP, 0, 0))


def test_menu_all_disabled():
    m = Menu([MenuItem('a', disabled=True), MenuItem('b', disabled=True)])
    assert m.selected is None
    m.move(1)
    assert m.selected_index is None
    assert not m.activate()
    assert _tags(m.render(4)) == ['menu.disabled', 'menu.disabled']
