"""
The sans-IO heart of a MySQL connection: all protocol state, and every exchange (handshake, authentication, queries,
result sets, LOAD DATA LOCAL, multi-results) expressed as stepwise Operations which consume server packets and produce
client packets without touching a transport. Sync and async drivers differ only in how they move bytes.
"""
import os
import struct
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from . import auth
from . import parsing
from ..charset import charset_by_name
from ..constants import CLIENT
from ..constants import COMMAND
from ..constants import SERVER_STATUS
from ..err import OperationalError
from ..err import ProtocolError
from ..err import raise_mysql_exception
from .messages import ColumnDefinition
from .messages import Handshake
from .packets import MAX_PACKET_LENGTH
from .packets import PacketReader
from .packets import encode_lenenc_str
from .results import ResultSchema
from .results import RowConverter
from .results import build_result_schema
from .results import decode_row


T = ta.TypeVar('T')

Row: ta.TypeAlias = tuple[ta.Any, ...]

# Yields the next Step, receives the next server packet payload (or None after a more/tls step), returns the result.
OperationGenerator: ta.TypeAlias = ta.Generator['Step', bytes, T]


##


DEFAULT_CHARSET = 'utf8mb4'
CLIENT_VERSION = '2.2.8'


##


@dc.dataclass(frozen=True)
class OutPacket:
    """A payload to send. `starts_command` resets the packet sequence to zero first, as every command must."""

    payload: bytes
    starts_command: bool = False


@dc.dataclass(frozen=True)
class Step:
    """
    What the driver must do next: send these packets (flushing after), then either wait for the next server packet or,
    if `more` is set, act and immediately ask the operation for its next step.
    """

    packets: ta.Sequence[OutPacket] = ()
    more: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, 'packets', tuple(self.packets))


class Operation(ta.Generic[T]):
    def __init__(self, gen: OperationGenerator[T]) -> None:
        super().__init__()

        self._gen = gen
        self._started = False
        self._done = False
        self._result: ta.Any = None
        self._error: BaseException | None = None

    @property
    def started(self) -> bool:
        return self._started

    @property
    def done(self) -> bool:
        return self._done

    def _advance(self, payload: bytes | None) -> Step:
        try:
            return self._gen.send(ta.cast('bytes', payload))
        except StopIteration as e:
            self._done = True
            self._result = e.value
            return Step()
        except Exception as e:  # noqa: BLE001
            self._done = True
            self._error = e
            return Step()

    def start(self) -> Step:
        check.state(not self._started)
        self._started = True
        return self._advance(None)

    def feed(self, payload: bytes | None) -> Step:
        check.state(self._started and not self._done)
        return self._advance(payload)

    def fail(self, exc: BaseException) -> None:
        check.state(not self._done)
        self._done = True
        self._error = exc
        self._gen.close()

    def result(self) -> T:
        check.state(self._done)
        if self._error is not None:
            raise self._error
        return self._result


##


@dc.dataclass(frozen=True)
class QueryResult:
    affected_rows: int
    insert_id: int
    server_status: int | None
    warning_count: int
    message: bytes
    description: tuple[tuple[ta.Any, ...], ...] | None
    fields: ta.Sequence[ColumnDefinition]
    rows: tuple[Row, ...] | None
    has_next: bool


@dc.dataclass()
class UnbufferedResult:
    """A result set being read one row at a time. Mutable, as it advances as rows are fetched."""

    schema: ResultSchema
    server_status: int | None = None
    warning_count: int = 0
    has_next: bool = False
    active: bool = True

    # The maximum value of a 64 bit unsigned integer, which is what MySQLdb reports for an unbuffered result's
    # unknown row count.
    affected_rows: int = 18446744073709551615
    insert_id: int = 0
    rows: tuple[Row, ...] | None = None

    @property
    def description(self) -> tuple[tuple[ta.Any, ...], ...]:
        return self.schema.description

    @property
    def fields(self) -> ta.Sequence[ColumnDefinition]:
        return self.schema.fields


##


class ProtocolSession:
    def __init__(
            self,
            *,
            user: bytes,
            password: bytes = b'',
            database: bytes | None = None,
            charset: str = DEFAULT_CHARSET,
            client_flag: int = 0,
            use_unicode: bool = True,
            decoders: ta.Mapping[int, RowConverter | None] | None = None,
            connect_attrs: ta.Mapping[str, str] | None = None,
            server_public_key: bytes | None = None,
            ssl_wanted: bool = False,
            ssl_required: bool = False,
            secure: bool = False,
            program_name: str | None = None,
            force_auth_plugin: str | None = None,
    ) -> None:
        super().__init__()

        self._user = user
        self._password = password
        self._database = database
        self._charset = charset
        self._base_client_flag = client_flag
        self._use_unicode = use_unicode
        self._decoders = dict(decoders or {})
        self._server_public_key = server_public_key
        self._ssl_wanted = ssl_wanted
        self._ssl_required = ssl_required
        self._secure = secure
        self._force_auth_plugin = force_auth_plugin

        self._encoding = charset_by_name(charset).encoding

        attrs = {
            '_client_name': 'omysql',
            '_client_version': CLIENT_VERSION,
            '_pid': str(os.getpid()),
            **(connect_attrs or {}),
        }
        if program_name:
            attrs['program_name'] = program_name
        self._connect_attrs = attrs

        self._handshake: Handshake | None = None
        self._salt = b''
        self._server_capabilities = 0
        self._server_status = 0
        self._server_version = ''
        self._thread_id = 0
        self._auth_plugin_name = ''
        self._client_flag = 0
        self._do_ssl = False

        self._current: Operation | None = None

    #
    # State

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def server_version(self) -> str:
        return self._server_version

    @property
    def server_status(self) -> int:
        return self._server_status

    @property
    def thread_id(self) -> int:
        return self._thread_id

    @property
    def server_capabilities(self) -> int:
        return self._server_capabilities

    @property
    def auth_plugin_name(self) -> str:
        return self._auth_plugin_name

    @property
    def secure(self) -> bool:
        return self._secure

    @property
    def will_ssl(self) -> bool:
        return self._do_ssl

    @property
    def current(self) -> Operation | None:
        return self._current

    def set_charset(self, charset: str) -> None:
        self._charset = charset
        self._encoding = charset_by_name(charset).encoding

    #
    # Driving

    def handle(self, payload: bytes) -> Step:
        if (op := self._current) is None:
            raise ProtocolError('Received a server packet with no operation in progress')
        step = op.feed(payload)
        if op.done:
            self._current = None
        return step

    def resume(self) -> Step:
        op = check.not_none(self._current)
        step = op.feed(None)
        if op.done:
            self._current = None
        return step

    def fail(self, exc: BaseException) -> None:
        if (op := self._current) is not None:
            self._current = None
            if not op.done:
                op.fail(exc)

    def _begin(self, gen: OperationGenerator[T]) -> Operation[T]:
        if (cur := self._current) is not None and not cur.done:
            raise ProtocolError('An operation is already in progress')
        op: Operation[T] = Operation(gen)
        self._current = op
        return op

    def mark_secure(self) -> None:
        """Called by the driver once a TLS upgrade completes."""

        self._secure = True

    #
    # Handshake and authentication

    def _apply_handshake(self, hs: Handshake) -> None:
        self._handshake = hs
        self._server_version = hs.server_version
        self._thread_id = hs.thread_id
        self._salt = hs.auth_plugin_data
        self._server_capabilities = hs.capabilities
        self._server_status = hs.status_flags
        self._auth_plugin_name = self._force_auth_plugin or hs.auth_plugin_name

    def _compute_client_flag(self) -> None:
        client_flag = self._base_client_flag | CLIENT.CAPABILITIES
        if int(self._server_version.split('.', 1)[0]) >= 5:
            client_flag |= CLIENT.MULTI_RESULTS
        if self._database and self._server_capabilities & CLIENT.CONNECT_WITH_DB:
            client_flag |= CLIENT.CONNECT_WITH_DB

        self._do_ssl = False
        if self._ssl_wanted:
            if self._server_capabilities & CLIENT.SSL:
                self._do_ssl = True
                client_flag |= CLIENT.SSL
            elif self._ssl_required:
                raise OperationalError(2026, "SSL is required but the server doesn't support it")

        self._client_flag = client_flag

    def _ssl_request_payload(self) -> bytes:
        charset_id = charset_by_name(self._charset).id
        return struct.pack('<iIB23s', self._client_flag, MAX_PACKET_LENGTH, charset_id, b'')

    def _initial_auth_response(self) -> tuple[bytes, bytes]:
        """Returns the plugin name and initial auth response for the handshake response packet."""

        plugin = self._auth_plugin_name
        if plugin in ('', 'mysql_native_password'):
            return plugin.encode('ascii'), auth.scramble_native_password(self._password, self._salt)
        elif plugin == 'caching_sha2_password':
            resp = auth.scramble_caching_sha2(self._password, self._salt) if self._password else b''
            return b'caching_sha2_password', resp
        elif plugin == 'sha256_password':
            if self._do_ssl or self._secure:
                resp = self._password + b'\0'
            elif self._password:
                resp = b'\1'  # request the server's public key
            else:
                resp = b'\0'
            return b'sha256_password', resp
        else:
            return plugin.encode('ascii'), b''

    def _handshake_response_payload(self) -> bytes:
        charset_id = charset_by_name(self._charset).id
        data = bytearray(struct.pack('<iIB23s', self._client_flag, MAX_PACKET_LENGTH, charset_id, b''))
        data += self._user + b'\0'

        plugin_name, authresp = self._initial_auth_response()

        if self._server_capabilities & CLIENT.PLUGIN_AUTH_LENENC_CLIENT_DATA:
            data += encode_lenenc_str(authresp)
        elif self._server_capabilities & CLIENT.SECURE_CONNECTION:
            data += struct.pack('B', len(authresp)) + authresp
        else:  # pragma: no cover - servers older than 4.1 are not supported
            data += authresp + b'\0'

        if self._database and self._server_capabilities & CLIENT.CONNECT_WITH_DB:
            data += self._database + b'\0'

        if self._server_capabilities & CLIENT.PLUGIN_AUTH:
            data += plugin_name + b'\0'

        if self._server_capabilities & CLIENT.CONNECT_ATTRS:
            attrs = bytearray()
            for k, v in self._connect_attrs.items():
                attrs += encode_lenenc_str(k.encode('utf-8'))
                attrs += encode_lenenc_str(v.encode('utf-8'))
            data += encode_lenenc_str(bytes(attrs))

        return bytes(data)

    def _switch_auth_response(self, plugin_name: str, plugin_data: bytes) -> OperationGenerator[bytes]:
        """Handles an AuthSwitchRequest, returning the packet payload received after responding."""

        if plugin_name == 'mysql_native_password':
            data = auth.scramble_native_password(self._password, plugin_data)
        elif plugin_name == 'client_ed25519':
            data = auth.ed25519_password(self._password, plugin_data)
        elif plugin_name == 'mysql_clear_password':
            data = self._password + b'\0'
        elif plugin_name == 'caching_sha2_password':
            self._auth_plugin_name = plugin_name
            self._salt = plugin_data
            return (yield from self._caching_sha2_auth((yield Step([OutPacket(
                auth.scramble_caching_sha2(self._password, plugin_data))]))))
        elif plugin_name == 'sha256_password':
            self._auth_plugin_name = plugin_name
            self._salt = plugin_data
            if self._secure:
                first = self._password + b'\0'
            elif self._password:
                first = b'\1'
            else:
                first = b'\0'
            return (yield from self._sha256_auth((yield Step([OutPacket(first)]))))
        else:
            raise OperationalError(2059, f"Authentication plugin '{plugin_name}' not configured")

        return (yield Step([OutPacket(data)]))

    def _sha256_auth(self, payload: bytes) -> OperationGenerator[bytes]:
        if self._secure or not self._password:
            return payload
        if parsing.is_auth_more_data(payload):
            self._server_public_key = payload[1:]
        if not self._server_public_key:
            raise OperationalError(2061, "Couldn't receive server's public key")
        enc = auth.sha2_rsa_encrypt(self._password, self._salt, self._server_public_key)
        return (yield Step([OutPacket(enc)]))

    def _caching_sha2_auth(self, payload: bytes) -> OperationGenerator[bytes]:
        if not self._password:
            return payload
        if not parsing.is_auth_more_data(payload):
            raise ProtocolError('caching_sha2_password: expected auth more data')
        r = PacketReader(payload)
        r.skip(1)
        n = r.read_uint8()
        if n == 3:  # fast auth succeeded
            return (yield Step())
        if n != 4:
            raise OperationalError(2061, f'caching sha2: Unknown result for fast auth: {n}')
        if self._secure:
            return (yield Step([OutPacket(self._password + b'\0')]))
        if not self._server_public_key:
            key_payload = yield Step([OutPacket(b'\x02')])  # request the public key
            if not parsing.is_auth_more_data(key_payload):
                raise ProtocolError('caching_sha2_password: expected a public key')
            self._server_public_key = key_payload[1:]
        enc = auth.sha2_rsa_encrypt(self._password, self._salt, self._server_public_key)
        return (yield Step([OutPacket(enc)]))

    def _read_handshake_flow(self) -> OperationGenerator[Handshake]:
        payload = yield Step()
        if parsing.is_err(payload):
            self._raise_err(payload)
        hs = parsing.parse_handshake(payload)
        self._apply_handshake(hs)
        self._compute_client_flag()
        return hs

    def read_handshake(self) -> Operation[Handshake]:
        return self._begin(self._read_handshake_flow())

    def _send_ssl_request_flow(self) -> OperationGenerator[None]:
        # The server sends no reply to this; it begins the TLS handshake, which the transport drives.
        yield Step([OutPacket(self._ssl_request_payload())], more=True)
        return None

    def send_ssl_request(self) -> Operation[None]:
        return self._begin(self._send_ssl_request_flow())

    def _authenticate_flow(self) -> OperationGenerator[None]:
        payload = yield Step([OutPacket(self._handshake_response_payload())])

        while True:
            if parsing.is_err(payload):
                self._raise_err(payload)
            elif parsing.is_ok(payload):
                self._apply_ok(payload)
                break
            elif parsing.is_auth_switch(payload):
                asr = parsing.parse_auth_switch(payload)
                payload = yield from self._switch_auth_response(asr.plugin_name, asr.data)
            elif parsing.is_auth_more_data(payload):
                if self._auth_plugin_name == 'caching_sha2_password':
                    payload = yield from self._caching_sha2_auth(payload)
                elif self._auth_plugin_name == 'sha256_password':
                    payload = yield from self._sha256_auth(payload)
                else:
                    raise OperationalError(2059, f'Received extra auth data for {self._auth_plugin_name!r}')
            else:
                raise ProtocolError(f'Unexpected packet during authentication: {payload[:1]!r}')

        return None

    def authenticate(self) -> Operation[None]:
        return self._begin(self._authenticate_flow())

    #
    # Result handling

    def _apply_ok(self, payload: bytes) -> parsing.OkPacket:
        ok = parsing.parse_ok(payload)
        self._server_status = ok.status_flags
        return ok

    def _raise_err(self, payload: bytes) -> ta.NoReturn:
        raise_mysql_exception(payload)

    def _query_flow(
            self,
            command: int,
            sql: bytes,
            local_infile: ta.Callable[[bytes], ta.Iterable[bytes]] | None,
    ) -> OperationGenerator[QueryResult]:
        first = yield Step([OutPacket(bytes([command]) + sql, starts_command=True)])
        return (yield from self._read_result(first, local_infile))

    def _read_result(
            self,
            first: bytes,
            local_infile: ta.Callable[[bytes], ta.Iterable[bytes]] | None,
    ) -> OperationGenerator[QueryResult]:
        if parsing.is_err(first):
            self._raise_err(first)

        if parsing.is_ok(first):
            return self._ok_result(first)

        if parsing.is_local_infile(first):
            first = yield from self._load_local(first, local_infile)
            if parsing.is_err(first):
                self._raise_err(first)
            return self._ok_result(first)

        schema = yield from self._read_columns_from(first)

        rows: list[Row] = []
        while True:
            payload = yield Step()
            if parsing.is_err(payload):
                self._raise_err(payload)
            if parsing.is_eof(payload):
                eof = parsing.parse_eof(payload)
                self._server_status = eof.status_flags
                return QueryResult(
                    affected_rows=len(rows),
                    insert_id=0,
                    server_status=eof.status_flags,
                    warning_count=eof.warning_count,
                    message=b'',
                    description=schema.description,
                    fields=schema.fields,
                    rows=tuple(rows),
                    has_next=eof.has_next,
                )
            rows.append(decode_row(payload, schema))

    def _read_columns_from(self, first: bytes) -> OperationGenerator[ResultSchema]:
        field_count = PacketReader(first).read_lenenc_int()
        fields: list[ColumnDefinition] = []
        for _ in range(check.not_none(field_count)):
            col_payload = yield Step()
            fields.append(parsing.parse_column_definition(col_payload, self._encoding))
        eof = yield Step()
        if not parsing.is_eof(eof):
            raise ProtocolError('Protocol error, expecting EOF after column definitions')
        return build_result_schema(
            fields,
            encoding=self._encoding,
            use_unicode=self._use_unicode,
            decoders=self._decoders,
        )

    def _ok_result(self, payload: bytes) -> QueryResult:
        ok = self._apply_ok(payload)
        return QueryResult(
            affected_rows=ok.affected_rows,
            insert_id=ok.insert_id,
            server_status=ok.status_flags,
            warning_count=ok.warning_count,
            message=ok.message,
            description=None,
            fields=(),
            rows=None,
            has_next=ok.has_next,
        )

    def _load_local(
            self,
            first: bytes,
            local_infile: ta.Callable[[bytes], ta.Iterable[bytes]] | None,
    ) -> OperationGenerator[bytes]:
        request = parsing.parse_local_infile(first)
        error: BaseException | None = None
        if local_infile is not None:
            try:
                for chunk in local_infile(request.filename):
                    if chunk:
                        yield Step([OutPacket(chunk)], more=True)
            except Exception as e:  # noqa: BLE001
                error = e
        # The empty terminating packet must be sent whatever happened, or the connection is left out of sync.
        final = yield Step([OutPacket(b'')])
        if error is not None:
            raise error
        return final

    def query(
            self,
            sql: bytes,
            *,
            command: int = COMMAND.COM_QUERY,
            local_infile: ta.Callable[[bytes], ta.Iterable[bytes]] | None = None,
    ) -> Operation[QueryResult]:
        return self._begin(self._query_flow(command, sql, local_infile))

    #
    # Unbuffered queries

    def _start_unbuffered_flow(
            self,
            sql: bytes,
            local_infile: ta.Callable[[bytes], ta.Iterable[bytes]] | None,
    ) -> OperationGenerator[QueryResult | UnbufferedResult]:
        first = yield Step([OutPacket(bytes([COMMAND.COM_QUERY]) + sql, starts_command=True)])
        if parsing.is_err(first):
            self._raise_err(first)
        if parsing.is_ok(first):
            return self._ok_result(first)
        if parsing.is_local_infile(first):
            first = yield from self._load_local(first, local_infile)
            if parsing.is_err(first):
                self._raise_err(first)
            return self._ok_result(first)
        schema = yield from self._read_columns_from(first)
        return UnbufferedResult(schema)

    def start_unbuffered(
            self,
            sql: bytes,
            *,
            local_infile: ta.Callable[[bytes], ta.Iterable[bytes]] | None = None,
    ) -> Operation[QueryResult | UnbufferedResult]:
        return self._begin(self._start_unbuffered_flow(sql, local_infile))

    def _fetch_row_flow(self, result: UnbufferedResult) -> OperationGenerator[Row | None]:
        payload = yield Step()
        if parsing.is_err(payload):
            result.active = False
            self._raise_err(payload)
        if parsing.is_eof(payload):
            eof = parsing.parse_eof(payload)
            result.server_status = eof.status_flags
            self._server_status = eof.status_flags
            result.warning_count = eof.warning_count
            result.has_next = eof.has_next
            result.active = False
            return None
        return decode_row(payload, result.schema)

    def fetch_row(self, result: UnbufferedResult) -> Operation[Row | None]:
        return self._begin(self._fetch_row_flow(result))

    #
    # Multi-results

    def _next_result_flow(
            self,
            unbuffered: bool,
    ) -> OperationGenerator[QueryResult | UnbufferedResult]:
        first = yield Step()
        if unbuffered:
            if parsing.is_err(first):
                self._raise_err(first)
            if parsing.is_ok(first):
                return self._ok_result(first)
            schema = yield from self._read_columns_from(first)
            return UnbufferedResult(schema)
        return (yield from self._read_result(first, None))

    def next_result(self, *, unbuffered: bool = False) -> Operation[QueryResult | UnbufferedResult]:
        return self._begin(self._next_result_flow(unbuffered))

    #
    # Simple commands

    def _command_flow(self, command: int, payload: bytes) -> OperationGenerator[parsing.OkPacket]:
        resp = yield Step([OutPacket(bytes([command]) + payload, starts_command=True)])
        if parsing.is_err(resp):
            self._raise_err(resp)
        if not parsing.is_ok(resp):
            raise OperationalError(2014, 'Command Out of Sync')
        return self._apply_ok(resp)

    def command(self, command: int, payload: bytes = b'') -> Operation[parsing.OkPacket]:
        return self._begin(self._command_flow(command, payload))

    def _quit_flow(self) -> OperationGenerator[None]:
        yield Step([OutPacket(bytes([COMMAND.COM_QUIT]), starts_command=True)])
        return None

    def quit(self) -> Operation[None]:
        return self._begin(self._quit_flow())

    @property
    def in_transaction(self) -> bool:
        return bool(self._server_status & SERVER_STATUS.SERVER_STATUS_IN_TRANS)

    @property
    def autocommit_enabled(self) -> bool:
        return bool(self._server_status & SERVER_STATUS.SERVER_STATUS_AUTOCOMMIT)

    @property
    def no_backslash_escapes(self) -> bool:
        return bool(self._server_status & SERVER_STATUS.SERVER_STATUS_NO_BACKSLASH_ESCAPES)
