# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import functools
import queue
import socket
import threading
import typing as ta

from .....sockets.endpoints import TcpSocketEndpoint
from ....fdio.manager import FdioManager
from ....fdio.wakeups import WakeupFdioHandler
from ...hosts.types import IoPipelineHostResolver
from ...hosts.types import IoPipelineHostResolveResult
from ...hosts.types import ResolveIoPipelineHostError


##


class ThreadedFdioIoPipelineHostResolver(IoPipelineHostResolver):
    """
    Resolves on one background thread, delivering each result on the manager's thread through a wakeup handler it
    registers with the manager. Not the fdio host's default - the fdio runtime is meant to stay single-threaded, and
    forkable - but available to a loop which can afford a thread. Close it when done: the thread is stopped and the
    wakeup pipe unregistered and closed; a lookup in progress at that point is dropped.
    """

    def __init__(
            self,
            manager: FdioManager,
            *,
            thread_name: str = 'fdio-resolver',
    ) -> None:
        super().__init__()

        self._manager = manager
        self._wakeup = WakeupFdioHandler()
        manager.register(self._wakeup)

        self._requests: queue.Queue = queue.Queue()
        self._closed = False
        self._thread = threading.Thread(target=self._run, name=thread_name, daemon=True)
        self._thread.start()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def closed(self) -> bool:
        return self._closed

    _STOP: ta.ClassVar[object] = object()

    def _run(self) -> None:
        while True:
            item = self._requests.get()
            if item is self._STOP:
                return

            host, port, on_done = item
            result: ta.Union[IoPipelineHostResolveResult, BaseException]
            try:
                infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            except OSError as e:
                result = ResolveIoPipelineHostError(TcpSocketEndpoint(host, port), [e])
            except BaseException as e:  # noqa
                result = e
            else:
                result = [(family, type_, proto, sockaddr) for family, type_, proto, _, sockaddr in infos]

            if not self._closed:
                self._wakeup.post(functools.partial(on_done, result))

    def resolve(
            self,
            host: str,
            port: int,
            on_done: ta.Callable[[ta.Union[IoPipelineHostResolveResult, BaseException]], None],
    ) -> None:
        if self._closed:
            raise RuntimeError('resolver is closed')
        self._requests.put((host, port, on_done))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._requests.put(self._STOP)
        self._thread.join(timeout=5.)
        try:
            self._manager.unregister(self._wakeup)
        except KeyError:
            pass
        self._wakeup.close()
