import fcntl
import json
import multiprocessing as mp
import os
import socket
import typing as ta
import warnings

from ... import check
from ...os.pidfiles.pidfile import Pidfile
from ..pidfiles import DaemonPidfileInfo
from ..pidfiles import read_daemon_pidfile_info


##


TEST_TIMEOUT_S = 10.


def make_unix_listener(path: str, *, backlog: int = 16) -> socket.socket:
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(path)
        listener.listen(backlog)
        listener.settimeout(TEST_TIMEOUT_S)
    except BaseException:
        listener.close()
        raise
    return listener


def receive_json_line(sock: socket.socket) -> ta.Mapping[str, ta.Any]:
    buf = bytearray()
    while not buf.endswith(b'\n'):
        chunk = sock.recv(1)
        if not chunk:
            raise RuntimeError('Connection closed before JSON line')
        buf.extend(chunk)
        if len(buf) > 64 * 1024:
            raise RuntimeError('JSON line too large')
    return check.isinstance(json.loads(buf.decode('utf-8')), dict)


def accept_worker(listener: socket.socket) -> tuple[socket.socket, ta.Mapping[str, ta.Any]]:
    conn, _ = listener.accept()
    conn.settimeout(TEST_TIMEOUT_S)
    try:
        info = receive_json_line(conn)
    except BaseException:
        conn.close()
        raise
    return conn, info


def release_worker(conn: socket.socket) -> None:
    try:
        conn.sendall(b'X')
        while conn.recv(4096):
            pass
    finally:
        conn.close()


def read_locked_pidfile(path: str) -> int:
    with Pidfile(
            path,
            inheritable=False,
            no_create=True,
    ) as pidfile:
        return check.not_none(pidfile.read())


def read_locked_daemon_pidfile_info(path: str) -> DaemonPidfileInfo:
    with Pidfile(
            path,
            inheritable=False,
            no_create=True,
    ) as pidfile:
        return check.not_none(read_daemon_pidfile_info(pidfile))


def wait_pidfile_unlocked(path: str) -> None:
    with Pidfile(
            path,
            inheritable=False,
            no_create=True,
    ) as pidfile:
        fcntl.flock(check.not_none(pidfile.fileno()), fcntl.LOCK_EX)


def find_multiprocessing_child(pid: int):
    for process in mp.active_children():
        if process.pid == pid:
            return process
    raise RuntimeError(f'Multiprocessing child not found: {pid}')


def join_multiprocessing_child(process) -> int:
    process.join(TEST_TIMEOUT_S)
    if process.is_alive():
        process.terminate()
        process.join(TEST_TIMEOUT_S)
        raise TimeoutError(f'Multiprocessing child did not exit: {process.pid}')

    exit_code = check.isinstance(process.exitcode, int)
    process.close()
    return exit_code


def wait_fork_child(pid: int) -> int:
    waited_pid, status = os.waitpid(pid, 0)
    check.equal(waited_pid, pid)

    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    raise RuntimeError(f'Unexpected child status: {status}')


def launch_forking(launcher) -> bool:
    origin_pid = os.getpid()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore',
                message='This process .* is multi-threaded.*',
                category=DeprecationWarning,
            )
            return launcher.launch()
    except SystemExit as exc:
        if os.getpid() != origin_pid:
            os._exit(exc.code if isinstance(exc.code, int) else 1)
        raise
