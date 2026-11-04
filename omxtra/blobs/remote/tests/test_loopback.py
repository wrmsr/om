"""
The remote store's own behavior, over a deterministic in-process link: the client and service in one thread, the
service's store a dict store with faults injected where a test needs them.
"""
import typing as ta

import pytest

from omcore.lite.asyncs import sync_await
from omcore.rpc.dispatch import RpcMethodTableHandler
from omcore.rpc.pure import PureRpcConnectionPair
from omcore.rpc.pure import pure_rpc_connection_pair

from ...adapters import AsyncToSyncBlobStore
from ...caps import BlobCapability
from ...dicts import DictBlobStore
from ...errors import BlobConflictError
from ...errors import BlobDeleteManyError
from ...errors import BlobIndeterminateError
from ...errors import BlobNotFoundError
from ...errors import BlobPreconditionFailedError
from ...errors import BlobStoreError
from ...errors import BlobStreamLengthError
from ...errors import BlobTransportError
from ...errors import InvalidBlobKeyError
from ...errors import UnsupportedBlobOperationError
from ...types import Blob
from ...types import BlobIfAbsent
from ...types import BlobIfMatch
from ...types import BlobPrefix
from ...types import BlobRange
from ...types import BlobReadPrecondition
from ...types import BlobVersion
from ...types import BlobWritePrecondition
from ...types import OffsetBlobRange
from ...types import SuffixBlobRange
from ..client import RemoteBlobStore
from ..protocol import REMOTE_BLOBS_ERROR_TYPE_PREFIX
from ..protocol import remote_blob_error_of
from ..protocol import remote_blob_error_type
from ..server import RemoteBlobStoreService


T = ta.TypeVar('T')


##


class _FaultyDictBlobStore(DictBlobStore):
    def __init__(self, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)

        self.gets = 0
        self.on_get: ta.Callable[[int], None] | None = None
        self.on_put: ta.Callable[[], None] | None = None
        self.delete_failures: dict[str, BlobStoreError] = {}

    def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        self.gets += 1
        if (f := self.on_get) is not None:
            f(self.gets)
        return super().get(key, byte_range=byte_range, cond=cond)

    def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        if (f := self.on_put) is not None:
            f()
        return super().put(key, data, cond=cond)

    def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = list(keys)
        super().delete_many([k for k in ks if k not in self.delete_failures])
        if errs := {k: e for k, e in self.delete_failures.items() if k in ks}:
            raise BlobDeleteManyError(errs)


class _Fixture(ta.NamedTuple):
    pair: PureRpcConnectionPair
    backing: _FaultyDictBlobStore
    service: RemoteBlobStoreService
    store: RemoteBlobStore

    def run(self, aw: ta.Awaitable[T]) -> T:
        return sync_await(aw)

    def moved(self) -> int:
        return sum(self.pair.link.moved)


def _fixture(
        *,
        capabilities: BlobCapability | None = None,
        chunk_bytes: int = 10,
        page_size: int = 3,
) -> _Fixture:
    backing = _FaultyDictBlobStore(**({'capabilities': capabilities} if capabilities is not None else {}))
    service = RemoteBlobStoreService(backing)
    pair = pure_rpc_connection_pair(b_kwargs=dict(handler=RpcMethodTableHandler(service.method_table())))
    pair.b.add_close_callback(service.close)
    store = sync_await(RemoteBlobStore.connect(pair.a.connection, chunk_bytes=chunk_bytes, page_size=page_size))
    return _Fixture(pair, backing, service, store)


DATA = bytes(range(100))


##


def test_errors_cross_as_their_own_classes():
    for e in [BlobNotFoundError('k'), BlobPreconditionFailedError('k'), InvalidBlobKeyError('k')]:
        t = remote_blob_error_type(e)
        assert t == REMOTE_BLOBS_ERROR_TYPE_PREFIX + type(e).__name__
        r = remote_blob_error_of(t, str(e))
        assert type(r) is type(e)
        assert str(r) == str(e)

    class _UnknownNotFoundError(BlobNotFoundError):
        pass

    # A subclass the wire does not know crosses as its nearest known class.
    assert remote_blob_error_type(_UnknownNotFoundError('k')) == REMOTE_BLOBS_ERROR_TYPE_PREFIX + 'BlobNotFoundError'
    assert remote_blob_error_of('builtins.ValueError', 'x') is None


def test_chunked_reads_and_ranges():
    f = _fixture()
    f.run(f.store.put('k', DATA))

    for r, want in [
        (None, DATA),
        (OffsetBlobRange(5), DATA[5:]),
        (OffsetBlobRange(5, 37), DATA[5:37]),
        (OffsetBlobRange(95, 1_000), DATA[95:]),
        (OffsetBlobRange(500), b''),
        (SuffixBlobRange(23), DATA[-23:]),
        (SuffixBlobRange(1_000), DATA),
    ]:
        b = f.run(f.store.get('k', byte_range=r))
        assert b.data == want, r
        assert b.info.size == len(DATA)


def test_read_replaced_midway_starts_over():
    f = _fixture()
    f.run(f.store.put('k', DATA))

    def on_get(n: int) -> None:
        if n == 2:
            # Between the first chunk and the second.
            f.backing.put('k', DATA[::-1])

    f.backing.on_get = on_get
    b = f.run(f.store.get('k'))
    assert b.data == DATA[::-1]
    assert b.info.version == f.backing.head('k').version


def test_read_replaced_with_callers_version_fails():
    f = _fixture()
    v = f.run(f.store.put('k', DATA))

    def on_get(n: int) -> None:
        if n == 2:
            f.backing.put('k', DATA[::-1])

    f.backing.on_get = on_get
    with pytest.raises(BlobPreconditionFailedError):
        f.run(f.store.get('k', cond=BlobIfMatch(v)))


def test_read_replaced_endlessly_gives_up():
    f = _fixture()
    f.run(f.store.put('k', DATA))

    def on_get(n: int) -> None:
        if n % 2 == 0:
            f.backing.put('k', bytes([n % 256]) * 100)

    f.backing.on_get = on_get
    with pytest.raises(BlobConflictError):
        f.run(f.store.get('k'))


def test_listings_page():
    f = _fixture(page_size=3)
    keys = [f'k/{i:02d}' for i in range(10)] + ['a', 'z/x/y']
    for k in keys:
        f.backing.put(k, b'x')

    async def deep(**kw: ta.Any) -> list[str]:
        return [i.key async for i in f.store.list(**kw)]

    async def shallow(**kw: ta.Any) -> list[str]:
        return [e.prefix if isinstance(e, BlobPrefix) else e.key async for e in f.store.list_shallow(**kw)]

    assert f.run(deep()) == sorted(keys)
    assert f.run(deep(prefix='k/', start_after='k/04')) == [f'k/{i:02d}' for i in range(5, 10)]
    assert f.run(shallow()) == ['a', 'k/', 'z/']
    assert f.run(shallow(prefix='k/')) == [f'k/{i:02d}' for i in range(10)]


def test_large_writes_go_through_a_writer():
    f = _fixture(chunk_bytes=10)
    v = f.run(f.store.put('k', DATA, cond=BlobIfAbsent()))
    assert f.backing.get('k').data == DATA
    assert f.backing.head('k').version == v
    assert f.service.num_open_writers == 0

    with pytest.raises(BlobPreconditionFailedError):
        f.run(f.store.put('k', DATA, cond=BlobIfAbsent()))
    assert f.service.num_open_writers == 0


def test_abandoned_writers_publish_nothing():
    f = _fixture()

    async def abandon() -> None:
        async with f.store.open_writer('k') as w:
            await w.write(DATA)

    f.run(abandon())
    assert f.service.num_open_writers == 0
    with pytest.raises(BlobNotFoundError):
        f.backing.head('k')

    async def chunks() -> ta.AsyncIterator[bytes]:
        for i in range(0, len(DATA), 7):
            yield DATA[i:i + 7]

    with pytest.raises(BlobStreamLengthError):
        f.run(f.store.put_stream('k', chunks(), length=len(DATA) + 1))
    assert f.service.num_open_writers == 0
    with pytest.raises(BlobNotFoundError):
        f.backing.head('k')

    assert f.run(f.store.put_stream('k', chunks(), length=len(DATA))) == f.backing.head('k').version


def test_writers_of_a_closed_connection_are_discarded():
    f = _fixture()

    async def start() -> None:
        w = await f.store._begin_writer('k', None)  # noqa
        await w.write(DATA)

    f.run(start())
    assert f.service.num_open_writers == 1

    f.pair.a.close()
    f.pair.b.wait_closed()
    assert f.service.num_open_writers == 0
    with pytest.raises(BlobNotFoundError):
        f.backing.head('k')


def test_static_checks_precede_any_call():
    f = _fixture(capabilities=BlobCapability.PUT_IF_ABSENT)
    before = f.moved()

    for aw in [
        f.store.get('a//b'),
        f.store.head('/a'),
        f.store.put('a/', b'x'),
        f.store.delete_many(['ok', 'bad/']),
        f.store.copy('a', 'a'),
    ]:
        with pytest.raises(ValueError):  # noqa
            f.run(aw)

    for aw in [
        f.store.put('k', b'x', cond=BlobIfMatch(BlobVersion('v'))),
        f.store.copy('a', 'b', cond=BlobIfAbsent()),
        f.store.delete('k', cond=BlobIfMatch(BlobVersion('v'))),
    ]:
        with pytest.raises(UnsupportedBlobOperationError):
            f.run(aw)

    assert f.moved() == before


def test_delete_many_batches_and_gathers_failures():
    f = _fixture(page_size=3)
    keys = [f'k{i}' for i in range(8)]
    for k in keys:
        f.backing.put(k, b'x')
    f.backing.delete_failures = {'k1': BlobPreconditionFailedError('k1'), 'k6': BlobStoreError('boom')}

    with pytest.raises(BlobDeleteManyError) as ei:
        f.run(f.store.delete_many(keys))
    assert {k: type(e) for k, e in ei.value.errors.items()} == {
        'k1': BlobPreconditionFailedError,
        'k6': BlobStoreError,
    }
    assert sorted(i.key for i in f.backing.list()) == ['k1', 'k6']


def test_connection_failures():
    f = _fixture()
    f.run(f.store.put('k', b'x'))

    # A mutation in flight when the connection dies may or may not have happened.
    def die() -> None:
        f.pair.link.close()

    f.backing.on_put = die
    with pytest.raises(BlobIndeterminateError):
        f.run(f.store.put('k', b'y'))

    # Calls on a connection known closed never left.
    f.pair.a.wait_closed()
    for aw in [f.store.get('k'), f.store.put('k', b'z')]:
        with pytest.raises(BlobTransportError):
            f.run(aw)


def test_sync_facade():
    f = _fixture()
    st = AsyncToSyncBlobStore(f.store)
    v = st.put('a/b', DATA)
    assert st.get('a/b').data == DATA
    assert [i.key for i in st.list()] == ['a/b']
    with st.open_writer('c', cond=BlobIfAbsent()) as w:
        w.write(DATA)
        assert w.commit() != v
    assert st.get('c').data == DATA
