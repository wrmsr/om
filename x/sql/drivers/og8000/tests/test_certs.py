import hashlib
import os.path
import shutil
import ssl
import subprocess
import tempfile

import pytest

from ..certs import tls_server_end_point


@pytest.fixture(scope='session')
def cert_dir():
    if shutil.which('openssl') is None:
        pytest.skip('no openssl')

    def run(*cmd: str) -> None:
        subprocess.check_call(
            cmd,
            cwd=td,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    with tempfile.TemporaryDirectory() as td:
        run(
            'openssl', 'req',
            '-x509',
            '-newkey', 'rsa:2048',
            '-nodes',
            '-sha256',
            '-days', '7',
            '-subj', '/CN=localhost',
            '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1',
            '-keyout', 'server.key',
            '-out', 'server.crt',
        )

        run(
            'chmod',
            '0600',
            'server.key',
        )

        yield td


@pytest.fixture(scope='session')
def cert_der(cert_dir):
    with open(os.path.join(cert_dir, 'server.crt')) as f:
        pem = f.read()

    return ssl.PEM_cert_to_DER_cert(pem)


def test_certificate_backends_agree(cert_der):
    cryptography_result = tls_server_end_point(
        cert_der,
        backend='cryptography',
    )

    asn1crypto_result = tls_server_end_point(
        cert_der,
        backend='asn1crypto',
    )

    assert cryptography_result == asn1crypto_result


def test_sha256_certificate(cert_der):
    expected = hashlib.sha256(cert_der).digest()

    assert tls_server_end_point(
        cert_der,
        backend='cryptography',
    ) == expected

    assert tls_server_end_point(
        cert_der,
        backend='asn1crypto',
    ) == expected
