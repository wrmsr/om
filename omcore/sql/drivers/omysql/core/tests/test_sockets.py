import os.path
import ssl

import pytest

from ..sockets import make_ssl_context


def skip_if_no_ca(ca_pem):
    if not os.path.exists(ca_pem):
        pytest.skip('no server CA certificate available')


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


def test_make_ssl_context_verify_identity_and_mode(ca_pem):
    skip_if_no_ca(ca_pem)
    ctx = make_ssl_context({'ca': ca_pem, 'check_hostname': True, 'verify_mode': True})
    assert ctx.check_hostname is True
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_make_ssl_context_verify_mode_strings(ca_pem):
    skip_if_no_ca(ca_pem)
    for value in ('required', '1', 'yes', 'true', True):
        assert make_ssl_context({'ca': ca_pem, 'verify_mode': value}).verify_mode == ssl.CERT_REQUIRED
    assert make_ssl_context({'ca': ca_pem, 'verify_mode': 'optional'}).verify_mode == ssl.CERT_OPTIONAL


def test_make_ssl_context_relaxes_strict_verification(ca_pem):
    skip_if_no_ca(ca_pem)
    # MySQL's auto-generated self signed certs don't pass 3.13+ strict verification.
    ctx = make_ssl_context({'ca': ca_pem})
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)
