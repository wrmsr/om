"""
OpenBSD ``bcrypt_pbkdf``, the key derivation function behind passphrase-encrypted OpenSSH private key files
(``openssh-key-v1`` with a ``bcrypt`` kdfname), with two interchangeable backends:

* ``'bcrypt'`` - the PyCA ``bcrypt`` package's native ``kdf``.
* ``'stdlib'`` - a compact pure-Python implementation using only hashlib and struct.
* ``'auto'`` - try the preceding backends in that order (the default).

The stdlib backend exists because the underlying primitive - Blowfish's salted, repeatedly re-keyed 'eksblowfish'
schedule - cannot be reached through ``cryptography``, whose Blowfish exposes only OpenSSL's standard key schedule. It
is roughly two orders of magnitude slower than the native backend: on the order of 10-20 seconds rather than 150-250
milliseconds for a 48-byte key at ssh-keygen's 16 or 24 rounds. Its key-dependent table lookups are also not
constant-time. Prefer the bcrypt backend where either matters.

Cost is linear in both ``rounds`` and ``ceil(key_len / 32)``. When ``rounds`` is read from an untrusted key file, bound
it before calling.

The algorithm follows OpenBSD's ``bcrypt_pbkdf.c`` by Ted Unangst.
"""
import functools
import hashlib
import struct
import typing as ta


# The Blowfish P-array followed by its four S-boxes, mutated in place by the key schedule.
_State: ta.TypeAlias = tuple[list[int], ...]


##


MAX_KEY_LEN = 512

# One bcrypt_hash output block.
_HASH_SIZE = 32

_MASK32 = 0xFFFFFFFF

# Blowfish's initial state is an 18-word P-array and four 256-word S-boxes, filled in that order from the fractional
# hexadecimal digits of pi.
_NUM_P_WORDS = 18
_NUM_SBOXES = 4
_SBOX_SIZE = 256
_NUM_TABLE_WORDS = _NUM_P_WORDS + _NUM_SBOXES * _SBOX_SIZE

# SHA-256 of those 1042 words packed big-endian.
_INITIAL_TABLES_SHA256 = 'b5643208907b11b20e499a42187dc921f9579d28dadfccbe69a5ce232a55952f'

# The fixed plaintext which bcrypt_hash repeatedly enciphers.
_HASH_PLAINTEXT = b'OxychromaticBlowfishSwatDynamite'
_HASH_KEY_SCHEDULE_ROUNDS = 64
_HASH_ENCIPHER_ROUNDS = 64

# The widely published bcrypt_pbkdf answer for a 32-byte key at 4 rounds, used to probe the optional backend.
_PROBE_PASSWORD = b'password'
_PROBE_SALT = b'salt'
_PROBE_ROUNDS = 4
_PROBE_KEY = bytes.fromhex(
    '5bbf0cc293587f1c3635555c27796598'
    'd47e579071bf427e9d8fbe842aba34d9',
)


class BackendUnavailableError(RuntimeError):
    """The requested optional backend cannot be used in this environment."""


def _check_args(password: bytes, salt: bytes, key_len: int, rounds: int) -> None:
    """Apply the bcrypt package's argument rules up front, so every backend accepts and rejects the same inputs."""

    if not isinstance(password, bytes) or not isinstance(salt, bytes):
        raise TypeError('password and salt must be bytes')
    if not password or not salt:
        raise ValueError('password and salt must not be empty')
    if not 1 <= key_len <= MAX_KEY_LEN:
        raise ValueError(f'key_len must be 1-{MAX_KEY_LEN}')
    if rounds < 1:
        raise ValueError('rounds must be 1 or more')


def _pi_fraction_words(n: int) -> tuple[int, ...]:
    """Return the first ``n`` 32-bit words of the fractional part of pi."""

    # Fixed-point Machin formula: pi = 16*atan(1/5) - 4*atan(1/239). Every truncating division loses under one unit in
    # the last place, so the guard bits comfortably absorb the accumulated error of the few thousand terms summed.
    guard_bits = 64
    one = 1 << (n * 32 + guard_bits)

    def atan_inv(x: int) -> int:
        term = one // x
        total = term
        x_squared = x * x
        divisor = 1
        sign = -1
        while term:
            term //= x_squared
            divisor += 2
            total += sign * (term // divisor)
            sign = -sign
        return total

    pi = 16 * atan_inv(5) - 4 * atan_inv(239)
    fraction = (pi - 3 * one) >> guard_bits
    return struct.unpack(f'>{n}I', fraction.to_bytes(n * 4, 'big'))


@functools.lru_cache(maxsize=1)
def _load_initial_tables() -> tuple[tuple[int, ...], ...]:
    """Compute, verify, and split Blowfish's initial P-array and S-boxes."""

    words = _pi_fraction_words(_NUM_TABLE_WORDS)

    packed = struct.pack(f'>{_NUM_TABLE_WORDS}I', *words)
    if hashlib.sha256(packed).hexdigest() != _INITIAL_TABLES_SHA256:
        raise BackendUnavailableError('the stdlib Blowfish tables failed their integrity check')

    return (
        words[:_NUM_P_WORDS],
        *(
            words[start:start + _SBOX_SIZE]
            for start in range(_NUM_P_WORDS, _NUM_TABLE_WORDS, _SBOX_SIZE)
        ),
    )


def _cyclic_words(data: bytes, n: int) -> tuple[int, ...]:
    """Read ``n`` big-endian 32-bit words from ``data``, wrapping around at its end."""

    size = n * 4
    repeated = data * -(-size // len(data))
    return struct.unpack(f'>{n}I', repeated[:size])


def _encipher(state: _State, left: int, right: int) -> tuple[int, int]:
    """Encipher one 64-bit block, given and returned as two 32-bit words."""

    p, s0, s1, s2, s3 = state

    # The first addition of each round function may carry into bit 32, but the XOR which follows leaves that bit alone,
    # so a single trailing mask yields the same low 32 bits as reducing after every step.
    left ^= p[0]
    for i in range(1, 17, 2):
        right ^= p[i] ^ (
            (((s0[left >> 24] + s1[left >> 16 & 0xFF]) ^ s2[left >> 8 & 0xFF]) + s3[left & 0xFF]) & _MASK32
        )
        left ^= p[i + 1] ^ (
            (((s0[right >> 24] + s1[right >> 16 & 0xFF]) ^ s2[right >> 8 & 0xFF]) + s3[right & 0xFF]) & _MASK32
        )

    return right ^ p[17], left


def _expand_state(
        state: _State,
        key: ta.Sequence[int],
        data: ta.Sequence[int] | None = None,
) -> None:
    """
    Re-key ``state`` in place.

    ``key`` is 18 cyclic key words. With ``data`` - one cyclic word per table word - this is OpenBSD's salted
    ``Blowfish_expandstate``; without it, ``Blowfish_expand0state``, which from the initial tables is also the standard
    Blowfish key schedule.
    """

    p = state[0]
    for i in range(_NUM_P_WORDS):
        p[i] ^= key[i]

    # A single chained block is repeatedly enciphered under the evolving state, each output overwriting the next two
    # words of the P-array and then of each S-box in turn.
    left = right = 0
    j = 0
    for table in state:
        for i in range(0, len(table), 2):
            if data is not None:
                left ^= data[j]
                right ^= data[j + 1]
                j += 2
            left, right = _encipher(state, left, right)
            table[i] = left
            table[i + 1] = right


def _bcrypt_hash(sha2pass: bytes, sha2salt: bytes) -> bytes:
    """Return the 32-byte bcrypt_hash of two SHA-512 digests."""

    state: _State = tuple(list(table) for table in _load_initial_tables())

    pass_key = _cyclic_words(sha2pass, _NUM_P_WORDS)
    salt_key = _cyclic_words(sha2salt, _NUM_P_WORDS)

    _expand_state(state, pass_key, _cyclic_words(sha2salt, _NUM_TABLE_WORDS))
    for _ in range(_HASH_KEY_SCHEDULE_ROUNDS):
        _expand_state(state, salt_key)
        _expand_state(state, pass_key)

    words = list(struct.unpack('>8I', _HASH_PLAINTEXT))
    for _ in range(_HASH_ENCIPHER_ROUNDS):
        for i in range(0, len(words), 2):
            words[i], words[i + 1] = _encipher(state, words[i], words[i + 1])

    # The plaintext is read as big-endian words, but the reference writes each result word out least-significant byte
    # first.
    return struct.pack('<8I', *words)


def bcrypt_pbkdf_stdlib(
        password: bytes,
        salt: bytes,
        key_len: int,
        rounds: int,
) -> bytes:
    """Use only hashlib, struct, and Python integer arithmetic."""

    _check_args(password, salt, key_len, rounds)

    sha2pass = hashlib.sha512(password).digest()

    # This is PBKDF2 in shape, with bcrypt_hash as the PRF, except that the output blocks are interleaved rather than
    # concatenated: byte i of block b lands at index i * num_blocks + b, and a short key simply truncates that layout.
    num_blocks = -(-key_len // _HASH_SIZE)

    key = bytearray(key_len)
    for block in range(num_blocks):
        sha2salt = hashlib.sha512(salt + (block + 1).to_bytes(4, 'big')).digest()
        digest = _bcrypt_hash(sha2pass, sha2salt)
        accumulated = int.from_bytes(digest, 'big')

        for _ in range(rounds - 1):
            sha2salt = hashlib.sha512(digest).digest()
            digest = _bcrypt_hash(sha2pass, sha2salt)
            accumulated ^= int.from_bytes(digest, 'big')

        out = accumulated.to_bytes(_HASH_SIZE, 'big')
        key[block::num_blocks] = out[:len(range(block, key_len, num_blocks))]

    return bytes(key)


@functools.lru_cache(maxsize=1)
def _load_bcrypt_kdf() -> ta.Callable[..., bytes]:
    try:
        import bcrypt
    except ImportError as exc:
        raise BackendUnavailableError('bcrypt is not installed') from exc

    kdf = getattr(bcrypt, 'kdf', None)
    if not callable(kdf):
        raise BackendUnavailableError('bcrypt lacks the kdf function')

    # Probe the exact call shape used below, including the keyword which silences the low-round warning.
    try:
        probe = kdf(
            _PROBE_PASSWORD,
            _PROBE_SALT,
            len(_PROBE_KEY),
            _PROBE_ROUNDS,
            ignore_few_rounds=True,
        )
    except Exception as exc:
        raise BackendUnavailableError("bcrypt's kdf is unavailable") from exc

    if probe != _PROBE_KEY:
        raise BackendUnavailableError('bcrypt failed its kdf self-test')

    return kdf


def bcrypt_pbkdf_bcrypt(
        password: bytes,
        salt: bytes,
        key_len: int,
        rounds: int,
) -> bytes:
    """Use the PyCA bcrypt package's native implementation."""

    _check_args(password, salt, key_len, rounds)

    kdf = _load_bcrypt_kdf()

    # OpenSSH key files sit far below the package's 50-round warning threshold. The work factor was chosen by whoever
    # wrote the key file, so the warning has no audience here.
    return kdf(password, salt, key_len, rounds, ignore_few_rounds=True)


def available_backends() -> tuple[str, ...]:
    """Return the explicit backend names usable in the current process."""

    available = []

    try:
        _load_bcrypt_kdf()
    except BackendUnavailableError:
        pass
    else:
        available.append('bcrypt')

    available.append('stdlib')
    return tuple(available)


def bcrypt_pbkdf(
        password: bytes,
        salt: bytes,
        key_len: int,
        rounds: int,
        *,
        backend: str = 'auto',
) -> bytes:
    """
    Derive ``key_len`` bytes from ``password`` and ``salt`` using ``rounds`` iterations of bcrypt_pbkdf.

    Explicit backend selection never falls through silently; only ``backend='auto'`` does so.
    """

    implementations = {
        'bcrypt': bcrypt_pbkdf_bcrypt,
        'stdlib': bcrypt_pbkdf_stdlib,
    }

    if backend == 'auto':
        errors = []
        for name in ('bcrypt', 'stdlib'):
            try:
                return implementations[name](password, salt, key_len, rounds)
            except BackendUnavailableError as exc:
                errors.append((name, exc))

        # The stdlib backend has no optional dependencies, so this is only reachable after an internal programming error
        # represented as a BackendUnavailableError exception.
        detail = '; '.join(f'{name}: {exc}' for name, exc in errors)
        raise BackendUnavailableError('no bcrypt_pbkdf backend is usable: ' + detail)

    try:
        implementation = implementations[backend]
    except KeyError:
        choices = ', '.join(('auto', *tuple(implementations)))
        raise ValueError(f'unknown bcrypt_pbkdf backend {backend!r}; expected one of {choices}') from None

    return implementation(password, salt, key_len, rounds)
