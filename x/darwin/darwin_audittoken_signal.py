#!/usr/bin/env python3
"""Darwin audit-token signalling demo.

Server:
  * double-forks by default;
  * listens on an AF_UNIX stream socket;
  * sends a greeting from the final daemon process.

Client:
  * connects and reads that greeting;
  * asks the kernel for the connected peer's audit_token_t with
    getsockopt(SOL_LOCAL, LOCAL_PEERTOKEN);
  * passes the opaque token to private libproc SPI
    proc_signal_with_audittoken().

The libproc function is unsupported private SPI.  It may change or disappear
in a future macOS release.  No third-party Python packages are required.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import errno
import os
import signal
import socket
import stat
import sys
import tempfile
import time


# Darwin <sys/un.h>; Python's socket module does not expose these today.
SOL_LOCAL = 0
LOCAL_PEERTOKEN = 0x006

# struct sockaddr_un has char sun_path[104], including the trailing NUL.
SUN_PATH_CAPACITY = 104

GREETING = b'DARWIN-AUDITTOKEN-SIGNAL/1 '
MAX_LINE = 4096

RUNTIME_DIR = os.path.join(
    tempfile.gettempdir(), f'darwin-audittoken-signal-{os.getuid()}',
)
DEFAULT_SOCKET = os.path.join(RUNTIME_DIR, 'control.sock')
DEFAULT_LOG = os.path.join(RUNTIME_DIR, 'server.log')


class AuditToken(ctypes.Structure):
    # audit_token_t is opaque, but its ABI representation is uint32_t val[8].
    _fields_ = [('val', ctypes.c_uint32 * 8)]


assert ctypes.sizeof(AuditToken) == 32


def require_darwin() -> None:
    if sys.platform != 'darwin':
        raise RuntimeError(f'macOS/Darwin required, not {sys.platform!r}')


def abs_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def check_socket_path(path: str) -> None:
    length = len(os.fsencode(path))
    if length >= SUN_PATH_CAPACITY:
        raise RuntimeError(
            f'Unix-socket path is {length} bytes; Darwin requires fewer than '
            f'{SUN_PATH_CAPACITY}: {path}',
        )


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(path) or '.'
    os.makedirs(parent, mode=0o700, exist_ok=True)

    # Tighten only our dedicated default runtime directory.
    if parent == abs_path(RUNTIME_DIR):
        st = os.lstat(parent)
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid():
            raise RuntimeError(f'unsafe runtime directory: {parent}')
        os.chmod(parent, 0o700)


def remove_stale_socket(path: str, replace_stale: bool) -> None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return

    if not replace_stale:
        raise RuntimeError(
            f'socket path exists: {path}; after verifying no live server owns '
            'it, retry with --replace-stale',
        )
    if not stat.S_ISSOCK(st.st_mode):
        raise RuntimeError(f'refusing to unlink non-socket path: {path}')
    if st.st_uid != os.geteuid():
        raise RuntimeError(f'refusing to unlink socket owned by uid {st.st_uid}')
    os.unlink(path)


def bind_listener(path: str, replace_stale: bool) -> tuple[socket.socket, tuple[int, int]]:
    check_socket_path(path)
    ensure_parent(path)
    remove_stale_socket(path, replace_stale)

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    identity: tuple[int, int] | None = None
    try:
        listener.bind(path)
        st = os.lstat(path)
        identity = st.st_dev, st.st_ino
        os.chmod(path, 0o600)
        listener.listen(16)
        listener.settimeout(0.5)
        return listener, identity
    except BaseException:
        listener.close()
        if identity is not None:
            try:
                st = os.lstat(path)
            except FileNotFoundError:
                pass
            else:
                if stat.S_ISSOCK(st.st_mode) and (st.st_dev, st.st_ino) == identity:
                    os.unlink(path)
        raise


def unlink_bound_socket(path: str, identity: tuple[int, int]) -> None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return
    if stat.S_ISSOCK(st.st_mode) and (st.st_dev, st.st_ino) == identity:
        os.unlink(path)


def write_status(fd: int | None, message: str) -> None:
    if fd is None:
        return
    data = (message.replace('\n', ' ') + '\n').encode('utf-8', 'replace')
    try:
        while data:
            count = os.write(fd, data)
            data = data[count:]
    except OSError:
        pass


def read_status(fd: int) -> str:
    data = bytearray()
    while len(data) < MAX_LINE:
        chunk = os.read(fd, MAX_LINE - len(data))
        if not chunk:
            break
        data.extend(chunk)
        if b'\n' in chunk:
            break
    return bytes(data).partition(b'\n')[0].decode('utf-8', 'replace')


def daemonize() -> tuple[bool, int]:
    """Return (True, status_fd) in daemon, (False, exit_status) in parent."""
    status_r, status_w = os.pipe()
    first_child = os.fork()

    if first_child > 0:
        os.close(status_w)
        try:
            status = read_status(status_r)
        finally:
            os.close(status_r)
            os.waitpid(first_child, 0)

        if status.startswith('READY '):
            print(status)
            return False, 0
        print(status or 'ERROR daemon exited before reporting status', file=sys.stderr)
        return False, 1

    os.close(status_r)
    try:
        os.setsid()
        second_child = os.fork()
        if second_child > 0:
            os._exit(0)

        os.chdir('/')
        os.umask(0o077)
        return True, status_w
    except BaseException as exc:
        write_status(status_w, f'ERROR daemonization failed: {exc}')
        os.close(status_w)
        os._exit(1)


def redirect_daemon_stdio(log_path: str) -> None:
    ensure_parent(log_path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    flags |= getattr(os, 'O_CLOEXEC', 0)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    log_fd = os.open(log_path, flags, 0o600)
    st = os.fstat(log_fd)
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid():
        os.close(log_fd)
        raise RuntimeError(f'unsafe log file: {log_path}')
    os.fchmod(log_fd, 0o600)

    null_fd = os.open(os.devnull, os.O_RDONLY)
    try:
        os.dup2(null_fd, 0)
        os.dup2(log_fd, 1)
        os.dup2(log_fd, 2)
    finally:
        if null_fd > 2:
            os.close(null_fd)
        if log_fd > 2:
            os.close(log_fd)


def log(message: str) -> None:
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S%z')
    data = f'{timestamp} pid={os.getpid()} {message}\n'.encode(
        'utf-8', 'backslashreplace',
    )
    try:
        os.write(2, data)
    except OSError:
        pass


def signal_name(signum: int) -> str:
    try:
        return signal.Signals(signum).name
    except ValueError:
        return str(signum)


def parse_signal(value: str) -> int:
    text = value.strip().upper()
    if text.startswith('SIG'):
        text = text[3:]

    if text.isdecimal():
        signum = int(text)
    else:
        signum_value = getattr(signal, f'SIG{text}', None)
        if signum_value is None or not isinstance(signum_value, int):
            raise argparse.ArgumentTypeError(f'unknown signal: {value!r}')
        signum = int(signum_value)

    nsig = getattr(signal, 'NSIG', 128)
    if not 0 < signum < nsig:
        raise argparse.ArgumentTypeError(f'signal must be in 1..{nsig - 1}')
    return signum


def nonnegative_float(value: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if result < 0:
        raise argparse.ArgumentTypeError('must be non-negative')
    return result


def recv_line(sock: socket.socket) -> bytes:
    data = bytearray()
    while len(data) < MAX_LINE:
        chunk = sock.recv(MAX_LINE - len(data))
        if not chunk:
            break
        data.extend(chunk)
        index = data.find(b'\n')
        if index >= 0:
            return bytes(data[:index])
    raise RuntimeError('peer closed without a complete greeting')


def get_peer_audit_token(sock: socket.socket) -> AuditToken:
    size = ctypes.sizeof(AuditToken)
    try:
        raw = sock.getsockopt(SOL_LOCAL, LOCAL_PEERTOKEN, size)
    except OSError as exc:
        raise OSError(
            exc.errno,
            'LOCAL_PEERTOKEN failed; this must be a connected Darwin AF_UNIX '
            f'socket: {exc.strerror}',
        ) from exc
    if len(raw) != size:
        raise RuntimeError(f'LOCAL_PEERTOKEN returned {len(raw)} bytes, expected {size}')
    return AuditToken.from_buffer_copy(raw)


def load_token_signaller() -> tuple[ctypes.CDLL, object]:
    candidates: list[str] = []
    found = ctypes.util.find_library('proc')
    if found:
        candidates.append(found)
    candidates += [
        '/usr/lib/libproc.dylib',
        'libproc.dylib',
        '/usr/lib/libSystem.B.dylib',
    ]

    errors: list[str] = []
    for name in dict.fromkeys(candidates):
        try:
            library = ctypes.CDLL(name, use_errno=True)
        except OSError as exc:
            errors.append(f'{name}: {exc}')
            continue
        try:
            function = library.proc_signal_with_audittoken
        except AttributeError:
            errors.append(f'{name}: symbol not exported')
            continue
        function.argtypes = [ctypes.POINTER(AuditToken), ctypes.c_int]
        function.restype = ctypes.c_int
        return library, function

    raise RuntimeError(
        'private symbol proc_signal_with_audittoken is unavailable: '
        + '; '.join(errors),
    )


def signal_with_token(token: AuditToken, signum: int) -> None:
    # Keep the CDLL object alive across the call.
    _library, function = load_token_signaller()

    # This private wrapper returns an errno value directly, not -1/errno.
    result = int(function(ctypes.byref(token), signum))
    if result == 0:
        return
    if result == -1:  # Defensive fallback if Apple changes the convention.
        result = ctypes.get_errno() or errno.EIO

    detail = os.strerror(result)
    if result == errno.ESRCH:
        detail += ' (target exited, execed, or the audit token became stale)'
    elif result == errno.EPERM:
        detail += ' (normal signal permissions or MAC/sandbox policy denied it)'
    raise OSError(result, f'proc_signal_with_audittoken: {detail}')


def run_server(args: argparse.Namespace) -> int:
    require_darwin()
    socket_path = abs_path(args.socket)
    log_path = abs_path(args.log or (DEFAULT_LOG if socket_path == abs_path(DEFAULT_SOCKET) else socket_path + '.log'))

    status_fd: int | None = None
    if not args.foreground:
        is_daemon, value = daemonize()
        if not is_daemon:
            return value
        status_fd = value

    listener: socket.socket | None = None
    identity: tuple[int, int] | None = None
    try:
        if not args.foreground:
            redirect_daemon_stdio(log_path)

        listener, identity = bind_listener(socket_path, args.replace_stale)
        ready = f'READY pid={os.getpid()} socket={socket_path}'
        if not args.foreground:
            ready += f' log={log_path}'
        write_status(status_fd, ready)
        if status_fd is not None:
            os.close(status_fd)
            status_fd = None
        if args.foreground:
            print(ready, file=sys.stderr, flush=True)

        stopping = False

        def on_signal(signum: int, _frame: object) -> None:
            nonlocal stopping
            log(f'received {signal_name(signum)}')
            if signum in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
                stopping = True

        handled = [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]
        for name in ('SIGHUP', 'SIGUSR1', 'SIGUSR2'):
            value = getattr(signal, name, None)
            if value is not None:
                handled.append(value)
        for signum in handled:
            signal.signal(signum, on_signal)

        log(f'listening on {socket_path}')
        while not stopping:
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            except InterruptedError:
                continue

            with connection:
                connection.settimeout(2.0)
                try:
                    # This operation comes from the final daemon.  The client
                    # waits for it before asking the kernel for LOCAL_PEERTOKEN.
                    connection.sendall(GREETING + str(os.getpid()).encode() + b'\n')
                    try:
                        connection.recv(64)  # Keep the peer connected until ACK.
                    except OSError:
                        pass
                except OSError:
                    pass

        log('stopping')
        return 0
    except BaseException as exc:
        write_status(status_fd, f'ERROR server failed: {exc}')
        if args.foreground:
            raise
        log(f'fatal: {type(exc).__name__}: {exc}')
        return 1
    finally:
        if status_fd is not None:
            os.close(status_fd)
        if listener is not None:
            listener.close()
        if identity is not None:
            unlink_bound_socket(socket_path, identity)


def run_client(args: argparse.Namespace) -> int:
    require_darwin()
    socket_path = abs_path(args.socket)
    check_socket_path(socket_path)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(args.timeout)
        connection.connect(socket_path)

        greeting = recv_line(connection)
        if not greeting.startswith(GREETING):
            raise RuntimeError(f'unexpected greeting: {greeting!r}')
        reported_pid = int(greeting[len(GREETING):])

        # This is the important operation: the token comes from the kernel's
        # view of the connected peer, not from bytes supplied by the server.
        token = get_peer_audit_token(connection)

        if args.delay:
            print(
                f'acquired peer token (server reports pid {reported_pid}); '
                f'delaying {args.delay:g}s',
                file=sys.stderr,
                flush=True,
            )
            time.sleep(args.delay)

        signal_with_token(token, args.signal)
        try:
            connection.sendall(b'DONE\n')
        except OSError:
            pass  # Expected for SIGKILL and harmless after successful delivery.

    print(
        f'sent {signal_name(args.signal)} using the audit token '
        f'(server reported pid {reported_pid})',
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Darwin LOCAL_PEERTOKEN + proc_signal_with_audittoken demo',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    server = sub.add_parser('server', help='double-fork and listen on a Unix socket')
    server.add_argument('--socket', default=DEFAULT_SOCKET)
    server.add_argument('--foreground', action='store_true', help='do not double-fork')
    server.add_argument('--log', help=f'daemon log path (default: {DEFAULT_LOG})')
    server.add_argument(
        '--replace-stale',
        action='store_true',
        help='remove an existing same-uid socket after you verify it is stale',
    )
    server.set_defaults(function=run_server)

    client = sub.add_parser('client', help='signal the exact connected server process')
    client.add_argument('--socket', default=DEFAULT_SOCKET)
    client.add_argument(
        '--signal',
        type=parse_signal,
        default=int(signal.SIGTERM),
        help='number or name, with or without SIG (default: TERM)',
    )
    client.add_argument(
        '--delay',
        type=nonnegative_float,
        default=0.0,
        help='sleep after token acquisition, for stale-token testing',
    )
    client.add_argument(
        '--timeout', type=nonnegative_float, default=5.0, help='socket timeout',
    )
    client.set_defaults(function=run_client)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.function(args))
    except KeyboardInterrupt:
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        print(f'{parser.prog}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
