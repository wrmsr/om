import abc
import os
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True, kw_only=True)
class FsDirEntry:
    name: str
    path: str

    is_dir: bool
    is_file: bool
    is_symlink: bool


class FsOps(lang.Abstract):
    @abc.abstractmethod
    def read_file(self, path: str) -> ta.Awaitable[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def write_file(self, path: str, content: lang.BytesLike) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_dir(self, path: str) -> list[FsDirEntry]:
        raise NotImplementedError


##


class LocalFsOps(FsOps):
    async def read_file(self, path: str) -> bytes:
        with open(path, 'rb') as f:  # noqa
            return f.read()

    async def write_file(self, path: str, content: lang.BytesLike) -> None:
        with open(path, 'wb') as f:  # noqa
            f.write(content)

    async def list_dir(self, path: str) -> list[FsDirEntry]:
        return [
            FsDirEntry(
                name=e.name,
                path=e.path,

                is_dir=e.is_dir(),
                is_file=e.is_file(),
                is_symlink=e.is_symlink(),
            )
            for e in os.scandir(path)
        ]
