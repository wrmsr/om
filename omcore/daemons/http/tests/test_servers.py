import asyncio
import concurrent.futures
import contextlib
import http.client
import threading
import time
import typing as ta

import pytest

from ....http.pipelines.requests import FullIoPipelineHttpRequest
from ....http.pipelines.responses import FullIoPipelineHttpResponse
from ....io.streambufs.utils import ByteStreamBuffers
from ...tests.testing import TEST_TIMEOUT_S
from .. import AsyncHttpHandler
from .. import AsyncioPipelineHttpServer
from .. import AsyncioPipelineHttpServerConfig
from .. import HttpServerRuntime
from .. import PipelineHttpServer
from .. import PipelineHttpServerConfig
from .. import SimpleHttpServerRuntime
from .. import ThreadedAsyncHttpHandler


##


def _http_request(
        address: tuple[str, int],
        target: str,
        *,
        method: str = 'GET',
        body: bytes | None = None,
) -> tuple[int, bytes]:
    conn = http.client.HTTPConnection(*address, timeout=TEST_TIMEOUT_S)
    try:
        conn.request(method, target, body=body)
        response = conn.getresponse()
        return response.status, response.read()
    finally:
        conn.close()


def _run_sync_server(
        server: PipelineHttpServer,
        runtime: HttpServerRuntime,
) -> tuple[threading.Thread, list[BaseException]]:
    errors: list[BaseException] = []

    def run() -> None:
        try:
            server.run(runtime)
        except BaseException as exc:  # noqa
            errors.append(exc)

    thread = threading.Thread(target=run, name='PipelineHttpTestServer')
    thread.start()
    assert server.wait_started(TEST_TIMEOUT_S)
    return thread, errors


##


class _RecordingHttpRuntime:
    drain_timeout_s = TEST_TIMEOUT_S

    def __init__(self) -> None:
        super().__init__()

        self.shutdown = threading.Event()
        self.active_count = 0
        self.acquisitions = 0
        self._lock = threading.Lock()

    @property
    def shutdown_requested(self) -> bool:
        return self.shutdown.is_set()

    def wait_shutdown(self) -> None:
        self.shutdown.wait()

    def request_shutdown(self, message: str = 'requested') -> None:
        self.shutdown.set()

    @contextlib.contextmanager
    def _activity(self):
        with self._lock:
            self.active_count += 1
            self.acquisitions += 1
        try:
            yield
        finally:
            with self._lock:
                self.active_count -= 1

    def acquire_activity(self) -> ta.ContextManager[ta.Any] | None:
        if self.shutdown.is_set():
            return None
        return self._activity()


def test_sync_pipeline_http_health_is_separate_from_application_dispatch():
    calls: list[tuple[str, bytes]] = []

    def handler(request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        assert runtime.active_count == 1
        calls.append((request.head.target, ByteStreamBuffers.to_bytes(request.body, strict=True)))
        if request.head.target == '/failure':
            raise RuntimeError('application failed')
        return FullIoPipelineHttpResponse.simple(status=201, body=b'application')

    runtime = _RecordingHttpRuntime()
    server = PipelineHttpServer(PipelineHttpServerConfig(
        host='127.0.0.1',
        port=0,
        handler=handler,
        connection_timeout_s=TEST_TIMEOUT_S,
    ))
    thread, errors = _run_sync_server(server, runtime)
    try:
        assert _http_request(server.bound_address, '/healthz?probe=readiness') == (200, b'ready')
        assert calls == []
        assert runtime.acquisitions == 0
        assert _http_request(
            server.bound_address,
            '/work',
            method='POST',
            body=b'payload',
        ) == (201, b'application')
        assert calls == [('/work', b'payload')]
        assert runtime.acquisitions == 1
        assert runtime.active_count == 0
        assert _http_request(server.bound_address, '/failure') == (500, b'internal server error')
        assert calls == [('/work', b'payload'), ('/failure', b'')]
        assert runtime.acquisitions == 2
        assert runtime.active_count == 0
    finally:
        runtime.request_shutdown()
        thread.join(TEST_TIMEOUT_S)

    assert not thread.is_alive()
    assert not errors


def test_sync_pipeline_http_shutdown_drains_accepted_request():
    started = threading.Event()
    release = threading.Event()

    def handler(request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        started.set()
        assert release.wait(TEST_TIMEOUT_S)
        return FullIoPipelineHttpResponse.simple(body=b'drained')

    runtime = _RecordingHttpRuntime()
    server = PipelineHttpServer(PipelineHttpServerConfig(
        host='127.0.0.1',
        port=0,
        handler=handler,
        connection_timeout_s=TEST_TIMEOUT_S,
    ))
    server_thread, errors = _run_sync_server(server, runtime)
    with contextlib.ExitStack() as stack:
        executor = stack.enter_context(concurrent.futures.ThreadPoolExecutor(max_workers=1))
        response = executor.submit(_http_request, server.bound_address, '/block')
        assert started.wait(TEST_TIMEOUT_S)

        runtime.request_shutdown()
        time.sleep(.02)
        assert server_thread.is_alive()
        assert not response.done()
        assert runtime.active_count == 1

        release.set()
        assert response.result(TEST_TIMEOUT_S) == (200, b'drained')

    server_thread.join(TEST_TIMEOUT_S)
    assert not server_thread.is_alive()
    assert runtime.active_count == 0
    assert not errors


class _RejectingHttpRuntime:
    shutdown_requested = False
    drain_timeout_s = TEST_TIMEOUT_S

    def __init__(self) -> None:
        super().__init__()

        self.shutdown = threading.Event()

    def wait_shutdown(self) -> None:
        self.shutdown.wait()

    def request_shutdown(self, message: str) -> None:
        self.shutdown_requested = True
        self.shutdown.set()

    def acquire_activity(self) -> ta.ContextManager[ta.Any] | None:
        return None


def test_sync_pipeline_http_activity_rejection_returns_503_but_health_remains_available():
    application_called = False

    def handler(request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        nonlocal application_called
        application_called = True
        return FullIoPipelineHttpResponse.simple()

    runtime = _RejectingHttpRuntime()
    server = PipelineHttpServer(PipelineHttpServerConfig(
        host='127.0.0.1',
        port=0,
        handler=handler,
    ))
    errors: list[BaseException] = []

    def run() -> None:
        try:
            server.run(runtime)
        except BaseException as exc:  # noqa
            errors.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    assert server.wait_started(TEST_TIMEOUT_S)
    try:
        assert _http_request(server.bound_address, '/healthz') == (200, b'ready')
        assert _http_request(server.bound_address, '/work') == (503, b'shutting down')
        assert not application_called
    finally:
        runtime.request_shutdown('test-complete')
        thread.join(TEST_TIMEOUT_S)

    assert not errors


def test_asyncio_pipeline_http_server_and_explicit_threaded_handler_policy():
    def sync_handler(request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        if request.head.target == '/failure':
            raise RuntimeError('async application failed')
        return FullIoPipelineHttpResponse.simple(body=str(threading.get_ident()).encode())

    with pytest.raises(RuntimeError, match='ThreadedAsyncHttpHandler'):
        AsyncioPipelineHttpServerConfig(
            host='127.0.0.1',
            port=0,
            handler=ta.cast(AsyncHttpHandler, sync_handler),
        )

    async def run() -> None:
        loop_thread_id = threading.get_ident()
        runtime = SimpleHttpServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
        server = AsyncioPipelineHttpServer(AsyncioPipelineHttpServerConfig(
            host='127.0.0.1',
            port=0,
            handler=ThreadedAsyncHttpHandler(sync_handler),
            connection_timeout_s=TEST_TIMEOUT_S,
        ))
        await server.start(runtime)
        try:
            assert await asyncio.to_thread(_http_request, server.bound_address, '/healthz') == (200, b'ready')
            status, body = await asyncio.to_thread(_http_request, server.bound_address, '/work')
            assert status == 200
            assert int(body) != loop_thread_id
            assert await asyncio.to_thread(
                _http_request,
                server.bound_address,
                '/failure',
            ) == (500, b'internal server error')
        finally:
            await server.close()

    asyncio.run(run())


def test_asyncio_pipeline_http_close_drains_accepted_request():
    async def run() -> None:
        started = asyncio.Event()
        release = asyncio.Event()

        async def handler(request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
            started.set()
            await release.wait()
            return FullIoPipelineHttpResponse.simple(body=b'async-drained')

        runtime = SimpleHttpServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
        server = AsyncioPipelineHttpServer(AsyncioPipelineHttpServerConfig(
            host='127.0.0.1',
            port=0,
            handler=handler,
            connection_timeout_s=TEST_TIMEOUT_S,
        ))
        await server.start(runtime)

        response_task = asyncio.create_task(asyncio.to_thread(
            _http_request,
            server.bound_address,
            '/block',
        ))
        await asyncio.wait_for(started.wait(), TEST_TIMEOUT_S)
        close_task = asyncio.create_task(server.close())
        await asyncio.sleep(.02)
        assert not close_task.done()

        release.set()
        assert await response_task == (200, b'async-drained')
        assert await close_task

    asyncio.run(run())
