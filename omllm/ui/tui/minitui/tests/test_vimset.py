"""
`:set nu` reaches the chat surface through the vim engine's builtin ex commands: the line number column toggles while
whatever is typed in the box - harness commands included - stays put and is never submitted.
"""
from omdev.tui import minitui as mt

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


def test_set_number_toggles_gutter_and_keeps_entry():
    app, driver = make_app()
    submitted: list[str] = []
    app.on_submit = submitted.append

    type_text(app, '/help please')
    press(app, 'enter')
    type_text(app, 'second line')
    assert visible(app)[:2] == ['1 /help please', '2 second line']

    press(app, 'escape')
    type_text(app, ':set nu!')
    press(app, 'enter')
    assert visible(app)[:2] == ['/help please', 'second line']

    type_text(app, ':set number')
    press(app, 'enter')
    assert visible(app)[:2] == ['1 /help please', '2 second line']

    type_text(app, ':set nonu')
    press(app, 'enter')
    assert visible(app)[:2] == ['/help please', 'second line']

    # Nothing left the box, and the app-side ex handler (quit) was never involved.
    assert submitted == []
    assert not driver.stopped


def test_set_unknown_option_reports_in_status():
    app, _ = make_app()
    type_text(app, 'draft')
    press(app, 'escape')
    type_text(app, ':set foo')
    press(app, 'enter')
    lines = visible(app)
    assert lines[0] == '1 draft'
    assert any('Unknown option: foo' in line for line in lines)
