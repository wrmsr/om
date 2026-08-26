import base64
import hashlib

import pytest

from .. import auth


def _der_length(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    encoded = length.to_bytes((length.bit_length() + 7) // 8, 'big')
    return bytes([0x80 | len(encoded)]) + encoded


def _der_value(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _der_length(len(value)) + value


def _der_integer(value: int) -> bytes:
    encoded = value.to_bytes((value.bit_length() + 7) // 8, 'big')
    if encoded[0] & 0x80:
        encoded = b'\0' + encoded
    return _der_value(0x02, encoded)


def _der_sequence(*values: bytes) -> bytes:
    return _der_value(0x30, b''.join(values))


def _public_numbers() -> tuple[int, int]:
    # The parser cannot prove that a modulus is a product of primes, and need not do so. This gives the structure tests
    # a correctly sized, odd value without depending on a third-party key generator.
    modulus = (1 << 2047) | (1 << 1024) | 0x12345
    return modulus, 65537


def _pkcs1_der(modulus: int, exponent: int) -> bytes:
    return _der_sequence(_der_integer(modulus), _der_integer(exponent))


def _spki_der(modulus: int, exponent: int, *, parameters: bytes = _der_value(0x05, b'')) -> bytes:
    algorithm = _der_sequence(_der_value(0x06, auth._RSA_ENCRYPTION_OID), parameters)  # noqa: SLF001
    return _der_sequence(algorithm, _der_value(0x03, b'\0' + _pkcs1_der(modulus, exponent)))


def _pem(label: str, der: bytes) -> bytes:
    encoded = base64.b64encode(der)
    body = b'\n'.join(encoded[i:i + 64] for i in range(0, len(encoded), 64))
    return b'-----BEGIN ' + label.encode() + b'-----\n' + body + b'\n-----END ' + label.encode() + b'-----\n'


@pytest.mark.parametrize(
    ('label', 'der'),
    [
        ('PUBLIC KEY', _spki_der),
        ('RSA PUBLIC KEY', _pkcs1_der),
    ],
)
def test_load_rsa_public_key_pem(label, der):
    numbers = _public_numbers()
    assert auth._load_rsa_public_key_pem(_pem(label, der(*numbers))) == numbers  # noqa: SLF001


def test_load_spki_without_null_parameters():
    numbers = _public_numbers()
    assert auth._load_rsa_public_key_pem(  # noqa: SLF001
        _pem('PUBLIC KEY', _spki_der(*numbers, parameters=b'')),
    ) == numbers


@pytest.mark.parametrize(
    ('public_key', 'match'),
    [
        (b'', 'invalid RSA public-key PEM'),
        (b'not a key', 'invalid RSA public-key PEM'),
        (b'-----BEGIN CERTIFICATE-----\nAA==\n-----END CERTIFICATE-----\n', 'unsupported .* envelope'),
        (b'-----BEGIN PUBLIC KEY-----\n%%%\n-----END PUBLIC KEY-----\n', 'invalid base64'),
        (b'-----BEGIN PUBLIC KEY-----\nAA==\n-----END RSA PUBLIC KEY-----\n', 'unsupported .* envelope'),
    ],
)
def test_load_rsa_public_key_pem_rejects_bad_envelopes(public_key, match):
    with pytest.raises(ValueError, match=match):
        auth._load_rsa_public_key_pem(public_key)  # noqa: SLF001


def test_parse_rsa_public_key_rejects_trailing_data():
    modulus, exponent = _public_numbers()
    with pytest.raises(ValueError, match='trailing'):
        auth._parse_pkcs1_rsa_public_key(_pkcs1_der(modulus, exponent) + b'\0')  # noqa: SLF001


def test_parse_rsa_public_key_rejects_nonminimal_integer():
    modulus, exponent = _public_numbers()
    modulus_bytes = modulus.to_bytes((modulus.bit_length() + 7) // 8, 'big')
    bad_modulus = _der_value(0x02, b'\0\0' + modulus_bytes)
    with pytest.raises(ValueError, match='non-minimal DER INTEGER'):
        auth._parse_pkcs1_rsa_public_key(  # noqa: SLF001
            _der_sequence(bad_modulus, _der_integer(exponent)),
        )


def test_parse_rsa_public_key_rejects_negative_integer():
    _, exponent = _public_numbers()
    bad_modulus = _der_value(0x02, b'\x80' + bytes(127))
    with pytest.raises(ValueError, match='negative DER INTEGER'):
        auth._parse_pkcs1_rsa_public_key(  # noqa: SLF001
            _der_sequence(bad_modulus, _der_integer(exponent)),
        )


def test_parse_spki_rejects_wrong_algorithm():
    modulus, exponent = _public_numbers()
    algorithm = _der_sequence(_der_value(0x06, bytes.fromhex('2a8648ce3d0201')))
    der = _der_sequence(algorithm, _der_value(0x03, b'\0' + _pkcs1_der(modulus, exponent)))
    with pytest.raises(ValueError, match='not an rsaEncryption key'):
        auth._parse_spki_rsa_public_key(der)  # noqa: SLF001


def test_parse_spki_rejects_unused_bits():
    modulus, exponent = _public_numbers()
    algorithm = _der_sequence(
        _der_value(0x06, auth._RSA_ENCRYPTION_OID),  # noqa: SLF001
        _der_value(0x05, b''),
    )
    der = _der_sequence(algorithm, _der_value(0x03, b'\x01' + _pkcs1_der(modulus, exponent)))
    with pytest.raises(ValueError, match='unused bits'):
        auth._parse_spki_rsa_public_key(der)  # noqa: SLF001


@pytest.mark.parametrize(
    ('modulus', 'exponent', 'match'),
    [
        ((1 << 511) | 1, 65537, 'too small'),
        ((1 << 1024), 65537, 'must be odd'),
        ((1 << 1024) | 1, 2, 'odd integer'),
        ((1 << 1024) | 1, 1 << 65 | 1, 'exponent is too large'),
    ],
)
def test_validate_rsa_public_numbers(modulus, exponent, match):
    with pytest.raises(ValueError, match=match):
        auth._validate_rsa_public_numbers(modulus, exponent)  # noqa: SLF001


def test_mgf1_sha1_known_value():
    # Fixed regression value for the MGF1 definition.
    assert auth._mgf1_sha1(b'seed', 37).hex() == (  # noqa: SLF001
        '09d8db2214e56d4dec8f9a3099b851a46886fe3f'
        '682e3c4f6a35ff98dd072c1124a6b7b411'
    )


def test_oaep_seed_validation():
    modulus, exponent = _public_numbers()
    with pytest.raises(ValueError, match='exactly 20 bytes'):
        auth._rsa_oaep_sha1_encrypt(b'message', modulus, exponent, seed=b'bad')  # noqa: SLF001


def test_xor_password_rejects_empty_salt():
    with pytest.raises(ValueError, match='salt'):
        auth.xor_password(b'password', b'')


def test_sha2_rsa_encrypt_cross_checks_with_cryptography():
    hashes = pytest.importorskip('cryptography.hazmat.primitives.hashes')
    serialization = pytest.importorskip('cryptography.hazmat.primitives.serialization')
    padding_module = pytest.importorskip('cryptography.hazmat.primitives.asymmetric.padding')
    rsa = pytest.importorskip('cryptography.hazmat.primitives.asymmetric.rsa')

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    padding = padding_module.OAEP(
        mgf=padding_module.MGF1(hashes.SHA1()),  # noqa: S303
        algorithm=hashes.SHA1(),  # noqa: S303
        label=None,
    )
    password = b'pass_caching_sha2_01234567890123456789'  # noqa: S105
    salt = bytes(range(1, 21))
    expected_plaintext = auth.xor_password(password + b'\0', salt)

    for public_format in (
            serialization.PublicFormat.SubjectPublicKeyInfo,
            serialization.PublicFormat.PKCS1,
    ):
        pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            public_format,
        )
        first = auth.sha2_rsa_encrypt(password, salt, pem)
        second = auth.sha2_rsa_encrypt(password, salt, pem)
        assert first != second
        assert len(first) == 256
        assert private_key.decrypt(first, padding) == expected_plaintext
        assert private_key.decrypt(second, padding) == expected_plaintext


def test_deterministic_oaep_cross_checks_with_cryptography():
    hashes = pytest.importorskip('cryptography.hazmat.primitives.hashes')
    padding = pytest.importorskip('cryptography.hazmat.primitives.asymmetric.padding')
    rsa = pytest.importorskip('cryptography.hazmat.primitives.asymmetric.rsa')

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    numbers = private_key.public_key().public_numbers()
    ciphertext = auth._rsa_oaep_sha1_encrypt(  # noqa: SLF001
        b'deterministic message',
        numbers.n,
        numbers.e,
        seed=bytes(range(hashlib.sha1().digest_size)),  # noqa: S324
    )
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA1()),  # noqa: S303
            algorithm=hashes.SHA1(),  # noqa: S303
            label=None,
        ),
    )
    assert plaintext == b'deterministic message'


def test_sha2_rsa_encrypt_rejects_message_too_long():
    serialization = pytest.importorskip('cryptography.hazmat.primitives.serialization')
    rsa = pytest.importorskip('cryptography.hazmat.primitives.asymmetric.rsa')

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with pytest.raises(ValueError, match='message is too long'):
        auth.sha2_rsa_encrypt(bytes(100), bytes(range(20)), pem)
