# ruff: noqa: UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import threading
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...base import HttpClientRequest
from ..asyncio import AsyncioIoPipelineAsyncHttpClient
from ..sync import IoPipelineHttpClient


class SyncLoopbackHttpServer:
    def __init__(self, response: bytes) -> None:
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


class TestSyncIoPipelineHttpClientResponses(unittest.TestCase):
    def test_head_ignores_advertised_body_length_without_waiting_for_eof(self) -> None:
        server = SyncLoopbackHttpServer(
            b'HTTP/1.1 200 OK\r\nContent-Length: 999\r\nContent-Encoding: gzip\r\n\r\n',
        )
        try:
            client = IoPipelineHttpClient(IoPipelineHttpClient.Config(request_timeout_s=.2))
            with client.stream_request(HttpClientRequest(
                    f'http://127.0.0.1:{server.port}/',
                    method='HEAD',
            )) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.stream.read(), b'')
        finally:
            server.close()

    def test_interim_response_is_skipped(self) -> None:
        server = SyncLoopbackHttpServer(
            b'HTTP/1.1 100 Continue\r\n\r\n'
            b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello',
        )
        try:
            client = IoPipelineHttpClient(IoPipelineHttpClient.Config(request_timeout_s=.2))
            with client.stream_request(HttpClientRequest(
                    f'http://127.0.0.1:{server.port}/',
                    method='POST',
                    data=b'',
            )) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.stream.read(), b'hello')
        finally:
            server.close()


class TestAsyncioIoPipelineHttpClientResponses(AsyncioIsolatedAsyncTestCase):
    async def _run_response_test(
            self,
            response: bytes,
            fn: ta.Callable[[str], ta.Awaitable[None]],
    ) -> None:
        release = asyncio.Event()
        handler_done = asyncio.Event()
        errors: ta.List[BaseException] = []

        async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            try:
                await reader.readuntil(b'\r\n\r\n')
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

    async def test_head_ignores_advertised_body_length_without_waiting_for_eof(self) -> None:
        async def run(url: str) -> None:
            client = AsyncioIoPipelineAsyncHttpClient(
                AsyncioIoPipelineAsyncHttpClient.Config(request_timeout_s=.2),
            )
            async with (await client.stream_request(HttpClientRequest(url, method='HEAD'))) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(await response.stream.read(), b'')

        await self._run_response_test(
            b'HTTP/1.1 200 OK\r\nContent-Length: 999\r\nContent-Encoding: gzip\r\n\r\n',
            run,
        )

    async def test_interim_response_is_skipped(self) -> None:
        async def run(url: str) -> None:
            client = AsyncioIoPipelineAsyncHttpClient(
                AsyncioIoPipelineAsyncHttpClient.Config(request_timeout_s=.2),
            )
            async with (await client.stream_request(HttpClientRequest(
                    url,
                    method='POST',
                    data=b'',
            ))) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(await response.stream.read(), b'hello')

        await self._run_response_test(
            b'HTTP/1.1 100 Continue\r\n\r\n'
            b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello',
            run,
        )
