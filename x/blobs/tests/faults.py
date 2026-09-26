import contextlib
import re
import threading
import typing as ta

from omcore import dataclasses as dc

from ..asyncs import AsyncBlobStore
from ..asyncs import AsyncBlobWriter
from ..caps import BlobCapability
from ..errors import BlobIndeterminateError
from ..types import Blob
from ..types import BlobInfo
from ..types import BlobPrefix
from ..types import BlobRange
from ..types import BlobReadPrecondition
from ..types import BlobVersion
from ..types import BlobWritePrecondition
from ..types import IfMatch


T = ta.TypeVar('T')


##


@dc.dataclass(frozen=True, kw_only=True)
class BlobFault:
    op: str  # put, put_stream, get, head, list, copy, delete, delete_many, commit
    key: str | re.Pattern[str] | None = None  # None matches any key
    nth: int = 0  # fire on the nth matching call
    after: bool = False  # False: delegate not called; True: called, result discarded
    side_effect: ta.Callable[[AsyncBlobStore], ta.Awaitable[None]] | None = None  # e.g. a rival write, run first
    error: ta.Callable[[str], BaseException] = BlobIndeterminateError

    def matches(self, op: str, key: str) -> bool:
        if op != self.op:
            return False
        if self.key is None:
            return True
        if isinstance(self.key, str):
            return key == self.key
        return self.key.fullmatch(key) is not None


class _FaultState:
    def __init__(self, fault: BlobFault) -> None:
        self.fault = fault
        self.seen = 0
        self.fired = False


class FaultInjectingBlobStore(AsyncBlobStore):
    """Wraps a store, failing scripted calls either before or after delegating them. Each fault fires once."""

    def __init__(self, store: AsyncBlobStore, faults: ta.Iterable[BlobFault] = ()) -> None:
        super().__init__()

        self._store = store
        self._lock = threading.Lock()
        self._faults: list[_FaultState] = [_FaultState(f) for f in faults]

    @property
    def store(self) -> AsyncBlobStore:
        return self._store

    def add_fault(self, fault: BlobFault) -> None:
        with self._lock:
            self._faults.append(_FaultState(fault))

    def pending_faults(self) -> list[BlobFault]:
        with self._lock:
            return [fs.fault for fs in self._faults if not fs.fired]

    def _match(self, op: str, key: str) -> BlobFault | None:
        with self._lock:
            for fs in self._faults:
                if fs.fired or not fs.fault.matches(op, key):
                    continue
                n = fs.seen
                fs.seen += 1
                if n == fs.fault.nth:
                    fs.fired = True
                    return fs.fault
        return None

    async def _call(self, op: str, key: str, fn: ta.Callable[[], ta.Awaitable[T]]) -> T:
        if (f := self._match(op, key)) is None:
            return await fn()
        if f.side_effect is not None:
            await f.side_effect(self._store)
        if f.after:
            await fn()
        raise f.error(key)

    #

    def capabilities(self) -> BlobCapability:
        return self._store.capabilities()

    async def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        return await self._call('head', key, lambda: self._store.head(key, cond=cond))

    async def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        return await self._call('get', key, lambda: self._store.get(key, byte_range=byte_range, cond=cond))

    async def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.AsyncIterator[BlobInfo]:
        if (f := self._match('list', prefix)) is not None:
            raise f.error(prefix)
        async for info in self._store.list(prefix=prefix, start_after=start_after):
            yield info

    async def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.AsyncIterator[BlobInfo | BlobPrefix]:
        if (f := self._match('list', prefix)) is not None:
            raise f.error(prefix)
        async for e in self._store.list_shallow(prefix=prefix, delimiter=delimiter):
            yield e

    async def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return await self._call('put', key, lambda: self._store.put(key, data, cond=cond))

    async def put_stream(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        return await self._call(
            'put_stream',
            key,
            lambda: self._store.put_stream(key, source, length=length, cond=cond),
        )

    @contextlib.asynccontextmanager
    async def open_writer(
            self,
            key: str,
            *,
            cond: BlobWritePrecondition | None = None,
    ) -> ta.AsyncIterator[AsyncBlobWriter]:
        async with self._store.open_writer(key, cond=cond) as w:
            yield _FaultInjectingBlobWriter(self, key, w)

    async def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return await self._call('copy', dst, lambda: self._store.copy(src, dst, cond=cond))

    async def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        await self._call('delete', key, lambda: self._store.delete(key, cond=cond))

    async def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = list(keys)
        for k in ks:
            if (f := self._match('delete_many', k)) is not None:
                if f.after:
                    await self._store.delete_many(ks)
                raise f.error(k)
        await self._store.delete_many(ks)


class _FaultInjectingBlobWriter(AsyncBlobWriter):
    def __init__(self, owner: FaultInjectingBlobStore, key: str, w: AsyncBlobWriter) -> None:
        super().__init__()

        self._owner = owner
        self._key = key
        self._w = w

    async def write(self, data: bytes) -> None:
        await self._w.write(data)

    async def commit(self) -> BlobVersion:
        return await self._owner._call('commit', self._key, self._w.commit)  # noqa
