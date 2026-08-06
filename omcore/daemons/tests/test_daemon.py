import socket
import threading

from ..daemon import Daemon
from ..spawning import ThreadSpawning
from ..targets import FnTarget
from ..waiting import ConnectWait
from .testing import TEST_TIMEOUT_S


##


def test_daemon_waits_for_real_tcp_readiness():
    accepted = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.settimeout(TEST_TIMEOUT_S)
        listener.bind(('localhost', 0))
        listener.listen()

        def run_server() -> None:
            conn, _ = listener.accept()
            conn.close()
            accepted.set()

        daemon = Daemon(
            FnTarget(run_server),
            Daemon.Config(
                spawning=ThreadSpawning(linger=True),
                wait=ConnectWait(listener.getsockname()),
                wait_timeout=TEST_TIMEOUT_S,
                wait_sleep_s=0.,
            ),
        )
        daemon.launch()

        assert accepted.wait(TEST_TIMEOUT_S)
