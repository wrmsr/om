import pytest

from ..endpoints import S3Endpoint
from ..endpoints import build_url
from ..endpoints import check_bucket_addressable
from ..endpoints import encode_query
from ..restxml import RestXmlRequest


def _rx(path, query=()):
    return RestXmlRequest(method='GET', path=path, query=list(query), headers=[], body=None)


def test_path_style():
    ep = S3Endpoint(url='http://127.0.0.1:9090', region='us-east-1')
    rx = _rx('/bkt/a/sp%20ace', [('list-type', '2'), ('prefix', 'a b+c'), ('uploads', None)])
    url, host = build_url(ep, 'bkt', rx)
    assert host == '127.0.0.1:9090'
    assert url == 'http://127.0.0.1:9090/bkt/a/sp%20ace?list-type=2&prefix=a%20b%2Bc&uploads'


def test_virtual_hosted():
    ep = S3Endpoint(url='https://s3.us-west-2.amazonaws.com', region='us-west-2', virtual_hosted=True)
    h = 'bkt.s3.us-west-2.amazonaws.com'
    assert build_url(ep, 'bkt', _rx('/bkt/k/x')) == (f'https://{h}/k/x', h)
    assert build_url(ep, 'bkt', _rx('/bkt', [('list-type', '2')]))[0] == 'https://bkt.s3.us-west-2.amazonaws.com/?list-type=2'
    with pytest.raises(ValueError):  # noqa
        build_url(ep, 'bkt', _rx('/other/k'))
    check_bucket_addressable(ep, 'my-bucket-1')
    for b in ['My.Bucket', 'a.b', 'ab', '-ab', 'UPPER']:
        with pytest.raises(ValueError):  # noqa
            check_bucket_addressable(ep, b)


def test_bad_endpoints():
    for u in ['ftp://x', 'http://', 'http://x/path', 'http://x?q=1']:
        with pytest.raises(ValueError):  # noqa
            S3Endpoint(url=u, region='r')
    S3Endpoint(url='https://x.example.com/', region='r')


def test_encode_query_sorted():
    assert encode_query([('b', '2'), ('a', '1'), ('a', '0'), ('delete', None)]) == 'a=0&a=1&b=2&delete'
    assert encode_query([('k', '~_.-!*')]) == 'k=~_.-%21%2A'
