import asyncio
import importlib.metadata
import importlib.util
import os
import signal
import subprocess
import sys
import time

from omcore.os.pidfiles.pidfile import Pidfile

from .agent import JobResult
from .agent import run_job
from .store import JobStore


##


JOBS_POLL_S = 2.


def _worker_lock(store: JobStore) -> Pidfile:
    return Pidfile(os.path.join(store.directory, 'jobs.lock'), inheritable=False)


def _stop_path(store: JobStore) -> str:
    return os.path.join(store.directory, 'jobs.stop')


def _file_stamp(path: str) -> tuple[int, int, int, int] | None:
    try:
        st = os.stat(path)
    except FileNotFoundError:
        return None
    return st.st_dev, st.st_ino, st.st_mtime_ns, st.st_ctime_ns


def _installation_stamps() -> dict[str, tuple[int, int, int, int]]:
    package = __package__.split('.')[0]
    spec = importlib.util.find_spec(package)
    paths = [sys.executable, os.path.join(sys.prefix, 'pyvenv.cfg')]
    if spec is not None and spec.origin is not None:
        paths.append(spec.origin)

    try:
        files = importlib.metadata.files(package)
    except importlib.metadata.PackageNotFoundError:
        files = None
    paths.extend(str(f.locate()) for f in files or () if f.name == 'METADATA' and f.parent.name.endswith('.dist-info'))

    return {
        path: stamp
        for path in paths
        if (stamp := _file_stamp(path)) is not None
    }


async def _run_jobs(store: JobStore) -> None:
    store.recover_interrupted()
    while True:
        if (claim := store.claim(int(time.time()))) is None:
            await asyncio.sleep(JOBS_POLL_S)
            continue

        job, run_id = claim
        try:
            async with asyncio.timeout(180.):
                result = await run_job(job)
        except asyncio.CancelledError:
            store.finish(run_id, 'interrupted', 'The worker stopped during this run.', None)
            raise
        except TimeoutError:
            result = JobResult(status='failed', text='The job exceeded its three-minute timeout.')
        except Exception as exc:  # noqa: BLE001
            result = JobResult(status='failed', text=f'{type(exc).__name__}: {exc}')

        store.finish(run_id, result.status, result.text, result.session_id)
        await asyncio.sleep(0)


async def run_worker(store: JobStore, *, installed: bool = False) -> bool:
    stop_path = _stop_path(store)
    stop_stamp = _file_stamp(stop_path)
    store.initialize()

    with _worker_lock(store) as lock:
        if not lock.try_acquire_lock():
            return False

        stamps = _installation_stamps() if installed else {}
        async with asyncio.TaskGroup() as tg:
            task = tg.create_task(_run_jobs(store))
            try:
                while (  # noqa: ASYNC110
                        _file_stamp(stop_path) == stop_stamp and
                        all(_file_stamp(p) == s for p, s in stamps.items())
                ):
                    await asyncio.sleep(JOBS_POLL_S)
            finally:
                task.cancel()

    return True


async def serve_worker(store: JobStore) -> bool:
    loop = asyncio.get_running_loop()
    task = loop.create_task(run_worker(store, installed=True))
    loop.add_signal_handler(signal.SIGTERM, task.cancel)
    try:
        return await task
    except asyncio.CancelledError:
        return True
    finally:
        loop.remove_signal_handler(signal.SIGTERM)


def _is_running(store: JobStore) -> bool:
    if not os.path.isdir(store.directory):
        return False
    with _worker_lock(store) as lock:
        return not lock.try_acquire_lock()


def start_worker(store: JobStore, log_path: str) -> bool:
    if _is_running(store):
        return False

    os.makedirs(os.path.dirname(log_path), mode=0o700, exist_ok=True)
    with open(log_path, 'ab') as log_file:
        proc = subprocess.Popen(
            [sys.executable, '-m', 'omllm.ui', 'jobs', 'serve'],
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )

    started = False
    try:
        deadline = time.monotonic() + 10.
        while time.monotonic() < deadline:
            if _is_running(store):
                started = True
                return True
            if proc.poll() is not None:
                break
            time.sleep(0.05)

        raise RuntimeError(f'Worker did not start. See {log_path}')
    finally:
        if not started and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5.)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5.)


def stop_worker(store: JobStore) -> bool:
    if not _is_running(store):
        return False

    # A running owner observes the changed stamp. No PID is signaled, even if the owner exits concurrently.
    with open(_stop_path(store), 'ab') as stop_file:
        os.utime(stop_file.fileno())

    deadline = time.monotonic() + 15.
    while time.monotonic() < deadline:
        if not _is_running(store):
            return True
        time.sleep(0.05)

    raise RuntimeError('Worker is still stopping')
