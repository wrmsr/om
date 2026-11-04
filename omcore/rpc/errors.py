# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The rpc error vocabulary.

Local errors are raised to callers. `RpcRemoteErrorData` is the wire shape of an error: a stable string code, the
remote exception type's name, a message, and optionally a traceback, which the receiving side raises as an
`RpcRemoteError`. Codes are plain strings so that both ends can be any mixture of versions and dialects; the ones the
toolbox itself emits are collected in `RpcErrorCodes`.
"""
import dataclasses as dc
import typing as ta

from ..lite.marshal import OBJ_MARSHALER_FIELD_KEY
from ..lite.namespaces import NamespaceClass


##


class RpcError(Exception):
    """Base class for all rpc errors."""


class RpcProtocolError(RpcError):
    """
    The peer violated the protocol in a way the connection cannot recover from: framing desync, malformed envelopes.
    """  # noqa


class RpcConnectionClosedError(RpcError, ConnectionError):
    """The connection closed, or was already closed, before an operation could complete."""


class RpcTimeoutError(RpcError, TimeoutError):
    """An operation did not complete within its configured timeout."""


class RpcMessageTooLargeError(RpcError, ValueError):
    """
    A message exceeded the configured maximum frame size. Sending one fails just that message, like any other value
    which cannot be encoded; receiving one is fatal to the connection, as the stream cannot be resynchronized past it.
    """


class RpcTooManyRequestsError(RpcError):
    """The local limit on concurrently pending outbound requests was reached."""


class RpcCancelledError(RpcError):
    """An in-flight request was cancelled: by the peer, by a timeout, or by the connection closing."""


class RpcMethodNotFoundError(RpcError):
    """Raised by a handler for a method it does not implement; answered on the wire as `method_not_found`."""

    def __init__(self, method: str) -> None:
        super().__init__(f'RPC method not found: {method!r}')

        self.method = method


class RpcUnexpectedMessageError(RpcProtocolError):
    """A message of an unexpected kind was received, such as a response to a request this side never issued."""


class RpcHandlerError(RpcError):
    """
    Raised by a handler to answer the request with exactly this error data - a code of its own, say, or an answer kept
    from an earlier attempt. Any other exception is answered as code `remote`.
    """

    def __init__(self, data: 'RpcRemoteErrorData') -> None:
        super().__init__(data.message)

        self.data = data


##


class RpcErrorCodes(NamespaceClass):
    """The error codes the toolbox itself emits. Handlers are free to use any other string."""

    # A handler raised an ordinary exception; `type` names it.
    REMOTE = 'remote'

    # The handler was cancelled before producing a result.
    CANCELLED = 'cancelled'

    METHOD_NOT_FOUND = 'method_not_found'

    # The result could not be encoded for the wire.
    RESULT_ENCODING = 'result_encoding'

    # The receiving session is at its in-flight limit.
    BUSY = 'busy'

    # The receiving session is closing.
    SHUTTING_DOWN = 'shutting_down'

    # Handling exceeded the receiving session's handling timeout.
    HANDLING_TIMEOUT = 'handling_timeout'

    # The result exceeded the frame limit.
    RESULT_TOO_LARGE = 'result_too_large'


##


@dc.dataclass(frozen=True)
class RpcRemoteErrorData:
    """The wire shape of an error. `remote_type` is spelled `type` on the wire."""

    code: str
    remote_type: str = dc.field(metadata={OBJ_MARSHALER_FIELD_KEY: 'type'})
    message: str
    traceback: ta.Optional[str] = None


class RpcRemoteError(RpcError):
    """The peer answered a request with an error."""

    def __init__(self, data: RpcRemoteErrorData) -> None:
        super().__init__(data.message)

        self.data = data

    def __str__(self) -> str:
        d = self.data
        return f'[{d.code}] {d.remote_type}: {d.message}'

    @property
    def code(self) -> str:
        return self.data.code

    @property
    def remote_type(self) -> str:
        return self.data.remote_type

    @property
    def remote_message(self) -> str:
        return self.data.message

    @property
    def remote_traceback(self) -> ta.Optional[str]:
        return self.data.traceback


class RpcRemoteCancelledError(RpcRemoteError):
    """The peer reported that handling of the request was cancelled."""


class RpcRemoteMethodNotFoundError(RpcRemoteError):
    """The peer does not implement the method."""


class RpcRemoteShuttingDownError(RpcRemoteError, RpcConnectionClosedError):
    """
    The peer answered that it is closing and will not handle the request. Also an `RpcConnectionClosedError`, since that
    is what it means for the caller: code which handles a lost connection handles this too.
    """


def rpc_exception_type_name(obj: ta.Union[BaseException, ta.Type[BaseException]]) -> str:
    """The qualified name error data carries for an exception's type, such as `builtins.FileNotFoundError`."""

    cls = obj if isinstance(obj, type) else type(obj)
    return f'{cls.__module__}.{cls.__qualname__}'


def rpc_remote_error_for_data(data: RpcRemoteErrorData) -> RpcRemoteError:
    """Builds the local exception a remote error is raised as, with subclasses for the codes callers tend to catch."""

    if data.code == RpcErrorCodes.CANCELLED:
        return RpcRemoteCancelledError(data)
    if data.code == RpcErrorCodes.METHOD_NOT_FOUND:
        return RpcRemoteMethodNotFoundError(data)
    if data.code == RpcErrorCodes.SHUTTING_DOWN:
        return RpcRemoteShuttingDownError(data)
    return RpcRemoteError(data)
