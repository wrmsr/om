# MIT No Attribution
#
# Copyright The Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# https://codeberg.org/tlocke/scramp/src/commit/58a281a2b0570834a39e78dcc9d52aa8245c0aea
#
# Only the client half of scramp is vendored here - the server half is unused by this driver.
import base64
import collections
import enum
import functools
import hashlib
import hmac
import itertools
import operator
import secrets
import ssl
import stringprep
import types
import typing as ta
import unicodedata

from .certs import CertificateBackend
from .certs import tls_server_end_point


ChannelBindingTuple: ta.TypeAlias = tuple[str, bytes | ssl.SSLSocket | ssl.SSLObject]

HashFn: ta.TypeAlias = ta.Callable[..., ta.Any]


##


class ServerError(enum.Enum):
    INVALID_ENCODING = 'invalid-encoding'
    EXTENSIONS_NOT_SUPPORTED = 'extensions-not-supported'
    INVALID_PROOF = 'invalid-proof'
    CHANNEL_BINDINGS_DONT_MATCH = 'channel-bindings-dont-match'
    SERVER_DOES_SUPPORT_CHANNEL_BINDING = 'server-does-support-channel-binding'
    CHANNEL_BINDING_NOT_SUPPORTED = 'channel-binding-not-supported'
    UNSUPPORTED_CHANNEL_BINDING_TYPE = 'unsupported-channel-binding-type'
    UNKNOWN_USER = 'unknown-user'
    INVALID_USERNAME_ENCODING = 'invalid-username-encoding'
    NO_RESOURCES = 'no-resources'
    OTHER_ERROR = 'other-error'


class ScramError(Exception):
    def __init__(self, message: str, server_error: ServerError | None = None) -> None:
        super().__init__(message)

        if not isinstance(server_error, (types.NoneType, ServerError)):
            raise ScramError('Server error must be None or of type ServerError', ServerError.OTHER_ERROR)

        self.server_error = server_error

    def __str__(self) -> str:
        s_str = '' if self.server_error is None else f': {self.server_error.value}'
        return super().__str__() + s_str


def hmac_digest(hf: HashFn, key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg=msg, digestmod=hf).digest()


def pbkdf2_hmac_pure_python(hf: HashFn, password, salt, iterations):
    u = ui = hmac_digest(hf, password, salt + b'\x00\x00\x00\x01')
    for _ in range(int(iterations) - 1):
        ui = hmac_digest(hf, password, ui)
        u = xor(u, ui)
    return u


def pbkdf2_hmac_hashlib(hf: HashFn, password, salt, iterations):
    return hashlib.pbkdf2_hmac(hf().name, password, salt, int(iterations))


def hi(hf: HashFn, password, salt, iterations):
    if hasattr(hashlib, 'pbkdf2_hmac'):
        pbkdf2_hmac = pbkdf2_hmac_hashlib
    else:
        pbkdf2_hmac = pbkdf2_hmac_pure_python
    return hi_pbkdf2_hmac(pbkdf2_hmac, hf, password, salt, iterations)


def hi_pbkdf2_hmac(pbkdf2_hmac, hf: HashFn, password, salt, iterations):
    return pbkdf2_hmac(hf, password, salt, iterations)


def h(hf: HashFn, msg: bytes) -> bytes:
    return hf(msg).digest()


def xor(bytes1: bytes, bytes2: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(bytes1, bytes2, strict=True))


def b64enc(binary: bytes) -> str:
    return base64.b64encode(binary).decode('utf8')


def b64dec(string: str) -> bytes:
    try:
        return base64.b64decode(string, validate=True)
    except ValueError:
        raise ScramError('Invalid base 64 encoding', ServerError.INVALID_ENCODING) from None


def uenc(string: str) -> bytes:
    return string.encode('utf-8')


@functools.total_ordering
class IterationCount:
    MAX_ITERATION_COUNT: ta.ClassVar[int] = 10_000_000  # DoS guard
    MIN_ITERATION_COUNT: ta.ClassVar[int] = 4096  # Lowest recommended of any mechanism

    def __init__(self, value: int) -> None:
        if type(value) is not int:
            raise ScramError('The value must be an int', ServerError.OTHER_ERROR)

        if value > self.MAX_ITERATION_COUNT:
            raise ScramError(f'The value must not be > {self.MAX_ITERATION_COUNT}', ServerError.OTHER_ERROR)

        if value < self.MIN_ITERATION_COUNT:
            raise ScramError(f'The value must not be < {self.MIN_ITERATION_COUNT}', ServerError.OTHER_ERROR)

        self.value = value

    def __hash__(self) -> int:
        return hash((IterationCount, self.value))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IterationCount) and self.value == other.value

    def __lt__(self, other: object) -> object:
        if not isinstance(other, IterationCount):
            return NotImplemented
        return self.value < other.value

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def from_str(cls, value_str: str) -> ta.Self:
        for c in value_str:
            if not (c.isascii() and c.isdigit()):
                raise ScramError('The iteration count can only contain ASCII digits', ServerError.OTHER_ERROR)

        if len(value_str) == 0:
            raise ScramError('The iteration count must not be empty', ServerError.OTHER_ERROR)

        if value_str[0] == '0':
            raise ScramError('The iteration count must not begin with a zero', ServerError.OTHER_ERROR)

        try:
            value = int(value_str)
        except ValueError as e:
            raise ScramError('Server iteration count is not valid') from e

        return cls(value)


##
# https://tools.ietf.org/html/rfc5802
# https://www.rfc-editor.org/rfc/rfc7677.txt


@ta.final
class Salt:
    MIN_LENGTH: ta.ClassVar[int] = 12

    def __init__(self, salt: bytes) -> None:
        if type(salt) is not bytes:
            raise ScramError(
                f"The 'salt' must be of type bytes, but found type {type(salt)}",
                ServerError.OTHER_ERROR,
            )

        len_salt = len(salt)
        if len_salt < self.MIN_LENGTH:
            raise ScramError(
                f"The 'salt' is {len_salt} bytes long, but it must be at least {self.MIN_LENGTH} bytes long",
                ServerError.OTHER_ERROR,
            )

        self.salt = salt

    def __str__(self) -> str:
        return b64enc(self.salt)

    def __bytes__(self) -> bytes:
        return self.salt

    def __hash__(self) -> int:
        return hash((Salt, self.salt))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Salt) and self.salt == other.salt

    @classmethod
    def from_str(cls, s: str) -> ta.Self:
        return cls(b64dec(s))

    @classmethod
    def create(cls) -> ta.Self:
        return cls(secrets.token_bytes())


@ta.final
class Nonce:
    def __init__(self, nonce: str) -> None:
        if not isinstance(nonce, str):
            raise ScramError(
                f"The 'nonce' must be of type str, but found type {type(nonce)}",
                ServerError.OTHER_ERROR,
            )

        if not all(0x21 <= ord(c) <= 0x7E and c != ',' for c in nonce):
            raise ScramError('Nonce contains invalid characters', ServerError.OTHER_ERROR)

        if len(nonce) == 0:
            raise ScramError("An empty string isn't allowed", ServerError.OTHER_ERROR)

        self.nonce = nonce

    def __str__(self) -> str:
        return self.nonce

    def __hash__(self) -> int:
        return hash((Nonce, self.nonce))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nonce) and self.nonce == other.nonce

    def __add__(self, other: Nonce) -> Nonce:
        if not isinstance(other, Nonce):
            return NotImplemented

        return Nonce(self.nonce + other.nonce)

    def __len__(self) -> int:
        return len(self.nonce)

    def startswith(self, other: Nonce) -> bool:
        if not isinstance(other, Nonce):
            raise TypeError(f'expected Nonce, got {type(other).__name__}')

        return self.nonce.startswith(other.nonce)

    @classmethod
    def create(cls) -> ta.Self:
        return cls(secrets.token_hex())


@ta.final
class CbName:
    SUPPORTED_TYPES: ta.ClassVar[frozenset[str]] = frozenset({
        'tls-server-end-point',
        'tls-unique',
        'tls-unique-for-telnet',
    })

    UNSUPPORTED_TYPES: ta.ClassVar[frozenset[str]] = frozenset({
        'tls-exporter',
    })

    def __init__(self, cb_name):
        if not isinstance(cb_name, str):
            raise ScramError(
                f"The 'cb_name' must be of type str, but found type {type(cb_name)}",
                ServerError.OTHER_ERROR,
            )

        for c in cb_name:
            if not (c.isascii() and (c.isalpha() or c.isdigit() or c in '.-')):
                raise ScramError(
                    "The channel binding name must contain only ASCII characters that are alphabetic or a digit or '.' "
                    "or '-'",
                    ServerError.OTHER_ERROR,
                )

        if cb_name in self.UNSUPPORTED_TYPES:
            raise ScramError(
                f'The channel binding types {sorted(self.UNSUPPORTED_TYPES)} are not supported by Scramp. Please see '
                f'the README for details',
                ServerError.UNSUPPORTED_CHANNEL_BINDING_TYPE,
            )

        elif cb_name not in self.SUPPORTED_TYPES:
            raise ScramError(
                f'The channel binding type is not recognised by Scramp. The recognised types are '
                f'{sorted(self.SUPPORTED_TYPES | self.UNSUPPORTED_TYPES)}',
                ServerError.UNSUPPORTED_CHANNEL_BINDING_TYPE,
            )

        self.cb_name = cb_name

    def __str__(self) -> str:
        return self.cb_name

    def __repr__(self) -> str:
        return f"'{self}'"

    def __hash__(self) -> int:
        return hash((CbName, self.cb_name))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CbName) and self.cb_name == other.cb_name


@ta.final
class CBindData:
    def __init__(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise ScramError(
                f"The 'data' must be of type bytes, but found type {type(data)}",
                ServerError.OTHER_ERROR,
            )

        if len(data) == 0:
            raise ScramError("The 'data' can't be of zero length.", ServerError.OTHER_ERROR)

        self.data = data

    def __bytes__(self) -> bytes:
        return self.data

    def __hash__(self) -> int:
        return hash((CBindData, self.data))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CBindData) and self.data == other.data

    @classmethod
    def from_der(
            cls,
            der: bytes,
            *,
            certificate_backend: CertificateBackend = 'auto',
    ) -> ta.Self:
        try:
            cb_data = tls_server_end_point(
                der,
                backend=certificate_backend,
            )
        except Exception as e:
            raise ScramError('Problem loading certificate from DER', ServerError.OTHER_ERROR) from e

        return cls(cb_data)


@enum.unique
@ta.final
class ClientStage(enum.IntEnum):
    get_client_first = 1
    set_server_first = 2
    get_client_final = 3
    set_server_final = 4


def _check_stage(stages, current_stage, next_stage):
    if current_stage is None:
        if next_stage != 1:
            raise ScramError(f'The method {stages(1).name} must be called first.')

    elif current_stage == 4:
        raise ScramError('The authentication sequence has already finished.')

    elif next_stage != current_stage + 1:
        raise ScramError(f'The next method to be called is {stages(current_stage + 1).name}, not this method.')


Mech = collections.namedtuple(  # noqa
    'Mech', [
        'hf',
        'use_binding',
        'iteration_count',
        'strength',
    ],
)


MECHS = types.MappingProxyType({
    'SCRAM-SHA-1': Mech(hashlib.sha1, False, IterationCount(4096), 0),
    'SCRAM-SHA-256': Mech(hashlib.sha256, False, IterationCount(4096), 1),
    'SCRAM-SHA-512': Mech(hashlib.sha512, False, IterationCount(4096), 2),
    'SCRAM-SHA3-512': Mech(hashlib.sha3_512, False, IterationCount(10000), 3),
    'SCRAM-SHA-1-PLUS': Mech(hashlib.sha1, True, IterationCount(4096), 4),
    'SCRAM-SHA-256-PLUS': Mech(hashlib.sha256, True, IterationCount(4096), 5),
    'SCRAM-SHA-512-PLUS': Mech(hashlib.sha512, True, IterationCount(4096), 6),
    'SCRAM-SHA3-512-PLUS': Mech(hashlib.sha3_512, True, IterationCount(10000), 7),
})


@ta.final
class ChannelBinding:
    def __init__(self, name: CbName, data: CBindData) -> None:
        if not isinstance(name, CbName):
            raise ScramError('The channel binding name must be a CbName object.')

        self.name = name

        if not isinstance(data, CBindData):
            raise ScramError('The channel binding data must be a CBindData object.')
        self.data = data

    def __hash__(self) -> int:
        return hash((ChannelBinding, self.name, self.data))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ChannelBinding) and
            self.name == other.name and
            self.data == other.data
        )


@ta.final
class ScramMechanism:
    def __init__(self, mechanism: str = 'SCRAM-SHA-256') -> None:
        if not isinstance(mechanism, str):
            raise ScramError('The mechanism name must be a str')

        try:
            mech = MECHS[mechanism]
        except KeyError:
            raise ScramError(
                f'The mechanism name is not supported. The supported mechanisms are {sorted(MECHS.keys())}',
            ) from None

        self.name = mechanism
        self.hf = mech.hf
        self.use_binding = mech.use_binding
        self.iteration_count = mech.iteration_count
        self.strength = mech.strength

    def make_auth_info(
            self,
            password: str,
            iteration_count: int | None = None,
            salt: bytes | None = None,
    ) -> tuple[
        bytes,
        bytes,
        bytes,
        int,
    ]:
        salt_ = Salt(salt) if salt is not None else None

        password_ = Password(password)

        if iteration_count is None:
            i = self.iteration_count
        else:
            i = IterationCount(iteration_count)
            if i < self.iteration_count:
                raise ScramError(
                    f'The iteration count must not be < {self.iteration_count}',
                    ServerError.OTHER_ERROR,
                )

        out_salt, stored_key, server_key = _make_auth_info(
            self.hf,
            password_,
            i,
            salt=salt_,
        )

        return (
            bytes(out_salt),
            stored_key,
            server_key,
            int(i),
        )


def _make_auth_info(hf: HashFn, password, i, salt=None):
    if salt is None:
        salt = Salt.create()

    salted_password = hi(hf, bytes(password), bytes(salt), i)
    _, stored_key, server_key = _c_key_stored_key_s_key(hf, salted_password)
    return salt, stored_key, server_key


class ScramClient:
    def __init__(
            self,
            mechanisms: list[str] | tuple[str],
            username: str,
            password: str,
            channel_binding: ChannelBindingTuple | None = None,
            c_nonce: str | None = None,
            *,
            certificate_backend: CertificateBackend = 'auto',
    ):
        if not isinstance(mechanisms, (list, tuple)):
            raise ScramError(f"'{mechanisms}' The 'mechanisms' parameter must be a list or tuple of mechanism names.")

        if not len(mechanisms) > 0:
            raise ScramError("The 'mechanisms' parameter must contain at least one mechanism name")

        if channel_binding is None:
            cb = None

        else:
            try:
                cb_name_str, d_s = channel_binding
            except ValueError:
                raise ScramError(
                    'Channel binding must be a tuple with two items',
                    ServerError.OTHER_ERROR,
                ) from None

            cb_name = CbName(cb_name_str)
            cb_data = None

            if isinstance(d_s, bytes):
                cb_data = CBindData(d_s)

            elif isinstance(d_s, (ssl.SSLSocket, ssl.SSLObject)):
                ssl_socket = d_s
                if cb_name == CbName('tls-unique'):
                    if (gcb_data := ssl_socket.get_channel_binding(str(cb_name))) is None:
                        raise ScramError(f'SSLSocket channel binding must not be None', ServerError.OTHER_ERROR)

                    cb_data = CBindData(gcb_data)

                elif cb_name == CbName('tls-server-end-point'):
                    der = ssl_socket.getpeercert(binary_form=True)
                    if der is None:
                        raise ScramError(
                            'There is no peer certificate for the SSL socket',
                            ServerError.OTHER_ERROR,
                        )
                    cb_data = CBindData.from_der(
                        der,
                        certificate_backend=certificate_backend,
                    )

                else:
                    raise ScramError('Channel binding name not recognized', ServerError.OTHER_ERROR)

            else:
                raise ScramError(
                    'The second item of the channel_binding tuple must be of type bytes or ssl.SSLSocket',
                    ServerError.OTHER_ERROR,
                )

            cb = ChannelBinding(cb_name, cb_data)

        ms = (ScramMechanism(m) for m in mechanisms)
        mechs = [m for m in ms if not (cb is None and m.use_binding)]

        if len(mechs) == 0:
            raise ScramError(
                "The mechanisms in the 'mechanisms' parameter all require channel binding but a 'channel_binding' "
                "parameter hasn't been provided",
            )

        mech = max(mechs, key=operator.attrgetter('strength'))

        self.hf, use_binding = mech.hf, mech.use_binding
        self.mechanism_name = mech.name

        self.c_nonce = Nonce.create() if c_nonce is None else Nonce(c_nonce)
        self.username = Username(username)
        self.password = Password(password)
        self.cb = cb
        self.stage: ClientStage | None = None
        self.gs2_header = Gs2Header.from_binding(self.cb, use_binding)

    def _set_stage(self, next_stage: ClientStage) -> None:
        _check_stage(ClientStage, self.stage, next_stage)
        self.stage = next_stage

    def get_client_first(self):
        self._set_stage(ClientStage.get_client_first)
        self.client_first_bare, client_first = _get_client_first(self.username, self.c_nonce, self.gs2_header)
        return client_first

    def set_server_first(self, message):
        self._set_stage(ClientStage.set_server_first)
        self.server_first = message
        (
            self.nonce,
            self.salt,
            self.iterations,
        ) = _set_server_first(ServerFirst(message), self.c_nonce)

    def get_client_final(self):
        self._set_stage(ClientStage.get_client_final)
        self.server_signature, cfinal = _get_client_final(
            self.hf,
            self.password,
            self.salt,
            self.iterations,
            self.nonce,
            self.client_first_bare,
            self.server_first,
            self.cb,
            self.gs2_header,
        )
        return cfinal

    def set_server_final(self, message):
        self._set_stage(ClientStage.set_server_final)
        _set_server_final(ServerFinal(message), self.server_signature)


def _make_auth_message(client_first_bare, server_first, client_final_without_proof):
    msg = client_first_bare, server_first, client_final_without_proof
    return uenc(','.join(msg))


def _c_key_stored_key_s_key(hf, salted_password):
    client_key = hmac_digest(hf, salted_password, b'Client Key')
    stored_key = h(hf, client_key)
    server_key = hmac_digest(hf, salted_password, b'Server Key')

    return client_key, stored_key, server_key


@ta.final
class Gs2Header:
    # gs2-header      = gs2-cbind-flag "," [ authzid ] ","
    def __init__(self, gs2_char: str, cb_name: CbName | None) -> None:
        self.gs2_char = gs2_char

        if not isinstance(cb_name, (types.NoneType, CbName)):
            raise ScramError('must be CbName or None')

        self.cb_name = cb_name

    def __str__(self) -> str:
        if self.gs2_char == 'n':
            return 'n,,'
        elif self.gs2_char == 'y':
            return 'y,,'
        elif self.gs2_char == 'p':
            return f'p={self.cb_name},,'
        else:
            raise ScramError('Invalid GS2 char')

    def __bytes__(self) -> bytes:
        return str(self).encode('ascii')

    def __hash__(self) -> int:
        return hash((Gs2Header, self.gs2_char, self.cb_name))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Gs2Header) and
            self.gs2_char == other.gs2_char and
            self.cb_name == other.cb_name
        )

    def make_cbind_input(self, cb: ChannelBinding) -> bytes:
        gs2_header_bin = bytes(self)

        if self.gs2_char in ('y', 'n'):
            return gs2_header_bin

        elif self.gs2_char == 'p':
            return gs2_header_bin + bytes(cb.data)

        else:
            raise ScramError('Invalid GS2 char', ServerError.OTHER_ERROR)

    @classmethod
    def from_str(cls, s: str) -> ta.Self:
        try:
            gs2_cbind_flag, authzid, trail = s.split(',')
        except ValueError:
            raise ScramError(
                'The gs2-header must contain exactly two commas',
                ServerError.OTHER_ERROR,
            ) from None

        if gs2_cbind_flag == 'y':
            gs2_char, cb_name = 'y', None

        elif gs2_cbind_flag == 'n':
            gs2_char, cb_name = 'n', None

        elif gs2_cbind_flag.startswith('p='):
            gs2_char = 'p'

            cb_name = CbName(gs2_cbind_flag[2:])

        else:
            raise ScramError("GS2 flag must be one of ('y', 'n', 'p=')", ServerError.OTHER_ERROR)

        if authzid != '':
            raise ScramError('The GS2 authzid must be empty', ServerError.OTHER_ERROR)

        if trail != '':
            raise ScramError(
                "The gs2-header can't have characters after the last comma",
                ServerError.OTHER_ERROR,
            )
        return cls(gs2_char, cb_name)

    @classmethod
    def from_binding(cls, cb: ChannelBinding | None, use_binding: bool) -> ta.Self:
        if cb is None:
            gs2_char, cb_name = 'n', None

        elif use_binding:
            gs2_char, cb_name = 'p', cb.name

        else:
            gs2_char, cb_name = 'y', None

        return cls(gs2_char, cb_name)


class Message:
    PROTO_ATTRS = frozenset({'a', 'n', 'm', 'r', 'c', 's', 'i', 'p', 'v', 'e'})

    def __init__(self, msg, desc, *expected_attr_strs):
        if not isinstance(msg, str):
            raise ScramError(
                'A message must be of type str', ServerError.OTHER_ERROR,
            )

        m = collections.OrderedDict()

        for p in msg.split(','):
            if len(p) < 2 or p[1] != '=':
                raise ScramError(
                    f"Malformed {desc} message. Attributes must be separated by a ',' and each attribute must start "
                    f"with a letter followed by a '='",
                    ServerError.OTHER_ERROR,
                )

            k = p[0]

            if not (k.isalpha() and k.isascii()):
                raise ScramError(
                    f'Malformed {desc} message. Attributes must be US-ASCII alpha characters.',
                    ServerError.OTHER_ERROR,
                )

            elif k == 'm':
                raise ScramError(
                    "The 'm' attribute isn't supported by this version of the protocol.",
                    ServerError.EXTENSIONS_NOT_SUPPORTED,
                )

            elif k in m:
                raise ScramError('Duplicate attributes not allowed in message', ServerError.OTHER_ERROR)

            v = p[2:]

            if v == '':
                raise ScramError(
                    f'Malformed {desc} message. Attribute values must at least one character long',
                    ServerError.OTHER_ERROR,
                )

            elif '\x00' in v:
                raise ScramError(
                    f"Malformed {desc} message. Attribute values can't contain the NUL character",
                    ServerError.OTHER_ERROR,
                )

            elif ',' in v:
                raise ScramError(
                    f"Malformed {desc} message. Attribute values can't contain the ',' character",
                    ServerError.OTHER_ERROR,
                )

            m[k] = v

        attr_list = [k if k in Message.PROTO_ATTRS else '*' for k in m]
        attr_str = ''.join(k for k, _ in itertools.groupby(attr_list))

        if '*' in attr_str:
            exp_strs = list(expected_attr_strs)
        else:
            exp_strs = [s.replace('*', '') for s in expected_attr_strs]

        if attr_str not in exp_strs:
            star_exp = " (where '*' is unrecognised attributes)" if '*' in attr_str else ''
            raise ScramError(
                f"Malformed {desc} message. Expected the attribute str to be one of {exp_strs} but found "
                f"'{attr_str}'{star_exp}",
                ServerError.OTHER_ERROR,
            )

        self._msg = collections.OrderedDict()

        kv: ta.Any
        for k, v_str in m.items():
            match k:
                case 'n':
                    kv = Username.from_escaped(v_str)
                case 'r':
                    kv = Nonce(v_str)
                case 's':
                    kv = Salt.from_str(v_str)
                case 'i':
                    kv = IterationCount.from_str(v_str)
                case 'p':
                    kv = b64dec(v_str)
                case 'v':
                    kv = b64dec(v_str)
                case 'e':
                    try:
                        kv = ServerError(v_str)
                    except ValueError:
                        raise ScramError('The server returned an invalid error') from None
                case _:
                    kv = v_str

            self._msg[k] = kv

    def __getitem__(self, key):
        return self._msg[key]

    def items(self):
        return self._msg.items()

    def __contains__(self, key):
        return key in self._msg

    def __len__(self):
        return len(self._msg)

    def _iter__(self):
        return iter(self._msg)


class ServerFirst(Message):
    def __init__(self, message):
        super().__init__(message, 'server first', 'rsi*', 'e*')


class ServerFinal(Message):
    def __init__(self, message):
        super().__init__(message, 'server final', 'v*', 'e*')


@ta.final
class Username:
    def __init__(self, username):
        try:
            self.username = saslprep(username)
        except ScramError as e:
            raise ScramError(e.args[0], ServerError.INVALID_USERNAME_ENCODING) from None

        if len(self.username) == 0:
            raise ScramError('The username cannot be empty', ServerError.OTHER_ERROR)

    def __str__(self) -> str:
        return self.username

    def __hash__(self) -> int:
        return hash((Username, self.username))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Username) and self.username == other.username

    def escape(self):
        return _username_escape(self.username)

    @classmethod
    def from_escaped(cls, username):
        return cls(_username_unescape(username))


ESCAPE_EQUALS = '=3D'
ESCAPE_COMMA = '=2C'


def _username_escape(username: str) -> str:
    return username.replace('=', ESCAPE_EQUALS).replace(',', ESCAPE_COMMA)


def _username_unescape(username):
    for i in (i for i, c in enumerate(username) if c == '='):
        if username[i:i + 3] not in (ESCAPE_EQUALS, ESCAPE_COMMA):
            raise ScramError(
                "An '=' in a username must be followed by '3D', or  '2C'",
                ServerError.INVALID_USERNAME_ENCODING,
            )

    return username.replace(ESCAPE_COMMA, ',').replace(ESCAPE_EQUALS, '=')


@ta.final
class Password:
    def __init__(self, password: str) -> None:
        try:
            self.password = saslprep(password)
        except ScramError as e:
            raise ScramError(e.args[0], ServerError.OTHER_ERROR) from None

    def __bytes__(self) -> bytes:
        return uenc(self.password)


def _make_message(**kwargs):
    return ','.join((f'{k}={v}' for k, v in kwargs.items()))


def _get_client_first(username, c_nonce, gs2_header):
    bare = _make_message(n=username.escape(), r=c_nonce)
    return bare, f'{gs2_header}{bare}'


def _set_server_first(msg, c_nonce):
    if 'e' in msg:
        raise ScramError('The server returned an error', msg['e'])

    nonce = msg['r']
    salt = msg['s']
    i = msg['i']

    if not nonce.startswith(c_nonce):
        raise ScramError("Client nonce doesn't match.", ServerError.OTHER_ERROR)

    if not len(nonce) > len(c_nonce):
        raise ScramError('The nonce must be longer than the client nonce', ServerError.OTHER_ERROR)

    return nonce, salt, i


def _get_client_final(
    hf,
    password,
    salt,
    iterations,
    nonce,
    client_first_bare,
    server_first,
    channel_binding,
    gs2_header,
):
    salted_password = hi(hf, bytes(password), bytes(salt), iterations)
    client_key, stored_key, server_key = _c_key_stored_key_s_key(hf, salted_password)

    cbind_input = gs2_header.make_cbind_input(channel_binding)
    client_final_without_proof = _make_message(c=b64enc(cbind_input), r=nonce)
    auth_msg = _make_auth_message(client_first_bare, server_first, client_final_without_proof)

    client_signature = hmac_digest(hf, stored_key, auth_msg)
    client_proof = xor(client_key, client_signature)
    server_signature = hmac_digest(hf, server_key, auth_msg)
    client_final = f'{client_final_without_proof},p={b64enc(client_proof)}'
    return server_signature, client_final


def _set_server_final(msg, server_signature):
    if 'e' in msg:
        raise ScramError('The server returned an error', msg['e'])

    if not hmac.compare_digest(server_signature, msg['v']):
        raise ScramError("The server signature doesn't match.", ServerError.OTHER_ERROR)


def saslprep(source: str) -> str:
    # mapping stage
    #   - map non-ascii spaces to U+0020 (stringprep C.1.2)
    #   - strip 'commonly mapped to nothing' chars (stringprep B.1)
    data = ''.join(' ' if stringprep.in_table_c12(c) else c for c in source if not stringprep.in_table_b1(c))

    # normalize to KC form
    data = unicodedata.ucd_3_2_0.normalize('NFKC', data)
    if not data:
        return ''

    # check for invalid bi-directional strings. stringprep requires the following:
    #   - chars in C.8 must be prohibited.
    #   - if any R/AL chars in string:
    #       - no L chars allowed in string
    #       - first and last must be R/AL chars
    # this checks if start/end are R/AL chars. if so, prohibited loop will forbid all L chars. if not, prohibited loop
    # will forbid all R/AL chars instead. in both cases, prohibited loop takes care of C.8.
    is_ral_char = stringprep.in_table_d1
    if is_ral_char(data[0]):
        if not is_ral_char(data[-1]):
            raise ScramError('malformed bidi sequence', ServerError.INVALID_ENCODING)
        # forbid L chars within R/AL sequence.
        is_forbidden_bidi_char = stringprep.in_table_d2
    else:
        # forbid R/AL chars if start not setup correctly; L chars allowed.
        is_forbidden_bidi_char = is_ral_char

    # check for prohibited output
    # stringprep tables A.1, B.1, C.1.2, C.2 - C.9
    for c in data:
        for f, msg in (
            # check for chars mapping stage should have removed
            (stringprep.in_table_b1, 'failed to strip B.1 in mapping stage'),
            (stringprep.in_table_c12, 'failed to replace C.1.2 in mapping stage'),
            # check for forbidden chars
            (stringprep.in_table_a1, 'unassigned code points forbidden'),
            (stringprep.in_table_c21_c22, 'control characters forbidden'),
            (stringprep.in_table_c3, 'private use characters forbidden'),
            (stringprep.in_table_c4, 'non-char code points forbidden'),
            (stringprep.in_table_c5, 'surrogate codes forbidden'),
            (stringprep.in_table_c6, 'non-plaintext chars forbidden'),
            (stringprep.in_table_c7, 'non-canonical chars forbidden'),
            (stringprep.in_table_c8, 'display-modifying/deprecated chars forbidden'),
            (stringprep.in_table_c9, 'tagged characters forbidden'),
            (is_forbidden_bidi_char, 'forbidden bidi character'),
        ):
            if f(c):
                raise ScramError(msg, ServerError.INVALID_ENCODING)

    return data
