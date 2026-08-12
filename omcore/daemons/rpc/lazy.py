import typing as ta
import uuid

from ... import lang
from ..lazy import LazyDaemon
from .client import RpcClient
from .protocol import RpcCallIndeterminateError
from .protocol import RpcUnavailableError


##


class _LazyRpcRetryError(RpcUnavailableError):
    pass


class LazyRpcClient(lang.Final):
    """Combines an RPC client with lazy daemon launch and safe same-instance replay."""

    def __init__(
            self,
            lazy_daemon: LazyDaemon,
            client: RpcClient,
    ) -> None:
        super().__init__()

        self._lazy_daemon = lazy_daemon
        self._client = client

    @property
    def lazy_daemon(self) -> LazyDaemon:
        return self._lazy_daemon

    @property
    def client(self) -> RpcClient:
        return self._client

    def call(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout: lang.TimeoutLike = lang.Timeout.DEFAULT,
    ) -> ta.Any:
        request = self._client.new_request(method, params)
        expected_instance_id: uuid.UUID | None = None

        def attempt() -> ta.Any:
            nonlocal expected_instance_id

            try:
                return self._client.call_request(
                    request,
                    expected_instance_id=expected_instance_id,
                )
            except RpcCallIndeterminateError as exc:
                if exc.actual_instance_id is not None:
                    raise
                expected_instance_id = exc.instance_id
                raise _LazyRpcRetryError(str(exc)) from exc

        return self._lazy_daemon.call(
            attempt,
            is_unavailable=lambda exc: isinstance(exc, RpcUnavailableError),
            timeout=timeout,
        )
