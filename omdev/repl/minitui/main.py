"""
Entry point: `python -m omdev.repl.minitui [--lang=py|js] [--no-js]`. The asyncio-specific part of the frontend: the
driver, the runner, the engine's thread executor, and the kernel's SIGINT routed to the app as an interrupt.
"""
import asyncio
import signal
import sys

from omcore import lang

from ... import minitui as mt
from ..asyncio import AsyncioRunner
from ..asyncio import AsyncioThreadExecutor
from ..defaults import DEFAULT_PYTHON_NAME
from ..defaults import make_default_session
from ..python.interpreter import PythonInterpreter
from .app import ReplApp


##


async def _a_main(argv: lang.SequenceNotStr[str]) -> None:
    language: str | None = None
    javascript = True
    for arg in argv:
        if arg.startswith('--lang='):
            language = arg.partition('=')[2]
        elif arg == '--no-js':
            javascript = False
        else:
            raise ValueError(f'Unknown option: {arg}')

    driver = mt.AsyncioDriver(mt.InlineSurface(kitty_keys=True))
    runner = AsyncioRunner()
    session = make_default_session(
        javascript=javascript,
        blocking_executor=AsyncioThreadExecutor(),
    )
    if language is not None:
        session.switch(language)

    app = ReplApp(driver, session, runner=runner)

    # The python namespace sees the app it is running in - the smallest manhole.
    python = session.get(DEFAULT_PYTHON_NAME)
    if isinstance(python, PythonInterpreter):
        python.namespace.update(
            app=app,
            driver=driver,
            session=session,
        )

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, app.interrupt)
    try:
        await driver.run(app)
    finally:
        loop.remove_signal_handler(signal.SIGINT)
        await runner.aclose()
        await session.aclose()


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    asyncio.run(_a_main(sys.argv[1:] if argv is None else argv))


if __name__ == '__main__':
    _main()
