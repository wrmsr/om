# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import threading
import typing as ta
import unittest

from .....io.pipelines.errors import TimeoutIoPipelineError
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....pipelines.clients.timeouts import IoPipelineHttpClientRequestTimeoutHandler
from ...base import HttpClientError
from ...base import HttpClientRequest
from ..asyncio import AsyncioIoPipelineAsyncHttpClient
from ..sync import IoPipelineHttpClient


class SyncLoopbackHttpServer:
    def __init__(self, response: ta.Optional[bytes]) -> None:
        super().__init__()

        self._response = response
        self._release = threading.Event()
        self._errors: ta.List[BaseException] = []

        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('127.0.0.1', 0))
        self._sock.listen()
        self.port = self._sock.getsockname()[1]

        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self) -> None:
        try:
            conn, _ = self._sock.accept()
            with conn:
                request = b''
                while b'\r\n\r\n' not in request:
                    if not (chunk := conn.recv(4096)):
                        return
                    request += chunk

                if self._response is not None:
                    conn.sendall(self._response)

                self._release.wait(2.)

        except BaseException as e:  # noqa
            self._errors.append(e)

    def close(self) -> None:
        self._release.set()
        self._sock.close()
        self._thread.join(2.)

        if self._thread.is_alive():
            raise RuntimeError('Loopback HTTP server did not stop')
        if self._errors:
            raise self._errors[0]


def find_timeout_handlers(
        client: IoPipelineHttpClient,
        request: HttpClientRequest,
) -> ta.List[IoPipelineHttpClientRequestTimeoutHandler]:
    return [
        handler
        for handler in client._prepare_request(request).pipeline_spec.handlers
        if isinstance(handler, IoPipelineHttpClientRequestTimeoutHandler)
    ]


class TestIoPipelineHttpClientTimeoutConfig(unittest.TestCase):
    def test_disabled_omits_timeout_handler(self) -> None:
        client = IoPipelineHttpClient()

        self.assertEqual(find_timeout_handlers(client, HttpClientRequest('http://test/')), [])

    def test_configured_default_and_request_override(self) -> None:
        client = IoPipelineHttpClient(IoPipelineHttpClient.Config(request_timeout_s=3.))

        default_handlers = find_timeout_handlers(client, HttpClientRequest('http://test/'))
        self.assertEqual(len(default_handlers), 1)
        self.assertEqual(default_handlers[0]._timeout_s, 3.)

        override_handlers = find_timeout_handlers(client, HttpClientRequest('http://test/', timeout_s=2.))
        self.assertEqual(len(override_handlers), 1)
        self.assertEqual(override_handlers[0]._timeout_s, 2.)

    def test_timeout_handler_is_immediately_outside_client_handler(self) -> None:
        client = IoPipelineHttpClient(IoPipelineHttpClient.Config(request_timeout_s=3.))
        handlers = client._prepare_request(HttpClientRequest('http://test/')).pipeline_spec.handlers

        index = next(
            i
            for i, handler in enumerate(handlers)
            if isinstance(handler, IoPipelineHttpClientRequestTimeoutHandler)
        )
        self.assertEqual(type(handlers[index + 1]).__name__, 'IoPipelineHttpClientHandler')


class TestSyncIoPipelineHttpClientTimeout(unittest.TestCase):
    def test_timeout_before_response_head(self) -> None:
        server = SyncLoopbackHttpServer(None)
        try:
            client = IoPipelineHttpClient(IoPipelineHttpClient.Config(request_timeout_s=.02))

            with self.assertRaises(HttpClientError) as raised:
                client.stream_request(HttpClientRequest(f'http://127.0.0.1:{server.port}/'))

            self.assertIsInstance(raised.exception.cause, TimeoutIoPipelineError)
        finally:
            server.close()

    def test_timeout_while_streaming_response_body(self) -> None:
        server = SyncLoopbackHttpServer(
            b'HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\n',
        )
        try:
            client = IoPipelineHttpClient()
            with client.stream_request(HttpClientRequest(
                    f'http://127.0.0.1:{server.port}/',
                    timeout_s=.02,
            )) as response:
                sock = response.underlying._sock
                self.assertEqual(sock.gettimeout(), 0.)

                with self.assertRaises(HttpClientError) as raised:
                    response.stream.read()

                self.assertIsInstance(raised.exception.cause, TimeoutIoPipelineError)

            self.assertIsNone(sock.gettimeout())
        finally:
            server.close()


class TestAsyncioIoPipelineHttpClientTimeout(AsyncioIsolatedAsyncTestCase):
    async def _run_timeout_test(
            self,
            response: ta.Optional[bytes],
            fn: ta.Callable[[str], ta.Awaitable[None]],
    ) -> None:
        release = asyncio.Event()
        handler_done = asyncio.Event()
        errors: ta.List[BaseException] = []

        async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            try:
                await reader.readuntil(b'\r\n\r\n')

                if response is not None:
                    writer.write(response)
                    await writer.drain()

                try:
                    await asyncio.wait_for(release.wait(), 2.)
                except TimeoutError:
                    pass

            except BaseException as e:  # noqa
                errors.append(e)

            finally:
                writer.close()
                await writer.wait_closed()
                handler_done.set()

        server = await asyncio.start_server(handle, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        try:
            await fn(f'http://127.0.0.1:{port}/')
        finally:
            release.set()
            server.close()
            await server.wait_closed()
            await asyncio.wait_for(handler_done.wait(), 2.)

        if errors:
            raise errors[0]

    async def test_timeout_before_response_head(self) -> None:
        async def run(url: str) -> None:
            client = AsyncioIoPipelineAsyncHttpClient(
                AsyncioIoPipelineAsyncHttpClient.Config(request_timeout_s=.02),
            )

            with self.assertRaises(HttpClientError) as raised:
                await client.stream_request(HttpClientRequest(url))

            self.assertIsInstance(raised.exception.cause, TimeoutIoPipelineError)

        await self._run_timeout_test(None, run)

    async def test_timeout_while_streaming_response_body(self) -> None:
        async def run(url: str) -> None:
            client = AsyncioIoPipelineAsyncHttpClient()
            async with (await client.stream_request(HttpClientRequest(
                    url,
                    timeout_s=.02,
            ))) as response:
                with self.assertRaises(HttpClientError) as raised:
                    await response.stream.read()

                self.assertIsInstance(raised.exception.cause, TimeoutIoPipelineError)

        await self._run_timeout_test(
            b'HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\n',
            run,
        )
