#!/usr/bin/env python3
"""
Demonstrate race-free signalling of a connected Darwin process identity.

The server double-forks by default, binds a private AF_UNIX socket, and waits.
The client connects, asks the kernel for the socket peer's audit_token_t via
LOCAL_PEERTOKEN, then calls the private libproc SPI:

    proc_signal_with_audittoken(audit_token_t *, int)

This is intentionally Darwin-specific and relies on private SPI.  It is useful
for internal tooling, but it is not an Apple-supported compatibility contract.

Examples:

    python3 darwin_audit_signal.py server
    python3 darwin_audit_signal.py client --dry-run
    python3 darwin_audit_signal.py client --signal TERM

Use --foreground while debugging:

    python3 darwin_audit_signal.py server --foreground
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import os
import resource
import signal
import socket
import stat
import sys
import tempfile
from pathlib import Path
from typing import Iterable
from typing import NoReturn


# Darwin <sys/un.h>:
#
#     #define SOL_LOCAL       0
#     #define LOCAL_PEERPID   2
#     #define LOCAL_PEERTOKEN 6
#
# Python does not currently expose these names on every macOS release, so the
# script uses their stable Darwin numeric values directly.
SOL_LOCAL = 0
LOCAL_PEERPID = 2
LOCAL_PEERTOKEN = 6

# XNU defines audit_token_t as eight 32-bit unsigned integers.
_AUDIT_TOKEN_WORDS = 8
_AUDIT_TOKEN_SIZE = _AUDIT_TOKEN_WORDS * ctypes.sizeof(ctypes.c_uint32)
_DARWIN_UNIX_PATH_MAX = 103  # sun_path[104], reserving one byte for NUL.


class AuditToken(ctypes.Structure):
    _fields_ = [('val', ctypes.c_uint32 * _AUDIT_TOKEN_WORDS)]

    @property
    def pid(self) -> int:
        # audit_token_to_pid() uses val[5]. pid_t is signed, although valid
        # process IDs are positive.
        return ctypes.c_int32(self.val[5]).value

    @property
    def pidversion(self) -> int:
        # XNU's exact audit-token lookup compares val[7] with p_idversion.
        return int(self.val[7])

    def hex_words(self) -> str:
        return ' '.join(f'{int(word):08x}' for word in self.val)


if ctypes.sizeof(AuditToken) != _AUDIT_TOKEN_SIZE:
    raise RuntimeError('unexpected ctypes layout for audit_token_t')


_STOP_REQUESTED = False


def _request_stop(_signum: int, _frame: object) -> None:
    global _STOP_REQUESTED
    _STOP_REQUESTED = True


def _require_darwin() -> None:
    if sys.platform != 'darwin':
        raise RuntimeError('this program requires macOS/Darwin')


def _default_socket_path() -> str:
    # macOS normally gives each user a private TMPDIR.  We still create our own
    # mode-0700 directory so a custom umask cannot accidentally expose it.
    directory = Path(tempfile.gettempdir()) / f'darwin-audit-signal-{os.getuid()}'
    return str(directory / 'control.sock')


def _validate_socket_path(path: str) -> str:
    path = os.path.abspath(os.path.expanduser(path))
    encoded = os.fsencode(path)
    if len(encoded) > _DARWIN_UNIX_PATH_MAX:
        raise ValueError(
            f'Unix socket path is {len(encoded)} bytes; Darwin permits at most '
            f'{_DARWIN_UNIX_PATH_MAX}: {path!r}',
        )
    return path


def _ensure_private_parent(path: str) -> None:
    parent = os.path.dirname(path) or '.'
    try:
        os.makedirs(parent, mode=0o700, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f'cannot create socket directory {parent!r}: {exc}') from exc

    st = os.stat(parent)
    if st.st_uid != os.getuid():
        raise RuntimeError(
            f'socket directory {parent!r} is owned by uid {st.st_uid}, '
            f'not the current uid {os.getuid()}',
        )

    # Refuse a directory writable by other users unless it has sticky-dir
    # semantics (for example /tmp).  The default directory is always 0700.
    unsafe_write_bits = st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    if unsafe_write_bits and not (st.st_mode & stat.S_ISVTX):
        raise RuntimeError(
            f'socket directory {parent!r} is group/world-writable without the '
            'sticky bit; use a private directory',
        )


def _remove_stale_socket(path: str) -> None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return

    if not stat.S_ISSOCK(st.st_mode):
        raise RuntimeError(f'refusing to replace non-socket path {path!r}')
    if st.st_uid != os.getuid():
        raise RuntimeError(
            f'refusing to replace socket {path!r} owned by uid {st.st_uid}',
        )

    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.settimeout(0.25)
        try:
            probe.connect(path)
        except OSError as exc:
            if exc.errno not in (errno.ECONNREFUSED, errno.ENOENT):
                raise RuntimeError(
                    f'cannot determine whether socket {path!r} is stale: {exc}',
                ) from exc
        else:
            raise RuntimeError(f'a server is already listening on {path!r}')
    finally:
        probe.close()

    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _unlink_if_same_socket(path: str, expected_dev: int, expected_ino: int) -> None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return
    if stat.S_ISSOCK(st.st_mode) and (st.st_dev, st.st_ino) == (
        expected_dev,
        expected_ino,
    ):
        os.unlink(path)


def _write_pipe_message(fd: int, kind: str, message: str) -> None:
    # One short, newline-terminated record.  Escape control characters so the
    # parent can always parse it as a single line.
    clean = message.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')
    payload = f'{kind}\t{clean}\n'.encode('utf-8', 'replace')
    try:
        os.write(fd, payload[:4096])
    except OSError:
        pass


def _read_pipe_message(fd: int) -> tuple[str, str]:
    chunks: list[bytes] = []
    total = 0
    while total < 4096:
        chunk = os.read(fd, min(4096 - total, 512))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if b'\n' in chunk:
            break

    raw = b''.join(chunks).split(b'\n', 1)[0]
    if not raw:
        return 'ERR', 'daemon exited before reporting readiness'
    kind, sep, message = raw.partition(b'\t')
    if not sep:
        return 'ERR', f'malformed daemon readiness record: {raw!r}'
    return kind.decode('ascii', 'replace'), message.decode('utf-8', 'replace')


class _ReadinessReporter:
    """One-shot daemon-readiness pipe whose fd cannot be reused accidentally."""

    def __init__(self, fd: int) -> None:
        self.fd = fd

    def _finish(self, kind: str, message: str) -> None:
        if self.fd < 0:
            return
        fd, self.fd = self.fd, -1
        try:
            _write_pipe_message(fd, kind, message)
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    def ok(self, message: str) -> None:
        self._finish('OK', message)

    def error(self, message: str) -> None:
        self._finish('ERR', message)


def _redirect_standard_fds() -> None:
    devnull = os.open(os.devnull, os.O_RDWR)
    try:
        for fd in (0, 1, 2):
            os.dup2(devnull, fd)
    finally:
        if devnull > 2:
            os.close(devnull)


def _close_fds_except(keep: Iterable[int]) -> None:
    keep_set = {fd for fd in keep if fd >= 0}

    try:
        names = os.listdir('/dev/fd')
    except OSError:
        soft_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if soft_limit == resource.RLIM_INFINITY:
            soft_limit = 65536
        upper = min(int(soft_limit), 1 << 20)
        for fd in range(3, upper):
            if fd not in keep_set:
                try:
                    os.close(fd)
                except OSError:
                    pass
        return

    for name in names:
        try:
            fd = int(name)
        except ValueError:
            continue
        if fd > 2 and fd not in keep_set:
            try:
                os.close(fd)
            except OSError:
                pass


def _install_server_signal_handlers() -> None:
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, _request_stop)


def _serve(path: str, readiness: _ReadinessReporter | None) -> int:
    global _STOP_REQUESTED
    _STOP_REQUESTED = False

    _require_darwin()
    path = _validate_socket_path(path)
    _ensure_private_parent(path)
    _remove_stale_socket(path)

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_identity: tuple[int, int] | None = None
    try:
        old_umask = os.umask(0o077)
        try:
            listener.bind(path)
        finally:
            os.umask(old_umask)

        os.chmod(path, 0o600)
        st = os.lstat(path)
        socket_identity = (st.st_dev, st.st_ino)

        listener.listen(16)
        listener.settimeout(0.5)
        _install_server_signal_handlers()

        ready_message = f'pid={os.getpid()} socket={path}'
        if readiness is not None:
            readiness.ok(ready_message)
        else:
            print(ready_message, flush=True)

        while not _STOP_REQUESTED:
            try:
                conn, _ = listener.accept()
            except socket.timeout:
                continue
            except InterruptedError:
                continue

            # Keeping the accepted endpoint alive is enough for the client to
            # ask the kernel for LOCAL_PEERTOKEN.  No token bytes are supplied
            # by this process.  A tiny greeting merely makes manual testing
            # and diagnosis friendlier.
            with conn:
                conn.settimeout(0.5)
                try:
                    conn.sendall(b'darwin-audit-signal/1\n')
                except (BrokenPipeError, ConnectionResetError):
                    continue

                while not _STOP_REQUESTED:
                    try:
                        data = conn.recv(4096)
                    except socket.timeout:
                        continue
                    except (ConnectionResetError, InterruptedError):
                        break
                    if not data:
                        break
                    if b'PING' in data.upper():
                        try:
                            conn.sendall(b'PONG\n')
                        except (BrokenPipeError, ConnectionResetError):
                            break

        return 0
    finally:
        listener.close()
        if socket_identity is not None:
            _unlink_if_same_socket(path, *socket_identity)


def _run_daemon_child(path: str, ready_fd: int) -> NoReturn:
    readiness = _ReadinessReporter(ready_fd)
    try:
        os.setsid()
        second_pid = os.fork()
        if second_pid != 0:
            os._exit(0)

        os.chdir('/')
        os.umask(0o077)
        _redirect_standard_fds()
        _close_fds_except({0, 1, 2, readiness.fd})
        os._exit(_serve(path, readiness))
    except BaseException as exc:
        readiness.error(f'{type(exc).__name__}: {exc}')
        os._exit(1)


def _start_daemon(path: str) -> int:
    _require_darwin()
    path = _validate_socket_path(path)

    read_fd, write_fd = os.pipe()
    first_pid = os.fork()
    if first_pid == 0:
        os.close(read_fd)
        _run_daemon_child(path, write_fd)

    os.close(write_fd)
    try:
        kind, message = _read_pipe_message(read_fd)
    finally:
        os.close(read_fd)
        # Reap only the short-lived first child.  The grandchild has been
        # reparented and is intentionally unrelated to this process.
        while True:
            try:
                os.waitpid(first_pid, 0)
                break
            except InterruptedError:
                continue

    if kind != 'OK':
        raise RuntimeError(message)
    print(message)
    return 0


def _recv_protocol_greeting(sock: socket.socket) -> None:
    expected = b'darwin-audit-signal/1\n'
    received = bytearray()
    while len(received) < len(expected):
        chunk = sock.recv(len(expected) - len(received))
        if not chunk:
            raise ConnectionError('server closed before sending its protocol greeting')
        received.extend(chunk)
    if bytes(received) != expected:
        raise RuntimeError(
            f'unexpected server greeting {bytes(received)!r}; expected {expected!r}',
        )


def _peer_audit_token(sock: socket.socket) -> AuditToken:
    raw = sock.getsockopt(SOL_LOCAL, LOCAL_PEERTOKEN, _AUDIT_TOKEN_SIZE)
    if len(raw) != _AUDIT_TOKEN_SIZE:
        raise RuntimeError(
            f'LOCAL_PEERTOKEN returned {len(raw)} bytes, expected {_AUDIT_TOKEN_SIZE}',
        )
    return AuditToken.from_buffer_copy(raw)


def _peer_pid(sock: socket.socket) -> int:
    # LOCAL_PEERPID returns a native pid_t.  Darwin pid_t is a signed 32-bit int.
    raw = sock.getsockopt(SOL_LOCAL, LOCAL_PEERPID, ctypes.sizeof(ctypes.c_int32))
    if len(raw) != ctypes.sizeof(ctypes.c_int32):
        raise RuntimeError(
            f'LOCAL_PEERPID returned {len(raw)} bytes, expected '
            f'{ctypes.sizeof(ctypes.c_int32)}',
        )
    value = ctypes.c_int32.from_buffer_copy(raw)
    return int(value.value)


def _load_proc_signal_with_audittoken():
    try:
        libproc = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
    except OSError as exc:
        raise RuntimeError(f'cannot load /usr/lib/libproc.dylib: {exc}') from exc

    try:
        function = libproc.proc_signal_with_audittoken
    except AttributeError as exc:
        raise RuntimeError(
            'this macOS release does not export the private '
            'proc_signal_with_audittoken SPI',
        ) from exc

    function.argtypes = (ctypes.POINTER(AuditToken), ctypes.c_int)
    function.restype = ctypes.c_int
    # Keep the owning CDLL alive for as long as the function object exists.
    function._libproc_owner = libproc  # type: ignore[attr-defined]
    return function


def _parse_signal(value: str) -> int:
    text = value.strip()
    if not text:
        raise argparse.ArgumentTypeError('signal must not be empty')

    try:
        number = int(text, 10)
    except ValueError:
        name = text.upper()
        if not name.startswith('SIG'):
            name = 'SIG' + name
        number_obj = getattr(signal, name, None)
        if number_obj is None or name in {'SIG_DFL', 'SIG_IGN'}:
            raise argparse.ArgumentTypeError(f'unknown signal {value!r}')
        number = int(number_obj)

    if number <= 0 or number >= signal.NSIG:
        raise argparse.ArgumentTypeError(
            f'signal number must be in [1, {signal.NSIG - 1}], got {number}',
        )
    return number


def _signal_name(number: int) -> str:
    try:
        return signal.Signals(number).name
    except ValueError:
        return str(number)


def _run_client(path: str, sig: int, dry_run: bool, timeout: float) -> int:
    _require_darwin()
    path = _validate_socket_path(path)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        sock.connect(path)

        # XNU implements LOCAL_PEERTOKEN using the peer socket's last_pid.
        # Reading a greeting that this daemon instance just wrote ensures the
        # accepted endpoint was most recently operated by the daemon itself
        # before we ask the kernel for its token. Do not share/pass that
        # accepted endpoint to another process.
        _recv_protocol_greeting(sock)

        # These values are supplied by the kernel for the connected peer; they
        # are not claims parsed from bytes sent by the server.
        token = _peer_audit_token(sock)
        peer_pid = _peer_pid(sock)
        if token.pid != peer_pid:
            raise RuntimeError(
                f'kernel peer identity disagreement: token pid={token.pid}, '
                f'LOCAL_PEERPID={peer_pid}',
            )

        print(f'peer pid:        {token.pid}')
        print(f'peer pidversion: {token.pidversion}')
        print(f'audit token:     {token.hex_words()}')

        if dry_run:
            print('dry run: no signal sent')
            return 0

        proc_signal = _load_proc_signal_with_audittoken()
        result = int(proc_signal(ctypes.byref(token), sig))
        if result != 0:
            # This private wrapper returns an errno value directly rather than
            # returning -1 and leaving errno for the caller.
            raise OSError(
                result,
                f'proc_signal_with_audittoken({_signal_name(sig)}) failed: '
                f'{os.strerror(result)}',
            )

        print(
            f'sent {_signal_name(sig)} ({sig}) to exact peer identity '
            f'pid={token.pid}, pidversion={token.pidversion}',
        )
        return 0
    finally:
        sock.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Darwin audit-token signalling demo using an AF_UNIX peer token '
            'and private libproc SPI'
        ),
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    server_parser = subparsers.add_parser(
        'server', help='double-fork and listen on a Unix socket',
    )
    server_parser.add_argument(
        '--socket',
        default=_default_socket_path(),
        help='Unix socket path (default: %(default)s)',
    )
    server_parser.add_argument(
        '--foreground',
        action='store_true',
        help='do not double-fork; useful for debugging',
    )

    client_parser = subparsers.add_parser(
        'client', help="obtain the socket peer's audit token and signal it",
    )
    client_parser.add_argument(
        '--socket',
        default=_default_socket_path(),
        help='Unix socket path (default: %(default)s)',
    )
    client_parser.add_argument(
        '--signal',
        type=_parse_signal,
        default=int(signal.SIGTERM),
        metavar='NAME|NUMBER',
        help='signal to send (default: TERM)',
    )
    client_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='print the kernel-issued peer identity without signalling it',
    )
    client_parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='socket connection timeout in seconds (default: %(default)s)',
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == 'server':
            path = _validate_socket_path(args.socket)
            if args.foreground:
                return _serve(path, None)
            return _start_daemon(path)

        if args.command == 'client':
            if args.timeout <= 0:
                parser.error('--timeout must be greater than zero')
            return _run_client(
                _validate_socket_path(args.socket),
                args.signal,
                args.dry_run,
                args.timeout,
            )

        parser.error(f'unknown command: {args.command}')
    except (OSError, RuntimeError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
