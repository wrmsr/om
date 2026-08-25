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
Sync and async MySQL connections share this driver-independent core: a ProtocolSession driven through the pipeline
handlers, plus the value adaptation (escaping, result wrapping) the cursor layer needs. The two flavors differ only in
whether the pipeline driver is stepped with a blocking socket or awaited on asyncio streams.
"""
import typing as ta

from omcore import lang
from omcore.io.pipelines.ssl.handlers import SslIoPipelineHandler

from .. import converters
from ..charset import charset_by_name
from ..constants import CLIENT
from ..errors import Error
from ..errors import OperationalError
from ..protocol.session import ProtocolSession
from ..protocol.session import QueryResult
from ..protocol.session import UnbufferedResult
from .handlers import OperationDone
from .sockets import SslContextArg
from .sockets import make_ssl_context


##


DEFAULT_CHARSET = 'utf8mb4'


class BaseConnection(lang.Abstract):
    def __init__(
            self,
            *,
            user: str | bytes,
            password: str | bytes = '',
            database: str | bytes | None = None,
            charset: str = '',
            collation: str | None = None,
            use_unicode: bool = True,
            client_flag: int = 0,
            conv: ta.Mapping[ta.Any, ta.Any] | None = None,
            local_infile: bool = False,
            max_allowed_packet: int = 16 * 1024 * 1024,
            binary_prefix: bool = False,
            server_public_key: bytes | None = None,
            program_name: str | None = None,
            ssl: SslContextArg = None,
            ssl_disabled: bool = False,
            server_hostname: str | None = None,
            force_auth_plugin: str | None = None,
    ) -> None:
        super().__init__()

        self._charset = charset or DEFAULT_CHARSET
        self._collation = collation
        self._use_unicode = use_unicode
        self._encoding = charset_by_name(self._charset).encoding
        self._local_infile = bool(local_infile)
        self._max_allowed_packet = max_allowed_packet
        self._binary_prefix = binary_prefix

        conv = converters.conversions if conv is None else conv
        self._encoders = {k: v for k, v in conv.items() if type(k) is not int}
        self._decoders: dict[int, ta.Any] = {k: v for k, v in conv.items() if type(k) is int}

        base_client_flag = client_flag | CLIENT.CAPABILITIES
        if self._local_infile:
            base_client_flag |= CLIENT.LOCAL_FILES

        db_bytes = database.encode(self._encoding) if isinstance(database, str) else database
        pw_bytes = password.encode('latin1') if isinstance(password, str) else (password or b'')
        user_bytes = user.encode(self._encoding) if isinstance(user, str) else user

        self._ssl_arg = ssl
        self._ssl_disabled = bool(ssl_disabled)
        self._server_hostname = server_hostname
        self._ssl_handler: SslIoPipelineHandler | None = None
        self._secure_transport = False  # unix sockets are secure without TLS

        # The keyword arguments needed to build a fresh session, so a reconnect can start clean.
        self._session_kwargs: dict[str, ta.Any] = dict(
            user=user_bytes,
            password=pw_bytes,
            database=db_bytes,
            charset=self._charset,
            client_flag=base_client_flag,
            use_unicode=use_unicode,
            decoders=self._decoders,
            server_public_key=server_public_key,
            ssl_wanted=not ssl_disabled,
            ssl_required=ssl is not None,
            program_name=program_name,
            force_auth_plugin=force_auth_plugin,
        )
        self._reset_session()

        self._result: QueryResult | UnbufferedResult | None = None

    def _reset_session(self) -> None:
        self._ssl_handler = None
        self._secure_transport = False
        self._session = ProtocolSession(**self._session_kwargs)

    def _after_connect(self) -> None:
        """Runs after a successful handshake, on both the initial connect and any reconnect. Overridden for setup."""

    def _mark_secure_transport(self) -> None:
        self._secure_transport = True
        self._session._secure = True  # noqa: SLF001

    #
    # State

    @property
    def session(self) -> ProtocolSession:
        return self._session

    @property
    def result(self) -> QueryResult | UnbufferedResult | None:
        return self._result

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def is_ssl(self) -> bool:
        return self._ssl_handler is not None

    def get_server_info(self) -> str:
        return self._session.server_version

    def thread_id(self) -> int:
        return self._session.thread_id

    def get_autocommit(self) -> bool:
        return self._session.autocommit_enabled

    @property
    def open(self) -> bool:
        raise NotImplementedError

    #
    # SSL

    def _wants_ssl(self) -> bool:
        return (
            not self._ssl_disabled and
            not self._secure_transport and
            self._session.will_ssl
        )

    def _make_ssl_handler(self) -> SslIoPipelineHandler:
        self._ssl_handler = SslIoPipelineHandler(
            make_ssl_context(self._ssl_arg),
            server_side=False,
            server_hostname=self._server_hostname,
        )
        return self._ssl_handler

    #
    # Escaping

    def escape(self, obj: ta.Any, mapping: ta.Mapping[ta.Any, ta.Any] | None = None) -> ta.Any:
        if isinstance(obj, str):
            return "'" + self.escape_string(obj) + "'"
        if isinstance(obj, (bytes, bytearray)):
            ret = self._quote_bytes(obj)
            if self._binary_prefix:
                ret = '_binary' + ret
            return ret
        return converters.escape_item(obj, self._charset, mapping=mapping)

    def literal(self, obj: ta.Any) -> ta.Any:
        return self.escape(obj, self._encoders)

    def escape_string(self, s: str) -> str:
        if self._session.no_backslash_escapes:
            return s.replace("'", "''")
        return converters.escape_string(s)

    def _quote_bytes(self, s: bytes | bytearray) -> str:
        if self._session.no_backslash_escapes:
            return "'{}'".format(s.replace(b"'", b"''").decode('ascii', 'surrogateescape'))
        return converters.escape_bytes(s)

    #
    # Result adaptation

    def _local_infile_reader(self) -> ta.Callable[[bytes], ta.Iterable[bytes]] | None:
        if not self._local_infile:
            return None

        packet_size = min(self._max_allowed_packet, 16 * 1024)

        def read(filename: bytes) -> ta.Iterable[bytes]:
            try:
                f = open(filename.decode(self._encoding), 'rb')  # noqa: SIM115,PTH123
            except OSError as e:
                raise OperationalError(1017, f"Can't open file {filename!r}: {e}") from e
            with f:
                while (chunk := f.read(packet_size)):
                    yield chunk

        return read

    def _check_output(self, op: ta.Any, out: ta.Any, *, running: bool) -> bool:
        if out is None:
            if not running:
                raise Error('Lost connection to MySQL server during query')
            return False
        if isinstance(out, OperationDone):
            return out.op is op
        raise Error(f'Unexpected pipeline output: {out!r}')
