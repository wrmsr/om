from ..keys import Key
from ..motion import coalesce_mouse_motion
from ..types import KeyEvent
from ..types import MouseEvent
from ..types import MouseEventKind


##


def _move(x, y):
    return MouseEvent(MouseEventKind.MOVE, x, y)


def test_motion_runs_collapse_to_their_last():
    click = MouseEvent(MouseEventKind.DOWN, 5, 5)
    key = KeyEvent(Key('a'), text='a')
    events = [_move(1, 0), _move(2, 0), _move(3, 0), click, _move(4, 0), key, _move(5, 0), _move(6, 0)]
    assert list(coalesce_mouse_motion(events)) == [_move(3, 0), click, _move(4, 0), key, _move(6, 0)]


def test_motion_coalescing_leaves_other_streams_alone():
    assert list(coalesce_mouse_motion([])) == []
    scroll = MouseEvent(MouseEventKind.SCROLL_UP, 0, 0)
    up = MouseEvent(MouseEventKind.UP, 0, 0)
    assert list(coalesce_mouse_motion([scroll, up, scroll])) == [scroll, up, scroll]
    assert list(coalesce_mouse_motion([_move(0, 0)])) == [_move(0, 0)]
