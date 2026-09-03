"""ctrl+z as an app key: the extended-key wire delivers the chord to the app, which hands it to the driver."""
from omdev.tui import minitui as mt

from ..app import AppKey
from .utils import app_key
from .utils import frame_lines
from .utils import make_app


##


def test_suspend_key_reaches_driver():
    app, driver = make_app()
    assert driver.suspends == 0

    app.handle_event(mt.KeyEvent(app_key(AppKey.SUSPEND)))
    assert driver.suspends == 1

    # The chord is the app's, never the editor's: nothing was typed into the input.
    assert not any('z' in line for line in frame_lines(app) if line.startswith('>'))


def test_suspend_and_resume_events_are_harmless():
    app, driver = make_app()
    before = frame_lines(app)

    app.handle_event(mt.SuspendEvent())
    app.handle_event(mt.ResumeEvent())
    assert frame_lines(app) == before
    assert driver.suspends == 0
