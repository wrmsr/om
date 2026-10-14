"""
ctrl+l is the polite clear: the app hands it to the driver, which scrolls the live region to the top of the terminal
with the transcript above it into scrollback, and nothing in the box is touched - in every editor mode, and fullscreen
alike.
"""
from omdev import minitui as mt

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


def visible(app):
    return [line for line in frame_lines(app) if line.strip()]


def test_ctrl_l_clears_through_the_driver():
    app, driver = make_app()
    submitted: list[str] = []
    app.on_submit = submitted.append

    type_text(app, 'draft')
    press(app, mt.Key('l', ctrl=True))
    assert driver.clears == 1
    assert visible(app)[0] == '1 draft'

    press(app, 'escape', mt.Key('l', ctrl=True))
    assert driver.clears == 2
    assert visible(app)[0] == '1 draft'

    press(app, 'f12', mt.Key('l', ctrl=True))
    assert (app.is_browsing, driver.clears) == (True, 3)

    # Nothing left the box.
    assert submitted == []
    assert not driver.stopped
