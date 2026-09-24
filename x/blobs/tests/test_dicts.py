import pytest

from ..caps import BlobCapability
from ..dicts import DictBlobStore
from ..errors import BlobAlreadyExistsError
from ..errors import BlobNotFoundError
from ..errors import BlobNotModifiedError
from ..errors import BlobPreconditionFailedError
from ..errors import InvalidBlobKeyError
from ..errors import UnsupportedBlobOperationError
from ..types import BlobPrefix
from ..types import IfAbsent
from ..types import IfMatch
from ..types import IfNoneMatch
from ..types import OffsetBlobRange
from ..types import SuffixBlobRange


def test_preconditions():
    s = DictBlobStore()
    v1 = s.put('a', b'1', cond=IfAbsent())
    with pytest.raises(BlobAlreadyExistsError):
        s.put('a', b'2', cond=IfAbsent())
    v2 = s.put('a', b'2', cond=IfMatch(v1))
    with pytest.raises(BlobPreconditionFailedError):
        s.put('a', b'3', cond=IfMatch(v1))
    with pytest.raises(BlobNotModifiedError):
        s.get('a', cond=IfNoneMatch(v2))
    with pytest.raises(BlobPreconditionFailedError):
        s.delete('a', cond=IfMatch(v1))
    s.delete('a', cond=IfMatch(v2))
    s.delete('a')
    with pytest.raises(BlobPreconditionFailedError):
        s.put('a', b'4', cond=IfMatch(v2))
    with pytest.raises(BlobNotFoundError):
        s.get('a')


def test_ranges():
    s = DictBlobStore()
    s.put('k', b'0123456789')
    assert s.get('k', byte_range=OffsetBlobRange(2, 5)).data == b'234'
    assert s.get('k', byte_range=OffsetBlobRange(8, 100)).data == b'89'
    b = s.get('k', byte_range=SuffixBlobRange(3))
    assert (b.data, b.info.size) == (b'789', 10)


def test_listing_order():
    s = DictBlobStore()
    for k in ['a/b', 'a-c', 'a', 'a/d/e', 'b']:
        s.put(k, b'')
    assert [i.key for i in s.list()] == ['a', 'a-c', 'a/b', 'a/d/e', 'b']
    assert [i.key for i in s.list(prefix='a/', start_after='a/b')] == ['a/d/e']
    assert [e.prefix if isinstance(e, BlobPrefix) else e.key for e in s.list_shallow(prefix='a/')] == ['a/b', 'a/d/']


def test_writer_needs_explicit_commit():
    s = DictBlobStore()
    with s.open_writer('w') as w:
        w.write(b'x')
    with pytest.raises(BlobNotFoundError):
        s.head('w')
    with s.open_writer('w', cond=IfAbsent()) as w:
        w.write(b'y')
        w.commit()
    assert s.get('w').data == b'y'


def test_capabilities_and_keys():
    s = DictBlobStore(capabilities=BlobCapability.PUT_IF_ABSENT)
    v = s.put('a', b'', cond=IfAbsent())
    with pytest.raises(UnsupportedBlobOperationError):
        s.put('a', b'', cond=IfMatch(v))
    for k in ['', '/a', 'a/', 'a//b', 'a/../b', 'a\x00', 'x' * 1025, '\ud800']:
        with pytest.raises(InvalidBlobKeyError):
            s.put(k, b'')
