import datetime
import enum
import xml.etree.ElementTree as ET  # noqa

import pytest

from omcore import lang
from ominfra.clouds.aws.models.services import s3

from ..restxml import RestXmlKind
from ..restxml import analyze_shape
from ..restxml import deserialize_rest_xml_response
from ..restxml import parse_rest_xml_error
from ..restxml import serialize_rest_xml_request


with lang.auto_proxy_import(globals()):
    import botocore.awsrequest
    import botocore.parsers
    import botocore.serialize
    import botocore.session
    import botocore.utils


@pytest.fixture(scope='module')
def model():
    try:
        return botocore.session.get_session().get_service_model('s3')
    except ImportError:
        pytest.skip('botocore not available')


def _conv(t, v):
    if t.kind == RestXmlKind.SHAPE:
        return build_shape(t.cls, v)
    if t.kind == RestXmlKind.LIST:
        return [_conv(t.elem, x) for x in v]
    if t.kind == RestXmlKind.MAP:
        return {k: _conv(t.elem, x) for k, x in v.items()}
    if t.kind == RestXmlKind.ENUM:
        return t.cls(v)
    return v


def build_shape(cls, params):
    fs = {f.member_name: f for f in analyze_shape(cls)}
    return cls(**{fs[mn].name: _conv(fs[mn].type, v) for mn, v in params.items()})


def _unconv(v):
    if isinstance(v, s3._base.Shape):  # noqa
        return {f.member_name: _unconv(x) for f in analyze_shape(type(v)) if (x := getattr(v, f.name)) is not None}
    if isinstance(v, list):
        return [_unconv(x) for x in v]
    if isinstance(v, dict):
        return {k: _unconv(x) for k, x in v.items()}
    if isinstance(v, enum.Enum):
        return v.value
    return v


def _norm_boto_value(v):
    if isinstance(v, datetime.datetime):
        return v
    if isinstance(v, list):
        return [_norm_boto_value(x) for x in v]
    if isinstance(v, dict):
        return {k: _norm_boto_value(x) for k, x in v.items()}
    return v


def _canon_xml(b):
    if not b:
        return None
    return ET.canonicalize(b.decode('utf-8') if isinstance(b, bytes) else b, strip_text=True)


##


SER_CASES = [
    ('PutObject', {
        'Bucket': 'bkt',
        'Key': 'a/b c+d%e~f/\u00e9\U0001f600',
        'Body': b'hello',
        'IfNoneMatch': '*',
        'ContentType': 'text/plain',
        'Metadata': {'foo': 'bar', 'baz': 'q x'},
        'ContentLength': 5,
    }),
    ('PutObject', {'Bucket': 'bkt', 'Key': 'k', 'Body': b'', 'IfMatch': '"abc"'}),
    ('GetObject', {
        'Bucket': 'bkt',
        'Key': 'a/b',
        'Range': 'bytes=0-9',
        'IfMatch': '"a"',
        'IfNoneMatch': '"b"',
        'IfModifiedSince': 'Wed, 21 Oct 2015 07:28:00 GMT',
        'VersionId': 'v1+/=',
        'PartNumber': 3,
    }),
    ('HeadObject', {'Bucket': 'bkt', 'Key': 'a?b#c', 'IfMatch': '"a"'}),
    ('DeleteObject', {'Bucket': 'bkt', 'Key': 'a&b=c', 'IfMatch': '"a"'}),
    ('ListObjectsV2', {
        'Bucket': 'bkt',
        'Prefix': 'a/ b',
        'Delimiter': '/',
        'StartAfter': 'a/x+y',
        'ContinuationToken': 'abc+/=',
        'MaxKeys': 7,
        'EncodingType': 'url',
    }),
    ('CopyObject', {'Bucket': 'bkt', 'Key': 'dst', 'CopySource': '/bkt/src%20key', 'IfNoneMatch': '*'}),
    ('CreateMultipartUpload', {'Bucket': 'bkt', 'Key': 'big', 'ContentType': 'application/octet-stream'}),
    ('UploadPart', {'Bucket': 'bkt', 'Key': 'big', 'Body': b'part', 'PartNumber': 2, 'UploadId': 'u/p+id'}),
    ('CompleteMultipartUpload', {
        'Bucket': 'bkt',
        'Key': 'big',
        'UploadId': 'uid',
        'IfNoneMatch': '*',
        'MultipartUpload': {'Parts': [{'ETag': '"a"', 'PartNumber': 1}, {'ETag': '"b"', 'PartNumber': 2}]},
    }),
    ('AbortMultipartUpload', {'Bucket': 'bkt', 'Key': 'big', 'UploadId': 'uid'}),
    ('DeleteObjects', {
        'Bucket': 'bkt',
        'Delete': {'Objects': [{'Key': 'a'}, {'Key': 'b c&<d>'}], 'Quiet': True},
    }),
    ('ListMultipartUploads', {
        'Bucket': 'bkt',
        'Prefix': 'p/',
        'KeyMarker': 'k m',
        'UploadIdMarker': 'u',
        'MaxUploads': 5,
    }),
    ('CreateBucket', {'Bucket': 'bkt', 'CreateBucketConfiguration': {'LocationConstraint': 'us-west-2'}}),
    ('CreateBucket', {'Bucket': 'bkt'}),
    ('DeleteBucket', {'Bucket': 'bkt'}),
    ('ListBuckets', {'MaxBuckets': 10}),
]


def _op(name):
    return next(o for o in s3.ALL_OPERATIONS if o.name == name)


def test_covers_all_operations():
    assert {n for n, _ in SER_CASES} == {o.name for o in s3.ALL_OPERATIONS}


@pytest.mark.parametrize(('op_name', 'params'), SER_CASES)
def test_serialize_matches_botocore(model, op_name, params):
    op = _op(op_name)
    ours = serialize_rest_xml_request(op, build_shape(op.input, params))

    ser = botocore.serialize.create_serializer('rest-xml', include_validation=False)
    theirs = ser.serialize_to_request(params, model.operation_model(op_name))

    t_path, _, t_static = theirs['url_path'].partition('?')
    t_query = []
    for part in t_static.split('&') if t_static else []:
        k, _, v = part.partition('=')
        t_query.append((k, v))
    for k, v in (theirs['query_string'] or {}).items():
        for x in (v if isinstance(v, list) else [v]):
            t_query.append((k, str(x)))

    assert ours.method == theirs['method']
    assert ours.path == t_path
    assert sorted((k, v or '') for k, v in ours.query) == sorted(t_query)
    assert dict(ours.headers) == dict(theirs['headers'])

    t_body = theirs['body']
    pm = op.input.__shape__.payload_member
    pf = next((f for f in analyze_shape(op.input) if f.member_name == pm), None)
    if pf is not None and pf.type.kind == RestXmlKind.SHAPE:
        assert _canon_xml(ours.body) == _canon_xml(t_body)
    else:
        assert (ours.body or b'') == (t_body or b'')


def test_serialize_missing_label():
    with pytest.raises(ValueError):  # noqa
        serialize_rest_xml_request(s3.GET_OBJECT, s3.GetObjectRequest(bucket='b', key=None))  # type: ignore[arg-type]


##


LIST_V2_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>bucket</Name>
  <Prefix>a/</Prefix>
  <KeyCount>3</KeyCount>
  <MaxKeys>1000</MaxKeys>
  <Delimiter>/</Delimiter>
  <IsTruncated>true</IsTruncated>
  <Contents>
    <Key>a/b</Key>
    <LastModified>2009-10-12T17:50:30.000Z</LastModified>
    <ETag>&quot;fba9dede5f27731c9771645a39863328&quot;</ETag>
    <Size>434234</Size>
    <StorageClass>STANDARD</StorageClass>
  </Contents>
  <Contents>
    <Key>a/sp%20ace</Key>
    <LastModified>2009-10-12T17:50:31.500Z</LastModified>
    <ETag>&quot;beef-2&quot;</ETag>
    <Size>0</Size>
    <StorageClass>STANDARD</StorageClass>
  </Contents>
  <CommonPrefixes><Prefix>a/c/</Prefix></CommonPrefixes>
  <CommonPrefixes><Prefix>a/d/</Prefix></CommonPrefixes>
  <NextContinuationToken>1ueGcxLPRx1Tr/XYExHnhbYLgveDs2J/wm36Hy4vbOwM=</NextContinuationToken>
  <EncodingType>url</EncodingType>
</ListBucketResult>"""

LIST_V2_EMPTY_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>bucket</Name><Prefix>zzz</Prefix><KeyCount>0</KeyCount><MaxKeys>1000</MaxKeys><IsTruncated>false</IsTruncated>
</ListBucketResult>"""

COPY_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<CopyObjectResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <LastModified>2009-10-28T22:32:00.000Z</LastModified>
  <ETag>&quot;9b2cf535f27731c974343645a3985328&quot;</ETag>
</CopyObjectResult>"""

CREATE_MPU_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<InitiateMultipartUploadResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Bucket>bucket</Bucket>
  <Key>big</Key>
  <UploadId>VXBsb2FkIElEIGZvciA2aWWpbmcncyBteS1tb3ZpZS5tMnRzIHVwbG9hZA</UploadId>
</InitiateMultipartUploadResult>"""

COMPLETE_MPU_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<CompleteMultipartUploadResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Location>http://bucket.s3.amazonaws.com/big</Location>
  <Bucket>bucket</Bucket>
  <Key>big</Key>
  <ETag>&quot;3858f62230ac3c915f300c664312c11f-9&quot;</ETag>
</CompleteMultipartUploadResult>"""

DELETE_OBJECTS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<DeleteResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Deleted><Key>sample1.txt</Key></Deleted>
  <Error><Key>sample2.txt</Key><Code>AccessDenied</Code><Message>Access Denied</Message></Error>
</DeleteResult>"""

LIST_UPLOADS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListMultipartUploadsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Bucket>bucket</Bucket>
  <KeyMarker></KeyMarker>
  <UploadIdMarker></UploadIdMarker>
  <NextKeyMarker>my-movie.m2ts</NextKeyMarker>
  <NextUploadIdMarker>YW55IGlkZWEgd2h5IGVsdmluZydzIHVwbG9hZCBmYWlsZWQ</NextUploadIdMarker>
  <MaxUploads>3</MaxUploads>
  <IsTruncated>true</IsTruncated>
  <Upload>
    <Key>my-divisor</Key>
    <UploadId>XMgbGlrZSBlbHZpbmcncyBub3QgaGF2aW5nIG11Y2ggbHVjaw</UploadId>
    <Initiator><ID>arn:aws:iam::111122223333:user/user1</ID><DisplayName>user1</DisplayName></Initiator>
    <Owner><ID>75aa57f09aa0c8caeab4f8c24e99d10f8e7faeebf76c078efc7c6caea54ba06a</ID><DisplayName>OwnerDisplayName</DisplayName></Owner>
    <StorageClass>STANDARD</StorageClass>
    <Initiated>2010-11-10T20:48:33.000Z</Initiated>
  </Upload>
  <Upload>
    <Key>my-movie.m2ts</Key>
    <UploadId>VXBsb2FkIElEIGZvciBlbHZpbmcncyBteS1tb3ZpZS5tMnRzIHVwbG9hZA</UploadId>
    <StorageClass>STANDARD</StorageClass>
    <Initiated>2010-11-10T20:48:33.000Z</Initiated>
  </Upload>
</ListMultipartUploadsResult>"""

PARSE_CASES = [
    ('ListObjectsV2', {'x-amz-request-id': 'r1'}, LIST_V2_BODY),
    ('ListObjectsV2', {}, LIST_V2_EMPTY_BODY),
    ('CopyObject', {'x-amz-version-id': 'v1'}, COPY_BODY),
    ('CreateMultipartUpload', {}, CREATE_MPU_BODY),
    ('CompleteMultipartUpload', {'x-amz-version-id': 'v2'}, COMPLETE_MPU_BODY),
    ('DeleteObjects', {}, DELETE_OBJECTS_BODY),
    ('ListMultipartUploads', {}, LIST_UPLOADS_BODY),
    ('HeadObject', {
        'last-modified': 'Wed, 28 Oct 2009 22:32:00 GMT',
        'etag': '"etag"',
        'content-length': '434234',
        'content-type': 'text/plain',
        'x-amz-meta-foo': 'bar',
        'x-amz-meta-baz': 'q x',
        'accept-ranges': 'bytes',
    }, b''),
    ('PutObject', {'etag': '"abc"', 'x-amz-version-id': 'v3'}, b''),
    ('UploadPart', {'etag': '"part"'}, b''),
    ('DeleteObject', {'x-amz-delete-marker': 'true'}, b''),
]


@pytest.mark.parametrize(('op_name', 'headers', 'body'), PARSE_CASES)
def test_parse_matches_botocore(model, op_name, headers, body):
    op = _op(op_name)
    ours = deserialize_rest_xml_response(op, status=200, headers={k: [v] for k, v in headers.items()}, body=body)

    parser = botocore.parsers.create_parser('rest-xml')
    theirs = parser.parse(
        {'status_code': 200, 'headers': botocore.awsrequest.HeadersDict(headers), 'body': body},
        model.operation_model(op_name).output_shape,
    )
    theirs.pop('ResponseMetadata', None)

    def cmp(o, t, path):
        if isinstance(t, datetime.datetime):
            assert botocore.utils.parse_timestamp(o) == t, path
        elif isinstance(t, dict):
            assert isinstance(o, dict), path
            assert set(o) == set(t), path
            for k in t:
                cmp(o[k], t[k], (*path, k))
        elif isinstance(t, list):
            assert len(o) == len(t), path
            for i, (a, b) in enumerate(zip(o, t)):
                cmp(a, b, (*path, i))
        else:
            assert o == t, path

    cmp(_unconv(ours), _norm_boto_value(theirs), ())


def test_get_object_payload():
    out = deserialize_rest_xml_response(
        s3.GET_OBJECT,
        status=206,
        headers={'Content-Range': ['bytes 0-4/10'], 'ETag': ['"e"'], 'Content-Length': ['5']},
        body=b'hello',
    )
    assert (out.body, out.content_range, out.etag, out.content_length) == (b'hello', 'bytes 0-4/10', '"e"', 5)


def test_parse_errors():
    e = parse_rest_xml_error(
        status=404,
        headers={'x-amz-request-id': ['rid']},
        body=b'<?xml version="1.0"?><Error><Code>NoSuchKey</Code><Message>nope</Message>'
             b'<Key>k</Key><RequestId>r2</RequestId><HostId>h</HostId></Error>',
    )
    assert (e.status, e.code, e.message, e.request_id, e.host_id) == (404, 'NoSuchKey', 'nope', 'r2', 'h')

    e = parse_rest_xml_error(status=404, headers={'x-amz-request-id': ['rid'], 'x-amz-id-2': ['hid']}, body=b'')
    assert (e.code, e.request_id, e.host_id) == (None, 'rid', 'hid')

    e = parse_rest_xml_error(status=502, headers={}, body=b'<html>bad gateway</html')
    assert (e.status, e.code) == (502, None)

    e = parse_rest_xml_error(status=400, headers={}, body=b'{"detail": "not xml"}')
    assert e.code is None
