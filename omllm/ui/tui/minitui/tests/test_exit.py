# ruff: noqa: SLF001
import pytest

from omdev import minitui as mt
from omdev.minitui.docs.positions import Pos

from ..app import AppKey
from .utils import app_key
from .utils import frame_lines
from .utils import make_app


##


def _ctrl_d(app):
    app.handle_event(mt.KeyEvent(app_key(AppKey.EXIT)))


def _has_hint(app):
    return any('press ctrl-d again to exit' in line for line in frame_lines(app))


@pytest.mark.parametrize('browsing', [False, True])
def test_empty_input_confirms_exit(browsing):
    app, driver = make_app()
    app.set_browsing(browsing)

    _ctrl_d(app)
    stopped_before = driver.stopped
    assert not stopped_before
    assert _has_hint(app)
    driver.fire_after(.5)
    _ctrl_d(app)
    assert driver.stopped
    assert not _has_hint(app)


@pytest.mark.parametrize('busy', [False, True])
def test_hint_expires_and_survives_status_updates(busy):
    app, driver = make_app()
    if busy:
        app.begin_ai_turn()
    _ctrl_d(app)
    driver.fire_after(.9)
    assert _has_hint(app)
    driver.fire_after(.1)
    assert not _has_hint(app)
    assert not driver.stopped

    _ctrl_d(app)
    assert _has_hint(app)
    assert not driver.stopped


@pytest.mark.parametrize('event', [mt.KeyEvent(mt.Key('left')), mt.PasteEvent('')])
def test_other_input_disarms_exit(event):
    app, driver = make_app()
    _ctrl_d(app)
    app.handle_event(event)
    assert not _has_hint(app)
    driver.fire_after(.5)
    _ctrl_d(app)
    driver.fire_after(.5)  # the cancelled timer must not clear the new confirmation
    assert _has_hint(app)
    assert not driver.stopped


@pytest.mark.parametrize(('text', 'cursor', 'expected'), [
    ('abc', (0, 1), 'ac'),
    ('ab\ncd', (0, 2), 'abcd'),
    ('abc', (0, 3), 'abc'),
    (' ', (0, 0), ''),
    ('\n', (0, 0), ''),
])
@pytest.mark.parametrize('browsing', [False, True])
def test_nonempty_input_deletes_without_quitting(text, cursor, expected, browsing):
    app, driver = make_app()
    app._input.set_text(text)
    app._input.engine.set_cursor(Pos(*cursor))
    app.set_browsing(browsing)

    _ctrl_d(app)
    assert app._input.doc.text() == expected
    assert not app.is_browsing
    assert not driver.stopped
    assert not _has_hint(app)
