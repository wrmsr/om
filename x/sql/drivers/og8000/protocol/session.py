"""
The sans-IO heart of a connection: all protocol state, and every request/response flow expressed as a stepwise
Operation which consumes backend messages and produces frontend messages without ever touching a transport. Sync and
async drivers differ only in how they shuttle bytes between a transport and a session.
"""
import codecs
import collections
import hashlib
import io
import itertools
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .. import scramp
from ..converters import PG_PY_ENCODINGS
from ..converters import PG_TYPES
from ..converters import PY_TYPES
from ..converters import InAdapter
from ..converters import OutAdapter
from ..converters import make_params
from ..converters import string_in
from ..errors import DatabaseError
from ..errors import InterfaceError
from . import messages as msgs
from .codes import DescribeKind
from .codes import TransactionStatus
from .decoding import BackendMessageDecoder
from .encoding import FrontendMessageEncoder


T = ta.TypeVar('T')

CopyStream: ta.TypeAlias = ta.IO[ta.Any] | ta.Iterable[str | bytes]

Columns: ta.TypeAlias = ta.Sequence[ta.Mapping[str, ta.Any]]

# Yields the next Step for the driver, receives the next backend message (or None after a `more` step), returns the
# operation's result.
OperationGenerator: ta.TypeAlias = ta.Generator['Step', msgs.BackendMessage | None, T]


##


@dc.dataclass(frozen=True)
class Step:
    """
    What a driver must do next on behalf of an operation: send these messages (flushing the transport afterwards), then
    either wait for the next backend message or, if `more` is set, immediately ask the operation for its next step.
    """

    messages: ta.Sequence[msgs.FrontendMessage] = ()
    more: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, 'messages', tuple(self.messages))


class Operation(ta.Generic[T]):
    """A single protocol round trip (or sequence thereof) in progress, driven by a Step-yielding generator."""

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

    def _advance(self, msg: msgs.BackendMessage | None) -> Step:
        try:
            return self._gen.send(msg)
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

    def feed(self, msg: msgs.BackendMessage | None) -> Step:
        check.state(self._started and not self._done)
        return self._advance(msg)

    def fail(self, exc: BaseException) -> None:
        """Abandons the operation, typically because its transport failed. Any later step is an error."""

        check.state(not self._done)
        self._done = True
        self._error = exc
        self._gen.close()

    def result(self) -> T:
        check.state(self._done)
        if self._error is not None:
            raise self._error
        return self._result


class Context:
    """The result state accumulated by a query operation."""

    stream_write: ta.Callable[[bytes], ta.Any]

    def __init__(
            self,
            statement: str | None,
            stream: CopyStream | None = None,
            columns: Columns | None = None,
            input_funcs: ta.Sequence[InAdapter] | None = None,
    ) -> None:
        super().__init__()

        self.statement = statement
        self.rows: list[list[ta.Any]] | None = None if columns is None else []
        self.row_count = -1
        self.columns = columns
        self.stream = stream
        self.input_funcs: ta.Sequence[InAdapter] = [] if input_funcs is None else input_funcs
        self.error: Exception | None = None


class PreparedStatementInfo(ta.NamedTuple):
    name: str
    columns: Columns | None
    input_funcs: ta.Sequence[InAdapter]


##


class ProtocolSession:
    def __init__(
            self,
            *,
            user: bytes,
            password: bytes | None = None,
            startup_params: ta.Mapping[str, bytes],
            channel_binding: scramp.ChannelBinding | ta.Callable[[], scramp.ChannelBinding | None] | None = None,
            pg_types: ta.Mapping[int, InAdapter] | None = None,
            py_types: ta.Mapping[type, OutAdapter] | None = None,
    ) -> None:
        super().__init__()

        self._user = user
        self._password = password
        self._startup_params = dict(startup_params)

        # Channel binding data may only become available after a TLS handshake that the startup exchange itself drives,
        # so it can be supplied lazily.
        self._channel_binding: ta.Callable[[], scramp.ChannelBinding | None]
        if callable(channel_binding):
            self._channel_binding = channel_binding
        else:
            self._channel_binding = lambda: channel_binding

        self._client_encoding = 'utf8'
        self._encoder = FrontendMessageEncoder(encoding=self._client_encoding)
        self._decoder = BackendMessageDecoder(encoding=self._client_encoding)

        self._parameter_statuses: dict[str, str] = {}
        self._notices: collections.deque[msgs.NoticeResponse] = collections.deque(maxlen=100)
        self._notifications: collections.deque[msgs.NotificationResponse] = collections.deque(maxlen=100)
        self._transaction_status: TransactionStatus | None = None
        self._backend_key_data: msgs.BackendKeyData | None = None

        self._pg_types: collections.defaultdict[int, InAdapter] = collections.defaultdict(
            lambda: string_in,
            PG_TYPES if pg_types is None else pg_types,
        )
        self._py_types: dict[type, OutAdapter] = dict(PY_TYPES if py_types is None else py_types)

        self._statement_names: set[str] = set()
        self._auth: scramp.ScramClient | None = None
        self._current: Operation | None = None

    #
    # State

    @property
    def encoder(self) -> FrontendMessageEncoder:
        return self._encoder

    @property
    def decoder(self) -> BackendMessageDecoder:
        return self._decoder

    @property
    def client_encoding(self) -> str:
        return self._client_encoding

    @property
    def parameter_statuses(self) -> ta.Mapping[str, str]:
        return self._parameter_statuses

    @property
    def notices(self) -> collections.deque[msgs.NoticeResponse]:
        return self._notices

    @property
    def notifications(self) -> collections.deque[msgs.NotificationResponse]:
        return self._notifications

    @property
    def transaction_status(self) -> TransactionStatus | None:
        return self._transaction_status

    @property
    def backend_key_data(self) -> msgs.BackendKeyData | None:
        return self._backend_key_data

    @property
    def pg_types(self) -> ta.Mapping[int, InAdapter]:
        return self._pg_types

    @property
    def py_types(self) -> ta.Mapping[type, OutAdapter]:
        return self._py_types

    def register_in_adapter(self, oid: int, in_func: InAdapter) -> None:
        self._pg_types[oid] = in_func

    def register_out_adapter(self, typ: type, out_func: OutAdapter) -> None:
        self._py_types[typ] = out_func

    @property
    def sasl_mechanism(self) -> str | None:
        """The SASL mechanism negotiated during startup, if SASL authentication was used."""

        return None if self._auth is None else self._auth.mechanism_name

    @property
    def current(self) -> Operation | None:
        return self._current

    #
    # Driving

    def _observe(self, msg: msgs.BackendMessage) -> None:
        """Applies the connection-wide effects of a backend message, independent of any operation in progress."""

        if isinstance(msg, msgs.ParameterStatus):
            self._parameter_statuses[msg.name] = msg.value
            if msg.name == 'client_encoding':
                encoding = msg.value.lower()
                py_encoding = PG_PY_ENCODINGS.get(encoding, encoding)
                if py_encoding is None:
                    raise InterfaceError(f'Unsupported client encoding: {msg.value}')
                self._client_encoding = py_encoding
                self._encoder.set_encoding(py_encoding)
                self._decoder.set_encoding(py_encoding)

        elif isinstance(msg, msgs.NoticeResponse):
            self._notices.append(msg)

        elif isinstance(msg, msgs.NotificationResponse):
            self._notifications.append(msg)

        elif isinstance(msg, msgs.BackendKeyData):
            self._backend_key_data = msg

        elif isinstance(msg, msgs.ReadyForQuery):
            self._transaction_status = msg.status

    def handle(self, msg: msgs.BackendMessage) -> Step:
        """Feeds a received backend message to the session, returning what to do next for the current operation."""

        self._observe(msg)

        if (op := self._current) is None:
            if isinstance(msg, msgs.ErrorResponse):
                raise DatabaseError(dict(msg.fields))
            return Step()

        step = op.feed(msg)
        if op.done:
            self._current = None
        return step

    def resume(self) -> Step:
        """Asks the current operation for its next step after one flagged as having more to send."""

        op = check.not_none(self._current)
        step = op.feed(None)
        if op.done:
            self._current = None
        return step

    def fail(self, exc: BaseException) -> None:
        """Fails the current operation, if any, typically because the transport is gone."""

        if (op := self._current) is not None:
            self._current = None
            if not op.done:
                op.fail(exc)

    def _begin(self, gen: OperationGenerator[T]) -> Operation[T]:
        if (cur := self._current) is not None and not cur.done:
            raise InterfaceError('An operation is already in progress')
        op: Operation[T] = Operation(gen)
        self._current = op
        return op

    #
    # SSL negotiation

    def _negotiate_ssl_flow(self) -> OperationGenerator[bool]:
        msg = yield Step([msgs.SslRequest()])
        if not isinstance(msg, msgs.SslResponse):
            raise InterfaceError(f'Expected an SSL response but got {msg!r}')
        return msg.accepted

    def negotiate_ssl(self) -> Operation[bool]:
        """Asks the server whether it will speak SSL. The transport itself must perform any resulting TLS handshake."""

        return self._begin(self._negotiate_ssl_flow())

    #
    # Startup and authentication

    def _authenticate(self, msg: msgs.Authentication) -> list[msgs.FrontendMessage]:
        if isinstance(msg, msgs.AuthenticationOk):
            return []

        elif isinstance(msg, msgs.AuthenticationCleartextPassword):
            if self._password is None:
                raise InterfaceError('server requesting password authentication, but no password was provided')
            return [msgs.PasswordMessage(self._password)]

        elif isinstance(msg, msgs.AuthenticationMd5Password):
            if self._password is None:
                raise InterfaceError('server requesting MD5 password authentication, but no password was provided')
            pwd = b'md5' + hashlib.md5(  # noqa: S324
                hashlib.md5(self._password + self._user).hexdigest().encode('ascii') + msg.salt,  # noqa: S324
            ).hexdigest().encode('ascii')
            return [msgs.PasswordMessage(pwd)]

        elif isinstance(msg, msgs.AuthenticationSasl):
            if self._password is None:
                raise InterfaceError('server requesting SASL authentication, but no password was provided')
            self._auth = auth = scramp.ScramClient(
                list(msg.mechanisms),
                self._user.decode('utf8'),
                self._password.decode('utf8'),
                channel_binding=self._channel_binding(),
            )
            return [msgs.SaslInitialResponse(auth.mechanism_name, auth.get_client_first().encode('utf8'))]

        elif isinstance(msg, msgs.AuthenticationSaslContinue):
            auth = check.not_none(self._auth)
            auth.set_server_first(msg.data.decode('utf8'))
            return [msgs.SaslResponse(auth.get_client_final().encode('utf8'))]

        elif isinstance(msg, msgs.AuthenticationSaslFinal):
            check.not_none(self._auth).set_server_final(msg.data.decode('utf8'))
            return []

        elif isinstance(msg, msgs.AuthenticationOther):
            if msg.code in (2, 4, 6, 7, 8, 9):
                raise InterfaceError(f'Authentication method {msg.code} not supported by og8000.')
            else:
                raise InterfaceError(f'Authentication method {msg.code} not recognized by og8000.')

        else:
            raise TypeError(msg)

    def _startup_flow(self) -> OperationGenerator[None]:
        msg = yield Step([msgs.StartupMessage(self._startup_params)])
        while True:
            if isinstance(msg, msgs.Authentication):
                msg = yield Step(self._authenticate(msg))
            elif isinstance(msg, msgs.ErrorResponse):
                raise DatabaseError(dict(msg.fields))
            elif isinstance(msg, msgs.ReadyForQuery):
                return
            else:
                msg = yield Step()

    def startup(self) -> Operation[None]:
        return self._begin(self._startup_flow())

    #
    # Result handling

    def _handle_row_description(self, context: Context, msg: msgs.RowDescription) -> None:
        columns: list[dict[str, ta.Any]] = []
        input_funcs: list[InAdapter] = []
        for field in msg.fields:
            columns.append({
                'table_oid': field.table_oid,
                'column_attrnum': field.column_attrnum,
                'type_oid': field.type_oid,
                'type_size': field.type_size,
                'type_modifier': field.type_modifier,
                'format': field.format_code,
                'name': field.name,
            })
            input_funcs.append(self._pg_types[field.type_oid])

        context.columns = columns
        context.input_funcs = input_funcs
        if context.rows is None:
            context.rows = []

    def _handle_data_row(self, context: Context, msg: msgs.DataRow) -> None:
        encoding = self._client_encoding
        row = [
            None if value is None else func(value.decode(encoding))
            for func, value in zip(context.input_funcs, msg.values, strict=True)
        ]
        check.not_none(context.rows).append(row)

    def _handle_command_complete(self, context: Context, msg: msgs.CommandComplete) -> None:
        if self._transaction_status == TransactionStatus.IN_FAILED_TRANSACTION and context.error is None:
            statement = context.statement
            if statement is None or statement.split()[0].rstrip(';').upper() != 'ROLLBACK':
                context.error = InterfaceError('in failed transaction block')

        try:
            row_count = int(msg.tag.split(' ')[-1])
        except ValueError:
            return

        if context.row_count == -1:
            context.row_count = row_count
        else:
            context.row_count += row_count

    def _handle_copy_out_response(self, context: Context, msg: msgs.CopyOutResponse) -> None:
        stream = context.stream

        if stream is None:
            raise InterfaceError('An output stream is required for the COPY OUT response.')

        elif isinstance(stream, io.TextIOBase):
            if msg.is_binary:
                raise InterfaceError('The COPY OUT stream is binary, but the stream parameter is text.')

            decode = codecs.getdecoder(self._client_encoding)

            def w(data: bytes) -> None:
                stream.write(decode(data)[0])

            context.stream_write = w

        else:
            context.stream_write = stream.write  # type: ignore[union-attr]

    def _copy_in(
            self,
            context: Context,
            msg: msgs.CopyInResponse,
    ) -> ta.Generator[Step, msgs.BackendMessage | None, msgs.BackendMessage | None]:
        stream = context.stream

        if stream is None:
            raise InterfaceError(
                "The 'stream' parameter is required for the COPY IN response. The "
                "'stream' parameter can be an I/O stream or an iterable.",
            )

        if isinstance(stream, io.IOBase):
            readinto: ta.Callable[[bytearray], int]

            if isinstance(stream, io.TextIOBase):
                if msg.is_binary:
                    raise InterfaceError('The COPY IN stream is binary, but the stream parameter is a text stream.')

                def ri(bffr: bytearray) -> int:
                    bffr.clear()
                    bffr.extend(stream.read(4096).encode(self._client_encoding))
                    return len(bffr)

                readinto = ri

            else:
                readinto = stream.readinto  # type: ignore[attr-defined]

            bffr = bytearray(8192)
            while True:
                bytes_read = readinto(bffr)
                if bytes_read == 0:
                    break
                yield Step([msgs.CopyData(bytes(bffr[:bytes_read]))], more=True)

        else:
            for k in stream:
                if isinstance(k, str):
                    if msg.is_binary:
                        raise InterfaceError(
                            'The COPY IN stream is binary, but the stream parameter '
                            'is an iterable with str type items.',
                        )
                    b = k.encode(self._client_encoding)
                else:
                    b = k

                yield Step([msgs.CopyData(b)], more=True)

        return (yield Step([msgs.CopyDone(), msgs.Sync()]))

    def _drain(self, context: Context, msg: msgs.BackendMessage | None) -> OperationGenerator[None]:
        """Handles result messages into the context until the ReadyForQuery which ends the round trip."""

        while not isinstance(msg, msgs.ReadyForQuery):
            if msg is None:
                pass

            elif isinstance(msg, msgs.ErrorResponse):
                context.error = DatabaseError(dict(msg.fields))

            elif isinstance(msg, msgs.RowDescription):
                self._handle_row_description(context, msg)

            elif isinstance(msg, msgs.DataRow):
                self._handle_data_row(context, msg)

            elif isinstance(msg, msgs.CommandComplete):
                self._handle_command_complete(context, msg)

            elif isinstance(msg, msgs.CopyOutResponse):
                self._handle_copy_out_response(context, msg)

            elif isinstance(msg, msgs.CopyData):
                context.stream_write(msg.data)

            elif isinstance(msg, msgs.CopyInResponse):
                msg = yield from self._copy_in(context, msg)
                continue

            msg = yield Step()

        if context.error is not None:
            raise context.error

    #
    # Query operations

    def _execute_simple_flow(self, statement: str) -> OperationGenerator[Context]:
        context = Context(statement)
        msg = yield Step([msgs.Query(statement)])
        yield from self._drain(context, msg)
        return context

    def execute_simple(self, statement: str) -> Operation[Context]:
        return self._begin(self._execute_simple_flow(statement))

    def _execute_unnamed_flow(
            self,
            statement: str,
            vals: ta.Iterable[ta.Any],
            oids: ta.Sequence[int],
            stream: CopyStream | None,
    ) -> OperationGenerator[Context]:
        context = Context(statement, stream=stream)

        msg = yield Step([
            msgs.Parse('', statement, oids),
            msgs.Flush(),
            msgs.Sync(),
        ])
        yield from self._drain(context, msg)

        msg = yield Step([
            msgs.Describe(DescribeKind.STATEMENT, ''),
            msgs.Flush(),
            msgs.Sync(),
        ])
        yield from self._drain(context, msg)

        params = make_params(self._py_types, vals)
        msg = yield Step([
            msgs.Bind('', '', params),
            msgs.Flush(),
            msgs.Execute(''),
            msgs.Flush(),
            msgs.Sync(),
        ])
        yield from self._drain(context, msg)

        return context

    def execute_unnamed(
            self,
            statement: str,
            vals: ta.Iterable[ta.Any] = (),
            oids: ta.Sequence[int] = (),
            stream: CopyStream | None = None,
    ) -> Operation[Context]:
        return self._begin(self._execute_unnamed_flow(statement, vals, oids, stream))

    def _allocate_statement_name(self) -> str:
        for i in itertools.count():
            name = f'og8000_statement_{i}'
            if name not in self._statement_names:
                self._statement_names.add(name)
                return name
        raise RuntimeError  # pragma: no cover

    def _prepare_statement_flow(
            self,
            statement: str,
            oids: ta.Sequence[int],
    ) -> OperationGenerator[PreparedStatementInfo]:
        name = self._allocate_statement_name()
        context = Context(statement)

        msg = yield Step([
            msgs.Parse(name, statement, oids),
            msgs.Flush(),
            msgs.Describe(DescribeKind.STATEMENT, name),
            msgs.Flush(),
            msgs.Sync(),
        ])
        yield from self._drain(context, msg)

        return PreparedStatementInfo(name, context.columns, context.input_funcs)

    def prepare_statement(
            self,
            statement: str,
            oids: ta.Sequence[int] | None = None,
    ) -> Operation[PreparedStatementInfo]:
        return self._begin(self._prepare_statement_flow(statement, () if oids is None else oids))

    def _execute_named_flow(
            self,
            name: str,
            params: ta.Sequence[str | None],
            columns: Columns | None,
            input_funcs: ta.Sequence[InAdapter],
            statement: str,
    ) -> OperationGenerator[Context]:
        context = Context(statement, columns=columns, input_funcs=input_funcs)

        msg = yield Step([
            msgs.Bind('', name, params),
            msgs.Flush(),
            msgs.Execute(''),
            msgs.Flush(),
            msgs.Sync(),
        ])
        yield from self._drain(context, msg)

        return context

    def execute_named(
            self,
            name: str,
            params: ta.Sequence[str | None],
            columns: Columns | None,
            input_funcs: ta.Sequence[InAdapter],
            statement: str,
    ) -> Operation[Context]:
        return self._begin(self._execute_named_flow(name, params, columns, input_funcs, statement))

    def _close_prepared_statement_flow(self, name: str) -> OperationGenerator[None]:
        msg = yield Step([
            msgs.Close(DescribeKind.STATEMENT, name),
            msgs.Flush(),
            msgs.Sync(),
        ])
        yield from self._drain(Context(None), msg)
        self._statement_names.discard(name)

    def close_prepared_statement(self, name: str) -> Operation[None]:
        return self._begin(self._close_prepared_statement_flow(name))
