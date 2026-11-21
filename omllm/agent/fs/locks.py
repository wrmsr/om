import contextlib
import typing as ta

from omcore.asyncs.asynclite import all as asl


##


class FsPathLocks:
    """
    Per-path async locks serializing read-modify-write tool calls targeting the same canonical file path (such as
    parallel `edit` calls in one assistant message) while allowing operations on distinct files to run concurrently.
    Entries are ref-counted and removed once no waiters remain.
    """

    class _Entry:
        __slots__ = (
            'lock',
            'waiters',
        )

        def __init__(self, lock: asl.Lock) -> None:
            super().__init__()

            self.lock = lock
            self.waiters = 0

    def __init__(self, locks: asl.Locks) -> None:
        super().__init__()

        self._locks = locks
        self._entries: dict[str, FsPathLocks._Entry] = {}

    @contextlib.asynccontextmanager
    async def lock(self, path: str) -> ta.AsyncIterator[None]:
        entry = self._entries.get(path)
        if entry is None:
            entry = self._entries[path] = self._Entry(self._locks.make_lock())

        entry.waiters += 1
        try:
            async with entry.lock:
                yield
        finally:
            entry.waiters -= 1
            if entry.waiters == 0 and self._entries.get(path) is entry:
                del self._entries[path]
