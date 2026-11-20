import argparse
import asyncio
import datetime
import json
import os.path
import re
import sqlite3
import time

from omcore import lang
from omdev.home.paths import get_home_paths

from ...agent.environment.local import environment_resolve_cwd
from .store import Job
from .store import JobStore
from .texts import display_job_text
from .worker import serve_worker
from .worker import start_worker
from .worker import stop_worker


##


def _interval(value: str) -> int:
    if (m := re.fullmatch(r'([1-9][0-9]{0,3})([mhd])', value)) is None:
        raise argparse.ArgumentTypeError('expected an interval such as 15m, 2h, or 1d')
    return int(m[1]) * {'m': 60, 'h': 3_600, 'd': 86_400}[m[2]]


def _daily(value: str) -> datetime.time:
    try:
        return datetime.time.strptime(value, '%H:%M')
    except ValueError as e:
        raise argparse.ArgumentTypeError('expected a UTC time in HH:MM format') from e


def _next_daily(at: datetime.time, now: int) -> int:
    current = datetime.datetime.fromtimestamp(now, datetime.UTC)
    target = datetime.datetime.combine(current.date(), at, tzinfo=datetime.UTC)
    return int(target.timestamp()) + (86_400 if target <= current else 0)


def _utc(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp, datetime.UTC).isoformat(timespec='seconds')


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='om llm jobs', description='Manage local scheduled prompts.')
    sub = parser.add_subparsers(dest='command', required=True)

    add = sub.add_parser('add', help='save a recurring prompt')
    add.add_argument('name')
    add.add_argument('prompt')
    schedule = add.add_mutually_exclusive_group(required=True)
    schedule.add_argument('--every', type=_interval, metavar='INTERVAL')
    schedule.add_argument('--daily', type=_daily, metavar='HH:MM', help='time in UTC')
    add.add_argument('-C', '--cwd')
    add.add_argument('-m', '--model')
    add.add_argument('--input', nargs=argparse.REMAINDER, metavar='ARGV', help='fixed input command, supplied last')

    sub.add_parser('list', help='list saved jobs')
    runs = sub.add_parser('runs', help='show recent runs and findings')
    runs.add_argument('--limit', type=int, default=20)
    sub.add_parser('remove', help='remove a schedule').add_argument('name')
    sub.add_parser('run', help='request an immediate run').add_argument('name')
    sub.add_parser('start', help='start a detached worker for this OM_HOME')
    sub.add_parser('stop', help='stop the worker for this OM_HOME')
    sub.add_parser('serve', help='run a worker in the foreground')
    return parser


def run_jobs_cli(argv: lang.SequenceNotStr[str]) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    store = JobStore.from_home()
    try:
        if args.command == 'start':
            log_path = os.path.join(get_home_paths().log_dir, 'llm', 'jobs.log')
            if start_worker(store, log_path):
                print(f'Worker started. Log at {log_path}')
            else:
                print('Worker is already running.')
            return

        if args.command == 'stop':
            print('Worker stopped.' if stop_worker(store) else 'No worker is running.')
            return

        if args.command == 'serve':
            if not asyncio.run(serve_worker(store)):
                print('Worker is already running.')
            return

        store.initialize()
        if args.command == 'add':
            if not args.name.strip() or not args.name.isprintable() or not args.prompt.strip() or args.input == []:
                parser.error('expected a printable name, a non-blank prompt, and a command after any --input')

            now = int(time.time())
            next_at = _next_daily(args.daily, now) if args.daily is not None else now + args.every
            store.add(Job(
                name=args.name,
                cwd=environment_resolve_cwd(args.cwd),
                prompt=args.prompt,
                model=args.model,
                input_argv_json=json.dumps(args.input or []),
                interval_s=args.every if args.daily is None else 86_400,
                next_at=next_at,
            ))
            print(f'{args.name} scheduled for {_utc(next_at)}')

        elif args.command == 'list':
            for job in store.list_jobs():
                due = 'queued' if job.run_now else _utc(job.next_at)
                print(display_job_text(f'{job.name}  {due}  {job.cwd}'))

        elif args.command == 'runs':
            if args.limit < 1:
                parser.error('--limit must be positive')
            for run in store.list_runs(args.limit):
                print(display_job_text(f'{_utc(run.started_at)}  {run.name}  {run.status}'))
                if run.session_id is not None:
                    print(f'  Session {run.session_id}')
                if run.text is not None:
                    print(display_job_text(run.text))

        elif args.command == 'remove':
            if not store.remove(args.name):
                parser.error(f'unknown job {args.name!r}')

        elif args.command == 'run':
            if not store.request_run(args.name):
                parser.error(f'unknown job {args.name!r}')

    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, sqlite3.Error) as e:
        parser.error(str(e))
