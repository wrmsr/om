# ruff: noqa: SLF001
import hashlib
import random
import typing as ta

import cryptography.hazmat.primitives.asymmetric.ed25519 as chp_ed25519
import nacl.bindings
import pytest

from .. import ed25519 as sut


_BACKENDS = (
    'nacl',
    'cryptography',
    'stdlib',
)

_KNOWN_VECTORS = (
    (
        b'',
        b'',
        (
            '0dfcfc18188978b11ad410bd8c8da062'
            'a8c8dcf67d1ee418d4ec6e8c2eb59b4d'
            '723c5723f91cc4aa691d55f03a57e131'
            'a4232c11ceab04be6014779087796700'
        ),
    ),
    (
        b'password',
        bytes(range(32)),
        (
            '768662da1e0f760cdf3da47dabbc5028'
            '084fd0e0a3833619c15380cf47ea2a75'
            'dfd07752265f614275a3bde143a43da9'
            'de6f696cb824c67ddce77bc4d22b430e'
        ),
    ),
    (
        b'\x00binary\xff',
        b'scramble',
        (
            '40b8ec6b52d17994aeb584841a220ac5'
            'ff066bf2c536a9f4fdca1da7d02f1ff8'
            '92c76b318e6086df4d182b8d0337f3e9'
            'a805bb4e8a4e0ac23df91ec439ff5902'
        ),
    ),
    (
        b'a' * 200,
        bytes(range(64)),
        (
            'f03eccd9d7f237176c69e8cc27b34c45'
            '9770a4112d708e2a9db9fbb0c3b5dbe9'
            '34c8be5cb23f53a05450aec66324dd3d'
            'dd1030c8d1bf44b4e7e17910c128e303'
        ),
    ),
)


def _reference_ed25519_password(password: bytes, scramble: bytes) -> bytes:
    """The current PyMySQL algorithm, independently expressed with PyNaCl."""

    h = hashlib.sha512(password).digest()
    s: ta.Any = bytearray(h[:32])
    s[0] &= 248
    s[31] &= 127
    s[31] |= 64
    s = bytes(s)

    r = nacl.bindings.crypto_core_ed25519_scalar_reduce(
        hashlib.sha512(h[32:] + scramble).digest(),
    )
    r_encoded = nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(r)
    a_encoded = nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(s)

    k = nacl.bindings.crypto_core_ed25519_scalar_reduce(
        hashlib.sha512(r_encoded + a_encoded + scramble).digest(),
    )
    signature_scalar = nacl.bindings.crypto_core_ed25519_scalar_add(
        nacl.bindings.crypto_core_ed25519_scalar_mul(k, s),
        r,
    )
    return r_encoded + signature_scalar


def _randbytes(rng: random.Random, length: int) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(length))


def test_all_expected_backends_are_available() -> None:
    # The test environment is expected to contain both optional dependencies. This intentionally catches a future
    # cryptography private-API break.
    assert set(sut.available_backends()) == set(_BACKENDS)


@pytest.mark.parametrize(('password', 'scramble', 'expected_hex'), _KNOWN_VECTORS)
@pytest.mark.parametrize('backend', _BACKENDS)
def test_known_vectors(
        password: bytes,
        scramble: bytes,
        expected_hex: str,
        backend: str,
) -> None:
    expected = bytes.fromhex(expected_hex)
    assert sut.ed25519_password(password, scramble, backend=backend) == expected


@pytest.mark.parametrize(('password', 'scramble', '_'), _KNOWN_VECTORS)
def test_nacl_backend_is_exact_reference(
        password: bytes,
        scramble: bytes,
        _: str,
) -> None:
    expected = _reference_ed25519_password(password, scramble)
    assert sut.ed25519_password_nacl(password, scramble) == expected


def test_randomized_cross_backend_equivalence() -> None:
    rng = random.Random(0xED25519)
    scramble_lengths = (0, 1, 20, 31, 32, 33, 64, 255)

    for index in range(96):
        password = _randbytes(rng, rng.randrange(0, 257))
        scramble = _randbytes(rng, scramble_lengths[index % len(scramble_lengths)])
        expected = _reference_ed25519_password(password, scramble)

        assert sut.ed25519_password_nacl(password, scramble) == expected
        assert sut.ed25519_password_cryptography(password, scramble) == expected
        assert sut.ed25519_password_stdlib(password, scramble) == expected


@pytest.mark.parametrize(
    'scalar',
    [
        1,
        2,
        3,
        7,
        8,
        9,
        15,
        16,
        31,
        32,
        255,
        256,
        2**128 + 0x123456789ABCDEF,
        2**252,
        sut._L - 2,
        sut._L - 1,
    ],
)
def test_base_multiplication_matches_libsodium(scalar: int) -> None:
    canonical = scalar % sut._L
    assert canonical != 0

    expected = nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(
        canonical.to_bytes(32, 'little'),
    )
    assert sut._base_mult_stdlib(scalar) == expected
    assert sut._base_mult_cryptography(scalar) == expected


def test_zero_scalar_is_identity() -> None:
    identity = b'\x01' + b'\x00' * 31
    assert sut._base_mult_stdlib(0) == identity
    assert sut._base_mult_cryptography(0) == identity


@pytest.mark.parametrize(('password', 'scramble', '_'), _KNOWN_VECTORS)
@pytest.mark.parametrize('backend', _BACKENDS)
def test_result_is_a_standard_verifiable_ed25519_signature(
        password: bytes,
        scramble: bytes,
        _: str,
        backend: str,
) -> None:
    signature = sut.ed25519_password(password, scramble, backend=backend)
    assert len(signature) == 64
    assert int.from_bytes(signature[32:], 'little') < sut._L

    h = hashlib.sha512(password).digest()
    public_scalar = int.from_bytes(sut._scalar_clamp(h[:32]), 'little')
    public_bytes = sut._base_mult_stdlib(public_scalar)
    chp_ed25519.Ed25519PublicKey.from_public_bytes(public_bytes).verify(signature, scramble)


def test_default_auto_backend_prefers_nacl(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def nacl(password: bytes, scramble: bytes) -> bytes:
        calls.append(('nacl', password, scramble))
        return b'nacl'

    def should_not_run(password: bytes, scramble: bytes) -> bytes:
        raise AssertionError('lower-priority backend ran')

    monkeypatch.setattr(sut, 'ed25519_password_nacl', nacl)
    monkeypatch.setattr(sut, 'ed25519_password_cryptography', should_not_run)
    monkeypatch.setattr(sut, 'ed25519_password_stdlib', should_not_run)

    assert sut.ed25519_password(b'p', b's') == b'nacl'
    assert calls == [('nacl', b'p', b's')]


def test_auto_falls_through_unavailable_backends(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def unavailable(name: str):
        def run(password: bytes, scramble: bytes) -> bytes:
            calls.append(name)
            raise sut.BackendUnavailableError(name)
        return run

    def stdlib(password: bytes, scramble: bytes) -> bytes:
        calls.append('stdlib')
        return b'stdlib'

    monkeypatch.setattr(sut, 'ed25519_password_nacl', unavailable('nacl'))
    monkeypatch.setattr(
        sut,
        'ed25519_password_cryptography',
        unavailable('cryptography'),
    )
    monkeypatch.setattr(sut, 'ed25519_password_stdlib', stdlib)

    assert sut.ed25519_password(b'p', b's') == b'stdlib'
    assert calls == ['nacl', 'cryptography', 'stdlib']


def test_explicit_backend_does_not_fall_through(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(password: bytes, scramble: bytes) -> bytes:
        raise sut.BackendUnavailableError('deliberate')

    def should_not_run(password: bytes, scramble: bytes) -> bytes:
        raise AssertionError('explicit selection fell through')

    monkeypatch.setattr(sut, 'ed25519_password_nacl', unavailable)
    monkeypatch.setattr(sut, 'ed25519_password_cryptography', should_not_run)
    monkeypatch.setattr(sut, 'ed25519_password_stdlib', should_not_run)

    with pytest.raises(sut.BackendUnavailableError, match='deliberate'):
        sut.ed25519_password(b'p', b's', backend='nacl')


def test_unknown_backend_is_rejected() -> None:
    with pytest.raises(ValueError, match='unknown Ed25519 backend'):
        sut.ed25519_password(b'p', b's', backend='wat')
