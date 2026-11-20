import asyncio
import contextlib
import json
import os.path
import sqlite3
import sys

import pytest

from ..store import Job
from ..store import JobStore
from ..tui import tui_jobs
from ..worker import run_worker


##


def test_job_schedule_and_alerts(tmpdir):
    store = JobStore(str(tmpdir))
    store.initialize()
    store.add(Job(
        name='check',
        cwd=str(tmpdir),
        prompt='Check',
        model='scripted',
        input_argv_json='[]',
        interval_s=60,
        next_at=100,
    ))

    assert store.claim(99) is None
    assert store.request_run('check')
    manual = store.claim(99)
    assert manual is not None
    _, manual_id = manual
    store.finish(manual_id, 'quiet', 'NO_ALERT', 'first')
    assert store.take_alerts() == []
    assert store.list_jobs()[0].next_at == 100

    overdue = store.claim(241)
    assert overdue is not None
    _, overdue_id = overdue
    assert store.list_jobs()[0].next_at == 280
    assert store.claim(241) is None
    store.recover_interrupted()

    assert [(r.id, r.status) for r in store.take_alerts()] == [(overdue_id, 'interrupted')]
    assert store.take_alerts() == []
    assert store.remove('check')
    assert [r.id for r in store.list_runs()] == [overdue_id, manual_id]


@pytest.mark.asyncs('asyncio')
async def test_tui_runs_and_displays_job(tmpdir, monkeypatch):
    monkeypatch.setenv('OM_HOME', str(tmpdir))
    store = JobStore.from_home()
    store.initialize()
    store.add(Job(
        name='check',
        cwd=str(tmpdir),
        prompt='Check this output',
        model='scripted',
        input_argv_json=json.dumps([sys.executable, '-c', 'print("check fixture")']),
        interval_s=60,
        next_at=4_000_000_000,
    ))
    assert store.request_run('check')

    displayed: asyncio.Future[str] = asyncio.Future()

    async with tui_jobs(displayed.set_result, ready=lambda: True, in_process=True):
        assert (await asyncio.wait_for(displayed, 10.)).startswith('Job check (alert)\n')
        assert not await run_worker(store)

    assert store.take_alerts() == []
    run, = store.list_runs()
    assert run.session_id

    session_db = os.path.join(store.directory, 'sessions.db')
    with contextlib.closing(sqlite3.connect(session_db)) as db:
        assert db.execute('SELECT id, num_entries FROM sessions').fetchall() == [(run.session_id, 2)]
