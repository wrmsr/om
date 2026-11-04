"""
Test support: remote blob stores to run tests against, and a scenario runner on the long-lived loop their connections
belong to.
"""
import asyncio
import os.path
import socket
import sys
import threading
import typing as ta

from omcore.rpc.asyncio import AsyncioRpcConnections

from ...local.stores import LocalBlobStore
from ...tests.runners import ScenarioRunner
from .._main import serve_remote_blob_store
from ..client import RemoteBlobStore


T = ta.TypeVar('T')


##


# The target runs under the Python 3.8 venv when there is one: it is lite, and this is where that is proven.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
_PYTHON_38 = os.path.join(_REPO_ROOT, '.venvs', '8', 'bin', 'python')
REMOTE_BLOBS_TEST_PYTHON = _PYTHON_38 if os.path.isfile(_PYTHON_38) else sys.executable

# Small, so the conformance suite's larger objects and longer listings cross in many chunks and pages.
REMOTE_BLOBS_TEST_STORE_KWARGS: ta.Mapping[str, ta.Any] = dict(
    chunk_bytes=64 * 1024,
    page_size=7,
)


class LoopScenarioRunner(ScenarioRunner):
    """Scenarios on one long-lived loop: the one the store's connection belongs to."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()

        self._loop = loop

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    def run(self, fn: ta.Callable[[], ta.Awaitable[T]]) -> T:
        async def inner() -> T:
            return await fn()

        return self._loop.run_until_complete(inner())

    async def gather(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> list[T | BaseException]:
        return list(await asyncio.gather(*[fn() for fn in fns], return_exceptions=True))


class InProcessRemoteBlobStore:
    """
    A `LocalBlobStore` served on a thread over one end of a socketpair - through the same entry the target's main uses
    - and a `RemoteBlobStore` connected to the other end on a loop of its own.
    """

    def __init__(self, root: str, **store_kwargs: ta.Any) -> None:
        super().__init__()

        self.loop = asyncio.new_event_loop()

        client_sock, self._server_sock = socket.socketpair()
        self._thread = threading.Thread(
            target=serve_remote_blob_store,
            args=(
                LocalBlobStore(root, config=LocalBlobStore.Config(no_fsync=True)),
                self._server_sock.fileno(),
                self._server_sock.fileno(),
            ),
            daemon=True,
        )
        self._thread.start()

        async def connect() -> RemoteBlobStore:
            reader, writer = await asyncio.open_connection(sock=client_sock)
            conn = AsyncioRpcConnections.of_streams(reader, writer)
            await conn.start()
            return await RemoteBlobStore.connect(conn, **store_kwargs)

        self.store = self.loop.run_until_complete(connect())

    def close(self) -> None:
        try:
            self.loop.run_until_complete(self.store.connection.close())
            self._thread.join(10.)
            if self._thread.is_alive():
                raise RuntimeError('remote blob store server did not stop')
        finally:
            self._server_sock.close()
            self.loop.close()
