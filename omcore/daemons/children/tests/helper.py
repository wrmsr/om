import argparse
import http.server
import json
import os
import signal
import subprocess
import sys
import threading
import time
import typing as ta


##


def _write_event(path: str, event: str, **kwargs: ta.Any) -> None:
    payload = {
        'event': event,
        'pid': os.getpid(),
        **kwargs,
    }
    with open(path, 'a') as file:
        file.write(json.dumps(payload, separators=(',', ':')) + '\n')


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == '/healthz':
            status, body = 200, b'healthy'
        elif self.path == '/pid':
            status, body = 200, str(os.getpid()).encode()
        else:
            status, body = 404, b'not-found'

        self.send_response(status)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args) -> None:  # noqa
        pass


def _run(args: argparse.Namespace) -> int:
    stopped = threading.Event()

    def handle_signal(signum: int, frame) -> None:  # noqa
        _write_event(args.event_file, 'SIGNAL', role=args.role, signal=signum)
        if not args.ignore_signal:
            stopped.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    grandchild: subprocess.Popen | None = None
    if args.spawn_grandchild:
        grandchild = subprocess.Popen([
            sys.executable,
            '-m',
            'omcore.daemons.children.tests.helper',
            '--event-file', args.event_file,
            '--role', 'grandchild',
        ])

    if args.write_fd is not None:
        os.write(args.write_fd, b'passed-fd')
        os.close(args.write_fd)

    print(f'child-stdout:{args.role}', flush=True)
    print(f'child-stderr:{args.role}', file=sys.stderr, flush=True)

    _write_event(
        args.event_file,
        'STARTED',
        role=args.role,
        pgid=os.getpgrp(),
        cwd=os.getcwd(),
        test_env=os.environ.get('OMCORE_DAEMONS_CHILD_TEST'),
        grandchild_pid=grandchild.pid if grandchild is not None else None,
    )

    if args.exit_code is not None:
        time.sleep(args.exit_delay_s)
        return args.exit_code

    if args.port is not None:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), _Handler)
        server.daemon_threads = True
        server.timeout = .05
        try:
            while not stopped.is_set():
                server.handle_request()
        finally:
            server.server_close()
    else:
        stopped.wait()

    if grandchild is not None:
        grandchild.wait(timeout=5.)

    _write_event(args.event_file, 'EXITING', role=args.role)
    return 0


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--event-file', required=True)
    parser.add_argument('--role', default='child')
    parser.add_argument('--ignore-signal', action='store_true')
    parser.add_argument('--exit-code', type=int)
    parser.add_argument('--exit-delay-s', type=float, default=.05)
    parser.add_argument('--write-fd', type=int)
    parser.add_argument('--spawn-grandchild', action='store_true')
    parser.add_argument('--port', type=int)
    raise SystemExit(_run(parser.parse_args()))


if __name__ == '__main__':
    _main()
