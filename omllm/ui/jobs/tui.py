import asyncio
import contextlib
import os.path
import sqlite3
import typing as ta

from omcore.logs import all as logs

from .store import JobStore
from .texts import display_job_text
from .worker import JOBS_POLL_S
from .worker import run_worker


##


log = logs.get_module_logger(globals())


async def _display_alerts(
        store: JobStore,
        display: ta.Callable[[str], None],
        ready: ta.Callable[[], bool],
) -> None:
    while True:
        if ready() and os.path.isfile(store.path):
            try:
                alerts = store.take_alerts()
            except sqlite3.OperationalError:
                log.exception('Could not read scheduled job alerts')
            else:
                for run in alerts:
                    text = display_job_text(run.text or '')
                    display(f'Job {display_job_text(run.name)} ({run.status})\n{text[:2_000]}')

        await asyncio.sleep(JOBS_POLL_S)


@contextlib.asynccontextmanager
async def tui_jobs(
        display: ta.Callable[[str], None],
        *,
        ready: ta.Callable[[], bool],
        in_process: bool,
) -> ta.AsyncIterator[None]:
    store = JobStore.from_home()

    async def run_in_process() -> None:
        try:
            if not await run_worker(store):
                display('A jobs worker is already running for this OM_HOME.')
        except Exception:  # noqa: BLE001
            log.exception('In-process jobs worker stopped')
            display('The jobs worker stopped with an error. See the TUI log.')

    async with asyncio.TaskGroup() as tg:
        alerts = tg.create_task(_display_alerts(store, display, ready))
        worker = tg.create_task(run_in_process()) if in_process else None
        try:
            yield
        finally:
            alerts.cancel()
            if worker is not None:
                worker.cancel()
