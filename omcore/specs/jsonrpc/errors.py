import typing as ta

from ... import dataclasses as dc
from ... import lang
from .types import Error
from .types import Id
from .types import NotSpecified


##


@dc.dataclass(frozen=True)
class KnownError:
    code: int
    message: str
    meaning: str

    def to_error(self, data: ta.Any = NotSpecified, *, message: str | None = None) -> Error:
        return Error(
            self.code,
            message if message is not None else self.message,
            data,
        )


class KnownErrors(lang.Namespace):
    PARSE_ERROR = KnownError(-32700, 'Parse error', 'Invalid JSON was received by the server.')
    INVALID_REQUEST = KnownError(-32600, 'Invalid Request', 'The JSON sent is not a valid Request object.')
    METHOD_NOT_FOUND = KnownError(-32601, 'Method not found', 'The method does not exist / is not available.')
    INVALID_PARAMS = KnownError(-32602, 'Invalid params', 'Invalid method parameter(s).')
    INTERNAL_ERROR = KnownError(-32603, 'Internal error', 'Internal JSON-RPC error.')


# The range -32000 to -32099 is reserved for implementation-defined server errors.
CUSTOM_ERROR_BASE = -32000
CUSTOM_ERROR_MIN = -32099

# Codes used by this implementation for its own server-side conditions, chosen from the reserved range.
SERVER_BUSY_ERROR_CODE = -32000
SERVER_SHUTTING_DOWN_ERROR_CODE = -32001
REQUEST_TIMED_OUT_ERROR_CODE = -32002
RESPONSE_TOO_LARGE_ERROR_CODE = -32003


##


class JsonrpcError(Exception):
    """Base class for all JSON-RPC related errors."""


class JsonrpcProtocolError(JsonrpcError):
    """The peer violated the protocol in a way the connection cannot recover from (framing desync, etc)."""


class JsonrpcInvalidMessageError(JsonrpcProtocolError):
    """Raised by the strict parsing functions when a value is not a valid JSON-RPC message."""

    def __init__(self, message: str, *, id: Id = None, looks_like_response: bool = False) -> None:  # noqa
        super().__init__(message)

        self.id = id
        self.looks_like_response = looks_like_response


class JsonrpcConnectionClosedError(JsonrpcError, ConnectionError):
    """The connection closed, or was already closed, before an operation could complete."""


class JsonrpcTimeoutError(JsonrpcError, TimeoutError):
    """An operation did not complete within its configured timeout."""


class JsonrpcMessageTooLargeError(JsonrpcError):
    """A message exceeded the configured maximum frame size."""


class JsonrpcTooManyRequestsError(JsonrpcError):
    """The local limit on concurrently pending outbound requests was reached."""


##


class JsonrpcErrorResponseError(JsonrpcError):
    """Base class for exceptions carrying a JSON-RPC error object."""

    def __init__(self, error: Error) -> None:
        super().__init__(f'{error.code}: {error.message}')

        self.error = error

    @property
    def code(self) -> int:
        return self.error.code

    @property
    def message(self) -> str:
        return self.error.message

    @property
    def data(self) -> ta.Any:
        return self.error.data


class JsonrpcRemoteError(JsonrpcErrorResponseError):
    """The peer answered a request with an error response."""


class JsonrpcMethodError(JsonrpcErrorResponseError):
    """
    Raised by a method handler to answer the request being handled with a specific error response.

    Any other exception escaping a handler is answered with a generic Internal Error and never leaks its details.
    """

    def __init__(
            self,
            code: int | KnownError,
            message: str | None = None,
            data: ta.Any = NotSpecified,
    ) -> None:
        if isinstance(code, KnownError):
            error = code.to_error(data, message=message)
        else:
            if message is None:
                raise TypeError('message is required with a numeric code')
            error = Error(code, message, data)

        super().__init__(error)
