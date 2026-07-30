import typing as ta

from omcore import dataclasses as dc

from .types import DecidedPermissionState
from .types import PermissionDecider
from .types import PermissionState
from .types import PermissionTarget


#


@ta.final
@dc.dataclass(frozen=True)
class StaticPermissionDecider(PermissionDecider):
    state: DecidedPermissionState

    async def decide(self, target: PermissionTarget) -> DecidedPermissionState:
        return self.state


DENY_TOOL_PERMISSION_DECIDER: ta.Final = StaticPermissionDecider(PermissionState.DENY)
