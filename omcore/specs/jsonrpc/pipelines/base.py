"""
The driver-independent half of a connection: everything a host does with a session other than pumping the driver.

Subclasses tape a specific driver on: they own the pumping loop (a task for asyncio, the caller's thread for sync), the
waiter implementation callers block on, and how inbound requests get dispatched. Everything else - id assignment,
demultiplexing session events to waiters, result / error conversion, closure bookkeeping - lives here.
"""
import abc
import typing as ta

from .... import lang
from ....logs import all as logs
from ..conns import AsyncJsonrpcConnection
from ..conns import JsonrpcConnection
from ..dispatch import jsonrpc_error_for_exception
from ..errors import JsonrpcConnectionClosedError
from ..errors import JsonrpcRemoteError
from ..ids import JsonrpcIdCreator
from ..ids import JsonrpcIdCreatorLike
from ..ids import jsonrpc_id_creator_of
from ..types import Error
from ..types import Id
from ..types import NotSpecified
from ..types import Params
from ..types import Request
from ..types import Response
from ..types import notification
from ..types import request
from .configs import JsonrpcPipelineConfig
from .messages import JsonrpcPipelineMessages as Jpm


log = logs.get_module_logger(globals())


##


class JsonrpcResponseWaiter(lang.Abstract):
    """What a caller blocks on for one sent request. Exactly one of the two setters is ever called."""

    @abc.abstractmethod
    def set_response(self, response: Response) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def set_exception(self, exc: BaseException) -> None:
        raise NotImplementedError


##


class BaseJsonrpcConnection(lang.Abstract):
    def __init__(
            self,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            id_creator: JsonrpcIdCreatorLike | None = None,
            include_error_details: bool = False,
    ) -> None:
        super().__init__()

        self._config = config
        self._id_creator: JsonrpcIdCreator = jsonrpc_id_creator_of(id_creator)
        self._include_error_details = include_error_details

        self._waiters: dict[Id, JsonrpcResponseWaiter] = {}

        self._closed = False
        self._close_exc: BaseException | None = None

    @property
    def config(self) -> JsonrpcPipelineConfig:
        return self._config

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def close_exception(self) -> BaseException | None:
        """Why the connection closed, or None if it was closed cleanly or is still open."""

        return self._close_exc

    ##
    # building messages

    def _new_request(self, method: str, params: Params | None) -> Request:
        return request(self._id_creator(), method, params)

    def _new_notification(self, method: str, params: Params | None) -> Request:
        return notification(method, params)

    def _closed_error(self) -> JsonrpcConnectionClosedError:
        if (exc := self._close_exc) is not None:
            err = JsonrpcConnectionClosedError(f'connection failed: {exc!r}')
            err.__cause__ = exc
            return err
        return JsonrpcConnectionClosedError('connection closed')

    def _error_response(self, req: Request, exc: BaseException) -> Response:
        return Response(
            req.id_value(),
            error=jsonrpc_error_for_exception(exc, include_details=self._include_error_details),
        )

    @staticmethod
    def _result_of(response: Response) -> ta.Any:
        if response.is_error:
            raise JsonrpcRemoteError(ta.cast(Error, response.error))
        return response.result

    ##
    # waiters

    def _add_waiter(self, req: Request, waiter: JsonrpcResponseWaiter) -> None:
        rid = req.id_value()
        if rid in self._waiters:
            raise ValueError(f'duplicate request id: {rid!r}')
        self._waiters[rid] = waiter

    def _pop_waiter(self, rid: Id) -> JsonrpcResponseWaiter | None:
        return self._waiters.pop(rid, None)

    def _fail_all_waiters(self, exc: BaseException) -> None:
        waiters = list(self._waiters.values())
        self._waiters.clear()
        for w in waiters:
            w.set_exception(exc)

    ##
    # session events

    def _handle_event(self, ev: ta.Any) -> None:
        """Demultiplex one event returned by the driver. Never raises for a well-formed event."""

        if isinstance(ev, Jpm.ResponseReceived):
            if (w := self._pop_waiter(ev.request.id_value())) is not None:
                w.set_response(ev.response)

        elif isinstance(ev, Jpm.RequestFailed):
            if (w := self._pop_waiter(ev.request.id_value())) is not None:
                w.set_exception(ev.exc)

        elif isinstance(ev, Jpm.RequestReceived):
            self._on_request_received(ev.request)

        elif isinstance(ev, Jpm.NotificationReceived):
            self._on_notification_received(ev.notification)

        elif isinstance(ev, Jpm.RequestHandlingAborted):
            self._on_request_handling_aborted(ev.request, ev.exc)

        elif isinstance(ev, Jpm.OutputPaused):
            self._on_output_writable(False)

        elif isinstance(ev, Jpm.OutputResumed):
            self._on_output_writable(True)

        elif isinstance(ev, Jpm.Sent):
            self._on_sent(ev.command)

        elif isinstance(ev, Jpm.Closed):
            self._mark_closed(ev.exc)

        elif isinstance(ev, BaseException):
            # Drivers may return a failure as output rather than raising it.
            self._mark_closed(ev)

        else:
            log.warning('Unexpected pipeline output: %r', ev)

    def _mark_closed(self, exc: BaseException | None) -> None:
        """Record closure and fail everything still waiting. Idempotent; the first reason wins."""

        if self._closed:
            return
        self._closed = True
        self._close_exc = exc

        self._fail_all_waiters(self._closed_error())

        try:
            self._on_closed(exc)
        except Exception:  # noqa
            log.exception('Error in close callback')

    ##
    # subclass hooks

    @abc.abstractmethod
    def _on_request_received(self, req: Request) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _on_notification_received(self, note: Request) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _on_request_handling_aborted(self, req: Request, exc: BaseException) -> None:
        raise NotImplementedError

    def _on_sent(self, cmd: Jpm.Command) -> None:
        pass

    def _on_output_writable(self, writable: bool) -> None:
        pass

    def _on_closed(self, exc: BaseException | None) -> None:
        pass


##


class BaseSyncJsonrpcConnection(BaseJsonrpcConnection, JsonrpcConnection, lang.Abstract):
    pass


class BaseAsyncJsonrpcConnection(BaseJsonrpcConnection, AsyncJsonrpcConnection, lang.Abstract):
    pass


##


TimeoutArg: ta.TypeAlias = float | None | type[NotSpecified]
