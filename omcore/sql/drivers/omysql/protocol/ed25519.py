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
MariaDB ``client_ed25519`` password authentication, with three interchangeable backends:

* ``'nacl'`` - the same PyNaCl/libsodium operations used by PyMySQL.
* ``'cryptography'`` - a deliberately private-API-dependent backend that uses
  ``cryptography.hazmat.bindings._rust.openssl.x25519`` for native scalar multiplication, then reconstructs and converts
  the Edwards point.
* ``'stdlib'`` - a compact pure-Python Ed25519 implementation.
* ``'auto'`` - try the preceding backends in that order (the default).

The stdlib implementation, and the Python glue around the cryptography backend, are not constant-time. Prefer the PyNaCl
backend where local timing or cache side channels are in scope.
"""
import functools
import hashlib
import typing as ta


# Extended Edwards point (X, Y, Z, T), representing x=X/Z, y=Y/Z, and XY=ZT. These formulas are complete for
# edwards25519.
_Point: ta.TypeAlias = tuple[int, int, int, int]


##


# Base field and prime-order subgroup parameters for edwards25519.
_P = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = 37095705934669439343138083508754565189542113879843219016388785533085940283555

# RFC 7748 / RFC 8032 Ed25519 base point.
_BASE_X = 15112221349535400772501151409588531511454012693041857206046113283949847762202
_BASE_Y = 46316835694926478169428394003475163141307993866256225615783033603165251855960

_IDENTITY: _Point = (0, 1, 1, 0)
_BASE: _Point = (_BASE_X, _BASE_Y, 1, (_BASE_X * _BASE_Y) % _P)

# Montgomery Curve25519 parameters and the RFC 7748 base point.
_MONT_A = 486662
_MONT_BASE_U = 9
_MONT_BASE_V = 14781619447589544791020593568409986887264606134616475288964881837755586237401
_MONT_TO_EDWARDS_C = 51042569399160536130206135233146329284152202253034631822681833788666877215207


class BackendUnavailableError(RuntimeError):
    """The requested optional backend cannot be used in this environment."""


class _CryptographyX25519(ta.NamedTuple):
    module: ta.Any
    base_public_key: ta.Any


def _scalar_clamp(s32: bytes) -> bytes:
    """Perform RFC 8032 Ed25519 pruning on a 32-byte scalar buffer."""

    if len(s32) != 32:
        raise ValueError('an Ed25519 scalar buffer must be exactly 32 bytes')

    out = bytearray(s32)
    out[0] &= 248
    out[31] &= 127
    out[31] |= 64
    return bytes(out)


def _point_add(p: _Point, q: _Point) -> _Point:
    """Add extended Edwards points using the complete RFC 8032 formula."""

    x1, y1, z1, t1 = p
    x2, y2, z2, t2 = q

    a = ((y1 - x1) * (y2 - x2)) % _P
    b = ((y1 + x1) * (y2 + x2)) % _P
    c = (2 * _D * t1 * t2) % _P
    d = (2 * z1 * z2) % _P
    e = (b - a) % _P
    f = (d - c) % _P
    g = (d + c) % _P
    h = (b + a) % _P

    return (
        (e * f) % _P,
        (g * h) % _P,
        (f * g) % _P,
        (e * h) % _P,
    )


def _point_neg(p: _Point) -> _Point:
    x, y, z, t = p
    return ((-x) % _P, y, z, (-t) % _P)


def _point_mul_base(scalar: int) -> _Point:
    """Return ``[scalar]B`` in extended Edwards coordinates."""

    scalar %= _L
    result = _IDENTITY
    addend = _BASE

    # L has 253 bits. A fixed iteration count avoids the most obvious scalar-bit-length timing leak, but Python integer
    # arithmetic and the conditional below still make this unsuitable as constant-time code.
    for bit in range(_L.bit_length()):
        if (scalar >> bit) & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)

    return result


def _point_encode(p: _Point) -> bytes:
    x, y, z, _ = p
    z_inv = pow(z, _P - 2, _P)
    x = (x * z_inv) % _P
    y = (y * z_inv) % _P

    encoded = bytearray(y.to_bytes(32, 'little'))
    encoded[31] |= (x & 1) << 7
    return bytes(encoded)


def _base_mult_stdlib(scalar: int) -> bytes:
    return _point_encode(_point_mul_base(scalar))


def _ed25519_password_with_base_mult(
        password: bytes,
        scramble: bytes,
        base_mult: ta.Callable[[int], bytes],
) -> bytes:
    """Implement the PyMySQL/MariaDB signing construction."""

    h = hashlib.sha512(password).digest()
    s = int.from_bytes(_scalar_clamp(h[:32]), 'little')

    r = int.from_bytes(hashlib.sha512(h[32:] + scramble).digest(), 'little') % _L
    r_encoded = base_mult(r)
    a_encoded = base_mult(s)

    k = int.from_bytes(
        hashlib.sha512(r_encoded + a_encoded + scramble).digest(),
        'little',
    ) % _L
    signature_scalar = (r + k * s) % _L

    return r_encoded + signature_scalar.to_bytes(32, 'little')


@functools.lru_cache(maxsize=1)
def _load_nacl_bindings() -> ta.Any:
    try:
        from nacl import bindings
    except ImportError as exc:
        raise BackendUnavailableError('PyNaCl is not installed') from exc

    required = (
        'crypto_core_ed25519_scalar_reduce',
        'crypto_scalarmult_ed25519_base_noclamp',
        'crypto_core_ed25519_scalar_mul',
        'crypto_core_ed25519_scalar_add',
    )
    missing = [name for name in required if not callable(getattr(bindings, name, None))]
    if missing:
        raise BackendUnavailableError('PyNaCl lacks required libsodium functions: ' + ', '.join(missing))

    # Minimal libsodium builds can leave wrappers present while making the operations raise UnavailableError, so probe
    # all four required families.
    zero = bytes(32)
    one = (1).to_bytes(32, 'little')
    two = (2).to_bytes(32, 'little')
    try:
        reduced = bindings.crypto_core_ed25519_scalar_reduce(bytes(64))
        product = bindings.crypto_core_ed25519_scalar_mul(one, one)
        total = bindings.crypto_core_ed25519_scalar_add(one, one)
        base = bindings.crypto_scalarmult_ed25519_base_noclamp(one)
    except Exception as exc:
        raise BackendUnavailableError("PyNaCl's required Ed25519 arithmetic is unavailable") from exc

    if (
            reduced != zero or
            product != one or
            total != two or
            base != _point_encode(_BASE)
    ):
        raise BackendUnavailableError('PyNaCl failed its Ed25519 backend self-test')

    return bindings


def ed25519_password_nacl(password: bytes, scramble: bytes) -> bytes:
    """Use the same PyNaCl/libsodium operations as PyMySQL's implementation."""

    bindings = _load_nacl_bindings()

    h = hashlib.sha512(password).digest()
    s = _scalar_clamp(h[:32])

    r = hashlib.sha512(h[32:] + scramble).digest()
    r = bindings.crypto_core_ed25519_scalar_reduce(r)
    r_encoded = bindings.crypto_scalarmult_ed25519_base_noclamp(r)
    a_encoded = bindings.crypto_scalarmult_ed25519_base_noclamp(s)

    k = hashlib.sha512(r_encoded + a_encoded + scramble).digest()
    k = bindings.crypto_core_ed25519_scalar_reduce(k)
    ks = bindings.crypto_core_ed25519_scalar_mul(k, s)
    signature_scalar = bindings.crypto_core_ed25519_scalar_add(ks, r)

    return r_encoded + signature_scalar


def ed25519_password_stdlib(password: bytes, scramble: bytes) -> bytes:
    """Use only hashlib and Python integer arithmetic."""

    return _ed25519_password_with_base_mult(password, scramble, _base_mult_stdlib)


def _x25519_clamped_representative(scalar: int) -> bytes | None:
    """
    Find an X25519 input whose clamped scalar is congruent to ±scalar mod L.

    X25519 accepts only scalars of the form ``2**254 + 8*k`` after decoding. Its output is only a Montgomery
    u-coordinate, for which P and -P are indistinguishable. Therefore either residue ``scalar`` or ``-scalar`` is
    suitable here.
    """

    scalar %= _L
    low = 1 << 254
    high = 1 << 255

    for residue in (scalar, (-scalar) % _L):
        first_multiple = (low - residue + _L - 1) // _L
        last_multiple = (high - 1 - residue) // _L

        for multiple in range(first_multiple, last_multiple + 1):
            candidate = residue + multiple * _L
            if candidate & 7:
                continue

            raw = candidate.to_bytes(32, 'little')
            # Be defensive about the exact private backend's X25519 decoding.
            if _scalar_clamp(raw) == raw:
                return raw

    return None


@functools.lru_cache(maxsize=1)
def _load_cryptography_x25519() -> _CryptographyX25519:
    """Load and probe cryptography's non-public Rust/OpenSSL X25519 module."""

    try:
        from cryptography.hazmat.bindings import _rust
    except ImportError as exc:
        raise BackendUnavailableError("cryptography's Rust bindings are unavailable") from exc

    try:
        module = _rust.openssl.x25519
        from_private_bytes = module.from_private_bytes
        from_public_bytes = module.from_public_bytes
    except (AttributeError, ImportError) as exc:
        raise BackendUnavailableError("cryptography's private _rust.openssl.x25519 API is unavailable") from exc

    if not callable(from_private_bytes) or not callable(from_public_bytes):
        raise BackendUnavailableError("cryptography's private X25519 constructors are not callable")

    base_bytes = _MONT_BASE_U.to_bytes(32, 'little')
    try:
        base_public_key = from_public_bytes(base_bytes)
        private_bytes = _x25519_clamped_representative(1)
        if private_bytes is None:
            raise AssertionError('could not represent scalar one')
        probe = bytes(from_private_bytes(private_bytes).exchange(base_public_key))
    except Exception as exc:
        raise BackendUnavailableError("cryptography's private X25519 operations failed their probe") from exc

    # The chosen scalar is ±1 modulo L, so its u-coordinate must still be 9.
    if probe != base_bytes:
        raise BackendUnavailableError("cryptography's private X25519 API failed its scalar semantics self-test")

    return _CryptographyX25519(module, base_public_key)


def _x25519_base_u(private_bytes: bytes, ctx: _CryptographyX25519) -> int:
    output = bytes(ctx.module.from_private_bytes(private_bytes).exchange(ctx.base_public_key))
    if len(output) != 32:
        raise BackendUnavailableError("cryptography's private X25519 exchange returned a non-32-byte value")
    return int.from_bytes(output, 'little') % _P


def _recover_montgomery_v(u: int, u_plus_base: int) -> int:
    """
    Recover v(P) from u(P) and u(P+B), where B is the fixed base point.

    On ``v² = u³ + A*u² + u``, affine addition gives

        u(P+B) = ((v_B-v_P)/(u_B-u_P))² - A - u_P - u_B.

    Rearranging that equation determines the sign of v(P), which an X25519 u-coordinate by itself intentionally omits.
    """

    if u == _MONT_BASE_U:
        raise BackendUnavailableError('cannot recover a Montgomery v-coordinate at ±the base point')

    curve_rhs = (u * u * u + _MONT_A * u * u + u) % _P
    delta_u = (_MONT_BASE_U - u) % _P
    squared_numerator = ((u_plus_base + _MONT_A + u + _MONT_BASE_U) * delta_u * delta_u) % _P

    numerator = (_MONT_BASE_V * _MONT_BASE_V + curve_rhs - squared_numerator) % _P
    denominator_inv = pow((2 * _MONT_BASE_V) % _P, _P - 2, _P)
    v = (numerator * denominator_inv) % _P

    if (v * v - curve_rhs) % _P:
        raise BackendUnavailableError('cryptography X25519 coordinates failed Montgomery point recovery')

    return v


def _montgomery_to_edwards(u: int, v: int) -> _Point:
    if u == _P - 1 or v == 0:
        raise BackendUnavailableError('encountered a singular Montgomery/Edwards map')

    x = (_MONT_TO_EDWARDS_C * u * pow(v, _P - 2, _P)) % _P
    y = ((u - 1) * pow((u + 1) % _P, _P - 2, _P)) % _P

    # Validate the conversion before letting a changed private backend produce a plausible-looking but incorrect
    # authentication response.
    if (-x * x + y * y - 1 - _D * x * x * y * y) % _P:
        raise BackendUnavailableError('cryptography X25519 output did not map to an Ed25519 point')

    return (x, y, 1, (x * y) % _P)


def _base_mult_cryptography_with_ctx(
        scalar: int,
        ctx: _CryptographyX25519,
) -> bytes:
    """
    Compute ``[scalar]B`` using private cryptography X25519 operations.

    X25519 exposes only u-coordinates and only after mandatory scalar clamping. We therefore:

    1. shift to a nearby scalar ``a = scalar + shift`` for which both ``a``
       and ``a+1`` have valid clamped representatives modulo L;
    2. ask the private X25519 backend for u([a]B) and u([a+1]B); 3. recover v([a]B), convert the point to Edwards form;
    and 4. subtract ``[shift]B`` using the tiny stdlib point implementation.
    """

    scalar %= _L
    if scalar == 0:
        return _point_encode(_IDENTITY)

    # In normal cases shift is 0 or 1. The bounded search is deliberately generous and turns any unexpected
    # scalar-decoding behavior into a clean backend-unavailable result, allowing the automatic stdlib fallback.
    for shift in range(256):
        shifted = (scalar + shift) % _L
        shifted_plus_one = (shifted + 1) % _L

        # u(B) == u(-B), making the affine recovery denominator singular; the identity likewise has no finite Montgomery
        # u-coordinate.
        if shifted in (0, 1, _L - 1) or shifted_plus_one == 0:
            continue

        private_a = _x25519_clamped_representative(shifted)
        if private_a is None:
            continue
        private_a_plus_one = _x25519_clamped_representative(shifted_plus_one)
        if private_a_plus_one is None:
            continue

        u_a = _x25519_base_u(private_a, ctx)
        u_a_plus_one = _x25519_base_u(private_a_plus_one, ctx)
        v_a = _recover_montgomery_v(u_a, u_a_plus_one)
        point = _montgomery_to_edwards(u_a, v_a)

        if shift:
            point = _point_add(point, _point_neg(_point_mul_base(shift)))

        return _point_encode(point)

    raise BackendUnavailableError("could not adapt an Ed25519 scalar to cryptography's private X25519 API")


@functools.lru_cache(maxsize=1)
def _load_cryptography_backend() -> _CryptographyX25519:
    ctx = _load_cryptography_x25519()

    # Exercise scalar adaptation, sign recovery, and the birational map, not merely the presence of private function
    # names, before advertising or automatically selecting this brittle backend.
    for scalar in (2, 8, _L - 2):
        actual = _base_mult_cryptography_with_ctx(scalar, ctx)
        if actual != _base_mult_stdlib(scalar):
            raise BackendUnavailableError("cryptography's private X25519 backend failed its Ed25519 self-test")

    return ctx


def _base_mult_cryptography(scalar: int) -> bytes:
    return _base_mult_cryptography_with_ctx(
        scalar,
        _load_cryptography_backend(),
    )


def ed25519_password_cryptography(password: bytes, scramble: bytes) -> bytes:
    """Use cryptography's private X25519 backend for fixed-base multiplication."""

    return _ed25519_password_with_base_mult(
        password,
        scramble,
        _base_mult_cryptography,
    )


def available_backends() -> tuple[str, ...]:
    """Return the explicit backend names usable in the current process."""

    available = []

    try:
        _load_nacl_bindings()
    except BackendUnavailableError:
        pass
    else:
        available.append('nacl')

    try:
        _load_cryptography_backend()
    except BackendUnavailableError:
        pass
    else:
        available.append('cryptography')

    available.append('stdlib')
    return tuple(available)


def ed25519_password(
        password: bytes,
        scramble: bytes,
        *,
        backend: str = 'auto',
) -> bytes:
    """
    Return the 64-byte MariaDB ``client_ed25519`` authentication response.

    Explicit backend selection never falls through silently; only ``backend='auto'`` does so.
    """

    implementations = {
        'nacl': ed25519_password_nacl,
        'cryptography': ed25519_password_cryptography,
        'stdlib': ed25519_password_stdlib,
    }

    if backend == 'auto':
        errors = []
        for name in ('nacl', 'cryptography', 'stdlib'):
            try:
                return implementations[name](password, scramble)
            except BackendUnavailableError as exc:
                errors.append((name, exc))

        # The stdlib backend has no optional dependencies, so this is only reachable after an internal programming error
        # represented as a BackendUnavailableError exception.
        detail = '; '.join(f'{name}: {exc}' for name, exc in errors)
        raise BackendUnavailableError('no Ed25519 backend is usable: ' + detail)

    try:
        implementation = implementations[backend]
    except KeyError:
        choices = ', '.join(('auto', *tuple(implementations)))
        raise ValueError(f'unknown Ed25519 backend {backend!r}; expected one of {choices}') from None

    return implementation(password, scramble)
