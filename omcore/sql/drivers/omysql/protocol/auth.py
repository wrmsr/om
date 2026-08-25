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
"""The pure computations of the client authentication plugins. The exchanges themselves live in the session."""
import hashlib
import typing as ta

from ..... import lang


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
