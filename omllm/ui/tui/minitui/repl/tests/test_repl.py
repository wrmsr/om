import typing as ta

import pytest

from omcore import inject as inj
from omcore import lang
from omdev import minitui as mt
from omdev import repl

from ...... import harness as har
from ....config import Config
from ....tests.headless import bind_headless_tui
from ....tests.headless import headless_tui
from ...app import MinituiChatApp
from ...tests.utils import Driver
from ...tests.utils import commit_texts
from ...tests.utils import frame_lines
from ...tests.utils import make_app
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
