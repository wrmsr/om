# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
A TCP port forwarder assembled from nothing but the host service and the relay: every connection accepted on the
listening endpoint is connected onward to the target, and the two are joined by a relay.
"""
import typing as ta

from .....sockets.endpoints import SocketEndpoint
from ...core import IoPipeline
from ...hosts.types import IoPipelineHost
from ...hosts.types import IoPipelineHostedDriver
from ...hosts.types import IoPipelineHostedListener
from ...hosts.types import IoPipelineHostError
from ...hosts.types import IoPipelineHostTransportInfo
from ..handlers import IoPipelineRelay


##


class IoPipelinePortForwarder:
    def __init__(
            self,
            host: IoPipelineHost,
            listen_endpoint: SocketEndpoint,
            target_endpoint: SocketEndpoint,
            *,
            connect_timeout_s: ta.Optional[float] = 10.,
    ) -> None:
        super().__init__()

        self._host = host
        self._target_endpoint = target_endpoint
        self._connect_timeout_s = connect_timeout_s

        self.failures: ta.List[IoPipelineHostError] = []

        self._listener = host.listen(listen_endpoint, self._accepted_spec)

    @property
    def listener(self) -> IoPipelineHostedListener:
        return self._listener

    @property
    def bound_endpoint(self) -> SocketEndpoint:
        return self._listener.bound_endpoint

    def _accepted_spec(self, info: IoPipelineHostTransportInfo) -> IoPipeline.Spec:
        """The accepted side is one end of a relay; its other end is the connection made onward."""

        relay = IoPipelineRelay()
        self._host.connect(
            self._target_endpoint,
            lambda target_info: relay.spec('b'),
            on_connected=self._connected,
            on_failed=self._failed,
            timeout_s=self._connect_timeout_s,
        )
        return relay.spec('a')

    def _connected(self, ctx: ta.Any, driver: IoPipelineHostedDriver) -> None:
        pass  # The relay joins the two by itself once both ends are attached.

    def _failed(self, ctx: ta.Any, exc: IoPipelineHostError) -> None:
        # The accepted side's relay end, its other side never attached, sits reading nothing; closing the listener's
        # connections is left to whoever runs the forwarder. The failure is recorded.
        self.failures.append(exc)

    def close(self) -> None:
        self._listener.close()
