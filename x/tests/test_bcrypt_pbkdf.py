# ruff: noqa: SLF001
import hashlib
import random
import struct
import typing as ta
import warnings

import bcrypt
import cryptography.exceptions as cry_exc
import cryptography.hazmat.decrepit.ciphers.algorithms as cry_decrepit
import cryptography.hazmat.primitives.ciphers as cry_ciphers
import pytest

from .. import bcrypt_pbkdf as sut


_BACKENDS = (
    'bcrypt',
    'stdlib',
)

# (password, salt, key_len, rounds, expected). The first is the widely published bcrypt_pbkdf vector; the rest were
# generated with bcrypt 5.0.0. All are kept deliberately cheap, as every block-round costs the stdlib backend a few
# hundred milliseconds.
_KNOWN_VECTORS = (
    (
        b'password',
        b'salt',
        32,
        4,
        (
            '5bbf0cc293587f1c3635555c27796598'
            'd47e579071bf427e9d8fbe842aba34d9'
        ),
    ),
    (
        b'p',
        b's',
        1,
        1,
        'ca',
    ),
    (
        b'\x00binary\xff',
        bytes(range(16)),
        33,
        1,
        (
            'e59bc40c094c6924e7dca53582e3a59d'
            'a365321340be6dd001c73f977a25fafe'
            '72'
        ),
    ),
    (
        b'a' * 200,
        bytes(range(64)),
        64,
        1,
        (
            '2a39714cce5a402dd27a72536e81d273'
            '8502587c4bfef10385bf916c64644f60'
            '76c06b8e874a0fd050818f37e7e3fe40'
            '0248ad7b4de8ab665917dd892ffd143e'
        ),
    ),
)

# (key, plaintext, ciphertext), from the standard Blowfish ECB test vectors.
_BLOWFISH_VECTORS = (
    ('0000000000000000', '0000000000000000', '4ef997456198dd78'),
    ('ffffffffffffffff', 'ffffffffffffffff', '51866fd5b85ecb8a'),
    ('3000000000000000', '1000000000000001', '7d856f9a613063f2'),
)


def _reference_kdf(password: bytes, salt: bytes, key_len: int, rounds: int) -> bytes:
    return bcrypt.kdf(password, salt, key_len, rounds, ignore_few_rounds=True)


def _reference_bcrypt_pbkdf_with_hash(
        password: bytes,
        salt: bytes,
        key_len: int,
        rounds: int,
        bcrypt_hash: ta.Callable[[bytes, bytes], bytes],
) -> bytes:
    """A literal transcription of the loop in OpenBSD's bcrypt_pbkdf.c, parameterised on its hash."""

    stride = (key_len + 32 - 1) // 32
    amt = (key_len + stride - 1) // stride

    sha2pass = hashlib.sha512(password).digest()

    key = bytearray(key_len)
    remaining = key_len
    count = 1
    while remaining > 0:
        sha2salt = hashlib.sha512(salt + struct.pack('>I', count)).digest()
        tmpout = bcrypt_hash(sha2pass, sha2salt)
        out = bytearray(tmpout)

        for _ in range(1, rounds):
            sha2salt = hashlib.sha512(tmpout).digest()
            tmpout = bcrypt_hash(sha2pass, sha2salt)
            for j in range(len(out)):
                out[j] ^= tmpout[j]

        amt = min(amt, remaining)
        i = 0
        while i < amt:
            dest = i * stride + (count - 1)
            if dest >= key_len:
                break
            key[dest] = out[i]
            i += 1
        remaining -= i
        count += 1

    return bytes(key)


def _fake_bcrypt_hash(sha2pass: bytes, sha2salt: bytes) -> bytes:
    return hashlib.sha256(sha2pass + sha2salt).digest()


def _stdlib_blowfish_encrypt_block(key: bytes, block: bytes) -> bytes:
    """Standard Blowfish, assembled from the stdlib backend's tables, key schedule, and block function."""

    state = tuple(list(table) for table in sut._load_initial_tables())
    sut._expand_state(state, sut._cyclic_words(key, sut._NUM_P_WORDS))
    return struct.pack('>2I', *sut._encipher(state, *struct.unpack('>2I', block)))


def _randbytes(rng: random.Random, length: int) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(length))


def test_all_expected_backends_are_available() -> None:
    # The test environment is expected to contain the optional dependency.
    assert sut.available_backends() == _BACKENDS


@pytest.mark.parametrize(('password', 'salt', 'key_len', 'rounds', 'expected_hex'), _KNOWN_VECTORS)
@pytest.mark.parametrize('backend', _BACKENDS)
def test_known_vectors(
        password: bytes,
        salt: bytes,
        key_len: int,
        rounds: int,
        expected_hex: str,
        backend: str,
) -> None:
    expected = bytes.fromhex(expected_hex)
    assert sut.bcrypt_pbkdf(password, salt, key_len, rounds, backend=backend) == expected


@pytest.mark.parametrize(('password', 'salt', 'key_len', 'rounds', '_'), _KNOWN_VECTORS)
def test_bcrypt_backend_is_exact_reference(
        password: bytes,
        salt: bytes,
        key_len: int,
        rounds: int,
        _: str,
) -> None:
    expected = _reference_kdf(password, salt, key_len, rounds)
    assert sut.bcrypt_pbkdf_bcrypt(password, salt, key_len, rounds) == expected


def test_randomized_cross_backend_equivalence() -> None:
    rng = random.Random(0xBC2F9)

    # (key_len, rounds), covering one-, two-, and three-block layouts. The known vectors already pin the remaining
    # truncated shapes.
    shapes = (
        (32, 2),
        (48, 1),
        (65, 1),
    )
    salt_lengths = (1, 16, 65)

    for index, (key_len, rounds) in enumerate(shapes):
        password = _randbytes(rng, rng.randrange(1, 257))
        salt = _randbytes(rng, salt_lengths[index % len(salt_lengths)])
        expected = _reference_kdf(password, salt, key_len, rounds)

        assert sut.bcrypt_pbkdf_bcrypt(password, salt, key_len, rounds) == expected
        assert sut.bcrypt_pbkdf_stdlib(password, salt, key_len, rounds) == expected


@pytest.mark.slow
@pytest.mark.parametrize('rounds', [16, 24])
def test_stdlib_matches_bcrypt_at_ssh_keygen_work_factors(rounds: int) -> None:
    # A 48-byte key is an AES-256 key plus its IV, as derived for an encrypted OpenSSH private key file.
    password = b'correct horse battery staple'
    salt = bytes(range(16))

    expected = _reference_kdf(password, salt, 48, rounds)
    assert sut.bcrypt_pbkdf_stdlib(password, salt, 48, rounds) == expected


def test_reference_transcription_matches_bcrypt() -> None:
    actual = _reference_bcrypt_pbkdf_with_hash(b'password', b'salt', 33, 1, sut._bcrypt_hash)
    assert actual == _reference_kdf(b'password', b'salt', 33, 1)


@pytest.mark.parametrize('rounds', [1, 2, 5])
def test_stdlib_output_layout_for_every_key_length(
        rounds: int,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The real hash is far too slow to sweep every length, so check the block iteration and interleaving separately
    # from it, against the transcription anchored above.
    monkeypatch.setattr(sut, '_bcrypt_hash', _fake_bcrypt_hash)

    for key_len in range(1, sut.MAX_KEY_LEN + 1):
        expected = _reference_bcrypt_pbkdf_with_hash(b'password', b'salt', key_len, rounds, _fake_bcrypt_hash)
        assert sut.bcrypt_pbkdf_stdlib(b'password', b'salt', key_len, rounds) == expected


def test_initial_tables_are_the_digits_of_pi() -> None:
    p, *sboxes = sut._load_initial_tables()

    assert len(p) == 18
    assert [len(sbox) for sbox in sboxes] == [256] * 4

    assert (p[0], p[-1]) == (0x243F6A88, 0x8979FB1B)
    assert (sboxes[0][0], sboxes[-1][-1]) == (0xD1310BA6, 0x3AC372E6)


@pytest.mark.parametrize(('key_hex', 'plaintext_hex', 'ciphertext_hex'), _BLOWFISH_VECTORS)
def test_stdlib_blowfish_core_known_vectors(
        key_hex: str,
        plaintext_hex: str,
        ciphertext_hex: str,
) -> None:
    actual = _stdlib_blowfish_encrypt_block(bytes.fromhex(key_hex), bytes.fromhex(plaintext_hex))
    assert actual == bytes.fromhex(ciphertext_hex)


def test_stdlib_blowfish_core_matches_openssl() -> None:
    # Independent of the bcrypt package: with an unsalted schedule from the initial tables, the stdlib core is standard
    # Blowfish, which cryptography can still reach where OpenSSL's legacy provider is loaded.
    rng = random.Random(0xB10F15)

    for key_len in (4, 8, 16, 17, 32, 56):
        key = _randbytes(rng, key_len)
        block = _randbytes(rng, 8)

        try:
            cipher = cry_ciphers.Cipher(cry_decrepit.Blowfish(key), cry_ciphers.modes.ECB())  # noqa: S305
            encryptor = cipher.encryptor()
        except cry_exc.UnsupportedAlgorithm:
            pytest.skip('this OpenSSL build does not provide Blowfish')
        expected = encryptor.update(block) + encryptor.finalize()

        assert _stdlib_blowfish_encrypt_block(key, block) == expected


def test_bcrypt_backend_does_not_warn_at_ssh_keygen_work_factors() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert len(sut.bcrypt_pbkdf_bcrypt(b'password', b'salt', 48, 16)) == 48


@pytest.mark.parametrize(
    ('password', 'salt', 'key_len', 'rounds', 'expected_exception'),
    [
        (b'', b'salt', 32, 1, ValueError),
        (b'password', b'', 32, 1, ValueError),
        (b'password', b'salt', 0, 1, ValueError),
        (b'password', b'salt', sut.MAX_KEY_LEN + 1, 1, ValueError),
        (b'password', b'salt', 32, 0, ValueError),
        ('password', b'salt', 32, 1, TypeError),
        (b'password', bytearray(b'salt'), 32, 1, TypeError),
    ],
)
@pytest.mark.parametrize('backend', _BACKENDS)
def test_invalid_arguments_are_rejected_like_the_reference(
        password: ta.Any,
        salt: ta.Any,
        key_len: int,
        rounds: int,
        expected_exception: type[Exception],
        backend: str,
) -> None:
    with pytest.raises(expected_exception):
        bcrypt.kdf(password, salt, key_len, rounds, ignore_few_rounds=True)

    with pytest.raises(expected_exception):
        sut.bcrypt_pbkdf(password, salt, key_len, rounds, backend=backend)


def test_default_auto_backend_prefers_bcrypt(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def native(password: bytes, salt: bytes, key_len: int, rounds: int) -> bytes:
        calls.append(('bcrypt', password, salt, key_len, rounds))
        return b'bcrypt'

    def should_not_run(password: bytes, salt: bytes, key_len: int, rounds: int) -> bytes:
        raise AssertionError('lower-priority backend ran')

    monkeypatch.setattr(sut, 'bcrypt_pbkdf_bcrypt', native)
    monkeypatch.setattr(sut, 'bcrypt_pbkdf_stdlib', should_not_run)

    assert sut.bcrypt_pbkdf(b'p', b's', 32, 1) == b'bcrypt'
    assert calls == [('bcrypt', b'p', b's', 32, 1)]


def test_auto_falls_through_unavailable_backends(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def unavailable(password: bytes, salt: bytes, key_len: int, rounds: int) -> bytes:
        calls.append('bcrypt')
        raise sut.BackendUnavailableError('bcrypt')

    def stdlib(password: bytes, salt: bytes, key_len: int, rounds: int) -> bytes:
        calls.append('stdlib')
        return b'stdlib'

    monkeypatch.setattr(sut, 'bcrypt_pbkdf_bcrypt', unavailable)
    monkeypatch.setattr(sut, 'bcrypt_pbkdf_stdlib', stdlib)

    assert sut.bcrypt_pbkdf(b'p', b's', 32, 1) == b'stdlib'
    assert calls == ['bcrypt', 'stdlib']


def test_explicit_backend_does_not_fall_through(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(password: bytes, salt: bytes, key_len: int, rounds: int) -> bytes:
        raise sut.BackendUnavailableError('deliberate')

    def should_not_run(password: bytes, salt: bytes, key_len: int, rounds: int) -> bytes:
        raise AssertionError('explicit selection fell through')

    monkeypatch.setattr(sut, 'bcrypt_pbkdf_bcrypt', unavailable)
    monkeypatch.setattr(sut, 'bcrypt_pbkdf_stdlib', should_not_run)

    with pytest.raises(sut.BackendUnavailableError, match='deliberate'):
        sut.bcrypt_pbkdf(b'p', b's', 32, 1, backend='bcrypt')


def test_unknown_backend_is_rejected() -> None:
    with pytest.raises(ValueError, match='unknown bcrypt_pbkdf backend'):
        sut.bcrypt_pbkdf(b'p', b's', 32, 1, backend='wat')