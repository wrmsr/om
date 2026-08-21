"""
Sync and async core connections share one implementation: a ProtocolSession driven through the pipeline handlers, with
the only difference being whether the pipeline driver is stepped with a blocking socket or awaited on asyncio streams.
"""
import typing as ta

from omcore import lang
from omcore.io.pipelines.ssl.handlers import SslIoPipelineHandler

from .. import scramp
from ..converters import InAdapter
from ..converters import OutAdapter
from ..exceptions import InterfaceError
from ..protocol import messages as msgs
from ..protocol.codes import TransactionStatus
from ..protocol.session import Operation
from ..protocol.session import ProtocolSession
from ..protocol.startup import make_startup_params
from .handlers import OperationDone
from .sockets import SslContextArg
from .sockets import make_ssl_context


##


class BaseCoreConnection(lang.Abstract):
    """The driver-independent bulk of a connection."""

    def __init__(
            self,
            *,
            user: str | bytes,
            password: str | bytes | None = None,
            database: str | bytes | None = None,
            application_name: str | bytes | None = None,
            replication: str | bytes | None = None,
            startup_params: ta.Mapping[str, str | bytes] | None = None,
            ssl_context: SslContextArg = None,
            server_hostname: str | None = None,
    ) -> None:
        super().__init__()

        startup = make_startup_params(
            user=user,
            database=database,
            application_name=application_name,
            replication=replication,
            startup_params=startup_params,
        )

        self._ssl_context_arg = ssl_context
        self._server_hostname = server_hostname
        self._ssl_handler: SslIoPipelineHandler | None = None

        self._session = ProtocolSession(
            user=startup['user'],
            password=password.encode('utf8') if isinstance(password, str) else password,
            startup_params=startup,
            channel_binding=self._channel_binding,
        )

    #
    # State

    @property
    def session(self) -> ProtocolSession:
        return self._session

    @property
    def is_ssl(self) -> bool:
        return self._ssl_handler is not None

    @property
    def notifications(self) -> ta.Sequence[msgs.NotificationResponse]:
        return self._session.notifications

    @property
    def notices(self) -> ta.Sequence[msgs.NoticeResponse]:
        return self._session.notices

    @property
    def parameter_statuses(self) -> ta.Mapping[str, str]:
        return self._session.parameter_statuses

    @property
    def transaction_status(self) -> TransactionStatus | None:
        return self._session.transaction_status

    @property
    def pg_types(self) -> ta.Mapping[int, InAdapter]:
        return self._session.pg_types

    @property
    def py_types(self) -> ta.Mapping[type, OutAdapter]:
        return self._session.py_types

    def register_out_adapter(self, typ: type, out_func: OutAdapter) -> None:
        self._session.register_out_adapter(typ, out_func)

    def register_in_adapter(self, oid: int, in_func: InAdapter) -> None:
        self._session.register_in_adapter(oid, in_func)

    #
    # SSL

    def _channel_binding(self) -> scramp.ChannelBinding | None:
        if (h := self._ssl_handler) is None or (obj := h.ssl_object) is None:
            return None
        return scramp.make_channel_binding('tls-server-end-point', obj)

    def _wants_ssl(self) -> bool:
        return self._ssl_context_arg is not False

    def _on_ssl_response(self, accepted: bool) -> SslIoPipelineHandler | None:
        """Returns the TLS handler to add outermost to the pipeline, if the server agreed to SSL."""

        if accepted:
            self._ssl_handler = SslIoPipelineHandler(
                make_ssl_context(self._ssl_context_arg),
                server_side=False,
                server_hostname=self._server_hostname,
            )
            return self._ssl_handler

        if self._ssl_context_arg is not None:
            raise InterfaceError('Server refuses SSL')

        return None

    #
    # Operations

    def _check_output(self, op: Operation, out: ta.Any, *, running: bool) -> bool:
        """Returns whether the given pipeline output completes the given operation."""

        if out is None:
            if not running:
                raise InterfaceError('network error')
            return False

        if isinstance(out, OperationDone):
            return out.op is op

        raise InterfaceError(f'Unexpected pipeline output: {out!r}')
