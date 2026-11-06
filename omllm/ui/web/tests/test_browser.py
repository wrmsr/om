"""
The whole of it, in a real browser: the demo's model working through its project, its asks answered by clicking, and
the page reloaded to replay it all. Slow - a browser starts - and skipped without firefox.
"""
import asyncio
import os.path
import tempfile

import pytest

from ..main import running_web
from .demo import DEMO_FILE_NAME
from .demo import bind_demo_backend
from .demo import build_demo_config
from .demo import write_demo_project
from .marionette import ENTER_KEY
from .marionette import ESCAPE_KEY
from .marionette import find_firefox
from .marionette import headless_firefox


##


def _read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


_SUMMARY_JS = """
return {
    state: document.getElementById('status').dataset.state,
    kinds: [...document.querySelectorAll('#transcript .item')].map(e => e.classList[1]),
    tools: [...document.querySelectorAll('.tool')].map(e => [
        e.querySelector('.tool-name').textContent,
        e.classList[2],
    ]),
    asks: [...document.querySelectorAll('.ask')].map(e => e.classList[2]),
    table: document.querySelectorAll('.ai table').length,
}
"""


@pytest.mark.slow
@pytest.mark.asyncs('asyncio')
async def test_browser():
    if find_firefox() is None:
        pytest.skip('firefox not found')

    with tempfile.TemporaryDirectory() as cwd:
        cwd = os.path.realpath(cwd)
        write_demo_project(cwd)

        async with running_web(
                build_demo_config(cwd, port=0),
                overrides=[bind_demo_backend(cwd, pace_s=0.)],
        ) as rw:
            def drive() -> tuple[dict, dict]:
                with headless_firefox() as m:
                    m.navigate(rw.address.url)
                    m.wait_js("return document.querySelectorAll('#transcript .item').length > 0")

                    m.send_keys('.composer-input', 'Please tidy up the greeting.' + ENTER_KEY)

                    # The edit asks, then the bash.
                    for n in [1, 2]:
                        m.wait_js(f"return document.querySelectorAll('.ask').length === {n}", timeout_s=20.)
                        m.wait_js("return document.querySelector('.ask.is-pending') !== null")
                        m.click('.ask.is-pending .ask-allow')

                    m.wait_js("return document.getElementById('status').dataset.state === 'idle'", timeout_s=20.)
                    live = m.js(_SUMMARY_JS)

                    # A reload replays the feed into the same transcript.
                    m.navigate(rw.address.url)
                    m.wait_js('return document.querySelectorAll(".ai table").length === 1')
                    replayed = m.js(_SUMMARY_JS)

                    return live, replayed

            live, replayed = await asyncio.to_thread(drive)

            assert live['state'] == 'idle'
            assert live['tools'] == [
                ['ls', 'tool-ok'],
                ['read', 'tool-ok'],
                ['edit', 'tool-ok'],
                ['bash', 'tool-ok'],
            ]
            assert live['asks'] == ['is-allow', 'is-allow']
            assert live['table'] == 1
            assert replayed == live

            assert 'f"hello, {name}!"' in _read_file(os.path.join(cwd, DEMO_FILE_NAME))


@pytest.mark.slow
@pytest.mark.asyncs('asyncio')
async def test_browser_interruptions():
    if find_firefox() is None:
        pytest.skip('firefox not found')

    with tempfile.TemporaryDirectory() as cwd:
        cwd = os.path.realpath(cwd)
        write_demo_project(cwd)

        async with running_web(
                build_demo_config(cwd, port=0),
                overrides=[bind_demo_backend(cwd, pace_s=.005)],
        ) as rw:
            def drive() -> dict:
                out: dict = {}

                with headless_firefox() as m:
                    m.navigate(rw.address.url)
                    m.wait_js("return document.querySelectorAll('#transcript .item').length > 0")

                    # A second prompt while the first runs is turned away, and the composer keeps it.
                    m.send_keys('.composer-input', 'First.' + ENTER_KEY)
                    m.wait_js("return document.querySelector('.run.running') !== null")
                    m.send_keys('.composer-input', 'Second.' + ENTER_KEY)
                    m.wait_js("return !document.getElementById('toast').hidden")
                    out['toast'] = m.js("return document.getElementById('toast').textContent")
                    out['kept'] = m.js("return document.querySelector('.composer-input').value")

                    # Escape cancels, withdrawing the ask it was parked on.
                    m.wait_js("return document.querySelector('.ask.is-pending') !== null", timeout_s=20.)
                    m.send_keys('.composer-input', ESCAPE_KEY)
                    m.wait_js("return document.getElementById('status').dataset.state === 'idle'", timeout_s=20.)
                    out['cancelled'] = m.js("return [...document.querySelectorAll('.run-end')].map(e => e.textContent)")
                    out['withdrawn'] = m.js("return [...document.querySelectorAll('.ask')].map(e => e.classList[2])")

                    # A page loaded mid-run picks the run up where it is, asks and all.
                    m.js("document.querySelector('.composer-input').value = ''")
                    m.send_keys('.composer-input', 'Third.' + ENTER_KEY)
                    m.wait_js("return document.querySelectorAll('.run').length === 2")
                    m.navigate(rw.address.url)
                    m.wait_js("return document.querySelector('.ask.is-pending') !== null", timeout_s=20.)
                    out['reloaded'] = m.js("return document.getElementById('status').dataset.state")
                    m.click('.ask.is-pending .ask-deny')
                    m.wait_js("return document.querySelectorAll('.ask.is-pending').length === 1", timeout_s=20.)
                    m.click('.ask.is-pending .ask-deny')
                    m.wait_js("return document.getElementById('status').dataset.state === 'idle'", timeout_s=20.)
                    out['denied'] = m.js(
                        "return [...document.querySelectorAll('.tool-error .tool-name')].map(e => e.textContent)",
                    )

                return out

            out = await asyncio.to_thread(drive)

            assert out['toast'].startswith('Busy')
            assert out['kept'] == 'Second.'
            assert out['cancelled'] == ['(cancelled)']
            assert out['withdrawn'] == ['is-aborted']
            assert out['reloaded'] == 'waiting-for-you'
            assert out['denied'] == ['edit', 'bash']
