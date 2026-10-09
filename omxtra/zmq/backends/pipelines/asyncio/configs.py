from omcore import dataclasses as dc
from omcore.io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver


##


DEFAULT_DRIVER_CONFIG = PollAsyncioStreamIoPipelineDriver.Config(
    read_batch_max_bytes=64 * 1024,
)


@dc.dataclass(frozen=True)
class PipelinesBackendConfig:
    """Bounds and policies only the in-house backend can enforce."""

    driver: PollAsyncioStreamIoPipelineDriver.Config = DEFAULT_DRIVER_CONFIG

    max_queue_bytes: int = 32 * 1024 * 1024
    max_connections: int = 64
    max_peer_subscriptions: int = 1024
    max_command_size: int = 64 * 1024
    max_waiting_sends: int = 1024

    turn_output_budget: int = 64 * 1024

    connect_timeout: float = 10.

    def __post_init__(self) -> None:
        if min(
            self.max_queue_bytes,
            self.max_connections,
            self.max_command_size,
            self.max_waiting_sends,
            self.turn_output_budget,
        ) < 1:
            raise ValueError(self)
        if not self.connect_timeout > 0:
            raise ValueError(self.connect_timeout)


DEFAULT_PIPELINES_BACKEND_CONFIG = PipelinesBackendConfig()
