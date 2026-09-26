"""
The behavioral spec every AsyncBlobStore must pass. Backends subclass BlobStoreConformance (as `Test...Conformance`) and
override the `store` fixture - which must return an *empty* store, such as a fresh instance or a PrefixedBlobStore on a
unique prefix - and optionally the `runner` fixture and class attributes.
"""
import datetime
import typing as ta

import pytest

from ..asyncs import AsyncBlobStore
from ..caps import BlobCapability
from ..errors import BlobAlreadyExistsError
from ..errors import BlobConflictError
from ..errors import BlobNotFoundError
from ..errors import BlobNotModifiedError
from ..errors import BlobPreconditionFailedError
from ..errors import BlobStreamLengthError
from ..errors import InvalidBlobKeyError
from ..errors import UnsupportedBlobOperationError
from ..types import BlobPrefix
from ..types import BlobVersion
from ..types import IfAbsent
from ..types import IfMatch
from ..types import IfNoneMatch
from ..types import OffsetBlobRange
from ..types import SuffixBlobRange
from .runners import ScenarioRunner
from .runners import SyncAwaitScenarioRunner


T = ta.TypeVar('T')


##


AWKWARD_KEYS: ta.Sequence[str] = [
    'sp ace',
    'pl+us',
    'per%cent',
    'ha#sh',
    'que?ry',
    'amp&ersand',
    'eq=uals',
    'til~de',
    'st*ar',
    'quo\'te"s',
    'trailing.',
    'caf\u00e9',
    '\u65e5\u672c/\u8a9e',
    'emoji\U0001f600',
    'x.file',
    'x.dir',
    '%41',
    'A%41',
    'bang!(paren)',
    ',;:@$',
]

INVALID_KEYS: ta.Sequence[str] = ['', '/a', 'a/', 'a//b', 'a/./b', 'a/../b', 'a\x00b', 'a\x7f', 'x' * 1025, 'a\ufffe']


async def achunks(*bs: bytes) -> ta.AsyncIterator[bytes]:
    for b in bs:
        yield b


def data_of(n: int, seed: int = 0) -> bytes:
    return bytes((i * 7 + seed) % 251 for i in range(n))


async def list_keys(store: AsyncBlobStore, **kwargs: ta.Any) -> list[str]:
    return [i.key async for i in store.list(**kwargs)]


async def list_shallow_keys(store: AsyncBlobStore, **kwargs: ta.Any) -> list[str]:
    return [
        ('P:' + e.prefix) if isinstance(e, BlobPrefix) else e.key
        async for e in store.list_shallow(**kwargs)
    ]


def require(store: AsyncBlobStore, cap: BlobCapability) -> None:
    if not (store.capabilities() & cap):
        pytest.skip(f'store lacks {cap!r}')


def lacks(store: AsyncBlobStore, cap: BlobCapability) -> bool:
    return not (store.capabilities() & cap)


async def raises(exc: type[BaseException] | tuple[type[BaseException], ...], aw: ta.Awaitable[ta.Any]) -> BaseException:
    try:
        await aw
    except exc as e:
        return e
    raise AssertionError(f'expected {exc}')


##


class BlobStoreConformance:
    concurrency: ta.ClassVar[int] = 8
    cas_increments: ta.ClassVar[int] = 5
    large_size: ta.ClassVar[int] = 256 * 1024
    many_keys: ta.ClassVar[int] = 25
    xfail_astral_ordering: ta.ClassVar[bool] = False
    xfail_conditional_races: ta.ClassVar[bool] = False  # for backends whose preconditions are not atomic under races

    @pytest.fixture
    def store(self) -> AsyncBlobStore:
        raise NotImplementedError

    @pytest.fixture
    def runner(self) -> ScenarioRunner:
        return SyncAwaitScenarioRunner()

    ## Basics

    def test_round_trip(self, store, runner):
        async def inner():
            v = await store.put('a', b'hello')
            assert isinstance(v, BlobVersion)
            info = await store.head('a')
            assert info.key == 'a'
            assert info.size == 5
            assert info.version == v
            assert info.last_modified.tzinfo is not None
            assert info.last_modified.utcoffset() == datetime.timedelta(0)
            blob = await store.get('a')
            assert blob.data == b'hello'
            assert blob.info.version == v
            assert blob.info.size == 5

        runner.run(inner)

    def test_empty_object(self, store, runner):
        async def inner():
            v = await store.put('e', b'')
            assert (await store.head('e')).size == 0
            blob = await store.get('e')
            assert (blob.data, blob.info.version) == (b'', v)

        runner.run(inner)

    def test_large_object(self, store, runner):
        n = self.large_size
        data = data_of(n)

        async def inner():
            await store.put('p', data)
            assert (await store.get('p')).data == data

            cs = [data[i:i + 100_000] for i in range(0, n, 100_000)]
            await store.put_stream('s', achunks(*cs), length=n)
            assert (await store.get('s')).data == data

            async with store.open_writer('w') as w:
                for c in cs:
                    await w.write(c)
                await w.commit()
            got = await store.get('w')
            assert got.data == data
            assert got.info.size == n

        runner.run(inner)

    def test_versions_agree(self, store, runner):
        async def inner():
            v1 = await store.put('k', b'1')
            assert (await store.head('k')).version == v1
            assert (await store.get('k')).info.version == v1
            assert [i.version async for i in store.list(prefix='k')] == [v1]

            v2 = await store.put('k', b'2')
            assert v2 != v1
            assert (await store.head('k')).version == v2

            v3 = await store.put_stream('k', achunks(b'3', b'3'))
            assert v3 != v2
            assert (await store.head('k')).version == v3

            async with store.open_writer('k') as w:
                await w.write(b'4')
                v4 = await w.commit()
            assert v4 != v3
            assert (await store.head('k')).version == v4
            assert [i.version async for i in store.list(prefix='k')] == [v4]

            vc = await store.copy('k', 'k2')
            assert (await store.head('k2')).version == vc

        runner.run(inner)

    def test_missing(self, store, runner):
        async def inner():
            await raises(BlobNotFoundError, store.get('nope'))
            await raises(BlobNotFoundError, store.head('nope'))
            await raises(BlobNotFoundError, store.get('nope', byte_range=OffsetBlobRange(1, 2)))

        runner.run(inner)

    def test_awkward_keys(self, store, runner):
        async def inner():
            for _i, k in enumerate(AWKWARD_KEYS):
                await store.put(k, k.encode())
            assert await list_keys(store) == sorted(AWKWARD_KEYS)
            for k in AWKWARD_KEYS:
                assert (await store.get(k)).data == k.encode()
                assert (await store.head(k)).key == k
            for k in AWKWARD_KEYS:
                await store.copy(k, 'copies/' + k)
                assert (await store.get('copies/' + k)).data == k.encode()
            for k in AWKWARD_KEYS:
                await store.delete(k)
            assert await list_keys(store) == sorted('copies/' + k for k in AWKWARD_KEYS)

        runner.run(inner)

    def test_case_distinct(self, store, runner):
        async def inner():
            await store.put('A', b'upper')
            await store.put('a', b'lower')
            await store.put('D/x', b'upper-dir')
            await store.put('d/x', b'lower-dir')
            assert (await store.get('A')).data == b'upper'
            assert (await store.get('a')).data == b'lower'
            assert (await store.get('D/x')).data == b'upper-dir'
            assert (await store.get('d/x')).data == b'lower-dir'
            assert await list_keys(store) == ['A', 'D/x', 'a', 'd/x']

        runner.run(inner)

    def test_object_and_prefix_coexist(self, store, runner):
        async def inner():
            await store.put('a', b'1')
            await store.put('a/b', b'2')
            await store.put('a/b/c', b'3')
            assert await list_keys(store) == ['a', 'a/b', 'a/b/c']
            await store.delete('a/b')
            assert await list_keys(store) == ['a', 'a/b/c']
            assert (await store.get('a/b/c')).data == b'3'
            await store.delete('a')
            assert await list_keys(store) == ['a/b/c']
            await store.put('a/b', b'4')
            assert (await store.get('a/b')).data == b'4'

        runner.run(inner)

    def test_long_keys(self, store, runner):
        async def inner():
            segs = [f'{i:03d}' + 'x' * 190 for i in range(5)]
            k = '/'.join(segs)
            assert len(k.encode()) > 960
            await store.put(k, b'long')
            assert (await store.get(k)).data == b'long'
            assert await list_keys(store) == [k]
            k2 = '/'.join([*segs[:4], '\u00e9' * 12])
            await store.put(k2, b'long2')
            assert (await store.get(k2)).data == b'long2'

        runner.run(inner)

    def test_invalid_keys(self, store, runner):
        async def inner():
            await store.put('ok', b'')
            for k in INVALID_KEYS:
                await raises(InvalidBlobKeyError, store.put(k, b''))
                await raises(InvalidBlobKeyError, store.put_stream(k, achunks(b'')))
                await raises(InvalidBlobKeyError, store.get(k))
                await raises(InvalidBlobKeyError, store.head(k))
                await raises(InvalidBlobKeyError, store.delete(k))
                await raises(InvalidBlobKeyError, store.copy('ok', k))
                await raises(InvalidBlobKeyError, store.copy(k, 'ok2'))
                await raises(InvalidBlobKeyError, store.delete_many(['ok', k]))

                async def open_writer(k=k):
                    async with store.open_writer(k):
                        pass

                await raises(InvalidBlobKeyError, open_writer())
            assert await list_keys(store) == ['ok']

        runner.run(inner)

    ## Ranges

    def test_ranges(self, store, runner):
        async def inner():
            await store.put('k', b'0123456789')

            async def rng(br):
                b = await store.get('k', byte_range=br)
                assert b.info.size == 10
                return b.data

            assert await rng(OffsetBlobRange(2, 5)) == b'234'
            assert await rng(OffsetBlobRange(0, 10)) == b'0123456789'
            assert await rng(OffsetBlobRange(0)) == b'0123456789'
            assert await rng(OffsetBlobRange(7)) == b'789'
            assert await rng(OffsetBlobRange(8, 100)) == b'89'
            assert await rng(OffsetBlobRange(9, 10)) == b'9'
            assert await rng(OffsetBlobRange(10)) == b''
            assert await rng(OffsetBlobRange(10, 12)) == b''
            assert await rng(OffsetBlobRange(50)) == b''
            assert await rng(SuffixBlobRange(3)) == b'789'
            assert await rng(SuffixBlobRange(10)) == b'0123456789'
            assert await rng(SuffixBlobRange(100)) == b'0123456789'

        runner.run(inner)

    def test_ranges_empty_object(self, store, runner):
        async def inner():
            v = await store.put('e', b'')
            for br in [OffsetBlobRange(0), OffsetBlobRange(0, 5), OffsetBlobRange(3), SuffixBlobRange(5)]:
                b = await store.get('e', byte_range=br)
                assert (b.data, b.info.size, b.info.version) == (b'', 0, v)

        runner.run(inner)

    def test_range_with_if_match(self, store, runner):
        async def inner():
            v1 = await store.put('k', b'0123456789')
            assert (await store.get('k', byte_range=OffsetBlobRange(1, 3), cond=IfMatch(v1))).data == b'12'
            await store.put('k', b'abcdefghij')
            await raises(
                BlobPreconditionFailedError,
                store.get('k', byte_range=OffsetBlobRange(1, 3), cond=IfMatch(v1)),
            )
            await raises(
                BlobPreconditionFailedError,
                store.get('k', byte_range=OffsetBlobRange(20), cond=IfMatch(v1)),
            )

        runner.run(inner)

    ## Read preconditions

    def test_read_if_match(self, store, runner):
        async def inner():
            v1 = await store.put('k', b'1')
            v2 = await store.put('k', b'2')
            assert (await store.get('k', cond=IfMatch(v2))).data == b'2'
            assert (await store.head('k', cond=IfMatch(v2))).version == v2
            await raises(BlobPreconditionFailedError, store.get('k', cond=IfMatch(v1)))
            await raises(BlobPreconditionFailedError, store.head('k', cond=IfMatch(v1)))
            e = await raises(BlobPreconditionFailedError, store.get('missing', cond=IfMatch(v2)))
            assert not isinstance(e, BlobNotFoundError)
            await raises(BlobPreconditionFailedError, store.head('missing', cond=IfMatch(v2)))

        runner.run(inner)

    def test_read_if_none_match(self, store, runner):
        async def inner():
            v1 = await store.put('k', b'1')
            v2 = await store.put('k', b'2')
            await raises(BlobNotModifiedError, store.get('k', cond=IfNoneMatch(v2)))
            await raises(BlobNotModifiedError, store.head('k', cond=IfNoneMatch(v2)))
            assert (await store.get('k', cond=IfNoneMatch(v1))).data == b'2'
            assert (await store.head('k', cond=IfNoneMatch(v1))).version == v2
            await raises(BlobNotFoundError, store.get('missing', cond=IfNoneMatch(v1)))
            await raises(BlobNotFoundError, store.head('missing', cond=IfNoneMatch(v1)))

        runner.run(inner)

    ## Write preconditions

    def test_put_if_absent(self, store, runner):
        require(store, BlobCapability.PUT_IF_ABSENT)

        async def inner():
            await store.put('k', b'first', cond=IfAbsent())
            try:
                await store.put('k', b'second', cond=IfAbsent())
            except BlobAlreadyExistsError:
                pass
            else:
                raise AssertionError('backend claims PUT_IF_ABSENT but accepted a second IfAbsent put')
            await raises(BlobAlreadyExistsError, store.put_stream('k', achunks(b'x'), cond=IfAbsent()))
            assert (await store.get('k')).data == b'first'
            await store.put_stream('k2', achunks(b'a', b'b'), cond=IfAbsent())
            assert (await store.get('k2')).data == b'ab'

        runner.run(inner)

    def test_put_if_match(self, store, runner):
        require(store, BlobCapability.PUT_IF_MATCH)

        async def inner():
            v1 = await store.put('k', b'1')
            v2 = await store.put('k', b'2', cond=IfMatch(v1))
            try:
                await store.put('k', b'3', cond=IfMatch(v1))
            except BlobPreconditionFailedError:
                pass
            else:
                raise AssertionError('backend claims PUT_IF_MATCH but accepted a stale IfMatch put')
            await raises(BlobPreconditionFailedError, store.put_stream('k', achunks(b'3'), cond=IfMatch(v1)))
            e = await raises(BlobPreconditionFailedError, store.put('missing', b'x', cond=IfMatch(v2)))
            assert not isinstance(e, BlobAlreadyExistsError)
            assert (await store.get('k')).data == b'2'
            await raises(BlobNotFoundError, store.head('missing'))
            v3 = await store.put_stream('k', achunks(b'3'), cond=IfMatch(v2))
            assert (await store.head('k')).version == v3

        runner.run(inner)

    def test_delete_if_match(self, store, runner):
        require(store, BlobCapability.DELETE_IF_MATCH)

        async def inner():
            v1 = await store.put('k', b'1')
            v2 = await store.put('k', b'2')
            try:
                await store.delete('k', cond=IfMatch(v1))
            except BlobPreconditionFailedError:
                pass
            else:
                raise AssertionError('backend claims DELETE_IF_MATCH but accepted a stale IfMatch delete')
            assert (await store.get('k')).data == b'2'
            await store.delete('k', cond=IfMatch(v2))
            await raises(BlobNotFoundError, store.head('k'))
            await raises(BlobPreconditionFailedError, store.delete('k', cond=IfMatch(v2)))

        runner.run(inner)

    def test_unconditional_delete_missing(self, store, runner):
        async def inner():
            await store.delete('missing')
            await store.put('k', b'')
            await store.delete('k')
            await store.delete('k')
            await raises(BlobNotFoundError, store.head('k'))

        runner.run(inner)

    def test_copy(self, store, runner):
        async def inner():
            await store.put('src', b'data')
            v = await store.copy('src', 'dst')
            assert (await store.get('dst')).data == b'data'
            assert (await store.head('dst')).version == v
            await store.put('dst', b'other')
            await store.copy('src', 'dst')
            assert (await store.get('dst')).data == b'data'
            await raises(BlobNotFoundError, store.copy('missing', 'dst2'))
            await raises(BlobNotFoundError, store.head('dst2'))
            await raises(ValueError, store.copy('src', 'src'))

        runner.run(inner)

    def test_copy_if_absent(self, store, runner):
        require(store, BlobCapability.COPY_IF_ABSENT)

        async def inner():
            await store.put('src', b'data')
            await store.put('taken', b'mine')
            await store.copy('src', 'dst', cond=IfAbsent())
            assert (await store.get('dst')).data == b'data'
            try:
                await store.copy('src', 'taken', cond=IfAbsent())
            except BlobAlreadyExistsError:
                pass
            else:
                raise AssertionError('backend claims COPY_IF_ABSENT but overwrote an existing destination')
            assert (await store.get('taken')).data == b'mine'
            await raises(BlobNotFoundError, store.copy('missing', 'dst3', cond=IfAbsent()))

        runner.run(inner)

    def test_copy_if_match(self, store, runner):
        require(store, BlobCapability.COPY_IF_MATCH)

        async def inner():
            await store.put('src', b'data')
            v1 = await store.put('dst', b'1')
            v2 = await store.put('dst', b'2')
            try:
                await store.copy('src', 'dst', cond=IfMatch(v1))
            except BlobPreconditionFailedError:
                pass
            else:
                raise AssertionError('backend claims COPY_IF_MATCH but accepted a stale destination IfMatch')
            assert (await store.get('dst')).data == b'2'
            await store.copy('src', 'dst', cond=IfMatch(v2))
            assert (await store.get('dst')).data == b'data'
            await raises(BlobPreconditionFailedError, store.copy('src', 'missing', cond=IfMatch(v2)))
            await raises(BlobNotFoundError, store.copy('nosrc', 'dst', cond=IfMatch(v2)))

        runner.run(inner)

    def test_unsupported_capabilities(self, store, runner):
        async def inner():
            v = await store.put('k', b'1')
            await store.put('src', b's')
            if lacks(store, BlobCapability.PUT_IF_ABSENT):
                await raises(UnsupportedBlobOperationError, store.put('n', b'', cond=IfAbsent()))
                await raises(UnsupportedBlobOperationError, store.put_stream('n', achunks(b''), cond=IfAbsent()))
            if lacks(store, BlobCapability.PUT_IF_MATCH):
                await raises(UnsupportedBlobOperationError, store.put('k', b'2', cond=IfMatch(v)))
            if lacks(store, BlobCapability.DELETE_IF_MATCH):
                await raises(UnsupportedBlobOperationError, store.delete('k', cond=IfMatch(v)))
            if lacks(store, BlobCapability.COPY_IF_ABSENT):
                await raises(UnsupportedBlobOperationError, store.copy('src', 'n', cond=IfAbsent()))
            if lacks(store, BlobCapability.COPY_IF_MATCH):
                await raises(UnsupportedBlobOperationError, store.copy('src', 'k', cond=IfMatch(v)))
            assert (await store.get('k')).data == b'1'
            assert await list_keys(store) == ['k', 'src']

        runner.run(inner)

    ## Writers and put_stream

    def test_writer_discards_without_commit(self, store, runner):
        async def inner():
            async with store.open_writer('w') as w:
                await w.write(b'x')
            await raises(BlobNotFoundError, store.head('w'))

            async def fail():
                async with store.open_writer('w') as w:
                    await w.write(b'x')
                    raise KeyError('boom')

            await raises(KeyError, fail())
            await raises(BlobNotFoundError, store.head('w'))
            assert await list_keys(store) == []

        runner.run(inner)

    def test_writer_commit(self, store, runner):
        async def inner():
            async with store.open_writer('w') as w:
                await w.write(b'ab')
                await w.write(b'')
                await w.write(b'cd')
                v = await w.commit()
            got = await store.get('w')
            assert (got.data, got.info.version) == (b'abcd', v)

            async with store.open_writer('empty') as w:
                await w.commit()
            assert (await store.get('empty')).data == b''

        runner.run(inner)

    def test_writer_precondition_at_commit(self, store, runner):
        require(store, BlobCapability.PUT_IF_ABSENT)

        async def inner():
            async with store.open_writer('w', cond=IfAbsent()) as w:
                await w.write(b'mine')
                await store.put('w', b'rival')
                await raises(BlobAlreadyExistsError, w.commit())
            assert (await store.get('w')).data == b'rival'

        runner.run(inner)

    def test_writer_unusable_after(self, store, runner):
        async def inner():
            async with store.open_writer('w') as w:
                await w.write(b'x')
                await w.commit()
                await raises(RuntimeError, w.write(b'y'))
                await raises(RuntimeError, w.commit())
            async with store.open_writer('w2') as w2:
                await w2.write(b'x')
            await raises(RuntimeError, w2.write(b'y'))
            await raises(RuntimeError, w2.commit())
            await raises(BlobNotFoundError, store.head('w2'))
            assert (await store.get('w')).data == b'x'

        runner.run(inner)

    def test_writer_chunking_equivalence(self, store, runner):
        data = data_of(50_000, 3)

        async def inner():
            async with store.open_writer('small') as w:
                for i in range(0, len(data), 97):
                    await w.write(data[i:i + 97])
                await w.commit()
            async with store.open_writer('big') as w:
                await w.write(data[:40_000])
                await w.write(data[40_000:])
                await w.commit()
            assert (await store.get('small')).data == data
            assert (await store.get('big')).data == data

        runner.run(inner)

    def test_put_stream_length_mismatch(self, store, runner):
        async def inner():
            await raises(BlobStreamLengthError, store.put_stream('k', achunks(b'ab', b'c'), length=4))
            await raises(BlobStreamLengthError, store.put_stream('k', achunks(b'ab', b'cde'), length=4))
            await raises(BlobStreamLengthError, store.put_stream('k', achunks(), length=1))
            await raises(ValueError, store.put_stream('k', achunks(b'x'), length=0))
            assert await list_keys(store) == []

        runner.run(inner)

    def test_put_stream_sizes(self, store, runner):
        big = data_of(self.large_size, 5)

        async def inner():
            await store.put_stream('empty', achunks())
            assert (await store.get('empty')).data == b''
            await store.put_stream('small', achunks(b'a', b'b', b'c'), length=3)
            assert (await store.get('small')).data == b'abc'
            await store.put_stream('big', achunks(*[big[i:i + 65536] for i in range(0, len(big), 65536)]))
            assert (await store.get('big')).data == big
            await store.put_stream('big2', achunks(big), length=len(big))
            assert (await store.get('big2')).data == big

        runner.run(inner)

    ## Listing

    def test_listing_order(self, store, runner):
        keys = ['a', 'a-c', 'a/b', 'a/b/c', 'a0', 'b', 'Z', 'caf\u00e9', 'cafe', '\u65e5', 'z']

        async def inner():
            for k in keys:
                await store.put(k, b'')
            assert await list_keys(store) == sorted(keys)

        runner.run(inner)

    def test_listing_order_astral(self, store, runner):
        if self.xfail_astral_ordering:
            pytest.xfail('backend sorts by UTF-16 code units')
        keys = ['\ue000', '\U0001f600', '\uffef']

        async def inner():
            for k in keys:
                await store.put(k, b'')
            assert await list_keys(store) == sorted(keys)

        runner.run(inner)

    def test_list_prefix(self, store, runner):
        async def inner():
            for k in ['a', 'a/b', 'a/c/d', 'ab', 'abc/d', 'b']:
                await store.put(k, b'')
            assert await list_keys(store, prefix='a') == ['a', 'a/b', 'a/c/d', 'ab', 'abc/d']
            assert await list_keys(store, prefix='a/') == ['a/b', 'a/c/d']
            assert await list_keys(store, prefix='ab') == ['ab', 'abc/d']
            assert await list_keys(store, prefix='a/c/') == ['a/c/d']
            assert await list_keys(store, prefix='x') == []

        runner.run(inner)

    def test_list_start_after(self, store, runner):
        async def inner():
            for k in ['p/a', 'p/b', 'p/c/d', 'p/e', 'q']:
                await store.put(k, b'')
            assert await list_keys(store, prefix='p/', start_after='a') == ['p/a', 'p/b', 'p/c/d', 'p/e']
            assert await list_keys(store, prefix='p/', start_after='p/') == ['p/a', 'p/b', 'p/c/d', 'p/e']
            assert await list_keys(store, prefix='p/', start_after='p/b') == ['p/c/d', 'p/e']
            assert await list_keys(store, prefix='p/', start_after='p/bb') == ['p/c/d', 'p/e']
            assert await list_keys(store, prefix='p/', start_after='p/c') == ['p/c/d', 'p/e']
            assert await list_keys(store, prefix='p/', start_after='p/c/d') == ['p/e']
            assert await list_keys(store, prefix='p/', start_after='p/z') == []
            assert await list_keys(store, prefix='p/', start_after='r') == []
            assert await list_keys(store, start_after='p/e') == ['q']

        runner.run(inner)

    def test_list_paging(self, store, runner):
        keys = [f'k/{i:04d}' for i in range(self.many_keys)]

        async def inner():
            for k in keys:
                await store.put(k, b'')
            assert await list_keys(store) == keys
            assert await list_keys(store, start_after=keys[3]) == keys[4:]
            assert await list_shallow_keys(store) == ['P:k/']
            assert await list_shallow_keys(store, prefix='k/') == keys

        runner.run(inner)

    def test_list_abandon(self, store, runner):
        async def inner():
            for i in range(self.many_keys):
                await store.put(f'k{i:04d}', b'')
            n = 0
            async for _ in store.list():
                n += 1
                if n == 3:
                    break
            it = store.list_shallow()
            first = await anext(it)
            assert not isinstance(first, BlobPrefix)
            assert first.key == 'k0000'
            await it.aclose()
            await store.put('after', b'1')
            assert (await store.get('after')).data == b'1'
            assert len(await list_keys(store)) == self.many_keys + 1

        runner.run(inner)

    def test_list_shallow(self, store, runner):
        async def inner():
            for k in ['a', 'a-b', 'a/b', 'a/c/d', 'a/c/e', 'a/f/g/h', 'b|c|d', 'b|e', 'x/y']:
                await store.put(k, b'')
            assert await list_shallow_keys(store) == ['a', 'a-b', 'P:a/', 'b|c|d', 'b|e', 'P:x/']
            assert await list_shallow_keys(store, prefix='a') == ['a', 'a-b', 'P:a/']
            assert await list_shallow_keys(store, prefix='a/') == ['a/b', 'P:a/c/', 'P:a/f/']
            assert await list_shallow_keys(store, prefix='a/c/') == ['a/c/d', 'a/c/e']
            assert await list_shallow_keys(store, prefix='a/f') == ['P:a/f/']
            assert await list_shallow_keys(store, prefix='b', delimiter='|') == ['P:b|']
            assert await list_shallow_keys(store, prefix='b|', delimiter='|') == ['P:b|c|', 'b|e']
            assert await list_shallow_keys(store, prefix='q/') == []

            await store.delete('a/f/g/h')
            await store.delete('x/y')
            assert await list_shallow_keys(store) == ['a', 'a-b', 'P:a/', 'b|c|d', 'b|e']
            assert await list_shallow_keys(store, prefix='a/') == ['a/b', 'P:a/c/']

        runner.run(inner)

    ## delete_many

    def test_delete_many(self, store, runner):
        keys = [f'k/{i:04d}' for i in range(self.many_keys)]

        async def inner():
            for k in keys:
                await store.put(k, b'')
            await store.put('keep', b'')
            await store.delete_many([])
            await store.delete_many([*keys[:3], 'missing', 'k/zz'])
            assert await list_keys(store) == [*keys[3:], 'keep']
            await raises(InvalidBlobKeyError, store.delete_many([keys[3], 'bad//key']))
            assert await list_keys(store) == [*keys[3:], 'keep']
            await store.delete_many(iter(keys))
            assert await list_keys(store) == ['keep']

        runner.run(inner)

    ## Concurrency

    def _maybe_xfail_race(self, request):
        if self.xfail_conditional_races:
            request.applymarker(pytest.mark.xfail(reason='backend preconditions are not atomic under races'))

    def test_if_absent_race(self, store, runner, request):
        require(store, BlobCapability.PUT_IF_ABSENT)
        self._maybe_xfail_race(request)
        n = self.concurrency

        async def inner():
            def put(i):
                return lambda: store.put('race', str(i).encode(), cond=IfAbsent())

            results = await runner.gather([put(i) for i in range(n)])
            wins = [r for r in results if isinstance(r, BlobVersion)]
            losses = [r for r in results if isinstance(r, BlobAlreadyExistsError)]
            assert len(wins) == 1, results
            assert len(losses) == n - 1, results
            assert (await store.head('race')).version == wins[0]

        runner.run(inner)

    def test_cas_counter(self, store, runner, request):
        require(store, BlobCapability.PUT_IF_MATCH)
        self._maybe_xfail_race(request)
        n = self.concurrency
        m = self.cas_increments

        async def inner():
            await store.put('ctr', b'0')

            async def worker():
                done = 0
                while done < m:
                    b = await store.get('ctr')
                    try:
                        await store.put('ctr', str(int(b.data) + 1).encode(), cond=IfMatch(b.info.version))
                    except (BlobPreconditionFailedError, BlobConflictError):
                        continue
                    done += 1

            results = await runner.gather([worker for _ in range(n)])
            assert all(r is None for r in results), results
            assert int((await store.get('ctr')).data) == n * m

        runner.run(inner)

    def test_readers_during_overwrites(self, store, runner):
        rounds = 20
        size = 4096

        def content(i: int) -> bytes:
            return bytes([i % 256]) * size

        async def inner():
            await store.put('k', content(0))

            async def writer():
                for i in range(1, rounds):
                    await store.put('k', content(i))

            async def reader():
                for _ in range(rounds):
                    b = await store.get('k')
                    assert len(b.data) == size
                    assert len(set(b.data)) == 1
                    assert b.info.size == size

            results = await runner.gather([writer] + [reader for _ in range(max(1, self.concurrency - 1))])
            assert all(r is None for r in results), results

        runner.run(inner)
