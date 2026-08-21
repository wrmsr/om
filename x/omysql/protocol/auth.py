"""The pure computations of the client authentication plugins. The exchanges themselves live in the session."""
import hashlib
import typing as ta

from omcore import lang


with lang.auto_proxy_import(globals()):
    from cryptography.hazmat.primitives import hashes as chp_hash
    from cryptography.hazmat.primitives import serialization as chp_ser
    from cryptography.hazmat.primitives.asymmetric import padding as chp_pad


##


SCRAMBLE_LENGTH = 20


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b, strict=False))


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
    return bytes(c ^ salt[i % len(salt)] for i, c in enumerate(password))


def sha2_rsa_encrypt(password: bytes, salt: bytes, public_key: bytes) -> bytes:
    """Encrypts a password with the server's public key, as the sha256_password and caching_sha2_password plugins do."""

    message = xor_password(password + b'\0', salt)
    rsa_key = chp_ser.load_pem_public_key(public_key)
    return ta.cast(ta.Any, rsa_key).encrypt(
        message,
        chp_pad.OAEP(
            mgf=chp_pad.MGF1(algorithm=chp_hash.SHA1()),  # noqa: S303
            algorithm=chp_hash.SHA1(),  # noqa: S303
            label=None,
        ),
    )


def _scalar_clamp(s32: bytes) -> bytes:
    ba = bytearray(s32)
    return bytes([ba[0] & 248]) + bytes(s32[1:31]) + bytes([(ba[31] & 127) | 64])


def ed25519_password(password: bytes, scramble: bytes) -> bytes:
    """Signs a scramble with Ed25519 keys derived from the password, as the client_ed25519 plugin does."""

    try:
        from nacl import bindings as nb  # noqa: PLC0415
    except ImportError:
        raise RuntimeError("'pynacl' package is required for ed25519_password auth method") from None

    h = hashlib.sha512(password).digest()
    s = _scalar_clamp(h[:32])
    r = nb.crypto_core_ed25519_scalar_reduce(hashlib.sha512(h[32:] + scramble).digest())
    R = nb.crypto_scalarmult_ed25519_base_noclamp(r)  # noqa: N806
    A = nb.crypto_scalarmult_ed25519_base_noclamp(s)  # noqa: N806
    k = nb.crypto_core_ed25519_scalar_reduce(hashlib.sha512(R + A + scramble).digest())
    S = nb.crypto_core_ed25519_scalar_add(nb.crypto_core_ed25519_scalar_mul(k, s), r)  # noqa: N806
    return R + S
