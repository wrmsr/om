import asyncio
import os
import threading

from omcore.term.vt100.terminal import Vt100Terminal

from ...events.keys import Key
from ...events.types import KeyEvent
from ...screens.cells import line_from_segments
from ...surfaces.inlines import InlineSurface
from ...text.segments import Segment
from ...text.styles import EMPTY_THEME
from ..asyncio import AsyncioDriver
from .test_sync import PipeTty
from .test_sync import RecordingApp


##


def test_async_driver_dispatch_and_render():
    tty = PipeTty(height=6, width=40)
    driver = AsyncioDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)  # type: ignore[arg-type]  # duck-compatible: invalidate/stop match

    async def main():
        tty.send(b'\x1b[3;1R')  # answer the startup origin CPR
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
    driver = AsyncioDriver(InlineSurface(tty, term='xterm-256color'))
    driver.parser.escape_timeout_s = .05  # shrink the real-time wait so the test stays fast
    app = RecordingApp(driver)  # type: ignore[arg-type]

    async def main():
        tty.send(b'\x1b')

        async def later():
            await asyncio.sleep(.15)  # > the shrunken escape window
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
    driver = AsyncioDriver(InlineSurface(tty, term='xterm-256color'))
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


def test_async_driver_commit_before_run_buffers():
    # Commits made before run() prepares the surface buffer (like pre-run timers) and flush once running.
    tty = PipeTty(height=6, width=40)
    driver = AsyncioDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)  # type: ignore[arg-type]

    driver.commit([line_from_segments([Segment('early bird')], EMPTY_THEME)])  # must not raise

    async def main():
        tty.send(b'\x1b[3;1R')

        async def later():
            await asyncio.sleep(.05)
            driver.stop()

        task = asyncio.get_running_loop().create_task(later())
        await driver.run(app)
        await task

    asyncio.run(main())
    os.close(tty.read_fd)

    term = Vt100Terminal(rows=6, cols=40)
    term.feed(b''.join(tty.writes))
    assert 'early bird' in term.all_lines()


def test_async_driver_stop_before_origin_flushes_commits():
    # Stopping before the CPR answer (or its fallback) must still land buffered commits, not drop them.
    tty = PipeTty(height=6, width=40)
    driver = AsyncioDriver(InlineSurface(tty, term='xterm-256color'))
    app = RecordingApp(driver)  # type: ignore[arg-type]

    async def main():
        # No CPR answer sent: the origin stays unresolved for the whole (short) run.
        async def later():
            await asyncio.sleep(.02)  # < the 250ms origin fallback
            driver.commit([line_from_segments([Segment('parting words')], EMPTY_THEME)])
            driver.stop()

        task = asyncio.get_running_loop().create_task(later())
        await driver.run(app)
        await task

    asyncio.run(main())
    os.close(tty.read_fd)

    term = Vt100Terminal(rows=6, cols=40)
    term.feed(b''.join(tty.writes))
    assert 'parting words' in term.all_lines()


def test_async_driver_suspend_resume_cycle():
    tty = PipeTty(height=6, width=40)
    stops: list[int] = []

    def stop_process() -> None:
        stops.append(1)
        driver.job_control.resume()  # stand in for SIGSTOP + SIGCONT

    driver = AsyncioDriver(InlineSurface(tty, term='xterm-256color'), stop_process=stop_process)
    app = RecordingApp(driver)  # type: ignore[arg-type]

    async def main():
        tty.send(b'\x1b[3;1R')

        async def later():
            await asyncio.sleep(.02)
            driver.suspend()
            await asyncio.sleep(.02)
            tty.send(b'\x1b[2;1R')  # the post-`fg` origin
            await asyncio.sleep(.02)
            driver.stop()

        task = asyncio.get_running_loop().create_task(later())
        await driver.run(app)
        await task

    asyncio.run(main())
    os.close(tty.read_fd)
    os.close(tty.write_fd)

    assert stops == [1]
    assert not driver.job_control.suspended
    names = [type(e).__name__ for e in app.events]
    assert names.index('SuspendEvent') < names.index('ResumeEvent')

    data = b''.join(tty.writes)
    assert data.count(b'\x1b[?2004h') == 2  # startup + resume
    term = Vt100Terminal(rows=6, cols=40)
    term.feed(data)
    assert 'events: 2' in term.all_lines()
