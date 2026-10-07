"""The standalone repl app: in-process over a loop-free driver stand-in, and end to end under a real pty."""
import os.path
import sys

from omcore.term.vt100.terminal import Vt100Terminal

from .... import minitui as mt
from ....minitui.tests.ptys import PtyRun
from ...python.interpreter import PythonInterpreter
from ...runners import ImmediateRunner
from ...sessions import Session
from ..app import ReplApp


##


class _Clock:
    def __init__(self):
        super().__init__()

        self.now = 0.

    def __call__(self):
        return self.now


class _Surface:
    width = 80


class _Driver:
    def __init__(self):
        super().__init__()

        self.surface = _Surface()
        self.timers = mt.Timers(_Clock())
        self.commits = []
        self.invalidations = 0
        self.stopped = False
        self.suspends = 0

    def commit(self, lines):
        self.commits.append(tuple(lines))

    def invalidate(self):
        self.invalidations += 1

    def stop(self):
        self.stopped = True

    def suspend(self):
        self.suspends += 1


def make_app():
    driver = _Driver()
    session = Session({
        'py': PythonInterpreter(config=PythonInterpreter.Config(allow_await=False)),
        'py2': PythonInterpreter(config=PythonInterpreter.Config(allow_await=False)),
    })
    app = ReplApp(driver, session, runner=ImmediateRunner())  # type: ignore[arg-type]
    return app, driver


def press(app, *keys):
    for k in keys:
        key = mt.Key(k) if isinstance(k, str) else k
        app.handle_event(mt.KeyEvent(key, text=mt.key_text(key)))


def type_text(app, text):
    for c in text:
        press(app, c if c != ' ' else 'space')


def frame_lines(app):
    return [line.text for line in app.render(80, 24).lines]


def commit_texts(driver):
    return ['\n'.join(line.text for line in commit) for commit in driver.commits]


def test_type_and_run():
    app, driver = make_app()
    assert frame_lines(app)[0].startswith('>>> ')
    type_text(app, '1 + 1')
    assert frame_lines(app)[0] == '>>> 1 + 1'
    press(app, mt.Key('j', ctrl=True))
    assert commit_texts(driver) == ['>>> 1 + 1', '2', '']
    assert frame_lines(app)[0] == '>>> '
    assert 'python' in frame_lines(app)[-1]


def test_slash_commands_and_popup():
    app, driver = make_app()
    type_text(app, '/')
    lines = frame_lines(app)
    assert any(line.startswith('/py2') for line in lines)
    assert any(line.startswith('/quit') for line in lines)
    type_text(app, 'py2')
    press(app, mt.Key('j', ctrl=True))
    assert app.console.session.active_name == 'py2'

    type_text(app, '/nope')
    press(app, mt.Key('j', ctrl=True))
    assert commit_texts(driver)[-1].split('\n')[0] == 'unknown command: /nope'

    type_text(app, '/quit')
    press(app, mt.Key('j', ctrl=True))
    assert driver.stopped


def test_history_and_interrupt():
    app, driver = make_app()
    type_text(app, 'x = 1')
    press(app, mt.Key('j', ctrl=True))
    press(app, 'up')
    assert frame_lines(app)[0] == '>>> x = 1'
    app.interrupt()  # nothing running: clears the input
    assert frame_lines(app)[0] == '>>> '
    press(app, mt.Key('d', ctrl=True))
    assert driver.stopped


##


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 4)))


def test_pty_round_trip():
    run = PtyRun([sys.executable, '-m', 'omdev.repl.minitui', '--no-js'], cwd=_REPO_ROOT)
    try:
        run.read_until(b'\x1b[?2004h', timeout_s=30.)  # application mode: bracketed paste on
        run.send(b'6 * 7\n')  # ctrl+j submits
        run.read_until(b'42', timeout_s=10.)
        run.send(b'\x04')
        rc = run.finish()
    except BaseException:
        run.kill()
        raise

    assert rc == 0
    term = Vt100Terminal(rows=24, cols=80)
    term.feed(bytes(run.output))
    lines = [line.rstrip() for line in term.all_lines()]
    assert '>>> 6 * 7' in lines
    assert '42' in lines
