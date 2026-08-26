import typing as ta

from omcore import dataclasses as dc

from .managers import PermissionsManager
from .types import DecidedPermissionState
from .types import PermissionAsker
from .types import PermissionDecider
from .types import PermissionMatchContext
from .types import PermissionRequestor
from .types import PermissionState
from .types import PermissionTarget


##


@ta.final
@dc.dataclass(frozen=True)
class StaticPermissionDecider(PermissionDecider):
    state: DecidedPermissionState

    async def decide(self, requestor: PermissionRequestor, target: PermissionTarget) -> DecidedPermissionState:
        return self.state


DENY_TOOL_PERMISSION_DECIDER: ta.Final = StaticPermissionDecider(PermissionState.DENY)


##


class StandardPermissionDecider(PermissionDecider):
    def __init__(
            self,
            *,
            manager: PermissionsManager,
            asker: PermissionAsker,
    ) -> None:
        super().__init__()

        self._manager = manager
        self._asker = asker

    async def decide(self, requestor: PermissionRequestor, target: PermissionTarget) -> DecidedPermissionState:
        if (m := self._manager.match(PermissionMatchContext(
            target,
            requestor=requestor,
        ))) is None:
            return PermissionState.DENY

        mr = m.result
        if mr is PermissionState.ALLOW or mr is PermissionState.DENY:
            return mr

        elif mr is PermissionState.ASK:
            return await self._asker.ask(requestor, target, m)

        else:
            raise ValueError(mr)
