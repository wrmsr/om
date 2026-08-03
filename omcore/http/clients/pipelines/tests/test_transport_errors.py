# ruff: noqa: UP006 UP045
# @om-lite
import asyncio
import socket
import struct
import threading
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...base import HttpClientError
from ...base import HttpClientRequest
from ..asyncio import AsyncioIoPipelineAsyncHttpClient
from ..sync import IoPipelineHttpClient


##


class ResettingLoopbackHttpServer:
    """Sends a response head plus a short prefix of the promised body, then aborts the connection."""

    HEAD: ta.ClassVar[bytes] = (
        b'HTTP/1.1 200 OK\r\n'
        b'Content-Length: 1000\r\n'
        b'\r\n'
    )

    BODY_PREFIX: ta.ClassVar[bytes] = b'x' * 8

    def __init__(self) -> None:
        super().__init__()

        self._sent = threading.Event()
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

                conn.sendall(self.HEAD + self.BODY_PREFIX)
                self._sent.set()

                self._release.wait(2.)

                # SO_LINGER with a zero timeout makes close() send RST rather than FIN, so the peer sees a reset
                # mid-body rather than a clean EOF.
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))

        except BaseException as e:  # noqa
            self._errors.append(e)

    def wait_sent(self) -> None:
        self._sent.wait(2.)

    def reset(self) -> None:
        self._release.set()

    def close(self) -> None:
        self._release.set()
        self._sock.close()
        self._thread.join(2.)

        if self._thread.is_alive():
            raise RuntimeError('Loopback HTTP server did not stop')
        if self._errors:
            raise self._errors[0]


##


class TestSyncMidBodyTransportError(unittest.TestCase):
    def test_reset_mid_body_raises_http_client_error(self) -> None:
        server = ResettingLoopbackHttpServer()
        try:
            with IoPipelineHttpClient() as client:
                with client.stream_request(HttpClientRequest(
                        f'http://127.0.0.1:{server.port}/',
                )) as resp:
                    self.assertEqual(resp.status, 200)

                    server.wait_sent()
                    server.reset()

                    with self.assertRaises(HttpClientError):
                        while resp.stream.read(4096):
                            pass

        finally:
            server.close()


class TestAsyncioMidBodyTransportError(AsyncioIsolatedAsyncTestCase):
    async def test_reset_mid_body_raises_http_client_error(self) -> None:
        server = ResettingLoopbackHttpServer()
        try:
            async with AsyncioIoPipelineAsyncHttpClient() as client:
                async with await client.stream_request(HttpClientRequest(
                        f'http://127.0.0.1:{server.port}/',
                )) as resp:
                    self.assertEqual(resp.status, 200)

                    await asyncio.get_running_loop().run_in_executor(None, server.wait_sent)
                    server.reset()

                    with self.assertRaises(HttpClientError):
                        while await resp.stream.read(4096):
                            pass

        finally:
            server.close()
