"""Cross-validates the signer against botocore's, comparing canonical requests first as they are easier to debug."""
import datetime

import pytest

from omcore import lang

from .. import auth


with lang.auto_proxy_import(globals()):
    import botocore.auth
    import botocore.awsrequest
    import botocore.credentials


UTCNOW = datetime.datetime(2024, 8, 27, 19, 49, 46, tzinfo=datetime.UTC)
TIMESTAMP = '20240827T194946Z'

KEYS = [
    'plain',
    'sp ace',
    'pl+us',
    'per%cent',
    '~tilde',
    "bang!(star*)'",
    'eq=uals',
    'amp&ersand',
    'ha#sh',
    'que?ry',
    'caf\u00e9',
    '\u65e5\u672c/\u8a9e',
    'emoji\U0001f600',
    'trailing/',
    'a/b/c',
]

QUERIES = [
    '',
    'list-type=2&prefix=a%2Fb&continuation-token=abc%2B%2F%3D&start-after=z%20z',
    'uploads',
    'delete',
    'b=2&a=1&a=0',
    'uploadId=xyz&partNumber=1',
    'encoding-type=url&max-keys=1000&list-type=2',
]


def _enc_path(key):
    return '/' + auth.AwsSigner.uri_encode(key, encode_slash=False)


def _ours(*, service, url, method='GET', headers=None, body=b'', token=None, payload_hash=None, sign_payload=True):
    creds = auth.AwsSigner.Credentials('AKIDEXAMPLE', 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY', token)
    signer = auth.V4AwsSigner(creds, 'us-east-1', service)
    req = auth.AwsSigner.Request(method=method, url=url, headers=headers or {}, payload=body)
    if payload_hash is None:
        payload_hash = signer._sha256(body) if body else signer._EMPTY_SHA256  # noqa
        emit = sign_payload
    else:
        emit = True
    return signer._sign(req, payload_hash=payload_hash, emit_content_sha256=emit, utcnow=UTCNOW)  # noqa


def _boto(*, service, url, method='GET', headers=None, body=b'', token=None, payload_hash=None, sign_payload=True):
    creds = botocore.credentials.Credentials('AKIDEXAMPLE', 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY', token)
    cls = botocore.auth.S3SigV4Auth if service == 's3' else botocore.auth.SigV4Auth
    a = cls(creds, service, 'us-east-1')
    r = botocore.awsrequest.AWSRequest(
        method=method,
        url=url,
        headers={k: ','.join(vs) for k, vs in (headers or {}).items()},
        data=body,
    )
    r.context['timestamp'] = TIMESTAMP
    # What _modify_request_before_signing would do, without letting botocore read its own clock.
    r.headers['X-Amz-Date'] = TIMESTAMP
    if token is not None:
        r.headers['X-Amz-Security-Token'] = token
    if payload_hash is not None:
        r.headers['X-Amz-Content-SHA256'] = payload_hash
    elif sign_payload:
        r.headers['X-Amz-Content-SHA256'] = a.payload(r)
    cr = a.canonical_request(r)
    return cr, a.signature(a.string_to_sign(r, cr), r)


def _check(**kwargs):
    ours = _ours(**kwargs)
    cr, sig = _boto(**kwargs)
    assert ours.canonical_request == cr
    assert ours.signature == sig


@pytest.fixture(autouse=True)
def _require_botocore():
    try:
        import botocore  # noqa
    except ImportError:
        pytest.skip('botocore not available')


@pytest.mark.parametrize('key', KEYS)
@pytest.mark.parametrize('query', QUERIES)
def test_s3_paths_and_queries(key, query):
    url = 'https://bucket.s3.us-east-1.amazonaws.com' + _enc_path(key) + ('?' + query if query else '')
    _check(service='s3', url=url)


@pytest.mark.parametrize('key', KEYS)
def test_other_service_paths(key):
    _check(service='execute-api', url='https://api.example.com/stage' + _enc_path(key), sign_payload=False)


def test_other_service_normalization():
    for p in ['/a/./b/../c', '//a//b/', '/a/b%20c/', '']:
        _check(service='execute-api', url='https://api.example.com' + p, sign_payload=False)


def test_bodies_headers_tokens():
    url = 'https://bucket.s3.us-east-1.amazonaws.com/k?uploads'
    _check(
        service='s3',
        url=url,
        method='PUT',
        headers={'content-type': ['text/plain'], 'x-amz-meta-foo': ['a   b  c'], 'x-amz-meta-bar': ['x']},
        body=b'hello world',
    )
    _check(service='s3', url=url, method='PUT', body=b'hello', token='sessiontoken/abc=')  # noqa: S106
    _check(service='s3', url=url, method='PUT', body=b'hello', payload_hash=auth.AwsSigner.UNSIGNED_PAYLOAD)
    _check(
        service='ec2',
        url='https://ec2.us-west-1.amazonaws.com/',
        method='POST',
        body=b'Action=X',
        sign_payload=False,
    )


def test_host_with_port():
    _check(service='s3', url='http://127.0.0.1:9090/bucket/k?list-type=2')
    _check(service='s3', url='https://s3.example.com:443/bucket/k')


def test_returned_headers():
    creds = auth.AwsSigner.Credentials('AKID', 'secret', 'tok')
    h = auth.V4AwsSigner(creds, 'us-east-1', 's3').sign(
        auth.AwsSigner.Request(method='GET', url='https://b.s3.amazonaws.com/k'),
        payload_hash=auth.AwsSigner.UNSIGNED_PAYLOAD,
        utcnow=UTCNOW,
    )
    assert h['X-Amz-Content-SHA256'] == ['UNSIGNED-PAYLOAD']
    assert h['X-Amz-Security-Token'] == ['tok']
    assert 'x-amz-security-token' in h['Authorization'][0]
