import os.path
import socket
import subprocess
import sys
import time

import pytest

from ..diag import ManholeBootstrap
from ..harness import bootstrap


pytest.importorskip('omdev.repl.manhole')


##


def _connect(path, *, timeout_s=10.):
    deadline = time.monotonic() + timeout_s
    while True:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(path)
        except OSError:
            sock.close()
            if time.monotonic() >= deadline:
                raise
            time.sleep(.05)
        else:
            sock.settimeout(timeout_s)
            return sock


def _read_until(sock, marker, *, timeout_s=10.):
    deadline = time.monotonic() + timeout_s
    buf = b''
    while not buf.endswith(marker):
        if time.monotonic() >= deadline:
            raise TimeoutError(buf)
        data = sock.recv(65536)
        if not data:
            raise EOFError(buf)
        buf += data
    return buf


def test_manhole_bootstrap_in_process(tmp_path):
    path = str(tmp_path / 'm.sock')
    with bootstrap(ManholeBootstrap.Config(address=path)):
        sock = _connect(path)
        try:
            assert _read_until(sock, b'>>> ').startswith(b'manhole: python')
            sock.sendall(b'sys.version_info[0]\n')
            assert _read_until(sock, b'>>> ') == b'3\n>>> '
            sock.sendall(b'threading.current_thread().name\n')
            assert _read_until(sock, b'>>> ') == b"'om-manhole'\n>>> "
            sock.sendall(b'/quit\n')
            assert sock.recv(1) == b''
        finally:
            sock.close()
    assert not os.path.exists(path)


def test_manhole_bootstrap_disabled_by_default():
    with bootstrap(ManholeBootstrap.Config()):
        pass


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 3)))


def test_manhole_bootstrap_from_the_command_line(tmp_path):
    # An arbitrary entrypoint, started through bootstrap, gets a manhole without a line of its own about it.
    path = str(tmp_path / 'cli.sock')
    proc = subprocess.Popen(
        [
            sys.executable,
            '-m', 'omcore.bootstrap',
            f'--manhole:address={path}',
            '-c', 'import time\nwhile True:\n    time.sleep(.1)\n',
        ],
        cwd=_REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        sock = _connect(path, timeout_s=60.)
        try:
            _read_until(sock, b'>>> ')
            sock.sendall(b'os.getpid()\n')
            assert _read_until(sock, b'>>> ') == f'{proc.pid}\n>>> '.encode()
            sock.sendall(b'/quit\n')
        finally:
            sock.close()
    finally:
        proc.kill()
        proc.wait(timeout=30.)
