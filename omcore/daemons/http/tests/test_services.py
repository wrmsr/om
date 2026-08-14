import json
import multiprocessing as mp
import os
import socket
import tempfile
import threading
import time
import typing as ta

from ....http.pipelines.requests import FullIoPipelineHttpRequest
from ....http.pipelines.responses import FullIoPipelineHttpResponse
from ...daemon import Daemon
from ...httpwaiting import HttpWait
from ...lazy import LazyDaemon
from ...runtime import ServiceRuntime
from ...services import ServiceDaemon
from ...spawning import MultiprocessingSpawning
from ...spawning import ThreadSpawning
from ...tests.testing import TEST_TIMEOUT_S
from ...tests.testing import find_multiprocessing_child
from ...tests.testing import join_multiprocessing_child
from ...tests.testing import read_locked_daemon_pidfile_info
from ...tests.testing import read_locked_pidfile
from ...tests.testing import wait_pidfile_unlocked
from .. import AsyncioPipelineHttpService
from .. import PipelineHttpService
from .test_servers import _http_request


##


def _unused_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _cleanup_new_children(prior_child_pids: set[int]) -> None:
    for process in mp.active_children():
        if process.pid in prior_child_pids:
            continue
        if process.is_alive():
            process.terminate()
        process.join(TEST_TIMEOUT_S)
        process.close()


class _SharedHttpHandler:
    def __init__(self, *, delay_s: float = 0.) -> None:
        super().__init__()

        self._delay_s = delay_s
        self.calls: list[tuple[int, int, str]] = []

    def __call__(self, request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        self.calls.append((os.getpid(), threading.get_ident(), request.head.target))
        time.sleep(self._delay_s)
        return FullIoPipelineHttpResponse.simple(body=b'in-process')


class _SharedAsyncHttpHandler:
    def __init__(self) -> None:
        super().__init__()

        self.calls: list[tuple[int, int, str]] = []

    async def __call__(self, request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        self.calls.append((os.getpid(), threading.get_ident(), request.head.target))
        return FullIoPipelineHttpResponse.simple(body=b'async-in-process')


class _ProcessHttpHandler:
    def __init__(self, execution_log: str) -> None:
        super().__init__()

        self._execution_log = execution_log

    def __call__(self, request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        info = {
            'pid': os.getpid(),
            'target': request.head.target,
        }
        with open(self._execution_log, 'a') as file:
            file.write(json.dumps(info) + '\n')
        return FullIoPipelineHttpResponse.simple(body=str(os.getpid()).encode())


##


def test_thread_pipeline_http_service_shares_state_and_idles_after_application_activity():
    with tempfile.TemporaryDirectory() as temp_dir:
        port = _unused_tcp_port()
        pid_file = os.path.join(temp_dir, 'http.pid')
        idle_timeout_s = .2
        handler = _SharedHttpHandler(delay_s=.3)
        service = PipelineHttpService(PipelineHttpService.Config(
            runtime=ServiceRuntime.Config(
                idle_timeout_s=idle_timeout_s,
                drain_timeout_s=TEST_TIMEOUT_S,
            ),
            host='127.0.0.1',
            port=port,
            handler=handler,
            connection_timeout_s=TEST_TIMEOUT_S,
        ))
        service_daemon: ServiceDaemon[PipelineHttpService, PipelineHttpService.Config] = ServiceDaemon(
            service,
            Daemon.Config(
                spawning=ThreadSpawning(linger=True),
                pid_file=pid_file,
                wait=HttpWait(
                    url=f'http://127.0.0.1:{port}/healthz',
                    expected_body=b'ready',
                ),
                wait_timeout=TEST_TIMEOUT_S,
                wait_sleep_s=.01,
            ),
        )

        daemon = service_daemon.daemon_()
        daemon.launch()
        assert handler.calls == []
        assert _http_request(('127.0.0.1', port), '/work') == (200, b'in-process')
        response_time = time.monotonic()
        assert len(handler.calls) == 1
        pid, handler_thread_id, target = handler.calls[0]
        assert pid == os.getpid()
        assert handler_thread_id != threading.get_ident()
        assert target == '/work'

        # Work which outlasts the idle timeout remains accepted, and releasing
        # it starts a fresh full linger window. Health probes do not refresh it.
        health_responses = 0
        deadline = time.monotonic() + TEST_TIMEOUT_S
        while daemon.is_pidfile_locked():
            assert time.monotonic() < deadline
            try:
                status, _ = _http_request(('127.0.0.1', port), '/healthz')
            except OSError:
                pass
            else:
                if status == 200:
                    health_responses += 1
            time.sleep(.01)

        assert health_responses > 1
        assert time.monotonic() - response_time >= idle_timeout_s / 2
        wait_pidfile_unlocked(pid_file)


def test_thread_asyncio_pipeline_http_service_shares_state_and_idles():
    with tempfile.TemporaryDirectory() as temp_dir:
        port = _unused_tcp_port()
        pid_file = os.path.join(temp_dir, 'async-http.pid')
        handler = _SharedAsyncHttpHandler()
        service = AsyncioPipelineHttpService(AsyncioPipelineHttpService.Config(
            runtime=ServiceRuntime.Config(
                idle_timeout_s=.2,
                drain_timeout_s=TEST_TIMEOUT_S,
            ),
            host='127.0.0.1',
            port=port,
            handler=handler,
            connection_timeout_s=TEST_TIMEOUT_S,
        ))
        service_daemon: ServiceDaemon[AsyncioPipelineHttpService, AsyncioPipelineHttpService.Config] = ServiceDaemon(
            service,
            Daemon.Config(
                spawning=ThreadSpawning(linger=True),
                pid_file=pid_file,
                wait=HttpWait(
                    url=f'http://127.0.0.1:{port}/healthz',
                    expected_body=b'ready',
                ),
                wait_timeout=TEST_TIMEOUT_S,
                wait_sleep_s=.01,
            ),
        )

        service_daemon.daemon_().launch()
        assert handler.calls == []
        assert _http_request(('127.0.0.1', port), '/async-work') == (200, b'async-in-process')
        assert len(handler.calls) == 1
        pid, handler_thread_id, target = handler.calls[0]
        assert pid == os.getpid()
        assert handler_thread_id != threading.get_ident()
        assert target == '/async-work'

        wait_pidfile_unlocked(pid_file)


def test_lazy_multiprocessing_pipeline_http_service_idles_and_restarts():
    prior_child_pids = {process.pid for process in mp.active_children() if process.pid is not None}

    with tempfile.TemporaryDirectory() as temp_dir:
        port = _unused_tcp_port()
        pid_file = os.path.join(temp_dir, 'http.pid')
        execution_log = os.path.join(temp_dir, 'executions.jsonl')
        service_daemon: ServiceDaemon[PipelineHttpService, PipelineHttpService.Config] = ServiceDaemon(
            PipelineHttpService.Config(
                runtime=ServiceRuntime.Config(
                    idle_timeout_s=.25,
                    drain_timeout_s=TEST_TIMEOUT_S,
                ),
                host='127.0.0.1',
                port=port,
                handler=_ProcessHttpHandler(execution_log),
                connection_timeout_s=TEST_TIMEOUT_S,
            ),
            Daemon.Config(
                spawning=MultiprocessingSpawning(
                    start_method=MultiprocessingSpawning.StartMethod.SPAWN,
                ),
                pid_file=pid_file,
                wait=HttpWait(
                    url=f'http://127.0.0.1:{port}/healthz',
                    expected_status=200,
                    expected_body=b'ready',
                ),
                wait_timeout=TEST_TIMEOUT_S,
                wait_sleep_s=.01,
            ),
        )
        lazy = LazyDaemon(service_daemon.daemon_())

        try:
            assert lazy.ensure()
            assert not os.path.exists(execution_log)

            status, body = _http_request(('127.0.0.1', port), '/work')
            assert status == 200
            worker_pid = int(body)
            assert read_locked_pidfile(pid_file) == worker_pid
            first_info = read_locked_daemon_pidfile_info(pid_file)
            assert first_info.pid == worker_pid
            process = find_multiprocessing_child(worker_pid)

            with open(execution_log) as file:
                executions: list[ta.Any] = [json.loads(line) for line in file]
            assert executions == [{'pid': worker_pid, 'target': '/work'}]

            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(process) == 0

            assert lazy.ensure()
            second_info = read_locked_daemon_pidfile_info(pid_file)
            assert second_info.instance_id != first_info.instance_id

            status, body = _http_request(('127.0.0.1', port), '/work-again')
            assert status == 200
            second_worker_pid = int(body)
            assert second_info.pid == second_worker_pid
            second_process = find_multiprocessing_child(second_worker_pid)

            with open(execution_log) as file:
                executions = [json.loads(line) for line in file]
            assert executions == [
                {'pid': worker_pid, 'target': '/work'},
                {'pid': second_worker_pid, 'target': '/work-again'},
            ]

            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(second_process) == 0
        finally:
            _cleanup_new_children(prior_child_pids)
