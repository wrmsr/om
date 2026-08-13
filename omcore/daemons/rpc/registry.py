import collections
import threading
import typing as ta

from ... import check
from ... import dataclasses as dc
from .pipelines.messages import RpcWireError
from .pipelines.messages import RpcWireResponse
from .protocol import RpcRequest


##


def rpc_protocol_error_response(request: RpcRequest, message: str) -> RpcWireError:
    return RpcWireError(
        client_id=request.client_id,
        request_id=request.request_id,
        code='protocol',
        remote_type='omcore.daemons.rpc.RpcProtocolError',
        message=message,
    )


def rpc_cache_full_response(request: RpcRequest) -> RpcWireError:
    return RpcWireError(
        client_id=request.client_id,
        request_id=request.request_id,
        code='remote',
        remote_type='omcore.daemons.rpc.RpcRequestCacheFullError',
        message='RPC request cache is full',
    )


##


class RpcResponseEntry:
    """A runtime-neutral completion shared by duplicate in-progress requests."""

    def __init__(self, request: RpcRequest) -> None:
        super().__init__()

        self._request = request
        self._condition = threading.Condition(threading.RLock())
        self._response: RpcWireResponse | None = None
        self._done_callbacks: list[ta.Callable[[RpcWireResponse], None]] = []

    @property
    def request(self) -> RpcRequest:
        return self._request

    @property
    def done(self) -> bool:
        with self._condition:
            return self._response is not None

    def result(self) -> RpcWireResponse:
        with self._condition:
            if self._response is None:
                raise RuntimeError('RPC response is not complete')
            return self._response

    def wait(self, timeout_s: float | None = None) -> RpcWireResponse:
        with self._condition:
            if not self._condition.wait_for(lambda: self._response is not None, timeout_s):
                raise TimeoutError('Timed out waiting for an in-progress RPC response')
            return ta.cast(RpcWireResponse, check.not_none(self._response))

    def add_done_callback(self, fn: ta.Callable[[RpcWireResponse], None]) -> None:
        with self._condition:
            if (response := self._response) is None:
                self._done_callbacks.append(fn)
                return

        fn(response)

    def _complete(self, response: RpcWireResponse) -> list[ta.Callable[[RpcWireResponse], None]]:
        with self._condition:
            if self._response is not None:
                raise RuntimeError('RPC response is already complete')
            self._response = response
            callbacks, self._done_callbacks = self._done_callbacks, []
            self._condition.notify_all()
            return callbacks


@dc.dataclass(frozen=True, kw_only=True)
class RpcResponseExecute:
    entry: RpcResponseEntry


@dc.dataclass(frozen=True, kw_only=True)
class RpcResponsePending:
    entry: RpcResponseEntry


@dc.dataclass(frozen=True, kw_only=True)
class RpcResponseReplay:
    response: RpcWireResponse


@dc.dataclass(frozen=True, kw_only=True)
class RpcResponseRejected:
    response: RpcWireError


RpcResponseClaim: ta.TypeAlias = (
    RpcResponseExecute |
    RpcResponsePending |
    RpcResponseReplay |
    RpcResponseRejected
)


##


class RpcResponseRegistry:
    """Claim stable request identities without imposing a waiting or execution runtime."""

    def __init__(self, *, max_entries: int) -> None:
        super().__init__()

        check.arg(max_entries > 0)
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._entries: collections.OrderedDict[tuple[str, str], RpcResponseEntry] = collections.OrderedDict()

    @property
    def max_entries(self) -> int:
        return self._max_entries

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def claim(self, request: RpcRequest) -> RpcResponseClaim:
        key = (request.client_id, request.request_id)
        with self._lock:
            if (entry := self._entries.get(key)) is not None:
                if entry.request != request:
                    return RpcResponseRejected(response=rpc_protocol_error_response(
                        request,
                        'RPC request id was reused with different request data',
                    ))
                self._entries.move_to_end(key)
                if entry.done:
                    return RpcResponseReplay(response=entry.result())
                return RpcResponsePending(entry=entry)

            if len(self._entries) >= self._max_entries:
                return RpcResponseRejected(response=rpc_cache_full_response(request))

            entry = RpcResponseEntry(request)
            self._entries[key] = entry
            return RpcResponseExecute(entry=entry)

    def complete(self, entry: RpcResponseEntry, response: RpcWireResponse) -> None:
        request = entry.request
        if response.client_id != request.client_id or response.request_id != request.request_id:
            raise ValueError('RPC response identity does not match its request')

        key = (request.client_id, request.request_id)
        with self._lock:
            if self._entries.get(key) is not entry:
                raise ValueError('RPC response entry does not belong to this registry')
            callbacks = entry._complete(response)  # noqa
            self._entries.move_to_end(key)

        first_error: BaseException | None = None
        for callback in callbacks:
            try:
                callback(response)
            except BaseException as exc:  # noqa
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error
