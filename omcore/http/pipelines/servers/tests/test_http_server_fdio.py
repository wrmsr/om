# ruff: noqa: S310 UP006 UP045
# @om-lite
import socket
import threading
import typing as ta
import unittest
import urllib.error
import urllib.request

from .demos.http_server_fdio import FdioHttpPingServer


##


class FdioHttpServerRunner:
    def __init__(self) -> None:
        super().__init__()

        self._server: ta.Optional[FdioHttpPingServer] = None
        self._thread: ta.Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._errors: ta.List[BaseException] = []

    def __enter__(self) -> int:
        self._server = server = FdioHttpPingServer(port=0)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return server.port

    def __exit__(
            self,
            exc_type: ta.Optional[ta.Type[BaseException]],
            exc: ta.Optional[BaseException],
            tb: object,
    ) -> None:
        server = self._server
        thread = self._thread
        if server is None or thread is None:
            return

        self._stop.set()
        try:
            socket.create_connection(server.address, timeout=1.).close()
        except OSError:
            pass

        thread.join(timeout=2.)
        server.close()

        if thread.is_alive():
            self._errors.append(RuntimeError('fdio server thread did not stop'))
        if self._errors and exc_type is None:
            raise self._errors[0]

    def _run(self) -> None:
        try:
            server = self._server
            if server is None:
                raise RuntimeError('fdio server was not initialized')

            while not self._stop.is_set():
                server.poll()
        except BaseException as exc:  # noqa
            self._errors.append(exc)


class TestHttpServerFdio(unittest.TestCase):
    def test_ping_endpoint(self) -> None:
        with FdioHttpServerRunner() as port:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/ping') as resp:
                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.read(), b'pong')
                self.assertEqual(resp.headers.get('Content-Type'), 'text/plain; charset=utf-8')
                self.assertEqual(resp.headers.get('Connection'), 'close')

    def test_not_found_endpoint(self) -> None:
        with FdioHttpServerRunner() as port:
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{port}/unknown')
                self.fail('Expected HTTPError')
            except urllib.error.HTTPError as exc:
                self.assertEqual(exc.code, 404)
                self.assertEqual(exc.read(), b'not found')

    def test_multiple_connections(self) -> None:
        with FdioHttpServerRunner() as port:
            for _ in range(3):
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/ping') as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(resp.read(), b'pong')
