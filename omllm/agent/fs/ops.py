import abc
import typing as ta

from omcore import lang


##


class FsOps(lang.Abstract):
    @abc.abstractmethod
    def read_file(self, path: str) -> ta.Awaitable[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def write_file(self, path: str, content: lang.BytesLike) -> ta.Awaitable[None]:
        raise NotImplementedError


##


class LocalFsOps(FsOps):
    async def read_file(self, path: str) -> bytes:
        with open(path, 'rb') as f:  # noqa
            return f.read()

    async def write_file(self, path: str, content: lang.BytesLike) -> None:
        with open(path, 'wb') as f:  # noqa
            f.write(content)
