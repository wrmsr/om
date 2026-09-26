import pytest

from omcore import dataclasses as dc
from omcore import lang

from ... import base as _base
from .. import s3


with lang.auto_proxy_import(globals()):
    import botocore.model
    import botocore.session


@pytest.fixture(scope='module')
def model():
    try:
        return botocore.session.get_session().get_service_model('s3')
    except ImportError:
        pytest.skip('botocore not available')


def test_shapes(model):
    n = 0
    for cls in s3.ALL_SHAPES:
        si = cls.__shape__
        bs = model.shape_for(si.metadata[_base.SHAPE_NAME])
        assert si.payload_member == bs.serialization.get('payload'), cls
        if si.payload_member is not None:
            assert si.payload_field is not None
        for f in dc.fields(cls):
            md = f.metadata
            ms = bs.members[md[_base.MEMBER_NAME]]
            ser = ms.serialization
            assert md.get(_base.SERIALIZATION_NAME) == ser.get('name'), (cls, f.name)
            assert md.get(_base.LOCATION) == ser.get('location'), (cls, f.name)
            assert md.get(_base.XML_NAMESPACE) == (ser.get('xmlNamespace') or {}).get('uri'), (cls, f.name)
            assert md.get(_base.XML_FLATTENED, False) == bool(ser.get('flattened')), (cls, f.name)
            assert md.get(_base.XML_ATTRIBUTE, False) == bool(ser.get('xmlAttribute')), (cls, f.name)
            assert md.get(_base.TIMESTAMP_FORMAT) == ser.get('timestampFormat'), (cls, f.name)
            assert md.get(_base.STREAMING, False) == bool(ser.get('streaming')), (cls, f.name)
            if isinstance(ms, botocore.model.ListShape):
                assert md.get(_base.LIST_MEMBER_NAME) == ms.member.serialization.get('name'), (cls, f.name)
            n += 1
    assert n > 500


def test_operations(model):
    assert {op.name for op in s3.ALL_OPERATIONS} >= {'UploadPart', 'CreateBucket', 'DeleteBucket'}
    for op in s3.ALL_OPERATIONS:
        http = model.operation_model(op.name).http
        assert op.http_method == http['method']
        assert op.http_request_uri == http['requestUri']
        assert op.http_response_code == (int(http['responseCode']) if 'responseCode' in http else None)


def test_examples():
    fs = {f.name: f for f in dc.fields(s3.PutObjectRequest)}
    assert fs['if_none_match'].metadata[_base.LOCATION] == 'header'
    assert fs['if_none_match'].metadata[_base.SERIALIZATION_NAME] == 'If-None-Match'
    assert fs['key'].metadata[_base.LOCATION] == 'uri'
    assert s3.PutObjectRequest.__shape__.payload_member == 'Body'
    assert s3.PUT_OBJECT.http_request_uri == '/{Bucket}/{Key+}'
    lfs = {f.name: f for f in dc.fields(s3.ListObjectsV2Output)}
    assert lfs['contents'].metadata[_base.XML_FLATTENED]
    cfs = {f.name: f for f in dc.fields(s3.CompleteMultipartUploadRequest)}
    assert cfs['multipart_upload'].metadata[_base.XML_NAMESPACE] == 'http://s3.amazonaws.com/doc/2006-03-01/'
