"""
shift+tab unindents the chat input, IdeaVim-style, in every editor mode: the app claims plain tab for the suggestions
popup and nothing else of the pair, so the shifted key reaches the editor untouched.
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


def test_shift_tab_dedents_input():
    app, driver = make_app()
    submitted: list[str] = []
    app.on_submit = submitted.append

    press(app, 'tab', 'tab')
    type_text(app, 'foo')
    assert visible(app)[0] == '1         foo'

    press(app, mt.Key('tab', shift=True))
    assert visible(app)[0] == '1     foo'

    press(app, 'escape', mt.Key('tab', shift=True))
    assert visible(app)[0] == '1 foo'

    # Nothing left the box.
    assert submitted == []
    assert not driver.stopped
