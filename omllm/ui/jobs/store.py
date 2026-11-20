import contextlib
import os.path
import sqlite3
import typing as ta

from omcore import dataclasses as dc
from omdev.home.paths import get_home_paths


##


@dc.dataclass(frozen=True, kw_only=True)
class Job:
    name: str
    cwd: str
    prompt: str
    model: str | None
    input_argv_json: str
    interval_s: int
    next_at: int
    run_now: int = 0


@dc.dataclass(frozen=True, kw_only=True)
class JobRun:
    id: int
    name: str
    started_at: int
    status: str
    text: str | None
    session_id: str | None


##


class JobStore:
    def __init__(self, directory: str) -> None:
        super().__init__()

        self.directory = directory
        self.path = os.path.join(directory, 'jobs.db')

    @classmethod
    def from_home(cls) -> JobStore:
        return cls(os.path.realpath(os.path.join(get_home_paths().state_dir, 'llm')))

    @contextlib.contextmanager
    def _connect(self) -> ta.Iterator[sqlite3.Connection]:
        with contextlib.closing(sqlite3.connect(self.path, timeout=0.5)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    def initialize(self) -> None:
        os.makedirs(self.directory, mode=0o700, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                BEGIN;
                CREATE TABLE IF NOT EXISTS jobs (
                    name TEXT PRIMARY KEY,
                    cwd TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    model TEXT,
                    input_argv_json TEXT NOT NULL,
                    interval_s INTEGER NOT NULL CHECK (interval_s > 0),
                    next_at INTEGER NOT NULL,
                    run_now INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    started_at INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    text TEXT,
                    session_id TEXT,
                    announced INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS pending_alerts ON runs (id)
                WHERE announced = 0 AND status IN ('alert', 'failed', 'interrupted');
                COMMIT;
            """)

    def add(self, job: Job) -> None:
        with self._connect() as db:
            db.execute("""
                INSERT INTO jobs (name, cwd, prompt, model, input_argv_json, interval_s, next_at, run_now)
                VALUES (:name, :cwd, :prompt, :model, :input_argv_json, :interval_s, :next_at, :run_now)
            """, dc.asdict(job))

    def remove(self, name: str) -> bool:
        with self._connect() as db:
            return bool(db.execute('DELETE FROM jobs WHERE name = ?', (name,)).rowcount)

    def request_run(self, name: str) -> bool:
        with self._connect() as db:
            return bool(db.execute('UPDATE jobs SET run_now = 1 WHERE name = ?', (name,)).rowcount)

    def list_jobs(self) -> list[Job]:
        with self._connect() as db:
            return [Job(**dict(row)) for row in db.execute('SELECT * FROM jobs ORDER BY name')]

    def list_runs(self, limit: int = 20) -> list[JobRun]:
        with self._connect() as db:
            rows = db.execute(
                'SELECT id, name, started_at, status, text, session_id FROM runs ORDER BY id DESC LIMIT ?',
                (limit,),
            )
            return [JobRun(**dict(row)) for row in rows]

    def take_alerts(self, limit: int = 10) -> list[JobRun]:
        with self._connect() as db:
            rows = db.execute("""
                UPDATE runs SET announced = 1 WHERE id IN (
                    SELECT id FROM runs
                    WHERE announced = 0 AND status IN ('alert', 'failed', 'interrupted') ORDER BY id LIMIT ?
                ) RETURNING id, name, started_at, status, text, session_id
            """, (limit,))
            return sorted((JobRun(**dict(row)) for row in rows), key=lambda run: run.id)

    def claim(self, now: int) -> tuple[Job, int] | None:
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("""
                SELECT * FROM jobs WHERE run_now = 1 OR next_at <= ?
                ORDER BY CASE WHEN run_now = 1 THEN 0 ELSE 1 END, next_at, name LIMIT 1
            """, (now,)).fetchone()
            if row is None:
                return None

            job = Job(**dict(row))
            next_at = job.next_at
            if next_at <= now:
                next_at += ((now - next_at) // job.interval_s + 1) * job.interval_s

            db.execute('UPDATE jobs SET next_at = ?, run_now = 0 WHERE name = ?', (next_at, job.name))
            run_row = db.execute(
                'INSERT INTO runs (name, started_at) VALUES (?, ?) RETURNING id',
                (job.name, now),
            ).fetchone()
            return job, run_row['id']

    def finish(self, run_id: int, status: str, text: str, session_id: str | None) -> None:
        with self._connect() as db:
            db.execute(
                'UPDATE runs SET status = ?, text = ?, session_id = ? WHERE id = ?',
                (status, text, session_id, run_id),
            )

    def recover_interrupted(self) -> None:
        # Only the owner of the worker lock can have running rows. An old owner has gone away.
        with self._connect() as db:
            db.execute("""
                UPDATE runs SET status = 'interrupted', text = 'The previous worker exited during this run.'
                WHERE status = 'running'
            """)
