# ruff: noqa: UP006 UP007 UP045
from ..configs.snapshots import SystevisorConfigSnapshot
from ..platforms.runtime import SystevisorManagerRuntime
from ..platforms.runtime import SystevisorPreparedManagerRuntimeChange
from .configs import SystevisorConfigController
from .configs import SystevisorConfigParticipant
from .configs import SystevisorConfigPreparedChange


class SystevisorManagerConfigPreparedChange(SystevisorConfigPreparedChange):
    def __init__(self, change: SystevisorPreparedManagerRuntimeChange) -> None:
        self._change = change

    def commit(self) -> None:
        self._change.commit()

    def rollback(self) -> None:
        self._change.rollback()


class SystevisorManagerConfigParticipant(SystevisorConfigParticipant):
    def __init__(
            self,
            config_controller: SystevisorConfigController,
            manager_runtime: SystevisorManagerRuntime,
    ) -> None:
        self._manager_runtime = manager_runtime
        config_controller.add_participant(self)

    def prepare(self, snapshot: SystevisorConfigSnapshot) -> SystevisorConfigPreparedChange:
        return SystevisorManagerConfigPreparedChange(self._manager_runtime.prepare(snapshot.config.manager))
