import base64
import datetime
import hashlib

import pytest

from omcore import lang
from ominfra.clouds.aws import auth as aws_auth

from ..signing import S3RequestSigner


with lang.auto_proxy_import(globals()):
    import botocore.auth
    import botocore.awsrequest
    import botocore.credentials


NOW = datetime.datetime(2026, 9, 24, 12, 0, 0, tzinfo=datetime.UTC)
CREDS = aws_auth.AwsSigner.Credentials('AKIDEXAMPLE', 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY')


def _signer():
    return S3RequestSigner(CREDS, 'us-east-1', clock=lambda: NOW)


def test_headers():
    req = _signer().sign(
        method='PUT',
        url='http://127.0.0.1:9090/bkt/k',
        host='127.0.0.1:9090',
        headers=[('If-None-Match', '*'), ('content-length', '999')],
        body=b'',
    )
    h = {k.lower(): v for k, v in dict(req.headers).items()}
    assert h['host'] == ['127.0.0.1:9090']
    assert h['content-length'] == ['0']
    assert h['if-none-match'] == ['*']
    assert h['x-amz-date'] == ['20260924T120000Z']
    assert h['x-amz-content-sha256'] == [aws_auth.AwsSigner._EMPTY_SHA256]  # noqa
    assert 'if-none-match' in h['authorization'][0]
    assert req.method == 'PUT'
    assert req.data == b''

    req = _signer().sign(
        method='POST',
        url='https://s3.amazonaws.com/bkt?delete',
        host='s3.amazonaws.com',
        body=b'<Delete/>',
        xml_body=True,
        content_md5=True,
        unsigned_payload=True,
        no_decompress=True,
    )
    h = {k.lower(): v for k, v in dict(req.headers).items()}
    assert h['content-type'] == ['application/xml']
    assert h['content-md5'] == [base64.b64encode(hashlib.md5(b'<Delete/>').digest()).decode()]  # noqa
    assert h['x-amz-content-sha256'] == ['UNSIGNED-PAYLOAD']
    assert req.no_decompress

    req = _signer().sign(method='GET', url='http://x/bkt/k', host='x', unsigned_payload=True)
    h = {k.lower(): v for k, v in dict(req.headers).items()}
    assert h['x-amz-content-sha256'] == [aws_auth.AwsSigner._EMPTY_SHA256]  # noqa  - never unsigned over http
    assert 'content-length' not in h


@pytest.mark.parametrize(('method', 'url', 'headers', 'body'), [
    ('GET', 'https://bkt.s3.us-east-1.amazonaws.com/a/sp%20ace%2Bplus?list-type=2&prefix=a%20b', [], None),
    ('PUT', 'http://127.0.0.1:9090/bkt/k', [('If-Match', '"abc"'), ('Content-Type', 'text/plain')], b'hello'),
    ('POST', 'https://s3.amazonaws.com/bkt/k?uploadId=x%2By', [], b'<x/>'),
])
def test_matches_botocore(method, url, headers, body):
    try:
        bc = botocore.credentials.Credentials(CREDS.access_key_id, CREDS.secret_access_key)
        auth = botocore.auth.S3SigV4Auth(bc, 's3', 'us-east-1')
    except ImportError:
        pytest.skip('botocore not available')

    ours = _signer().sign(method=method, url=url, host=url.split('/')[2], headers=headers, body=body)
    oh = dict(ours.headers)

    r = botocore.awsrequest.AWSRequest(
        method=method,
        url=url,
        headers={k: v[0] for k, v in oh.items() if k != 'Authorization'},
        data=body or b'',
    )
    r.context['timestamp'] = '20260924T120000Z'
    cr = auth.canonical_request(r)
    sig = auth.signature(auth.string_to_sign(r, cr), r)
    assert oh['Authorization'][0].endswith(f'Signature={sig}')
