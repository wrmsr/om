import asyncio
import typing as ta

from ... import dataclasses as dc
from ..runtime import ActivityRejectedError
from ..runtime import DrainTimeoutError
from ..runtime import ServiceRuntime
from ..services import RuntimeService
from .asyncio import AsyncHttpHandler
from .asyncio import AsyncioPipelineHttpServer
from .asyncio import AsyncioPipelineHttpServerConfig
from .dispatch import HttpHandler
from .dispatch import HttpHealthConfig
from .server import HttpServerRuntime
from .server import PipelineHttpServer
from .server import PipelineHttpServerConfig
from .server import PipelineHttpServerDrainTimeoutError


##


class _ServiceHttpServerRuntime(HttpServerRuntime):
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


##


class PipelineHttpService(RuntimeService['PipelineHttpService.Config']):
    """Adapt the synchronous pipeline HTTP host to ServiceRuntime."""

    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RuntimeService.Config):
        host: str
        port: int
        handler: HttpHandler

        health: HttpHealthConfig | None = HttpHealthConfig()
        connection_timeout_s: float | None = 30.
        max_request_body_bytes: int = 64 * 1024
        backlog: int = 128

        def server_config(self) -> PipelineHttpServerConfig:
            return PipelineHttpServerConfig(
                host=self.host,
                port=self.port,
                handler=self.handler,
                health=self.health,
                connection_timeout_s=self.connection_timeout_s,
                max_request_body_bytes=self.max_request_body_bytes,
                backlog=self.backlog,
            )

        def __post_init__(self) -> None:
            self.server_config()

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _run_runtime(self, runtime: ServiceRuntime) -> None:
        try:
            PipelineHttpServer(self.config.server_config()).run(
                _ServiceHttpServerRuntime(runtime),
            )
        except PipelineHttpServerDrainTimeoutError as exc:
            raise DrainTimeoutError(str(exc)) from exc


class AsyncioPipelineHttpService(RuntimeService['AsyncioPipelineHttpService.Config']):
    """Adapt the asyncio pipeline HTTP host to ServiceRuntime."""

    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RuntimeService.Config):
        host: str
        port: int
        handler: AsyncHttpHandler

        health: HttpHealthConfig | None = HttpHealthConfig()
        connection_timeout_s: float | None = 30.
        max_request_body_bytes: int = 64 * 1024
        backlog: int = 128

        def server_config(self) -> AsyncioPipelineHttpServerConfig:
            return AsyncioPipelineHttpServerConfig(
                host=self.host,
                port=self.port,
                handler=self.handler,
                health=self.health,
                connection_timeout_s=self.connection_timeout_s,
                max_request_body_bytes=self.max_request_body_bytes,
                backlog=self.backlog,
            )

        def __post_init__(self) -> None:
            self.server_config()

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _run_runtime(self, runtime: ServiceRuntime) -> None:
        try:
            asyncio.run(AsyncioPipelineHttpServer(self.config.server_config()).run(
                _ServiceHttpServerRuntime(runtime),
            ))
        except PipelineHttpServerDrainTimeoutError as exc:
            raise DrainTimeoutError(str(exc)) from exc
