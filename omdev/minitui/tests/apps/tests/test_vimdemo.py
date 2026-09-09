from ....events.keys import Key
from ....events.keys import key_text
from ....events.types import KeyEvent
from ....runtime.sync import SyncDriver
from ...harness import SurfaceHarness
from ..vimdemo import VimDemoApp


##


def make_app(**kwargs):
    h = SurfaceHarness(height=10, width=40)
    return VimDemoApp(SyncDriver(h.surface), None, **kwargs)


def press(app, *keys):
    for k in keys:
        key = Key(k) if isinstance(k, str) else k
        app.handle_event(KeyEvent(key, text=key_text(key)))


def type_text(app, text):
    for c in text:
        press(app, c if c != ' ' else 'space')


def screen(app, width=40, max_height=10):
    return [line.text for line in app.render(width, max_height).lines]


def ex(app, line):
    type_text(app, ':' + line)
    press(app, 'enter')


def test_set_number_ex_command():
    app = make_app()
    press(app, 'i')
    type_text(app, 'one')
    press(app, 'enter')
    type_text(app, 'two')
    press(app, 'escape')
    assert screen(app)[:2] == ['one', 'two']

    ex(app, 'set nu')
    assert screen(app)[:2] == ['  1 one', '  2 two']

    ex(app, 'set nonumber')
    assert screen(app)[:2] == ['one', 'two']

    ex(app, 'set number!')
    assert screen(app)[0] == '  1 one'
    ex(app, 'set nu!')
    assert screen(app)[0] == 'one'

    # Unknown options report through the engine's message slot, which the status line shows.
    ex(app, 'set foo')
    assert any('Unknown option: foo' in line for line in screen(app))


def test_number_flag():
    app = make_app(number=True)
    press(app, 'i')
    type_text(app, 'x')
    press(app, 'escape')
    assert screen(app)[0] == '  1 x'
