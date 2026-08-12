import http.server
import threading
import urllib.request

from ... import check
from ..daemon import Daemon
from ..httpwaiting import HttpWait
from ..spawning import ThreadSpawning
from ..targets import FnTarget
from .testing import TEST_TIMEOUT_S


##


def test_thread_daemon_waits_for_dedicated_http_health_endpoint():
    health_calls = 0

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            nonlocal health_calls

            if self.path == '/healthz':
                health_calls += 1
                if health_calls < 3:
                    status, body = 503, b'not-ready'
                else:
                    status, body = 200, b'ready'
            elif self.path == '/work':
                status, body = 200, b'non-rpc-http-daemon'
            else:
                status, body = 404, b'not-found'

            self.send_response(status)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args) -> None:  # noqa
            pass

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    finished = threading.Event()

    def run_server() -> None:
        try:
            server.serve_forever()
        finally:
            finished.set()

    server_address = check.isinstance(server.server_address, tuple)
    host = check.isinstance(server_address[0], str)
    port = check.isinstance(server_address[1], int)
    daemon = Daemon(
        FnTarget(run_server),
        Daemon.Config(
            spawning=ThreadSpawning(linger=True),
            wait=HttpWait(
                url=f'http://{host}:{port}/healthz',
                expected_status=200,
                expected_body=b'ready',
                timeout_s=1.,
            ),
            wait_timeout=TEST_TIMEOUT_S,
            wait_sleep_s=.01,
        ),
    )

    try:
        daemon.launch()
        assert health_calls == 3

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://{host}:{port}/work', timeout=TEST_TIMEOUT_S) as response:
            assert response.status == 200
            assert response.read() == b'non-rpc-http-daemon'

    finally:
        server.shutdown()
        server.server_close()

    assert finished.wait(TEST_TIMEOUT_S)
