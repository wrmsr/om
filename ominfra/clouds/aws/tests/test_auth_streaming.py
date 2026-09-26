import datetime

import pytest

from .. import auth


CREDS = auth.AwsSigner.Credentials('AKIAIOSFODNN7EXAMPLE', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')


def _signer():
    return auth.V4AwsSigner(CREDS, 'us-east-1', 's3')


def _sign_streaming(decoded_length, chunk_size=65536):
    return _signer().sign_streaming(
        auth.AwsSigner.Request(
            method='PUT',
            url='https://s3.amazonaws.com/examplebucket/chunkObject.txt',
            headers={'x-amz-storage-class': ['REDUCED_REDUNDANCY']},
        ),
        decoded_length=decoded_length,
        chunk_size=chunk_size,
        utcnow=datetime.datetime(2013, 5, 24, tzinfo=datetime.UTC),
    )


def test_official_vector():
    # The worked 'PUT Object' example from https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-streaming.html : 66560
    # bytes of 'a' in 64KiB chunks.
    headers, cs = _sign_streaming(66560)

    assert headers['Authorization'] == [(
        'AWS4-HMAC-SHA256 '
        'Credential=AKIAIOSFODNN7EXAMPLE/20130524/us-east-1/s3/aws4_request, '
        'SignedHeaders=content-encoding;content-length;host;x-amz-content-sha256;x-amz-date;'
        'x-amz-decoded-content-length;x-amz-storage-class, '
        'Signature=4f232c4386841ef735655705268965c44a0e4690baa4adea153f7db9fa80a0a9'
    )]
    assert headers['Content-Length'] == ['66824']
    assert headers['X-Amz-Decoded-Content-Length'] == ['66560']
    assert headers['Content-Encoding'] == ['aws-chunked']
    assert headers['X-Amz-Content-SHA256'] == ['STREAMING-AWS4-HMAC-SHA256-PAYLOAD']

    c1 = cs.sign_chunk(b'a' * 65536)
    assert c1.startswith(b'10000;chunk-signature=ad80c730a21e5b8d04586a2213dd63b9a0e99e0e2307b0ade35a65485a288648\r\n')
    assert c1.endswith(b'a\r\n')
    c2 = cs.sign_chunk(b'a' * 1024)
    assert c2.startswith(b'400;chunk-signature=0055627c9e194cb4542bae2aa5492e3c1575bbb81b612b7d234b86a503ef5497\r\n')
    c3 = cs.final_chunk()
    assert c3 == b'0;chunk-signature=b6c6ea8a5354eaf15b3cb7646744f4275b71ea724fed81ceb9323e279d449df9\r\n\r\n'
    assert len(c1) + len(c2) + len(c3) == 66824


def test_encode_and_lengths():
    cs_size = 8192
    for n in [0, 1, cs_size - 1, cs_size, cs_size + 1, 2 * cs_size, 2 * cs_size + 5]:
        headers, cs = _sign_streaming(n, cs_size)
        enc = auth.aws_chunked_encode(b'x' * n, signer=cs)
        assert len(enc) == auth.aws_chunked_encoded_length(n, cs_size) == int(headers['Content-Length'][0]), n


def test_misuse():
    with pytest.raises(ValueError):  # noqa
        _sign_streaming(10, 1024)

    with pytest.raises(ValueError):  # noqa
        _signer().sign_streaming(
            auth.AwsSigner.Request(method='PUT', url='https://x.s3.amazonaws.com/k', payload=b'nope'),
            decoded_length=4,
            chunk_size=8192,
        )

    _, cs = _sign_streaming(20000, 8192)
    with pytest.raises(ValueError):  # noqa
        cs.sign_chunk(b'x' * 100)  # short, but not the last
    with pytest.raises(ValueError):  # noqa
        cs.sign_chunk(b'')
    with pytest.raises(ValueError):  # noqa
        cs.final_chunk()
    cs.sign_chunk(b'x' * 8192)
    cs.sign_chunk(b'x' * 8192)
    with pytest.raises(ValueError):  # noqa
        cs.sign_chunk(b'x' * 8192)  # past the end
    cs.sign_chunk(b'x' * (20000 - 16384))
    cs.final_chunk()
    with pytest.raises(RuntimeError):
        cs.final_chunk()


def test_existing_content_encoding():
    headers, _ = _signer().sign_streaming(
        auth.AwsSigner.Request(
            method='PUT',
            url='https://x.s3.amazonaws.com/k',
            headers={'Content-Encoding': ['gzip']},
        ),
        decoded_length=4,
        chunk_size=8192,
    )
    assert headers['Content-Encoding'] == ['aws-chunked,gzip']
