# ruff: noqa: UP006 UP007 UP045
from ..configs.snapshots import SystevisorConfigSnapshot
from .configs import SystevisorConfigController
from .configs import SystevisorConfigParticipant
from .configs import SystevisorConfigPreparedChange
from .http import SystevisorHttpServer


class SystevisorControlPlane(SystevisorConfigParticipant):
    def __init__(
            self,
            config_controller: SystevisorConfigController,
            http_server: SystevisorHttpServer,
    ) -> None:
        self._config_controller = config_controller
        self._http_server = http_server
        config_controller.add_participant(self)

    def prepare(self, snapshot: SystevisorConfigSnapshot) -> SystevisorConfigPreparedChange:
        return self._http_server.prepare_reconfigure(snapshot.config.api)

    def close(self) -> None:
        self._http_server.close()
