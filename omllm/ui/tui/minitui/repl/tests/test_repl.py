import asyncio
import shutil
import typing as ta

import pytest

from omcore import inject as inj
from omcore import lang
from omdev import minitui as mt
from omdev import repl

from ...... import harness as har
from ......core import processes
from ....config import Config
from ....tests.headless import bind_headless_tui
from ....tests.headless import headless_tui
from ...app import AppKey
from ...app import InputMode
from ...app import MinituiChatApp
from ...tests.utils import Driver
from ...tests.utils import app_key
from ...tests.utils import commit_texts
from ...tests.utils import frame_lines
from ...tests.utils import make_app
from ..inject import REPL_PROCESS_SCOPE_NAME
from ..inject import bind_repl
from ..inject import repl_namespace_seeds
from ..repl import MinituiRepl


##


def make_repl(app, driver, **namespace):
    session = repl.Session({
        'py': repl.PythonInterpreter(
            {'app': app, **namespace},
            config=repl.PythonInterpreter.Config(allow_await=False),
        ),
    })
    return MinituiRepl(
        app=app,
        driver=ta.cast(mt.AsyncioDriver, driver),
        session=session,
        runner=repl.ImmediateRunner(),
    )


def test_switching_takes_the_input_and_runs_code():
    app, driver = make_app()
    switcher = make_repl(app, driver)
    assert app.input_mode is app.chat_mode
    assert app.input_area.prompt == ''

    lang.sync_await(switcher.switch('py'))
    assert app.input_mode is not app.chat_mode
    assert app.input_area.prompt == '>>> '
    highlighter = app.input_area.highlighter
    assert highlighter is not None
    assert 'python' in frame_lines(app)[-1]

    app.input_mode.submit('app.width')
    texts = commit_texts(driver)
    assert texts[-3:] == ['>>> app.width', '80', '']

    lang.sync_await(switcher.switch(None))
    assert app.input_mode is app.chat_mode
    assert app.input_area.prompt == ''
    highlighter = app.input_area.highlighter
    assert highlighter is None
    assert 'python' not in frame_lines(app)[-1]


def test_unknown_repl():
    app, driver = make_app()
    switcher = make_repl(app, driver)
    assert switcher.names == ('py',)
    with pytest.raises(har.ReplSwitchError, match='nope'):
        lang.sync_await(switcher.switch('nope'))
    assert app.input_mode is app.chat_mode


def test_slash_commands_pass_through_and_exit_leaves():
    app, driver = make_app()
    switcher = make_repl(app, driver)
    submitted: list = []
    app.on_submit = submitted.append

    lang.sync_await(switcher.switch('py'))
    app.input_mode.submit('/chat')
    assert submitted == ['/chat']
    assert app.input_mode is not app.chat_mode  # the pump would run it; here nobody did

    app.input_mode.submit('exit()')
    assert app.input_mode is app.chat_mode


def test_command_popup_still_suggests_in_a_repl():
    app, driver = make_app()
    app.set_commands([('/chat', 'back'), ('/py', 'python')])
    switcher = make_repl(app, driver)
    lang.sync_await(switcher.switch('py'))
    assert [s.label for s in app.input_mode.suggestions('/c')] == ['/chat']
    assert app.input_mode.suggestions('x = 1') == ()


def test_the_cancel_key_is_the_modes_before_it_is_the_turns():
    class Mode(InputMode):
        has_running = True
        num_cancels = 0

        @property
        def label(self) -> str:
            return 'mode'

        def submit(self, text: str) -> None:
            pass

        def cancel(self) -> bool:
            self.num_cancels += 1
            return self.has_running

    app, _ = make_app()
    turn_cancels: list = []

    def cancel_turn() -> bool:
        turn_cancels.append(True)
        return True

    app.on_cancel = cancel_turn
    mode = Mode()
    app.set_input_mode(mode)

    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    assert (mode.num_cancels, turn_cancels) == (1, [])

    mode.has_running = False
    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    assert (mode.num_cancels, turn_cancels) == (2, [True])

    app.set_input_mode(app.chat_mode)
    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    assert (mode.num_cancels, turn_cancels) == (2, [True, True])


def test_cancelling_in_a_repl_with_nothing_running():
    app, driver = make_app()
    switcher = make_repl(app, driver)
    lang.sync_await(switcher.switch('py'))
    assert not app.input_mode.cancel()


@pytest.mark.asyncs('asyncio')
async def test_wiring():
    config = Config(
        model='scripted',
        in_memory=True,
    )
    driver = Driver()
    async with headless_tui(inj.override(
        inj.as_elements(
            bind_headless_tui(config),
            bind_repl(config),
            inj.bind(mt.AsyncioDriver, to_const=ta.cast(mt.AsyncioDriver, driver)),
            inj.bind(MinituiChatApp, singleton=True),
            repl_namespace_seeds().bind_item(to_const={'extra': 'seeded'}),
        ),
        inj.bind(repl.ImmediateRunner()),
        inj.bind(repl.Runner, to_key=repl.ImmediateRunner),
    )) as tui:
        app = await tui.injector[MinituiChatApp]
        names = set(tui.commands.get_commands())
        assert {'py', 'chat'} <= names

        await tui.commands.parse('py').run()
        assert app.input_mode is not app.chat_mode
        app.input_mode.submit('extra')
        assert commit_texts(driver)[-2] == "'seeded'"
        app.input_mode.submit('type(injector).__name__')
        assert 'Injector' in commit_texts(driver)[-2]

        await tui.commands.parse('chat').run()
        assert app.input_mode is app.chat_mode


class CommitSignallingDriver(Driver):
    """Says when something has been committed: what a test waits on when the committing is a real process's doing."""

    def __init__(self) -> None:
        super().__init__()

        self.committed = asyncio.Event()

    def commit(self, lines) -> None:
        super().commit(lines)
        self.committed.set()

    async def wait_for_row(self, row: str) -> None:
        async with asyncio.timeout(30.):
            while not any(row in text.split('\n') for text in commit_texts(self)):
                self.committed.clear()
                await self.committed.wait()


@pytest.mark.skipif(shutil.which('bash') is None, reason='requires bash')
@pytest.mark.asyncs('asyncio')
async def test_bash_wiring(tmp_path):
    # No `exec`: the user's shell does not depend on what tools the agent was given.
    config = Config(
        model='scripted',
        in_memory=True,
        cwd=str(tmp_path),
    )
    driver = CommitSignallingDriver()
    async with headless_tui(
        bind_headless_tui(config),
        bind_repl(config),
        inj.bind(mt.AsyncioDriver, to_const=ta.cast(mt.AsyncioDriver, driver)),
        inj.bind(MinituiChatApp, singleton=True),
    ) as tui:
        app = await tui.injector[MinituiChatApp]
        manager = await tui.injector[processes.ProcessManager]
        assert 'bash' in tui.commands.get_commands()

        await tui.commands.parse('bash').run()
        assert app.input_mode is not app.chat_mode
        assert app.input_area.prompt == '$ '
        assert 'bash' in frame_lines(app)[-1]
        assert not manager.processes  # nothing is started until something is run

        app.input_mode.submit('cd "$PWD" && echo "in ${PWD##*/}"')
        await driver.wait_for_row(f'in {tmp_path.name}')

        # The shell is the user's: in a scope of its own, where the agent's process tools - which see the root's - do
        # not find it.
        scope = manager.root.children[REPL_PROCESS_SCOPE_NAME]
        assert len(scope.processes) == 1
        assert not manager.root.processes

        # The cancel key reaches the running command, and the shell is there for the next one.
        app.input_mode.submit('sh -c "echo started; exec sleep 60"')
        await driver.wait_for_row('started')
        app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
        await driver.wait_for_row('interrupted')

        app.input_mode.submit('echo "still in ${PWD##*/}"')
        await driver.wait_for_row(f'still in {tmp_path.name}')
        assert len(scope.processes) == 1

        app.input_mode.submit('exit')
        await driver.wait_for_row('[the shell exited]')
        assert app.input_mode is app.chat_mode
        assert not scope.processes
