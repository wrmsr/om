# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import errno
import socket
import time
import typing as ta

from ...lite.check import check
from .handlers import FdioHandler


FdioConnectAddress = ta.Tuple[int, int, int, ta.Any]  # ta.TypeAlias  # (family, type, proto, sockaddr)


##


class FdioConnectError(Exception):
    """No address could be connected to; `errors` holds each attempt's failure, in order."""

    def __init__(self, errors: ta.Sequence[BaseException]) -> None:
        super().__init__(errors)

        self.errors = errors


class FdioConnectTimeoutError(FdioConnectError, TimeoutError):
    pass


class FdioConnectClosedError(FdioConnectError):
    """The connect handler was closed before any address connected."""


##


class ConnectingSocketFdioHandler(FdioHandler):
    """
    Connects a nonblocking socket to one address after another, each attempt under `timeout_s`, and hands the
    connected socket over.

    Registered with an `FdioManager`, the handler is writable while an attempt is in progress; on writability
    `SO_ERROR` says whether it succeeded. On success `on_connected` is called with the connected socket, still
    nonblocking, which the callback owns from then on. If every address fails, `on_failed` is called with an
    `FdioConnectError` holding each attempt's error; a timed-out last attempt makes it an `FdioConnectTimeoutError`.
    Closing the handler while connecting closes the attempt's socket and reports `FdioConnectClosedError`. Each
    callback runs within the manager's poll, from this handler's dispatch.
    """

    def __init__(
            self,
            addresses: ta.Sequence[FdioConnectAddress],
            on_connected: ta.Callable[[socket.socket], None],
            on_failed: ta.Callable[[FdioConnectError], None],
            *,
            timeout_s: ta.Optional[float] = None,
            clock: ta.Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__()

        check.not_empty(addresses)
        if timeout_s is not None and timeout_s < 0.:
            raise ValueError(timeout_s)

        self._addresses = list(addresses)
        self._on_connected: ta.Optional[ta.Callable[[socket.socket], None]] = on_connected
        self._on_failed: ta.Optional[ta.Callable[[FdioConnectError], None]] = on_failed
        self._timeout_s = timeout_s
        self._clock = clock

        self._sock: ta.Optional[socket.socket] = None
        self._deadline: ta.Optional[float] = None
        self._errors: ta.List[BaseException] = []
        self._done = False

        self._start_next()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{len(self._addresses)} left>'

    @property
    def errors(self) -> ta.Sequence[BaseException]:
        return self._errors

    @property
    def done(self) -> bool:
        return self._done

    #

    _IN_PROGRESS_ERRNOS: ta.ClassVar[ta.FrozenSet[int]] = frozenset([
        errno.EINPROGRESS,
        errno.EWOULDBLOCK,
        errno.EAGAIN,
    ])

    def _finish(self, *, connected: ta.Optional[socket.socket] = None, exc: ta.Optional[FdioConnectError] = None) -> None:  # noqa
        self._done = True
        self._sock = None
        self._deadline = None
        on_connected = self._on_connected
        on_failed = self._on_failed
        self._on_connected = None
        self._on_failed = None

        if connected is not None:
            check.not_none(on_connected)(connected)
        else:
            check.not_none(on_failed)(check.not_none(exc))

    def _start_next(self) -> None:
        while self._addresses:
            family, type_, proto, sockaddr = self._addresses.pop(0)
            try:
                sock = socket.socket(family, type_, proto)
            except OSError as e:
                self._errors.append(e)
                continue

            try:
                sock.setblocking(False)
                err = sock.connect_ex(sockaddr)
            except OSError as e:
                sock.close()
                self._errors.append(e)
                continue

            if err == 0:
                self._finish(connected=sock)
                return

            if err not in self._IN_PROGRESS_ERRNOS:
                sock.close()
                self._errors.append(OSError(err, os_strerror(err), sockaddr))
                continue

            self._sock = sock
            self._deadline = None if self._timeout_s is None else self._clock() + self._timeout_s
            return

        last = self._errors[-1] if self._errors else None
        if isinstance(last, TimeoutError):
            self._finish(exc=FdioConnectTimeoutError(list(self._errors)))
        else:
            self._finish(exc=FdioConnectError(list(self._errors)))

    #

    def fd(self) -> int:
        return check.not_none(self._sock).fileno()

    @property
    def closed(self) -> bool:
        return self._done

    def close(self) -> None:
        if self._done:
            return
        if (sock := self._sock) is not None:
            sock.close()
        self._finish(exc=FdioConnectClosedError(list(self._errors)))

    def cancel(self) -> None:
        """Closes the attempt without reporting, for a requester which reports for itself."""

        if self._done:
            return
        self._on_connected = None
        self._on_failed = None
        self._done = True
        if (sock := self._sock) is not None:
            self._sock = None
            sock.close()
        self._deadline = None

    def writable(self) -> bool:
        return not self._done and self._sock is not None

    def next_deadline(self) -> ta.Optional[float]:
        return None if self._done else self._deadline

    def on_writable(self) -> None:
        sock = check.not_none(self._sock)
        err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err == 0:
            self._finish(connected=sock)
            return

        self._sock = None
        self._deadline = None
        try:
            peer = sock.getpeername()
        except OSError:
            peer = None
        sock.close()
        self._errors.append(OSError(err, os_strerror(err), peer))
        self._start_next()

    def on_timeout(self) -> None:
        sock = check.not_none(self._sock)
        self._sock = None
        self._deadline = None
        sock.close()
        self._errors.append(TimeoutError(f'connect timed out after {self._timeout_s}s'))
        self._start_next()


def os_strerror(err: int) -> str:
    import os

    try:
        return os.strerror(err)
    except ValueError:
        return f'error {err}'
