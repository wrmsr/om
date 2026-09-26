import datetime

import pytest

from ominfra.clouds.aws.models.services import s3

from .... import blobs
from ..errors import S3FailureKind
from ..errors import S3ResponseError
from ..errors import classify_status
from ..errors import classify_transport_error
from ..errors import is_error_body
from ..ops import blob_from_get
from ..ops import build_copy
from ..ops import build_get
from ..ops import build_list
from ..ops import build_put
from ..ops import info_from_head
from ..ops import map_error
from ..ops import normalize_etag
from ..ops import page_from_list
from ..ops import parse_content_range
from ..ops import range_header


V = blobs.BlobVersion('"v"')


def mk(cls, **kwargs):
    return cls(**kwargs)


def test_ranges():
    assert range_header(None) is None
    assert range_header(blobs.OffsetBlobRange(0)) is None
    assert range_header(blobs.OffsetBlobRange(5)) == 'bytes=5-'
    assert range_header(blobs.OffsetBlobRange(2, 5)) == 'bytes=2-4'
    assert range_header(blobs.SuffixBlobRange(3)) == 'bytes=-3'
    assert parse_content_range('bytes 0-4/10') == (0, 4, 10)
    assert parse_content_range('bytes */10') == (None, None, 10)
    assert parse_content_range('bytes 0-4/*') == (0, 4, None)
    with pytest.raises(ValueError):  # noqa
        parse_content_range('items 0-4/10')


def test_etags():
    assert normalize_etag('abc') == blobs.BlobVersion('"abc"')
    assert normalize_etag('"abc"') == blobs.BlobVersion('"abc"')
    assert normalize_etag(' "abc-2" ') == blobs.BlobVersion('"abc-2"')


def test_builds():
    r = build_get('b', 'k', blobs.OffsetBlobRange(1, 3), blobs.IfMatch(V))
    assert (r.range, r.if_match, r.if_none_match) == ('bytes=1-2', '"v"', None)
    r2 = build_put('b', 'k', b'x', blobs.IfAbsent())
    assert (r2.if_none_match, r2.if_match, r2.body) == ('*', None, b'x')
    c, extra = build_copy(
        'b',
        'a b/c',
        'dst',
        blobs.IfAbsent(),
        dst_if_none_match_header='cf-copy-destination-if-none-match',
        dst_if_match_header='cf-copy-destination-if-match',
    )
    assert c.copy_source == '/b/a%20b/c'
    assert extra == [('cf-copy-destination-if-none-match', '*')]
    ls = build_list(
        'b',
        prefix='p/',
        start_after='p/a',
        continuation_token='tok',  # noqa: S106
        delimiter=None,
        max_keys=10,
        no_url_encoding=False,
    )
    assert ls.start_after is None
    assert ls.encoding_type == s3.EncodingType.URL


def test_interpret_head_and_get():
    info = info_from_head('k', mk(s3.HeadObjectOutput,
        content_length=10,
        etag='"e"',
        last_modified='Wed, 28 Oct 2009 22:32:00 GMT',
    ))
    assert info.size == 10
    assert info.last_modified == datetime.datetime(2009, 10, 28, 22, 32, tzinfo=datetime.UTC)

    b = blob_from_get('k', 206, mk(s3.GetObjectOutput,
        body=b'234',
        content_range='bytes 2-4/10',
        content_length=3,
        etag='"e"',
        last_modified='Wed, 28 Oct 2009 22:32:00 GMT',
    ), blobs.OffsetBlobRange(2, 5))
    assert (b.data, b.info.size) == (b'234', 10)

    # A server ignoring the Range header - slice locally.
    b = blob_from_get('k', 200, mk(s3.GetObjectOutput,
        body=b'0123456789',
        content_length=10,
        etag='"e"',
        last_modified='Wed, 28 Oct 2009 22:32:00 GMT',
    ), blobs.SuffixBlobRange(3))
    assert (b.data, b.info.size) == (b'789', 10)


def test_interpret_list():
    page = page_from_list(mk(s3.ListObjectsV2Output,
        contents=[
            mk(s3.Object, key='a/sp+ace%2Bplus', size=1, etag='"x"', last_modified='2009-10-12T17:50:30.000Z'),
            mk(s3.Object, key='a/%20pct', size=2, etag='y', last_modified='2009-10-12T17:50:30Z'),
            mk(s3.Object, key='bad//key', size=0, etag='"z"', last_modified='2009-10-12T17:50:30Z'),
        ],
        common_prefixes=[mk(s3.CommonPrefix, prefix='a/c+d/')],
        encoding_type=s3.EncodingType.URL,
        is_truncated=True,
        next_continuation_token='tok',  # noqa: S106
    ))
    assert [i.key for i in page.infos] == ['a/sp ace+plus', 'a/ pct']
    assert page.infos[1].version == blobs.BlobVersion('"y"')
    assert page.prefixes == ['a/c d/']
    assert page.next_token == 'tok'  # noqa: S105

    page = page_from_list(mk(s3.ListObjectsV2Output, contents=[], is_truncated=False, next_continuation_token='x'))  # noqa: S106
    assert page.next_token is None


def _err(status, code=None):
    return S3ResponseError(status=status, code=code)


@pytest.mark.parametrize(('op', 'status', 'code', 'cond', 'expected'), [
    ('get', 304, None, blobs.IfNoneMatch(V), blobs.BlobNotModifiedError),
    ('head', 412, 'PreconditionFailed', blobs.IfMatch(V), blobs.BlobPreconditionFailedError),
    ('get', 404, 'NoSuchKey', blobs.IfMatch(V), blobs.BlobPreconditionFailedError),
    ('head', 404, None, blobs.IfMatch(V), blobs.BlobPreconditionFailedError),
    ('get', 404, 'NoSuchKey', None, blobs.BlobNotFoundError),
    ('head', 404, None, blobs.IfNoneMatch(V), blobs.BlobNotFoundError),
    ('get', 404, 'NoSuchBucket', None, S3ResponseError),
    ('put', 412, 'PreconditionFailed', blobs.IfAbsent(), blobs.BlobAlreadyExistsError),
    ('put', 412, 'PreconditionFailed', blobs.IfMatch(V), blobs.BlobPreconditionFailedError),
    ('put', 404, 'NoSuchKey', blobs.IfMatch(V), blobs.BlobPreconditionFailedError),
    ('complete', 412, 'PreconditionFailed', blobs.IfAbsent(), blobs.BlobAlreadyExistsError),
    ('put', 409, 'ConditionalRequestConflict', blobs.IfAbsent(), blobs.BlobConflictError),
    ('copy', 412, 'PreconditionFailed', blobs.IfAbsent(), blobs.BlobAlreadyExistsError),
    ('copy', 404, 'NoSuchKey', None, S3ResponseError),
    ('delete', 412, 'PreconditionFailed', blobs.IfMatch(V), blobs.BlobPreconditionFailedError),
    ('delete', 404, 'NoSuchKey', blobs.IfMatch(V), blobs.BlobPreconditionFailedError),
    ('put', 501, 'NotImplemented', blobs.IfAbsent(), blobs.UnsupportedBlobOperationError),
    ('put', 403, 'AccessDenied', None, S3ResponseError),
    ('get', 301, 'PermanentRedirect', None, S3ResponseError),
])
def test_map_error(op, status, code, cond, expected):
    e = map_error(op, _err(status, code), key='k', cond=cond)
    assert type(e) is expected


def test_classify():
    assert classify_status(503, 'SlowDown', read=False) == S3FailureKind.THROTTLED
    assert classify_status(409, 'ConditionalRequestConflict', read=False) == S3FailureKind.NOT_APPLIED
    assert classify_status(500, 'InternalError', read=True) == S3FailureKind.READ_FAILED
    assert classify_status(500, 'InternalError', read=False) == S3FailureKind.AMBIGUOUS
    assert classify_status(503, 'ServiceUnavailable', read=False) == S3FailureKind.AMBIGUOUS
    assert classify_status(501, 'NotImplemented', read=False) == S3FailureKind.TERMINAL
    assert classify_status(403, 'AccessDenied', read=True) == S3FailureKind.TERMINAL

    def chained(inner):
        try:
            try:
                raise inner
            except BaseException as e:
                raise RuntimeError('wrapped') from e
        except RuntimeError as e:
            return e

    assert classify_transport_error(chained(ConnectionRefusedError()), read=False) == S3FailureKind.NOT_APPLIED
    assert classify_transport_error(chained(TimeoutError()), read=False) == S3FailureKind.AMBIGUOUS
    assert classify_transport_error(chained(TimeoutError()), read=True) == S3FailureKind.READ_FAILED


def test_error_body_detection():
    assert is_error_body(b'<?xml version="1.0" encoding="UTF-8"?>\n<Error><Code>InternalError</Code></Error>')
    assert is_error_body(b'  <Error><Code>X</Code></Error>')
    assert not is_error_body(b'<?xml version="1.0"?><CopyObjectResult><ETag>x</ETag></CopyObjectResult>')
    assert not is_error_body(b'')
