import os.path
import ssl

import pytest

from ...tests.dbs import CA_PEM
from ..sockets import make_ssl_context


needs_ca = pytest.mark.skipif(not os.path.exists(CA_PEM), reason='no server CA certificate available')


def test_make_ssl_context_from_existing_context():
    ctx = ssl.create_default_context()
    assert make_ssl_context(ctx) is ctx


def test_make_ssl_context_no_ca_disables_verification():
    ctx = make_ssl_context({})
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False


def test_make_ssl_context_no_ca_verify_mode_strings():
    for value in ('none', '0', 'no', 'false', False):
        assert make_ssl_context({'verify_mode': value}).verify_mode == ssl.CERT_NONE


@needs_ca
def test_make_ssl_context_verify_identity_and_mode():
    ctx = make_ssl_context({'ca': CA_PEM, 'check_hostname': True, 'verify_mode': True})
    assert ctx.check_hostname is True
    assert ctx.verify_mode == ssl.CERT_REQUIRED


@needs_ca
def test_make_ssl_context_verify_mode_strings():
    for value in ('required', '1', 'yes', 'true', True):
        assert make_ssl_context({'ca': CA_PEM, 'verify_mode': value}).verify_mode == ssl.CERT_REQUIRED
    assert make_ssl_context({'ca': CA_PEM, 'verify_mode': 'optional'}).verify_mode == ssl.CERT_OPTIONAL


@needs_ca
def test_make_ssl_context_relaxes_strict_verification():
    # MySQL's auto-generated self signed certs don't pass 3.13+ strict verification.
    ctx = make_ssl_context({'ca': CA_PEM})
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)
