# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
The RSA path intentionally implements only the public-key formats and RSAES-OAEP-SHA1 operation used by MySQL. Python
big-integer arithmetic is not constant-time; prefer TLS where local timing or cache side channels are in scope.
"""
import base64
import binascii
import hashlib
import secrets


##


SCRAMBLE_LENGTH = 20


_RSA_ENCRYPTION_OID = bytes.fromhex('2a864886f70d010101')
_RSA_MIN_MODULUS_BITS = 1024
_RSA_MAX_MODULUS_BITS = 16384
_RSA_MAX_PUBLIC_EXPONENT_BITS = 64
_RSA_MAX_PEM_LENGTH = 64 * 1024
_RSA_MAX_DER_LENGTH = 32 * 1024


class _DerReader:
    """A deliberately tiny, strict DER reader for the two RSA public-key structures accepted below."""

    def __init__(self, data: bytes | memoryview) -> None:
        super().__init__()

        self._data = memoryview(data)
        self._pos = 0

    @property
    def at_end(self) -> bool:
        return self._pos == len(self._data)

    def _read(self, size: int) -> memoryview:
        if size < 0 or size > len(self._data) - self._pos:
            raise ValueError('truncated DER value')
        start = self._pos
        self._pos += size
        return self._data[start:self._pos]

    def _read_byte(self) -> int:
        return self._read(1)[0]

    def _read_length(self) -> int:
        first = self._read_byte()
        if first < 0x80:
            return first

        size = first & 0x7f
        if not size:
            raise ValueError('indefinite DER lengths are not permitted')
        # The complete accepted key is capped at 32 KiB, so more than four length octets can only be malicious or
        # broken.
        if size > 4:
            raise ValueError('DER length is too large')

        encoded = self._read(size)
        if encoded[0] == 0:
            raise ValueError('non-minimal DER length')
        length = int.from_bytes(encoded, 'big')
        if length < 0x80:
            raise ValueError('non-minimal DER length')
        return length

    def read_value(self, tag: int) -> memoryview:
        actual_tag = self._read_byte()
        if actual_tag != tag:
            raise ValueError(f'expected DER tag 0x{tag:02x}, got 0x{actual_tag:02x}')
        return self._read(self._read_length())

    def read_nested(self, tag: int) -> _DerReader:
        return _DerReader(self.read_value(tag))

    def require_end(self) -> None:
        if not self.at_end:
            raise ValueError('trailing data in DER value')


def _read_der_positive_integer(reader: _DerReader) -> int:
    encoded = reader.read_value(0x02)
    if not encoded:
        raise ValueError('empty DER INTEGER')
    if encoded[0] & 0x80:
        raise ValueError('negative DER INTEGER')
    if len(encoded) > 1 and encoded[0] == 0 and not encoded[1] & 0x80:
        raise ValueError('non-minimal DER INTEGER')

    value = int.from_bytes(encoded, 'big')
    if not value:
        raise ValueError('RSA public-key integers must be positive')
    return value


def _validate_rsa_public_numbers(modulus: int, exponent: int) -> None:
    modulus_bits = modulus.bit_length()
    if modulus_bits < _RSA_MIN_MODULUS_BITS:
        raise ValueError(f'RSA modulus is too small ({modulus_bits} bits)')
    if modulus_bits > _RSA_MAX_MODULUS_BITS:
        raise ValueError(f'RSA modulus is too large ({modulus_bits} bits)')
    if not modulus & 1:
        raise ValueError('RSA modulus must be odd')

    if exponent < 3 or not exponent & 1:
        raise ValueError('RSA public exponent must be an odd integer of at least 3')
    if exponent >= modulus:
        raise ValueError('RSA public exponent must be smaller than the modulus')
    if exponent.bit_length() > _RSA_MAX_PUBLIC_EXPONENT_BITS:
        raise ValueError('RSA public exponent is too large')


def _parse_pkcs1_rsa_public_key(der: bytes | memoryview) -> tuple[int, int]:
    outer = _DerReader(der)
    key = outer.read_nested(0x30)
    outer.require_end()

    modulus = _read_der_positive_integer(key)
    exponent = _read_der_positive_integer(key)
    key.require_end()

    _validate_rsa_public_numbers(modulus, exponent)
    return modulus, exponent


def _parse_spki_rsa_public_key(der: bytes | memoryview) -> tuple[int, int]:
    outer = _DerReader(der)
    spki = outer.read_nested(0x30)
    outer.require_end()

    algorithm = spki.read_nested(0x30)
    if bytes(algorithm.read_value(0x06)) != _RSA_ENCRYPTION_OID:
        raise ValueError('public key is not an rsaEncryption key')
    # RFC 5280 requires rsaEncryption parameters to be NULL. Be liberal enough to accept encoders which omit them, but
    # reject every other parameter encoding.
    if not algorithm.at_end:
        if algorithm.read_value(0x05):
            raise ValueError('rsaEncryption parameters must be NULL')
    algorithm.require_end()

    subject_public_key = spki.read_value(0x03)
    if not subject_public_key:
        raise ValueError('empty SubjectPublicKeyInfo BIT STRING')
    if subject_public_key[0] != 0:
        raise ValueError('RSA SubjectPublicKeyInfo BIT STRING has unused bits')
    spki.require_end()

    return _parse_pkcs1_rsa_public_key(subject_public_key[1:])


def _load_rsa_public_key_pem(public_key: bytes) -> tuple[int, int]:
    if len(public_key) > _RSA_MAX_PEM_LENGTH:
        raise ValueError('RSA public-key PEM is too large')

    lines = public_key.strip().splitlines()
    if len(lines) < 3:
        raise ValueError('invalid RSA public-key PEM')

    begin = lines[0]
    end = lines[-1]
    if begin == b'-----BEGIN PUBLIC KEY-----' and end == b'-----END PUBLIC KEY-----':
        key_format = 'spki'
    elif begin == b'-----BEGIN RSA PUBLIC KEY-----' and end == b'-----END RSA PUBLIC KEY-----':
        key_format = 'pkcs1'
    else:
        raise ValueError('unsupported RSA public-key PEM envelope')

    body = b''.join(lines[1:-1])
    if not body:
        raise ValueError('empty RSA public-key PEM body')
    try:
        der = base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('invalid base64 in RSA public-key PEM') from exc
    if len(der) > _RSA_MAX_DER_LENGTH:
        raise ValueError('RSA public-key DER is too large')

    if key_format == 'spki':
        return _parse_spki_rsa_public_key(der)
    return _parse_pkcs1_rsa_public_key(der)


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError('cannot XOR byte strings of different lengths')
    return bytes(x ^ y for x, y in zip(a, b, strict=True))


def scramble_native_password(password: bytes, message: bytes) -> bytes:
    """The scramble of the mysql_native_password plugin."""

    if not password:
        return b''
    stage1 = hashlib.sha1(password).digest()  # noqa: S324
    stage2 = hashlib.sha1(stage1).digest()  # noqa: S324
    s = hashlib.sha1()  # noqa: S324
    s.update(message[:SCRAMBLE_LENGTH])
    s.update(stage2)
    return _xor_bytes(s.digest(), stage1)


def scramble_caching_sha2(password: bytes, nonce: bytes) -> bytes:
    """The fast path scramble of the caching_sha2_password plugin: XOR(SHA256(p), SHA256(SHA256(SHA256(p)), nonce))."""

    if not password:
        return b''
    p1 = hashlib.sha256(password).digest()
    p2 = hashlib.sha256(p1).digest()
    p3 = hashlib.sha256(p2 + nonce).digest()
    return _xor_bytes(p1, p3)


def xor_password(password: bytes, salt: bytes) -> bytes:
    salt = salt[:SCRAMBLE_LENGTH]
    if not salt:
        raise ValueError('password salt must not be empty')
    return bytes(c ^ salt[i % len(salt)] for i, c in enumerate(password))


def _mgf1_sha1(seed: bytes, length: int) -> bytes:
    if length < 0:
        raise ValueError('negative MGF1 output length')

    digest_size = hashlib.sha1().digest_size  # noqa: S324
    block_count = (length + digest_size - 1) // digest_size
    if block_count >= 1 << 32:
        raise ValueError('MGF1 output is too long')

    return b''.join(
        hashlib.sha1(seed + counter.to_bytes(4, 'big')).digest()  # noqa: S324
        for counter in range(block_count)
    )[:length]


def _rsa_oaep_sha1_encrypt(
        message: bytes,
        modulus: int,
        exponent: int,
        *,
        seed: bytes | None = None,
) -> bytes:
    """RSAES-OAEP-ENCRYPT with SHA-1 for both Hash and MGF1, as required by the MySQL authentication protocol."""

    _validate_rsa_public_numbers(modulus, exponent)
    modulus_size = (modulus.bit_length() + 7) // 8
    digest_size = hashlib.sha1().digest_size  # noqa: S324
    if len(message) > modulus_size - 2 * digest_size - 2:
        raise ValueError('message is too long for the RSA modulus and OAEP-SHA1')

    if seed is None:
        seed = secrets.token_bytes(digest_size)
    elif len(seed) != digest_size:
        raise ValueError(f'OAEP-SHA1 seed must be exactly {digest_size} bytes')

    label_hash = hashlib.sha1(b'').digest()  # noqa: S324
    padding = bytes(modulus_size - len(message) - 2 * digest_size - 2)
    data_block = label_hash + padding + b'\x01' + message

    masked_data_block = _xor_bytes(data_block, _mgf1_sha1(seed, len(data_block)))
    masked_seed = _xor_bytes(seed, _mgf1_sha1(masked_data_block, digest_size))
    encoded_message = b'\0' + masked_seed + masked_data_block

    message_representative = int.from_bytes(encoded_message, 'big')
    if message_representative >= modulus:  # Defensive: OAEP's leading zero makes this impossible for a valid modulus.
        raise ValueError('OAEP encoded message is out of range for the RSA modulus')
    ciphertext = pow(message_representative, exponent, modulus)
    return ciphertext.to_bytes(modulus_size, 'big')


def sha2_rsa_encrypt(password: bytes, salt: bytes, public_key: bytes) -> bytes:
    """Encrypt a password for the sha256_password and caching_sha2_password plugins, using only the stdlib."""

    message = xor_password(password + b'\0', salt)
    modulus, exponent = _load_rsa_public_key_pem(public_key)
    return _rsa_oaep_sha1_encrypt(message, modulus, exponent)
