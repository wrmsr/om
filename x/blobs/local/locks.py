import contextlib
import fcntl
import os
import typing as ta
import zlib


##


class StripedFileLocks:
    """
    Cross-process and cross-thread exclusive locks over a fixed pool of lock files, striped by key. The stripe is a
    crc32 of the key rather than hash(), which is randomized per process. Every acquisition opens its stripe file
    afresh, so each acquirer has its own open file description and flock excludes threads of the same process too.
    Lock files are created lazily and never deleted. Not reliable on NFS.
    """

    def __init__(self, dir_path: str, *, stripes: int = 256) -> None:
        super().__init__()

        if stripes < 1:
            raise ValueError(stripes)

        self._dir_path = dir_path
        self._stripes = stripes
        self._width = len(f'{stripes - 1:x}')

    def stripe(self, key: str) -> int:
        return zlib.crc32(key.encode('utf-8')) % self._stripes

    def path(self, key: str) -> str:
        return os.path.join(self._dir_path, f'{self.stripe(key):0{self._width}x}.lock')

    @contextlib.contextmanager
    def lock(self, key: str, *, no_block: bool = False) -> ta.Iterator[bool]:
        """Yields whether the lock was acquired, which is always True unless no_block is set."""

        fd = os.open(self.path(key), os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o644)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | (fcntl.LOCK_NB if no_block else 0))
            except BlockingIOError:
                yield False
                return
            yield True
        finally:
            # Closing the descriptor releases the lock.
            os.close(fd)
