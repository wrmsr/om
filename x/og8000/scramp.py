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
# https://codeberg.org/tlocke/scramp/src/commit/eff40acb147cefc3a9525f934a0e469acf5cb659
import base64
import enum
import functools
import hashlib
import hmac
import operator
import secrets
import stringprep
import typing as ta
import unicodedata

from .certs import CertificateBackend
from .certs import tls_server_end_point


if ta.TYPE_CHECKING:
    import ssl


T = ta.TypeVar('T')
P = ta.ParamSpec('P')

ChannelBinding: ta.TypeAlias = tuple[str, bytes]

HashFn: ta.TypeAlias = ta.Callable[..., ta.Any]

AuthInfo: ta.TypeAlias = tuple[bytes, bytes, bytes, int]
AuthFnCallable: ta.TypeAlias = ta.Callable[[str], AuthInfo]


##


class ServerErrors:
    def __new__(cls, *args: ta.Any, **kwargs: ta.Any) -> ta.Self:  # noqa
        raise TypeError

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


class ScramException(Exception):
    def __init__(self, message: str, server_error: str | None = None) -> None:
        super().__init__(message)
        self.server_error = server_error

    def __str__(self) -> str:
        s_str = '' if self.server_error is None else f': {self.server_error}'
        return super().__str__() + s_str


def hmac_digest(hf: HashFn, key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg=msg, digestmod=hf).digest()


def h(hf: HashFn, msg: bytes) -> bytes:
    return hf(msg).digest()


def xor(bytes1: bytes, bytes2: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(bytes1, bytes2, strict=True))


def b64enc(binary: bytes) -> str:
    return base64.b64encode(binary).decode('utf8')


def b64dec(string: str) -> bytes:
    try:
        return base64.b64decode(string, validate=True)
    except BaseException as e:
        raise ScramException(f"Invalid base 64 encoding '{string}'", ServerErrors.INVALID_ENCODING) from e


def uenc(string: str) -> bytes:
    return string.encode('utf-8')


class IterationCount(int):
    def __new__(cls, value: int | None, minimum: int, maximum: int) -> ta.Self:
        if value is None:
            value = minimum
        if value < minimum:
            raise ValueError(f'The value must not be < {minimum}')
        if value > maximum:
            raise ValueError(f'The value must not be > {maximum}')
        return super().__new__(cls, value)


##
# https://tools.ietf.org/html/rfc5802
# https://www.rfc-editor.org/rfc/rfc7677.txt


class Salt:
    def __init__(self, salt: bytes) -> None:
        if not isinstance(salt, bytes):
            raise ScramException(
                f"The 'salt' must be of type bytes, but found type {type(salt)}",
                ServerErrors.OTHER_ERROR,
            )
        self.salt = salt

    def __str__(self) -> str:
        return b64enc(self.salt)

    def __bytes__(self) -> bytes:
        return self.salt

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Salt) and self.salt == other.salt

    @classmethod
    def from_str(cls, s: str) -> ta.Self:
        try:
            return cls(b64dec(s))
        except ScramException as e:
            raise ScramException(
                f'Invalid salt encoding: {e}', ServerErrors.INVALID_ENCODING,
            ) from e

    @classmethod
    def create(cls) -> ta.Self:
        return cls(secrets.token_bytes())


class Nonce:
    def __init__(self, nonce: str) -> None:
        if not isinstance(nonce, str):
            raise ScramException(
                f"The 'nonce' must be of type str, but found type {type(nonce)}",
                ServerErrors.OTHER_ERROR,
            )
        if not all(0x21 <= ord(c) <= 0x7E and c != ',' for c in nonce):
            raise ScramException(
                'Nonce contains invalid characters.', ServerErrors.OTHER_ERROR,
            )

        self.nonce = nonce

    def __str__(self) -> str:
        return self.nonce

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nonce) and self.nonce == other.nonce

    def __add__(self, other: Nonce) -> Nonce:
        if not isinstance(other, Nonce):
            return NotImplemented
        return Nonce(self.nonce + other.nonce)

    def startswith(self, other: Nonce) -> bool:
        if not isinstance(other, Nonce):
            return NotImplemented
        return self.nonce.startswith(other.nonce)

    @classmethod
    def create(cls) -> ta.Self:
        return cls(secrets.token_hex())


@enum.unique
class ClientStage(enum.IntEnum):
    get_client_first = 1
    set_server_first = 2
    get_client_final = 3
    set_server_final = 4


@enum.unique
class ServerStage(enum.IntEnum):
    set_client_first = 1
    get_server_first = 2
    set_client_final = 3
    get_server_final = 4


def _check_stage(Stages: type[enum.IntEnum], current_stage: int | None, next_stage: int) -> None:
    if current_stage is None:
        if next_stage != 1:
            raise ScramException(f'The method {Stages(1).name} must be called first.')
    elif current_stage == 4:
        raise ScramException('The authentication sequence has already finished.')
    elif next_stage != current_stage + 1:
        raise ScramException(
            f'The next method to be called is '
            f'{Stages(current_stage + 1).name}, not this method.',
        )


MECHANISMS = (
    'SCRAM-SHA-1',
    'SCRAM-SHA-1-PLUS',
    'SCRAM-SHA-256',
    'SCRAM-SHA-256-PLUS',
    'SCRAM-SHA-512',
    'SCRAM-SHA-512-PLUS',
    'SCRAM-SHA3-512',
    'SCRAM-SHA3-512-PLUS',
)


CHANNEL_TYPES = (
    'tls-server-end-point',
    'tls-unique',
    'tls-unique-for-telnet',
)

MAX_ITERATION_COUNT = 10_000_000  # DoS guard


def _make_cb_data(
        name: str,
        ssl_socket: ssl.SSLSocket | ssl.SSLObject,
        *,
        certificate_backend: CertificateBackend = 'auto',
) -> bytes:
    if name == 'tls-unique':
        cb_data = ssl_socket.get_channel_binding(name)

        if cb_data is None:
            raise ValueError(
                'TLS channel binding data for tls-unique is not available',
            )

        return cb_data

    elif name == 'tls-server-end-point':
        cert_der = ssl_socket.getpeercert(binary_form=True)

        if cert_der is None:
            raise ValueError(
                'TLS peer did not provide a certificate',
            )

        return tls_server_end_point(
            cert_der,
            backend=certificate_backend,
        )

    else:
        raise ScramException(f'Channel binding name {name} not recognized.')


def make_channel_binding(
        name: str,
        ssl_socket: ssl.SSLSocket | ssl.SSLObject,
        *,
        certificate_backend: CertificateBackend = 'auto',
) -> ChannelBinding:
    return name, _make_cb_data(name, ssl_socket, certificate_backend=certificate_backend)


class ScramMechanism:
    MECH_LOOKUP: ta.ClassVar[ta.Mapping[str, tuple[HashFn, bool, int, int]]] = {
        'SCRAM-SHA-1': (hashlib.sha1, False, 4096, 0),
        'SCRAM-SHA-1-PLUS': (hashlib.sha1, True, 4096, 1),
        'SCRAM-SHA-256': (hashlib.sha256, False, 4096, 2),
        'SCRAM-SHA-256-PLUS': (hashlib.sha256, True, 4096, 3),
        'SCRAM-SHA-512': (hashlib.sha512, False, 4096, 4),
        'SCRAM-SHA-512-PLUS': (hashlib.sha512, True, 4096, 5),
        'SCRAM-SHA3-512': (hashlib.sha3_512, False, 10000, 6),
        'SCRAM-SHA3-512-PLUS': (hashlib.sha3_512, True, 10000, 7),
    }

    def __init__(self, mechanism: str = 'SCRAM-SHA-256') -> None:
        if mechanism not in MECHANISMS:
            raise ScramException(
                f"The mechanism name '{mechanism}' is not supported. The "
                f"supported mechanisms are {MECHANISMS}.",
            )
        self.name = mechanism
        (
            self.hf,
            self.use_binding,
            self.iteration_count,
            self.strength,
        ) = self.MECH_LOOKUP[mechanism]

    def make_auth_info(
            self,
            password: str,
            iteration_count: int | None = None,
            salt: bytes | None = None,
    ) -> AuthInfo:
        if salt is not None:
            salt = Salt(salt)  # type: ignore[assignment]

        try:
            i_count = self.parse_iteration_count(iteration_count)
        except ValueError as e:
            raise ScramException(f'The iteration count is not valid: {e}') from e
        salt, stored_key, server_key = _make_auth_info(  # type: ignore[assignment]
            self.hf,
            password,
            i_count,
            salt=salt,  # type: ignore[arg-type]
        )
        return bytes(salt), stored_key, server_key, i_count  # type: ignore[arg-type]

    def make_server(
            self,
            auth_fn: AuthFnCallable,
            channel_binding: ChannelBinding | None = None,
            s_nonce: str | None = None,
    ) -> ScramServer:
        if s_nonce is not None:
            s_nonce = Nonce(s_nonce)  # type: ignore[assignment]
        return ScramServer(
            self,
            AuthFn(auth_fn),
            channel_binding=channel_binding,
            s_nonce=s_nonce,  # type: ignore[arg-type]
        )

    def parse_iteration_count(self, i: int | None) -> IterationCount:
        return IterationCount(i, self.iteration_count, MAX_ITERATION_COUNT)


def _make_auth_info(hf: HashFn, password: str, i: int, salt: Salt | None = None) -> tuple[Salt, bytes, bytes]:
    if salt is None:
        salt = Salt.create()

    salted_password = _make_salted_password(hf, password, salt, i)
    _, stored_key, server_key = _c_key_stored_key_s_key(hf, salted_password)
    return salt, stored_key, server_key


def _validate_channel_binding(channel_binding: ChannelBinding | None) -> None:
    if channel_binding is None:
        return

    if not isinstance(channel_binding, tuple):
        raise ScramException('The channel_binding parameter must either be None or a tuple.')

    if len(channel_binding) != 2:
        raise ScramException(
            'The channel_binding parameter must either be None or a tuple of two '
            'elements (type, data).',
        )

    channel_type, channel_data = channel_binding
    if channel_type not in CHANNEL_TYPES:
        raise ScramException(
            f'The channel_binding parameter must either be None or a tuple with the '
            f'first element a str specifying one of the channel types {CHANNEL_TYPES}.',
        )

    if not isinstance(channel_data, bytes):
        raise ScramException(
            'The channel_binding parameter must either be None or a tuple with the '
            'second element a bytes object containing the bind data.',
        )


class ScramClient:
    def __init__(
            self,
            mechanisms: list[str] | tuple[str, ...],
            username: str,
            password: str,
            channel_binding: ChannelBinding | None = None,
            c_nonce: str | None = None,
    ) -> None:
        if not isinstance(mechanisms, (list, tuple)):
            raise ScramException("The 'mechanisms' parameter must be a list or tuple of mechanism names.")

        _validate_channel_binding(channel_binding)

        ms = (ScramMechanism(m) for m in mechanisms)
        mechs = [m for m in ms if not (channel_binding is None and m.use_binding)]
        if len(mechs) == 0:
            raise ScramException(f'There are no suitable mechanisms in the list provided: {mechanisms}')

        mech = sorted(mechs, key=operator.attrgetter('strength'))[-1]
        self.hf, use_binding = mech.hf, mech.use_binding
        self.mechanism_name = mech.name
        self.iterations = mech.iteration_count

        self.c_nonce = Nonce.create() if c_nonce is None else Nonce(c_nonce)
        self.username = Username(username)
        self.password = password
        self.channel_binding = channel_binding
        self.stage: ClientStage | None = None
        self.gs2_header = Gs2Header.from_binding(self.channel_binding, use_binding)

    def _set_stage(self, next_stage: ClientStage) -> None:
        _check_stage(ClientStage, self.stage, next_stage)
        self.stage = next_stage

    def get_client_first(self) -> str:
        self._set_stage(ClientStage.get_client_first)
        (
            self.client_first_bare,
            client_first,
        ) = _get_client_first(
            self.username,
            self.c_nonce,
            self.gs2_header,
        )
        return client_first

    def set_server_first(self, message: str) -> None:
        self._set_stage(ClientStage.set_server_first)
        self.server_first = message
        (
            self.nonce,
            self.salt,
            self.iterations,
        ) = _set_server_first(
            message,
            self.c_nonce,
            self.iterations,
        )

    def get_client_final(self) -> str:
        self._set_stage(ClientStage.get_client_final)
        (
            self.server_signature,
            cfinal,
        ) = _get_client_final(
            self.hf,
            self.password,
            self.salt,
            self.iterations,
            self.nonce,
            self.client_first_bare,
            self.server_first,
            self.channel_binding,
            self.gs2_header,
        )
        return cfinal

    def set_server_final(self, message: str) -> None:
        self._set_stage(ClientStage.set_server_final)
        _set_server_final(message, self.server_signature)


def set_error(f: ta.Callable[ta.Concatenate[ScramServer, P], T]) -> ta.Callable[ta.Concatenate[ScramServer, P], T]:
    @functools.wraps(f)
    def wrapper(self: ScramServer, *args: P.args, **kwds: P.kwargs) -> T:
        try:
            return f(self, *args, **kwds)
        except ScramException as e:
            if e.server_error is not None:
                self.error = e.server_error
                self.stage = ServerStage.set_client_final
            raise e

    return wrapper


class ScramServer:
    def __init__(
            self,
            mechanism: ScramMechanism,
            auth_fn: AuthFn,
            channel_binding: ChannelBinding | None = None,
            s_nonce: Nonce | None = None,
    ) -> None:
        _validate_channel_binding(channel_binding)

        self.channel_binding = channel_binding
        self.s_nonce = Nonce.create() if s_nonce is None else s_nonce
        self.auth_fn = auth_fn
        self.stage: ServerStage | None = None
        self.server_signature: str | None = None
        self.error: str | None = None
        self.nonce: Nonce | None = None

        self._set_mechanism(mechanism)

    def _set_mechanism(self, mechanism: ScramMechanism) -> None:
        if mechanism.use_binding and self.channel_binding is None:
            raise ScramException(
                "The mechanism requires channel binding, and so channel_binding can't "
                "be None.",
            )
        self.m = mechanism

    def _set_stage(self, next_stage: ServerStage) -> None:
        _check_stage(ServerStage, self.stage, next_stage)
        self.stage = next_stage

    @set_error
    def set_client_first(self, client_first: str) -> None:
        self._set_stage(ServerStage.set_client_first)
        (
            self.nonce,
            self.client_first_bare,
            upgrade_mechanism,
            self.gs2_header,
            self.salt,
            self.stored_key,
            self.server_key,
            self.i,
        ) = _set_client_first(
            client_first,
            self.s_nonce,
            self.channel_binding,
            self.m.use_binding,
            self.auth_fn,
        )

        if upgrade_mechanism:
            mech = ScramMechanism(f'{self.m.name}-PLUS')
            self._set_mechanism(mech)

    @set_error
    def get_server_first(self) -> str:
        self._set_stage(ServerStage.get_server_first)
        self.server_first = _get_server_first(
            self.nonce,  # type: ignore[arg-type]
            self.salt,
            self.i,
        )
        return self.server_first

    @set_error
    def set_client_final(self, client_final: str) -> None:
        self._set_stage(ServerStage.set_client_final)
        self.server_signature = _set_client_final(
            self.m.hf,
            client_final,
            self.nonce,  # type: ignore[arg-type]
            self.stored_key,
            self.server_key,
            self.client_first_bare,
            self.server_first,
            self.channel_binding,
            self.gs2_header,
        )

    @set_error
    def get_server_final(self) -> str:
        self._set_stage(ServerStage.get_server_final)
        return _get_server_final(self.server_signature, self.error)


def _make_auth_message(client_first_bare: str, server_first: str, client_final_without_proof: str) -> bytes:
    msg = client_first_bare, server_first, client_final_without_proof
    return uenc(','.join(msg))


def _make_salted_password(hf: HashFn, password: str, salt: Salt, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(
        hf().name,
        uenc(saslprep(password)),
        bytes(salt),
        iterations,
    )


def _c_key_stored_key_s_key(hf: HashFn, salted_password: bytes) -> tuple[bytes, bytes, bytes]:
    client_key = hmac_digest(hf, salted_password, b'Client Key')
    stored_key = h(hf, client_key)
    server_key = hmac_digest(hf, salted_password, b'Server Key')

    return client_key, stored_key, server_key


def _check_client_key(hf: HashFn, stored_key: bytes, auth_msg: bytes, proof: str) -> None:
    client_signature = hmac_digest(hf, stored_key, auth_msg)
    try:
        client_key = xor(client_signature, b64dec(proof))
    except ValueError as e:
        raise ScramException("Can't create client key.", ServerErrors.INVALID_PROOF) from e

    key = h(hf, client_key)

    if not hmac.compare_digest(key, stored_key):
        raise ScramException("The client keys don't match.", ServerErrors.INVALID_PROOF)


class Gs2Header:
    # gs2-header      = gs2-cbind-flag "," [ authzid ] ","
    def __init__(self, gs2_char: str, cb_name: str | None) -> None:
        self.gs2_char = gs2_char
        self.cb_name = cb_name

    def __str__(self) -> str:
        if self.gs2_char == 'n':
            return 'n,,'
        elif self.gs2_char == 'y':
            return 'y,,'
        elif self.gs2_char == 'p':
            return f'p={self.cb_name},,'
        else:
            raise ScramException('Invalid GS2 char')

    def __bytes__(self) -> bytes:
        return str(self).encode('ascii')

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Gs2Header) and
            self.gs2_char == other.gs2_char and
            self.cb_name == other.cb_name
        )

    @classmethod
    def from_str(cls, s: str) -> ta.Self:
        gs2_header = s.split(',')
        try:
            gs2_cbind_flag = gs2_header[0]
        except IndexError:
            raise ScramException('The client sent malformed gs2 data', ServerErrors.OTHER_ERROR)

        if gs2_cbind_flag == 'y':
            gs2_char, cb_name = 'y', None

        elif gs2_cbind_flag == 'n':
            gs2_char, cb_name = 'n', None

        elif gs2_cbind_flag.startswith('p='):
            gs2_char = 'p'

            cb_name = gs2_cbind_flag.split('=')[-1]
            for c in cb_name:
                if not (c.isascii() and (c.isalpha() or c.isdigit() or c in '.-')):
                    raise ScramException(
                        f'The channel binding name {cb_name} is not valid',
                        ServerErrors.OTHER_ERROR,
                    )

        else:
            raise ScramException(
                f"Received GS2 flag {gs2_cbind_flag} which isn't recognized",
                ServerErrors.OTHER_ERROR,
            )

        try:
            authzid = gs2_header[1]
        except IndexError:
            raise ScramException(
                'The client sent malformed gs2 data',
                ServerErrors.OTHER_ERROR,
            )

        if authzid != '':
            raise ScramException(
                f'The GS2 authzid {authzid} must be empty',
                ServerErrors.OTHER_ERROR,
            )
        return cls(gs2_char, cb_name)

    @classmethod
    def from_binding(cls, channel_binding: ChannelBinding | None, use_binding: bool) -> ta.Self:
        if channel_binding is None:
            gs2_char, cb_name = 'n', None
        else:
            if use_binding:
                channel_type, _ = channel_binding
                gs2_char, cb_name = 'p', channel_type
            else:
                gs2_char, cb_name = 'y', None
        return cls(gs2_char, cb_name)


def _make_cbind_input(channel_binding: ChannelBinding | None, gs2_header: Gs2Header) -> bytes | None:
    gs2_header_bin = bytes(gs2_header)

    # FIXME: implicitly returns None for an unknown gs2_char (unreachable as bytes(gs2_header) raises first).
    if gs2_header.gs2_char in ('y', 'n'):
        return gs2_header_bin
    elif gs2_header.gs2_char == 'p':
        _, cbind_data = channel_binding  # type: ignore[misc]
        return gs2_header_bin + cbind_data


def _print_set(s: ta.Iterable[str]) -> str:
    return '{' + ', '.join(sorted(set(s))) + '}'


PROTO_ATTRS = {'a', 'n', 'm', 'r', 'c', 's', 'i', 'p', 'v', 'e'}


def _parse_message(msg: str, desc: str, *expected_attr_sets: ta.AbstractSet[str]) -> dict[str, str]:
    m: dict[str, str] = {}
    for p in msg.split(','):
        if len(p) < 2 or p[1] != '=':
            raise ScramException(
                f"Malformed {desc} message. Attributes must be separated by a ',' and "
                f"each attribute must start with a letter followed by a '='",
                ServerErrors.OTHER_ERROR,
            )
        k = p[0]
        if not (k.isalpha() and k.isascii()):
            raise ScramException(
                f'Malformed {desc} message. Attributes must be US-ASCII alpha '
                f'characters.',
                ServerErrors.OTHER_ERROR,
            )
        elif k == 'm':
            raise ScramException(
                "The 'm' attribute isn't supported by this version of the protocol.",
                ServerErrors.EXTENSIONS_NOT_SUPPORTED,
            )
        elif k in m:
            raise ScramException(
                f'Duplicate attributes not allowed in message. The duplicated '
                f'attribute is {k}. ',
                ServerErrors.OTHER_ERROR,
            )
        elif k not in PROTO_ATTRS:  # Optional extensions ignored
            continue

        v = p[2:]
        if v == '':
            raise ScramException(
                f'Malformed {desc} message. Attribute values must at '
                f'least one character long',
                ServerErrors.OTHER_ERROR,
            )
        elif '\x00' in v:
            raise ScramException(
                f"Malformed {desc} message. Attribute values can't "
                f"contain the NUL character",
                ServerErrors.OTHER_ERROR,
            )
        elif ',' in v:
            raise ScramException(
                f"Malformed {desc} message. Attribute values can't "
                f"contain the ',' character",
                ServerErrors.OTHER_ERROR,
            )

        m[k] = v

    attr_set = m.keys()
    if attr_set in expected_attr_sets:
        return m

    raise ScramException(
        f"Malformed {desc} message. Expected the attribute set to be one of "
        f"[{', '.join([_print_set(s) for s in expected_attr_sets])}] but found "
        f"{_print_set(attr_set)}",
        ServerErrors.OTHER_ERROR,
    )


class Username:
    def __init__(self, username: str) -> None:
        try:
            self.username = saslprep(username)
        except ScramException as e:
            raise ScramException(e.args[0], ServerErrors.INVALID_USERNAME_ENCODING)

    def __str__(self) -> str:
        return self.username

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Username) and self.username == other.username

    def escape(self) -> str:
        return _username_escape(self.username)

    @classmethod
    def from_escaped(cls, username: str) -> ta.Self:
        return cls(_username_unescape(username))


ESCAPE_EQUALS = '=3D'
ESCAPE_COMMA = '=2C'


def _username_escape(username: str) -> str:
    return username.replace('=', ESCAPE_EQUALS).replace(',', ESCAPE_COMMA)


def _username_unescape(username: str) -> str:
    for i in (i for i, c in enumerate(username) if c == '='):
        if username[i : i + 3] not in (ESCAPE_EQUALS, ESCAPE_COMMA):
            raise ScramException(
                "An '=' in a username must be followed by '3D', or  '2C'",
                ServerErrors.INVALID_USERNAME_ENCODING,
            )
    return username.replace(ESCAPE_COMMA, ',').replace(ESCAPE_EQUALS, '=')


class AuthFn:
    def __init__(self, auth_fn: AuthFnCallable) -> None:
        if not callable(auth_fn):
            raise ScramException(
                "The 'auth_fn' must be callable", ServerErrors.OTHER_ERROR,
            )
        self.auth_fn = auth_fn

    def __call__(self, username: Username) -> tuple[Salt, bytes, bytes, IterationCount]:
        try:
            salt, stored_key, server_key, i = self.auth_fn(str(username))  # pyright: ignore[reportGeneralTypeIssues]
        except BaseException as e:
            raise ScramException('Unknown user', ServerErrors.UNKNOWN_USER) from e

        if not isinstance(stored_key, bytes):
            raise ScramException(
                f"The 'stored_key' must be of type bytes, "
                f"but found type {type(stored_key)}",
                ServerErrors.OTHER_ERROR,
            )

        if not isinstance(server_key, bytes):
            raise ScramException(
                f"The 'server_key' must be of type bytes, "
                f"but found type {type(server_key)}",
                ServerErrors.OTHER_ERROR,
            )

        return (
            Salt(salt),
            stored_key,
            server_key,
            IterationCount(i, 1, MAX_ITERATION_COUNT),
        )


def _get_client_first(username: Username, c_nonce: Nonce, gs2_header: Gs2Header) -> tuple[str, str]:
    bare = ','.join((f'n={username.escape()}', f'r={c_nonce}'))
    return bare, str(gs2_header) + bare


def _set_client_first(
        client_first: str,
        s_nonce: Nonce,
        channel_binding: ChannelBinding | None,
        use_binding: bool,
        auth_fn: AuthFn,
) -> tuple[Nonce, str, bool, Gs2Header, Salt, bytes, bytes, IterationCount]:
    try:
        first_comma = client_first.index(',')
        second_comma = client_first.index(',', first_comma + 1)
    except ValueError:
        raise ScramException(
            'The client sent a malformed first message',
            ServerErrors.OTHER_ERROR,
        )
    gs2_header = Gs2Header.from_str(client_first[:second_comma])
    upgrade_mechanism = False

    if gs2_header.gs2_char == 'y':
        if channel_binding is not None:
            raise ScramException(
                "Received GS2 flag 'y' which indicates that the client doesn't think "
                "the server supports channel binding, but in fact it does",
                ServerErrors.SERVER_DOES_SUPPORT_CHANNEL_BINDING,
            )

    elif gs2_header.gs2_char == 'n':
        if use_binding:
            raise ScramException(
                "Received GS2 flag 'n' which indicates that the client doesn't require "
                "channel binding, but the server does",
                ServerErrors.SERVER_DOES_SUPPORT_CHANNEL_BINDING,
            )

    elif gs2_header.gs2_char == 'p':
        if channel_binding is None:
            raise ScramException(
                "Received GS2 flag 'p' which indicates that the client requires "
                "channel binding, but the server does not",
                ServerErrors.CHANNEL_BINDING_NOT_SUPPORTED,
            )
        if not use_binding:
            upgrade_mechanism = True

        channel_type, _ = channel_binding
        cb_name = gs2_header.cb_name
        if cb_name != channel_type:
            raise ScramException(
                f'Received channel binding name {cb_name} but this server supports the '
                f'channel binding name {channel_type}',
                ServerErrors.UNSUPPORTED_CHANNEL_BINDING_TYPE,
            )

    client_first_bare = client_first[second_comma + 1 :]
    msg = _parse_message(client_first_bare, 'client first bare', {'n', 'r'})

    c_nonce = Nonce(msg['r'])
    nonce = c_nonce + s_nonce
    user = Username.from_escaped(msg['n'])

    (
        salt,
        stored_key,
        server_key,
        i,
    ) = auth_fn(user)

    return (
        nonce,
        client_first_bare,
        upgrade_mechanism,
        gs2_header,
        salt,
        stored_key,
        server_key,
        i,
    )


def _get_server_first(nonce: Nonce, salt: Salt, iterations: int) -> str:
    return ','.join((f'r={nonce}', f's={salt}', f'i={iterations}'))


def _set_server_first(
        server_first: str,
        c_nonce: Nonce,
        min_iteration_count: int,
) -> tuple[Nonce, Salt, IterationCount]:
    msg = _parse_message(server_first, 'server first', {'r', 's', 'i'}, {'e'})
    if 'e' in msg:
        raise ScramException(f"The server returned the error: {msg['e']}")

    nonce = Nonce(msg['r'])
    salt = Salt.from_str(msg['s'])
    iteration_count = msg['i']
    try:
        iterations = IterationCount(
            int(iteration_count),
            min_iteration_count,
            MAX_ITERATION_COUNT,
        )
    except ValueError as e:
        raise ScramException(
            f'Server iteration count {iteration_count} is not valid',
        ) from e

    if not nonce.startswith(c_nonce):
        raise ScramException("Client nonce doesn't match.", ServerErrors.OTHER_ERROR)

    return nonce, salt, iterations


def _get_client_final(
    hf: HashFn,
    password: str,
    salt: Salt,
    iterations: int,
    nonce: Nonce,
    client_first_bare: str,
    server_first: str,
    channel_binding: ChannelBinding | None,
    gs2_header: Gs2Header,
) -> tuple[str, str]:
    salted_password = _make_salted_password(hf, password, salt, iterations)
    client_key, stored_key, server_key = _c_key_stored_key_s_key(hf, salted_password)

    cbind_input = _make_cbind_input(channel_binding, gs2_header)
    client_final_without_proof = (
        f'c={b64enc(cbind_input)},r={nonce}'  # type: ignore[arg-type]
    )
    auth_msg = _make_auth_message(
        client_first_bare,
        server_first,
        client_final_without_proof,
    )

    client_signature = hmac_digest(hf, stored_key, auth_msg)
    client_proof = xor(client_key, client_signature)
    server_signature = hmac_digest(hf, server_key, auth_msg)
    client_final = f'{client_final_without_proof},p={b64enc(client_proof)}'
    return b64enc(server_signature), client_final


def _set_client_final(
    hf: HashFn,
    client_final: str,
    nonce: Nonce,
    stored_key: bytes,
    server_key: bytes,
    client_first_bare: str,
    server_first: str,
    channel_binding: ChannelBinding | None,
    gs2_header: Gs2Header,
) -> str:
    msg = _parse_message(client_final, 'client final', {'c', 'r', 'p'})
    chan_binding = msg['c']
    try:
        chan_binding_bin = b64dec(chan_binding)
    except ScramException as e:
        raise ScramException(
            f"The channel binding isn't correctly encoded: {e}",
            ServerErrors.INVALID_ENCODING,
        ) from e
    msg_nonce = Nonce(msg['r'])
    proof = msg['p']
    if not hmac.compare_digest(
        chan_binding_bin,
        _make_cbind_input(channel_binding, gs2_header),  # type: ignore[arg-type]
    ):
        raise ScramException("The channel bindings don't match.", ServerErrors.CHANNEL_BINDINGS_DONT_MATCH)

    if not nonce == msg_nonce:
        raise ScramException("Server nonce doesn't match.", ServerErrors.OTHER_ERROR)

    client_final_without_proof = f'c={chan_binding},r={nonce}'
    auth_msg = _make_auth_message(
        client_first_bare,
        server_first,
        client_final_without_proof,
    )
    _check_client_key(hf, stored_key, auth_msg, proof)

    sig = hmac_digest(hf, server_key, auth_msg)
    return b64enc(sig)


def _get_server_final(server_signature: str | None, error: str | None) -> str:
    return f'v={server_signature}' if error is None else f'e={error}'


def _set_server_final(message: str, server_signature: str) -> None:
    msg = _parse_message(message, 'server final', {'v'}, {'e'})
    if 'e' in msg:
        raise ScramException(f"The server returned the error: {msg['e']}")

    if not hmac.compare_digest(server_signature, msg['v']):
        raise ScramException("The server signature doesn't match.", ServerErrors.OTHER_ERROR)


def saslprep(source: str) -> str:
    # mapping stage
    #   - map non-ascii spaces to U+0020 (stringprep C.1.2)
    #   - strip 'commonly mapped to nothing' chars (stringprep B.1)
    data = ''.join(' ' if stringprep.in_table_c12(c) else c for c in source if not stringprep.in_table_b1(c))

    # normalize to KC form
    data = unicodedata.normalize('NFKC', data)
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
            raise ScramException('malformed bidi sequence', ServerErrors.INVALID_ENCODING)
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
                raise ScramException(msg, ServerErrors.INVALID_ENCODING)

    return data
