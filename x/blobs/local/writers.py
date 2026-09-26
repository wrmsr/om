import os
import typing as ta
import uuid

from omcore import check

from ..stores import BlobWriter
from ..types import BlobVersion


##


class LocalTmpFile:
    """An in-flight write: a uniquely named file in the store's tmp directory, kept open until commit or discard."""

    def __init__(self, tmp_dir: str) -> None:
        super().__init__()

        self._path = os.path.join(tmp_dir, f'{uuid.uuid7().hex}.tmp')
        self._fd: int | None = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_CLOEXEC, 0o644)
        self._size = 0

    @property
    def path(self) -> str:
        return self._path

    @property
    def fd(self) -> int:
        return check.not_none(self._fd)

    @property
    def size(self) -> int:
        return self._size

    def write(self, data: bytes) -> None:
        mv = memoryview(data)
        while mv:
            n = os.write(self.fd, mv)
            mv = mv[n:]
            self._size += n

    def close(self) -> None:
        if (fd := self._fd) is not None:
            self._fd = None
            os.close(fd)

    def discard(self) -> None:
        self.close()
        try:
            os.unlink(self._path)
        except FileNotFoundError:
            pass


class LocalBlobWriter(BlobWriter):
    def __init__(self, tmp: LocalTmpFile, commit: ta.Callable[[LocalTmpFile], BlobVersion]) -> None:
        super().__init__()

        self._tmp = tmp
        self._commit = commit
        self._done = False

    def close(self) -> None:
        if not self._done:
            self._done = True
            self._tmp.discard()

    def write(self, data: bytes) -> None:
        check.state(not self._done)
        self._tmp.write(data)

    def commit(self) -> BlobVersion:
        check.state(not self._done)
        self._done = True
        return self._commit(self._tmp)
