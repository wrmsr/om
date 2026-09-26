import abc
import typing as ta

from omcore import lang

from .caps import BlobCapability
from .types import Blob
from .types import BlobInfo
from .types import BlobPrefix
from .types import BlobRange
from .types import BlobReadPrecondition
from .types import BlobVersion
from .types import BlobWritePrecondition
from .types import IfMatch


##


class AsyncBlobWriter(lang.Abstract):
    """The async mirror of BlobWriter - see its docstring for semantics."""

    @abc.abstractmethod
    def write(self, data: bytes) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def commit(self) -> ta.Awaitable[BlobVersion]:
        raise NotImplementedError


class AsyncBlobStore(lang.Abstract):
    """The async mirror of BlobStore - see its docstrings for semantics."""

    @abc.abstractmethod
    def capabilities(self) -> BlobCapability:
        raise NotImplementedError

    @abc.abstractmethod
    def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> ta.Awaitable[BlobInfo]:
        raise NotImplementedError

    @abc.abstractmethod
    def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> ta.Awaitable[Blob]:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.AsyncIterator[BlobInfo]:
        raise NotImplementedError

    @abc.abstractmethod
    def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.AsyncIterator[BlobInfo | BlobPrefix]:
        raise NotImplementedError

    @abc.abstractmethod
    def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> ta.Awaitable[BlobVersion]:
        raise NotImplementedError

    @abc.abstractmethod
    def put_stream(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> ta.Awaitable[BlobVersion]:
        raise NotImplementedError

    @abc.abstractmethod
    def open_writer(
            self,
            key: str,
            *,
            cond: BlobWritePrecondition | None = None,
    ) -> ta.AsyncContextManager[AsyncBlobWriter]:
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> ta.Awaitable[BlobVersion]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, key: str, *, cond: IfMatch | None = None) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_many(self, keys: ta.Iterable[str]) -> ta.Awaitable[None]:
        raise NotImplementedError
