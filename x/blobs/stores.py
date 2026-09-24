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


class BlobWriter(lang.Abstract):
    """
    Nothing is visible until commit(), which applies the writer's precondition atomically. Leaving the open_writer
    context without committing discards everything written - on a normal exit too, not just on an exception.
    """

    @abc.abstractmethod
    def write(self, data: bytes) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def commit(self) -> BlobVersion:
        raise NotImplementedError


class BlobStore(lang.Abstract):
    """
    A flat keyspace of immutable, atomically replaced objects. '/' means nothing except to list_shallow. Listings are
    in code point order, which is UTF-8 byte order, which is what S3 and R2 use.
    """

    @abc.abstractmethod
    def capabilities(self) -> BlobCapability:
        raise NotImplementedError

    @abc.abstractmethod
    def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        raise NotImplementedError

    @abc.abstractmethod
    def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.Iterator[BlobInfo]:
        raise NotImplementedError

    @abc.abstractmethod
    def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.Iterator[BlobInfo | BlobPrefix]:
        raise NotImplementedError

    @abc.abstractmethod
    def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        raise NotImplementedError

    @abc.abstractmethod
    def open_writer(self, key: str, *, cond: BlobWritePrecondition | None = None) -> ta.ContextManager[BlobWriter]:
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        """The precondition applies to dst."""

        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        """Unconditionally deleting a missing key is a no-op, as on S3."""

        raise NotImplementedError
