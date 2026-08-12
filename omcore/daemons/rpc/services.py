import typing as ta

from ... import dataclasses as dc
from ..pidfiles import current_daemon_pidfile_info
from ..runtime import ActivityRejectedError
from ..runtime import DrainTimeoutError
from ..runtime import ServiceRuntime
from ..services import RuntimeService
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RpcHandler
from .server import RpcServer
from .server import RpcServerConfig
from .server import RpcServerDrainTimeoutError
from .server import RpcServerRuntime


##


class _ServiceRpcServerRuntime(RpcServerRuntime):
    def __init__(self, runtime: ServiceRuntime) -> None:
        super().__init__()

        self._runtime = runtime

    @property
    def shutdown_requested(self) -> bool:
        return self._runtime.shutdown.requested

    @property
    def drain_timeout_s(self) -> float | None:
        return self._runtime.config.drain_timeout_s

    def wait_shutdown(self) -> None:
        self._runtime.shutdown.wait()

    def request_shutdown(self, message: str) -> None:
        self._runtime.shutdown.request(message=message)

    def acquire_activity(self) -> ta.ContextManager[ta.Any] | None:
        try:
            return self._runtime.activity.acquire()
        except ActivityRejectedError:
            return None


class RpcService(RuntimeService['RpcService.Config']):
    """Adapts RpcServer to daemon ServiceRuntime lifecycle and activity."""

    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RuntimeService.Config):
        socket_path: str
        handler: RpcHandler

        socket_mode: int = 0o600
        connection_timeout_s: float | None = 30.
        max_frame_bytes: int = RPC_DEFAULT_MAX_FRAME_BYTES
        response_cache_size: int = 1_024
        backlog: int = 128

        def server_config(self) -> RpcServerConfig:
            return RpcServerConfig(
                socket_path=self.socket_path,
                handler=self.handler,
                socket_mode=self.socket_mode,
                connection_timeout_s=self.connection_timeout_s,
                max_frame_bytes=self.max_frame_bytes,
                response_cache_size=self.response_cache_size,
                backlog=self.backlog,
            )

        def __post_init__(self) -> None:
            self.server_config()

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _run_runtime(self, runtime: ServiceRuntime) -> None:
        pidfile_info = current_daemon_pidfile_info()
        try:
            RpcServer(self.config.server_config()).run(
                _ServiceRpcServerRuntime(runtime),
                instance_id=pidfile_info.instance_id if pidfile_info is not None else None,
            )
        except RpcServerDrainTimeoutError as exc:
            raise DrainTimeoutError(str(exc)) from exc
