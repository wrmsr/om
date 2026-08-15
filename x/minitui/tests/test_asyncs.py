import asyncio
import os
import threading

from omcore.term.vt100.terminal import Vt100Terminal

from ..events.keys import Key
from ..events.types import KeyEvent
from ..runtime.asyncs import AsyncDriver
from ..surfaces.inlines import InlineSurface
from .test_drivers import PipeTty
from .test_drivers import RecordingApp


##


def test_async_driver_dispatch_and_render():
    tty = PipeTty(height=6, width=40)
    driver = AsyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)  # type: ignore[arg-type]  # duck-compatible: invalidate/stop match

    async def main():
        tty.send(b'ab\x1b[A')

        async def later():
            await asyncio.sleep(.02)
            tty.send(b'\x04')

        task = asyncio.get_running_loop().create_task(later())
        await driver.run(app)
        await task

    asyncio.run(main())
    os.close(tty.read_fd)

    keys = [e.key for e in app.events if isinstance(e, KeyEvent)]
    assert keys == [Key('a'), Key('b'), Key('up'), Key('d', ctrl=True)]

    term = Vt100Terminal(rows=6, cols=40)
    term.feed(b''.join(tty.writes))
    assert 'events: 3' in term.all_lines()


def test_async_driver_escape_timeout():
    tty = PipeTty(height=6, width=40)
    driver = AsyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)  # type: ignore[arg-type]

    async def main():
        tty.send(b'\x1b')

        async def later():
            await asyncio.sleep(.15)  # > the 50ms escape timeout
            driver.stop()

        task = asyncio.get_running_loop().create_task(later())
        await driver.run(app)
        await task

    asyncio.run(main())
    os.close(tty.read_fd)
    os.close(tty.write_fd)

    keys = [e.key for e in app.events if isinstance(e, KeyEvent)]
    assert keys == [Key('escape')]


def test_async_driver_timers_and_cross_thread_post():
    tty = PipeTty(height=6, width=40)
    driver = AsyncDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)  # type: ignore[arg-type]

    ticks: list[int] = []
    posted = threading.Event()

    async def main():
        every = driver.timers.call_every(.01, lambda: ticks.append(1))

        def on_loop():
            posted.set()
            driver.stop()

        def from_thread():
            # The one legal cross-thread entry: post a callable onto the loop.
            driver.post(on_loop)

        async def later():
            await asyncio.sleep(.05)
            await asyncio.get_running_loop().run_in_executor(None, from_thread)

        task = asyncio.get_running_loop().create_task(later())
        await driver.run(app)
        await task
        every.cancel()

    asyncio.run(main())
    os.close(tty.read_fd)
    os.close(tty.write_fd)

    assert posted.is_set()
    assert len(ticks) >= 2
